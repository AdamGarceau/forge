#!/usr/bin/env python3
"""
synth_usability.py — synthetic usability test (personas x tasks) via local Ollama.

Walks a described UI through each persona x task combination, instructing
the model to HUNT FOR FAILURE rather than be polite. Scores COMPLETED
(yes/partial/no) and CONFIDENCE (1-10), aggregates a weighted overall
usability score, and writes a markdown report with a ranked punch list.

Stdlib + curl only. No third-party dependencies.

Usage:
    python3 synth_usability.py --personas personas.md --ui ui.md --tasks tasks.md
    python3 synth_usability.py --personas personas.md --ui ui.md --tasks tasks.md \\
        --model gemma4:12b --endpoint http://localhost:11434 --out report.md

Personas file: same format as synth_survey.py (see personas.example.md) —
"## Segment N: Name (n=X, weight=Y)" blocks. `n=` is ignored here; `weight=`
drives the overall weighted score. Include an accessibility/screen-reader
persona if the UI needs to be judged for that (this tool just honors
whatever personas the file contains — it does not synthesize one).

UI file: free-form markdown/text description of the interface (see
ui.example.md).

Tasks file: "## Task N: Name" blocks, body = task description (see
tasks.example.md).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_OLLAMA_MODEL = "gemma4:12b"
# Hosted fallback when no local LLM is available. Sonnet 5 by default; pass
# --model claude-haiku-4-5 for the cheaper option.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5"
DEFAULT_ENDPOINT = "http://localhost:11434"
CURL_TIMEOUT_SECONDS = "300"
NUM_CTX = 16384
NUM_PREDICT = 1500
TEMPERATURE = 0.6

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
ANTHROPIC_MAX_TOKENS = 4096

SEGMENT_HEADER_RE = re.compile(
    r"Segment\s+\d+:\s*(.+?)\s*\((?:n=(\d+),\s*)?weight=([\d.]+)\)"
)
TASK_HEADER_RE = re.compile(r"Task\s+\d+:\s*(.+)")

ACCESSIBILITY_KEYWORDS = (
    "screen reader", "screen-reader", "accessib", "blind", "low vision",
    "low-vision", "voiceover", "nvda", "jaws", "keyboard-only", "keyboard only",
)

# Models often wrap these labels in markdown emphasis (e.g. "**COMPLETED:** Partial"
# or "### COMPLETED: No**"), putting *,_,# characters between the label and the
# value. [\s*_#]* absorbs any of that without requiring plain whitespace.
COMPLETED_RE = re.compile(r"COMPLETED\s*:[\s*_#]*\b(yes|partial|no)\b", re.I)
CONFIDENCE_RE = re.compile(r"CONFIDENCE\s*:[\s*_#]*\b(\d+)\b", re.I)
# The colon can land either side of closing markdown emphasis ("**PROBLEMS:**"
# or "**PROBLEMS**:") - a trailing character class covering #/*/_/:/whitespace
# in any order handles both without needing to anchor their relative order.
PROBLEMS_HEADING_RE = re.compile(r"^[ \t#*_]*PROBLEMS[ \t#*_:]*$", re.M)
NEXT_LABEL_RE = re.compile(r"(?:COMPLETED|CONFIDENCE)\s*:", re.I)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def parse_personas(path: Path):
    text = path.read_text()
    blocks = re.split(r"\n## ", "\n" + text)[1:]
    personas = []
    for block in blocks:
        header, _, body = block.partition("\n")
        m = SEGMENT_HEADER_RE.match(header.strip())
        if not m:
            continue
        personas.append({
            "name": m.group(1).strip(),
            "weight": float(m.group(3)),
            "body": body.strip(),
        })
    return personas


def parse_tasks(path: Path):
    text = path.read_text()
    blocks = re.split(r"\n## ", "\n" + text)[1:]
    tasks = []
    for block in blocks:
        header, _, body = block.partition("\n")
        m = TASK_HEADER_RE.match(header.strip())
        if not m:
            continue
        tasks.append({"name": m.group(1).strip(), "body": body.strip()})
    return tasks


def warn_if_no_accessibility_persona(personas):
    haystack = " ".join(p["name"].lower() + " " + p["body"].lower() for p in personas)
    if not any(kw in haystack for kw in ACCESSIBILITY_KEYWORDS):
        eprint(
            "WARNING: no persona in the personas file appears to be an "
            "accessibility/screen-reader user. Usability failures for those "
            "users won't be caught. Consider adding one (see personas.example.md)."
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
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
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


def build_system_prompt(persona):
    return (
        f"You are usability-testing a web app AS this specific user. {persona['body']}\n\n"
        "CRITICAL: your job is to HUNT FOR FAILURE, not to be nice. Real users struggle; "
        "find every place THIS user would hesitate, misread, get lost, or give up. If you're "
        "unsure whether something is a problem, treat it as a problem. Praising a broken flow "
        "helps no one. A walkthrough that finds zero problems is a failed walkthrough."
    )


def build_user_prompt(ui_text, task):
    return (
        f"THE APP:\n{ui_text}\n\nTASK: {task['name']} - {task['body']}\n\n"
        "Walk through it step by step AS this user. For each step say what you look for, "
        "what you click, and where you hesitate or fail. Then give:\n"
        "- PROBLEMS: a bulleted list of concrete usability problems for THIS user (be specific).\n"
        "- COMPLETED: yes / partial / no - could this user finish the task?\n"
        "- CONFIDENCE: 1-10 how confident this user feels they did it right.\n"
        "Put the score on its own line as CONFIDENCE: N"
    )


def extract_problems(text):
    start_m = PROBLEMS_HEADING_RE.search(text)
    if not start_m:
        return []
    rest = text[start_m.end():]
    end_m = NEXT_LABEL_RE.search(rest)
    block = rest[:end_m.start()] if end_m else rest
    bullets = re.findall(r"^[ \t]*[-*]\s+(.+)$", block, re.M)
    return [b.strip() for b in bullets if b.strip()]


def render_report(model, personas, tasks, results, overall, by_persona_avg):
    lines = []
    lines.append("# Synthetic Usability Report\n")
    lines.append(f"**Model:** `{model}`  ")
    lines.append(f"**Personas:** {len(personas)}  ")
    lines.append(f"**Tasks:** {len(tasks)}\n")

    fails = [r for r in results if r["completed"] in ("no", "partial")]
    lines.append(f"## Overall Usability Score: {overall if overall is not None else 'N/A'} / 10\n")
    lines.append(f"Incomplete task-runs: {len(fails)} / {len(results)}\n")

    lines.append("## Per-Persona Summary\n")
    lines.append("| Persona | weight | avg confidence | task-runs |")
    lines.append("|---|---|---|---|")
    for p in personas:
        avg = by_persona_avg.get(p["name"])
        n_runs = sum(1 for r in results if r["persona"] == p["name"])
        lines.append(f"| {p['name']} | {p['weight']} | {avg if avg is not None else 'N/A'} | {n_runs} |")
    lines.append("")

    lines.append("## Ranked Punch List\n")
    lines.append("Incomplete or low-confidence task-runs, worst first (by weight, then score):\n")
    ranked = sorted(
        fails,
        key=lambda r: (-r["weight"], r["score"] if r["score"] is not None else 0),
    )
    if not ranked:
        lines.append("_No incomplete task-runs - nothing to rank. (Re-check: a walkthrough with zero "
                      "problems anywhere is itself suspect.)_\n")
    else:
        for i, r in enumerate(ranked, 1):
            lines.append(f"{i}. **[{r['persona']}]** {r['task']} "
                         f"— completed: {r['completed']}, confidence: {r['score']}")
            for prob in r["problems"]:
                lines.append(f"   - {prob}")
        lines.append("")

    lines.append("---\n")
    lines.append("## Full Walkthroughs\n")
    for r in results:
        lines.append(f"### {r['persona']} / {r['task']}\n")
        lines.append(r["raw"] or "_FAILED - no response._")
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
        description="Run personas x tasks through a failure-hunting synthetic usability test via local Ollama.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--personas", required=True, help="Path to personas markdown file.")
    ap.add_argument("--ui", required=True, help="Path to a markdown/text file describing the UI.")
    ap.add_argument("--tasks", required=True, help="Path to a markdown file listing core tasks.")
    ap.add_argument("--provider", choices=["auto", "ollama", "anthropic"], default="auto",
                     help="Which backend to use. 'auto' (default): local Ollama if reachable, "
                          "else hosted Claude if ANTHROPIC_API_KEY is set.")
    ap.add_argument("--model", default=None,
                     help="Model tag. Defaults per provider: "
                          f"'{DEFAULT_OLLAMA_MODEL}' (ollama), '{DEFAULT_ANTHROPIC_MODEL}' (anthropic). "
                          "For the cheaper hosted option pass --model claude-haiku-4-5.")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"Ollama endpoint (default: {DEFAULT_ENDPOINT}).")
    ap.add_argument("--out", default="usability-report.md", help="Output report path (markdown).")
    args = ap.parse_args()

    personas_path = Path(args.personas).expanduser()
    ui_path = Path(args.ui).expanduser()
    tasks_path = Path(args.tasks).expanduser()
    for p, label in ((personas_path, "personas"), (ui_path, "ui"), (tasks_path, "tasks")):
        if not p.is_file():
            eprint(f"FATAL: {label} file not found: {p}")
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
            eprint("FATAL: no LLM backend available.")
            eprint("  - Local: start Ollama (see SETUP.md), or")
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

    personas = parse_personas(personas_path)
    if not personas:
        eprint(f"FATAL: no personas parsed from {personas_path}.")
        eprint('  Expected headers like: "## Segment 1: Name (n=500, weight=0.5)"')
        sys.exit(1)
    warn_if_no_accessibility_persona(personas)

    tasks = parse_tasks(tasks_path)
    if not tasks:
        eprint(f"FATAL: no tasks parsed from {tasks_path}.")
        eprint('  Expected headers like: "## Task 1: Name"')
        sys.exit(1)

    ui_text = ui_path.read_text().strip()

    print(f"Personas: {len(personas)}  Tasks: {len(tasks)}  Model: {model} @ {source}\n")

    results = []
    total_runs = len(personas) * len(tasks)
    run_i = 0
    for persona in personas:
        system = build_system_prompt(persona)
        for task in tasks:
            run_i += 1
            user = build_user_prompt(ui_text, task)
            try:
                out = generate(provider, args.endpoint, model, system, user)
            except Exception as e:
                print(f"[{run_i}/{total_runs}] {persona['name'][:24]:24} {task['name'][:28]:28} -> ERROR: {e}", flush=True)
                results.append({
                    "persona": persona["name"], "weight": persona["weight"], "task": task["name"],
                    "score": None, "completed": "?", "problems": [], "raw": None,
                })
                continue
            score_m = CONFIDENCE_RE.search(out)
            score = int(score_m.group(1)) if score_m else None
            comp_m = COMPLETED_RE.search(out)
            completed = comp_m.group(1).lower() if comp_m else "?"
            results.append({
                "persona": persona["name"], "weight": persona["weight"], "task": task["name"],
                "score": score, "completed": completed, "problems": extract_problems(out), "raw": out,
            })
            print(f"[{run_i}/{total_runs}] {persona['name'][:24]:24} {task['name'][:28]:28} "
                  f"-> {completed:7} conf {score}", flush=True)

    scored = [r for r in results if r["score"] is not None]
    by_persona = {}
    for r in scored:
        by_persona.setdefault(r["persona"], []).append(r["score"])
    by_persona_avg = {name: round(sum(s) / len(s), 1) for name, s in by_persona.items()}

    overall_sum, weight_sum = 0.0, 0.0
    for persona in personas:
        avg = by_persona_avg.get(persona["name"])
        if avg is not None:
            overall_sum += avg * persona["weight"]
            weight_sum += persona["weight"]
    overall = round(overall_sum / weight_sum, 2) if weight_sum else None

    report = render_report(model, personas, tasks, results, overall, by_persona_avg)
    out_path = write_report(report, args.out)

    fails = [r for r in results if r["completed"] in ("no", "partial")]
    print(f"\nReport written to {out_path}")
    print(f"OVERALL_SCORE: {overall}  |  incomplete task-runs: {len(fails)}/{len(results)}")
    if not scored:
        sys.exit(2)


if __name__ == "__main__":
    main()
