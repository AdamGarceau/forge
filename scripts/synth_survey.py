#!/usr/bin/env python3
"""
synth_survey.py — synthetic-audience concept/copy survey.

Reads a personas file (markdown, one "## Segment N: Name (n=X, weight=Y)"
block per audience segment), sends each segment's persona profile + the
concept being tested to a local Ollama model, and produces a
population-weighted resonance score plus a full markdown report.

Stdlib + curl only. No third-party dependencies.

Usage:
    python3 synth_survey.py --personas personas.md --concept "A free tool that..."
    python3 synth_survey.py --personas personas.md --concept @concept.txt --n 1000
    python3 synth_survey.py --personas personas.md --concept "..." \\
        --model gemma4:12b --endpoint http://localhost:11434 --out report.md

Personas file format (see personas.example.md):

    ## Segment 1: Name (n=500, weight=0.5)
    **Profile:** ...
    **Psychographics:** ...
    **Decision Factors:** ...
    **Language Patterns:** ...
    **Top Objections:** ...

    ## Segment 2: Name (n=300, weight=0.3)
    ...

`n=` is the segment's reference population count in the persona file;
`weight=` is its population share and is what actually drives the
overall weighted score. Pass --n to rescale how many respondents each
segment is asked to simulate (effective_n = round(weight * total_n))
without having to hand-edit the persona file.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_OLLAMA_MODEL = "gemma4:12b"
# When no local LLM is available, fall back to a hosted Claude model. Sonnet 5 is
# the default (best persona quality; a survey is only a handful of calls, so the
# cost is negligible); pass --model claude-haiku-4-5 for the cheaper option.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_ENDPOINT = "http://localhost:11434"
DEFAULT_N = 1000
MAX_ATTEMPTS = 2
RETRY_SLEEP_SECONDS = 5
CURL_TIMEOUT_SECONDS = "600"
NUM_CTX = 16384
NUM_PREDICT = 4000
TEMPERATURE = 0.7

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
ANTHROPIC_MAX_TOKENS = 4096

SEGMENT_HEADER_RE = re.compile(
    r"Segment\s+\d+:\s*(.+?)\s*\((?:n=(\d+),\s*)?weight=([\d.]+)\)"
)
# Tolerate markdown emphasis between the label and the value (e.g. "**RESONANCE:** 7.2")
RESONANCE_RE = re.compile(r"RESONANCE\s*:[\s*_#]*\b([\d.]+)", re.I)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def resolve_text_or_file(value: str) -> str:
    """Support '--concept @path/to/file.md' as well as inline text."""
    if value.startswith("@"):
        path = Path(value[1:]).expanduser()
        if not path.is_file():
            eprint(f"FATAL: concept file not found: {path}")
            sys.exit(1)
        return path.read_text().strip()
    return value


def parse_personas(path: Path, total_n: int):
    text = path.read_text()
    blocks = re.split(r"\n## ", "\n" + text)[1:]
    segments = []
    for block in blocks:
        header, _, body = block.partition("\n")
        m = SEGMENT_HEADER_RE.match(header.strip())
        if not m:
            continue
        name = m.group(1).strip()
        weight = float(m.group(3))
        declared_n = int(m.group(2)) if m.group(2) else None
        effective_n = round(weight * total_n) if total_n else (declared_n or 0)
        segments.append({
            "name": name,
            "declared_n": declared_n,
            "n": effective_n or declared_n or 1,
            "weight": weight,
            "body": body.strip(),
        })
    return segments


def build_system_prompt(segment, concept_label):
    return (
        f"You are simulating the {segment['name']} segment of {concept_label}'s "
        "target audience.\n"
        "You have deeply internalized the following persona profile and must "
        "respond AS these customers - aggregating their likely reactions across "
        "the whole segment.\n\n"
        f"PERSONA PROFILE:\n{segment['body']}\n\n"
        "Respond only as these people would. Use their language patterns. "
        "Do not break character or speak as a marketer."
    )


def build_user_prompt(segment, concept_text):
    return (
        f"You are simulating {segment['n']} respondents from the {segment['name']} "
        "segment.\n"
        f"Respond AS these {segment['n']} people - aggregate their likely reactions.\n\n"
        f"CONCEPT/COPY BEING TESTED:\n---\n{concept_text}\n---\n\n"
        "Answer each question with percentage distributions and 2-3 representative "
        "quotes (in this segment's real voice).\n\n"
        "Q1: FIRST IMPRESSION - % positive / neutral / negative + top 3 reactions w/ quotes.\n"
        "Q2: KEY OBJECTIONS - top 3 reasons to hesitate or dismiss; objection, % who cite, quote.\n"
        "Q3: WHAT RESONATES - top 3 elements that work; element, % who respond, quote.\n"
        "Q4: CALL TO ACTION - % who would act / consider / ignore. What would make more act?\n"
        "Q5: COMPETITIVE COMPARISON - Better / Same / Worse vs what they expect (an incumbent, "
        "a manual workaround, or nothing), with reasoning.\n"
        "Q6: VALUE PROP MATCH - rate how well the copy hits each top decision factor (1-5).\n\n"
        "ALSO provide:\n"
        "- COPY RESONANCE SCORE (1-10): overall resonance with THIS segment (one decimal ok).\n"
        "- TOP STRENGTH: the single part that works best.\n"
        "- TOP WEAKNESS: what falls flat or could backfire.\n"
        "- WHAT WOULD MAKE THIS A 10/10: the 1-3 most important, concrete, specific changes.\n"
        "- ONE-LINE VERDICT: Yes / Lukewarm / No + brief why.\n\n"
        "Format as clean markdown with a header per question. Use tables for distributions.\n"
        "Put the COPY RESONANCE SCORE on its own line as: RESONANCE: N.N"
    )


def call_ollama(endpoint, model, system_prompt, user_prompt):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "think": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_predict": NUM_PREDICT,
            "num_ctx": NUM_CTX,
        },
    })
    r = subprocess.run(
        ["curl", "-s", "--max-time", CURL_TIMEOUT_SECONDS,
         f"{endpoint}/api/chat",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"curl failed (exit {r.returncode}): {r.stderr.strip()}")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"non-JSON response from Ollama: {r.stdout[:300]!r}")
    if "message" not in data:
        raise RuntimeError(f"unexpected Ollama response: {json.dumps(data)[:300]}")
    return data["message"]["content"]


def _anthropic_post(api_key, body):
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=int(CURL_TIMEOUT_SECONDS)) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_anthropic(model, system_prompt, user_prompt):
    """Hosted-Claude backend (raw HTTP, stdlib only — no SDK/pip install)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    body = {
        "model": model,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "stream": False,
        # Direct answers, no extended thinking — keeps the full token budget for
        # the structured survey output. Retried without this field if a model
        # rejects it.
        "thinking": {"type": "disabled"},
    }
    try:
        data = _anthropic_post(api_key, body)
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")
        if e.code == 400 and "thinking" in msg.lower():
            body.pop("thinking", None)
            try:
                data = _anthropic_post(api_key, body)
            except urllib.error.HTTPError as e2:
                raise RuntimeError(
                    f"Anthropic API HTTP {e2.code}: {e2.read().decode('utf-8', 'replace')[:300]}")
        else:
            raise RuntimeError(f"Anthropic API HTTP {e.code}: {msg[:300]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Anthropic API connection error: {e.reason}")
    if data.get("stop_reason") == "refusal":
        raise RuntimeError("Anthropic API declined the request (stop_reason=refusal)")
    for block in data.get("content", []):
        if block.get("type") == "text" and block.get("text"):
            return block["text"]
    raise RuntimeError(f"no text in Anthropic response: {json.dumps(data)[:300]}")


def generate(provider, endpoint, model, system_prompt, user_prompt):
    if provider == "anthropic":
        return call_anthropic(model, system_prompt, user_prompt)
    return call_ollama(endpoint, model, system_prompt, user_prompt)


def ollama_reachable(endpoint):
    ping = subprocess.run(
        ["curl", "-s", "--max-time", "5", f"{endpoint}/api/tags"],
        capture_output=True, text=True,
    )
    return ping.returncode == 0 and bool(ping.stdout)


def render_report(concept_text, model, source, results, overall):
    lines = []
    lines.append("# Synthetic Survey Report\n")
    lines.append("**Concept/copy tested:**\n")
    lines.append(f"> {concept_text}\n")
    lines.append(f"**Model:** `{model}` via `{source}`  ")
    lines.append(f"**Segments:** {len(results)}\n")
    lines.append(f"## Overall Score: {overall if overall is not None else 'N/A'} / 10\n")
    lines.append("| Segment | n | weight | Resonance |")
    lines.append("|---|---|---|---|")
    for r in results:
        score = r["score"] if r["score"] is not None else "FAILED"
        lines.append(f"| {r['segment']} | {r['n']} | {r['weight']} | {score} |")
    lines.append("\n---\n")
    for r in results:
        lines.append(f"## Segment: {r['segment']} (n={r['n']}, weight={r['weight']})\n")
        lines.append(r["content"] or "_SEGMENT FAILED - no response._")
        lines.append("\n---\n")
    return "\n".join(lines)


def write_report(report, out):
    """Write the report, creating parent dirs. On failure, fall back to cwd so an
    expensive run is never lost to a bad --out path."""
    out_path = Path(out).expanduser()
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report)
        return out_path
    except OSError as e:
        fallback = Path.cwd() / Path(out).name
        eprint(f"WARNING: could not write to {out_path} ({e}). Saving to {fallback} instead.")
        fallback.write_text(report)
        return fallback


def main():
    ap = argparse.ArgumentParser(
        description="Run a concept/copy through a synthetic, segmented audience survey via local Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--personas", required=True, help="Path to personas markdown file.")
    ap.add_argument("--concept", required=True,
                     help='Concept/copy text to test, or "@path/to/file.md" to read from a file.')
    ap.add_argument("--provider", choices=["auto", "ollama", "anthropic"], default="auto",
                     help="Which backend to use. 'auto' (default): local Ollama if reachable, "
                          "else hosted Claude if ANTHROPIC_API_KEY is set.")
    ap.add_argument("--model", default=None,
                     help="Model tag. Defaults per provider: "
                          f"'{DEFAULT_OLLAMA_MODEL}' (ollama), '{DEFAULT_ANTHROPIC_MODEL}' (anthropic). "
                          "For the cheaper hosted option pass --model claude-haiku-4-5.")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"Ollama endpoint (default: {DEFAULT_ENDPOINT}).")
    ap.add_argument("--n", type=int, default=DEFAULT_N,
                     help=f"Total simulated population; segment sizes are weight * n (default: {DEFAULT_N}).")
    ap.add_argument("--out", default="synth-survey-report.md", help="Output report path (markdown).")
    ap.add_argument("--concept-label", default="the concept",
                     help='What to call the thing being tested in prompts (default: "the concept").')
    args = ap.parse_args()

    personas_path = Path(args.personas).expanduser()
    if not personas_path.is_file():
        eprint(f"FATAL: personas file not found: {personas_path}")
        sys.exit(1)

    concept_text = resolve_text_or_file(args.concept)
    if not concept_text.strip():
        eprint("FATAL: concept text is empty.")
        sys.exit(1)

    # Resolve which backend to use.
    provider = args.provider
    have_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if provider == "auto":
        if ollama_reachable(args.endpoint):
            provider = "ollama"
        elif have_key:
            provider = "anthropic"
            eprint(f"Ollama not reachable at {args.endpoint} — falling back to hosted Claude.")
        else:
            eprint(f"FATAL: no LLM backend available.")
            eprint(f"  - Local: start Ollama (see SETUP.md), or")
            eprint(f"  - Hosted: export ANTHROPIC_API_KEY to use Claude ({DEFAULT_ANTHROPIC_MODEL}).")
            sys.exit(1)
    elif provider == "ollama":
        if not ollama_reachable(args.endpoint):
            eprint(f"FATAL: Ollama not reachable at {args.endpoint}")
            eprint("  - Is Ollama running? Try: ollama serve")
            eprint("  - Or use hosted Claude: --provider anthropic (needs ANTHROPIC_API_KEY).")
            eprint("  - See SETUP.md for install/verify steps.")
            sys.exit(1)
    elif provider == "anthropic" and not have_key:
        eprint("FATAL: --provider anthropic requires ANTHROPIC_API_KEY to be set.")
        sys.exit(1)

    model = args.model or (DEFAULT_ANTHROPIC_MODEL if provider == "anthropic" else DEFAULT_OLLAMA_MODEL)
    source = "Anthropic API" if provider == "anthropic" else args.endpoint

    segments = parse_personas(personas_path, args.n)
    if not segments:
        eprint(f"FATAL: no segments parsed from {personas_path}.")
        eprint('  Expected headers like: "## Segment 1: Name (n=500, weight=0.5)"')
        sys.exit(1)

    print(f"Parsed {len(segments)} segment(s) from {personas_path.name}. Model: {model} @ {source}\n")

    results = []
    for i, seg in enumerate(segments, 1):
        content, score = None, None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                content = generate(
                    provider, args.endpoint, model,
                    build_system_prompt(seg, args.concept_label),
                    build_user_prompt(seg, concept_text),
                )
                m = RESONANCE_RE.search(content)
                if m:
                    score = float(m.group(1))
                    break
                print(f"[{i}/{len(segments)}] {seg['name']}: no RESONANCE line (attempt {attempt})", flush=True)
            except Exception as e:
                print(f"[{i}/{len(segments)}] {seg['name']}: attempt {attempt} failed: {e}", flush=True)
                if attempt < MAX_ATTEMPTS:
                    time.sleep(RETRY_SLEEP_SECONDS)
        results.append({
            "segment": seg["name"], "n": seg["n"], "weight": seg["weight"],
            "score": score, "content": content,
        })
        print(f"[{i}/{len(segments)}] {seg['name']} complete - resonance {score}", flush=True)

    scored = [r for r in results if r["score"] is not None]
    overall = (
        round(sum(r["score"] * r["weight"] for r in scored) /
              max(sum(r["weight"] for r in scored), 1e-9), 2)
        if scored else None
    )

    report = render_report(concept_text, model, source, results, overall)
    out_path = write_report(report, args.out)

    print(f"\nReport written to {out_path}")
    print(f"OVERALL_SCORE: {overall}")
    if not scored:
        sys.exit(2)


if __name__ == "__main__":
    main()
