#!/usr/bin/env python3
"""The 90% MVP gates: checks a run's artifacts can't fake (forge 1.11, 2026-10-18).

Adam, 2026-10-18: "Fix forge. I'd actually like a product to be 90% MVP." and "It's
supposed to 'one-shot' code projects. It should be good enough for the ICP, and then
I can make it perfect after that by adding or refining features."

The audit (~/forge-reviews/MVP-READINESS-2026-10-18.md) measured ~60% at first
hand-off. Its failure classes, and the check here that refuses each:

    looks done, doesn't work (5 runs)      dead_controls_errs   DEAD-CONTROLS.md
    fine in sim, broken on device (6)      real_target_errs     REAL-TARGET.md + proof/ newer than the build
    feature Adam assumed, missing (6)      forge_spec.check_assumed (Stage S, SPEC.md ## Assumed features)
    domain content wrong (4)               domain_truth_errs    DOMAIN-TRUTH.md + a sourced ledger
    wrong delivery mode (4)                mode_errs            validation/05-verdict.md Delivery mode
    ICP can't do the job on hand-off       icp_errs             ICP-WALKTHROUGH.md, every SPEC core job done
    gemma4:12b judge fabricated            judge_errs           every judged file names a cloud/claude judge
                                                                and quotes its evidence

Each function returns a list of problems; empty means the artifact verifies. A
problem only a person can clear starts with "HUMAN:" so the driver (forge_driver.py)
stops with one exact ask instead of looping a worker at it.

Stdlib only, so the live skill and the product carry the same file. Formats are in
references/mvp90-gates.md.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_spec as sp  # noqa: E402  (section, field, table, col, words)

REAL_TARGET, DEAD_CONTROLS, ICP_WALK, DOMAIN_TRUTH = (
    "REAL-TARGET.md", "DEAD-CONTROLS.md", "ICP-WALKTHROUGH.md", "DOMAIN-TRUTH.md")

DEVICE_TARGETS = ("ios", "android", "game", "desktop")
AGENT_TARGETS = ("web", "cli", "sheet", "automation")
TARGETS = DEVICE_TARGETS + AGENT_TARGETS
MODES = ("native app", "web", "cli", "sheet", "automation", "desktop", "game")
DRIVERS = ("playwright", "xcuitest", "device-walk", "cli-sweep", "computer-use")
MEDIA_EXT = (".png", ".jpg", ".jpeg", ".heic", ".mov", ".mp4", ".gif", ".webp", ".m4v")
FAKE_INPUT = re.compile(r"(^|/)(tests?|fixtures?|samples?|dummy|mock|fake)(/|_|\.|$)", re.I)

# A judge that is only a local model is not a judge (the audit caught gemma4:12b
# inventing evidence). A cloud or claude model has to sign the verdict.
LOCAL_JUDGE = re.compile(r"gemma|llama|qwen|mistral|phi\d|deepseek|ollama|\blocal\b|e4b|minicpm", re.I)
CLOUD_JUDGE = re.compile(r"claude|sonnet|opus|haiku|fable|gemini|gpt|\bo[134]\b|jev|cloud", re.I)

SRC_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".swift", ".kt", ".java", ".go", ".rs",
           ".html", ".css", ".vue", ".svelte", ".gd", ".cs", ".lua", ".dart", ".rb", ".php", ".sh")
SKIP_DIRS = {".git", "node_modules", ".planning", "proof", "validation", "dist", "build", ".build",
             "__pycache__", ".venv", "venv", "DerivedData", ".next", ".pytest_cache", "Pods", ".reggie"}


def rd(root, name):
    return sp.rd(os.path.join(root, name))


def last_build(root, cap=20000):
    """Epoch of the newest source file under root: the build every proof must be newer than."""
    newest, n = 0.0, 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        for f in files:
            if f.endswith(SRC_EXT):
                n += 1
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(d, f)))
                except OSError:
                    pass
                if n >= cap:
                    return newest
    return newest


def _stale(root, rel, built):
    p = os.path.join(root, rel)
    return built and os.path.getmtime(p) + 1 < built


def _when(epoch):
    return dt.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %-I:%M %p") if epoch else "?"


def core_jobs(root):
    """The SPEC.md `## Core jobs` ids (J1, J2, ...), in order."""
    return re.findall(r"^\s*[-*\d.)\s]*\**(J\d+)\b", sp.section(rd(root, sp.SPEC) or "", "Core jobs"), re.M)


def judge_errs(text, name):
    j = sp.field(text, "Judge")
    if not j:
        return ["%s needs `Judge: <model>`: who ruled, so a local-only verdict can't hide" % name]
    if not CLOUD_JUDGE.search(j):
        return ["%s judge is %r: a gate verdict can't rest on a local model alone (the audit caught "
                "gemma4:12b fabricating). Re-judge with claude or a cloud model" % (name, j)]
    return []


def quoted(cell, n=3):
    """An evidence cell has to quote what it saw: text in quotes, n+ words."""
    m = re.search(r"[\"“](.+?)[\"”]", cell or "")
    return bool(m) and sp.words(m.group(1)) >= n


# ---------------------------------------------------------------- 1. real target
def http_status(url, timeout=10):
    """Live URL check. Tests replace this function."""
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "forge-real-target/1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def real_target_errs(root, built=None):
    """Proof on the real target, newer than the last build. Device targets need a person: HUMAN."""
    text = rd(root, REAL_TARGET)
    built = last_build(root) if built is None else built
    if text is None:
        return ["HUMAN: no %s yet. Proof on the real target is owed before hand-off "
                "(references/mvp90-gates.md #1)" % REAL_TARGET]
    errs = []
    target = sp.field(text, "Target").lower().split()[0] if sp.field(text, "Target") else ""
    if target not in TARGETS:
        return ["%s needs `Target:` one of %s" % (REAL_TARGET, ", ".join(TARGETS))]
    head, rows = sp.table(sp.section(text, "Proof"))
    pc = sp.col(head, "proof", "file")
    if not pc or not rows:
        errs.append("%s ## Proof needs a table: | Core job | Proof file | What it shows |" % REAL_TARGET)
        rows = []
    jc = sp.col(head, "core job", "job")
    if target in DEVICE_TARGETS:
        dev = sp.field(text, "Device")
        if not dev or re.search(r"simulat|emulat|preview|xcode", dev, re.I):
            errs.append("HUMAN: %s `Device:` must be the real %s device (got %r); a simulator is not the target"
                        % (REAL_TARGET, target, dev))
        for r in rows:
            f = r[pc].strip("` ")
            if not f.lower().endswith(MEDIA_EXT):
                errs.append("%s: %r is not a screenshot or video from the device" % (REAL_TARGET, f))
            elif not os.path.exists(os.path.join(root, f)):
                errs.append("HUMAN: proof file %s is missing; send the screenshot/video from the device" % f)
            elif _stale(root, f, built):
                errs.append("HUMAN: proof %s predates the last build (%s); re-shoot it on the new build"
                            % (f, _when(built)))
    else:
        if target == "web":
            url = sp.field(text, "URL")
            if not url.startswith("http"):
                errs.append("%s: a web target needs `URL: https://...` (the live site)" % REAL_TARGET)
            else:
                code = http_status(url)
                if not 200 <= code < 400:
                    errs.append("%s: live check of %s returned %s, not 2xx/3xx" % (REAL_TARGET, url, code or "no answer"))
        for r in rows:
            parts = [x.strip("` ") for x in re.split(r"\s*(?:->|→)\s*", r[pc])]
            if target in ("cli", "sheet", "automation") and len(parts) != 2:
                errs.append("%s: %s proof is `real input -> real output`, got %r" % (REAL_TARGET, target, r[pc]))
                continue
            for f in parts:
                if FAKE_INPUT.search(f):
                    errs.append("%s: %s is a test fixture, not real data from the real job" % (REAL_TARGET, f))
                elif not os.path.exists(os.path.join(root, f)):
                    errs.append("%s: proof file %s is missing" % (REAL_TARGET, f))
            out = parts[-1]
            if os.path.exists(os.path.join(root, out)) and _stale(root, out, built):
                errs.append("%s: %s predates the last build (%s); re-run it on the current build"
                            % (REAL_TARGET, out, _when(built)))
        jobs = core_jobs(root)
        if jc and jobs:
            have = {re.match(r"\s*(J\d+)", r[jc]).group(1) for r in rows if re.match(r"\s*(J\d+)", r[jc])}
            miss = [j for j in jobs if j not in have]
            if miss:
                errs.append("%s: no real-target proof for core job%s %s" % (REAL_TARGET, "s" if len(miss) > 1 else "",
                                                                            ", ".join(miss)))
    return errs


# ---------------------------------------------------------------- 2. dead controls
def dead_controls_errs(root, built=None):
    text = rd(root, DEAD_CONTROLS)
    built = last_build(root) if built is None else built
    if text is None:
        return ["no %s: an agent has to drive every control on the build (references/mvp90-gates.md #2)"
                % DEAD_CONTROLS]
    errs = []
    drv = sp.field(text, "Driver").lower()
    if not any(d in drv for d in DRIVERS):
        errs.append("%s `Driver:` must be one of %s (got %r)" % (DEAD_CONTROLS, ", ".join(DRIVERS), drv))
    if _stale(root, DEAD_CONTROLS, built):
        errs.append("%s predates the last build (%s); sweep the current build" % (DEAD_CONTROLS, _when(built)))
    head, rows = sp.table(sp.section(text, "Controls") or text)
    cc, rc, ec = sp.col(head, "control"), sp.col(head, "result"), sp.col(head, "evidence")
    if not (cc and rc and ec):
        return errs + ["%s needs a table: | Control | Screen | Action | Result | Evidence |" % DEAD_CONTROLS]
    if len(rows) < 3:
        errs.append("%s lists %d control(s); a real UI or CLI has more. Sweep every one" % (DEAD_CONTROLS, len(rows)))
    found = re.search(r"\d+", sp.field(text, "Controls found") or "")
    if not found:
        errs.append("%s needs `Controls found: N` (what the driver enumerated)" % DEAD_CONTROLS)
    elif int(found.group()) != len(rows):
        errs.append("%s: driver found %s controls, the table has %d. Every one gets a row"
                    % (DEAD_CONTROLS, found.group(), len(rows)))
    for r in rows:
        res = r[rc].strip("` *").lower()
        if res not in ("ok", "dead", "error"):
            errs.append("%s: %r result %r (ok | dead | error)" % (DEAD_CONTROLS, r[cc], res))
        elif res != "ok":
            errs.append("%s control %r is %s: %s" % (DEAD_CONTROLS, r[cc], res.upper(), r[ec][:80]))
        elif sp.words(r[ec]) < 2:
            errs.append("%s: %r says ok with no evidence of what changed" % (DEAD_CONTROLS, r[cc]))
    return errs


# ---------------------------------------------------------------- 6. domain truth
def domain_needed(root):
    v = sp.field(rd(root, sp.SPEC) or "", "Domain content").lower()
    return v.startswith("yes")


def _ledger_rows(path):
    """(items, unsourced) from a JSON list, a CSV, or a markdown table with a source column."""
    text = sp.rd(path)
    if text is None:
        return None, None
    if path.endswith(".json"):
        try:
            data = json.loads(text)
        except ValueError:
            return None, None
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [])
        items = [x for x in data if isinstance(x, dict)]
        return len(items), sum(1 for x in items if not str(x.get("source", "")).strip())
    if path.endswith(".csv"):
        import csv
        rows = list(csv.DictReader(text.splitlines()))
        key = next((k for k in (rows[0].keys() if rows else []) if k and k.strip().lower() == "source"), None)
        if key is None:
            return len(rows), len(rows)
        return len(rows), sum(1 for r in rows if not (r.get(key) or "").strip())
    head, rows = sp.table(text)
    sc = sp.col(head, "source")
    return len(rows), (sum(1 for r in rows if r[sc].lower() in sp.OPEN) if sc else len(rows))


def domain_truth_errs(root, builder=""):
    if not domain_needed(root):
        return []
    text = rd(root, DOMAIN_TRUTH)
    if text is None:
        return ["SPEC.md says `Domain content: yes`; no %s (every item sourced, 10 spot-checked by a fresh "
                "agent; references/mvp90-gates.md #6)" % DOMAIN_TRUTH]
    errs = judge_errs(text, DOMAIN_TRUTH)
    checker = sp.field(text, "Checker")
    if not checker:
        errs.append("%s needs `Checker: <agent id>` (a fresh agent, never the builder)" % DOMAIN_TRUTH)
    elif builder and checker == builder:
        errs.append("%s checker %s is the builder; a fresh agent spot-checks" % (DOMAIN_TRUTH, checker))
    ledger = sp.field(text, "Ledger")
    n, unsourced = _ledger_rows(os.path.join(root, ledger)) if ledger else (None, None)
    if n is None:
        errs.append("%s needs `Ledger: <path>` to the product's content with a source per item "
                    "(.json list with \"source\", .csv with a source column, or a .md table)" % DOMAIN_TRUTH)
        n = 0
    elif unsourced:
        errs.append("%s: %d of %d content items in %s cite no source" % (DOMAIN_TRUTH, unsourced, n, ledger))
    head, rows = sp.table(sp.section(text, "Spot check"))
    src, says, res = sp.col(head, "source"), sp.col(head, "source says"), sp.col(head, "result")
    if not (src and says and res):
        return errs + ["%s ## Spot check needs: | # | Item | Source | Product says | Source says | Result |"
                       % DOMAIN_TRUTH]
    need = min(10, n) if n else 10
    if len(rows) < need:
        errs.append("%s spot-checked %d item(s); %d owed" % (DOMAIN_TRUTH, len(rows), need))
    for i, r in enumerate(rows, 1):
        if r[src].lower() in sp.OPEN:
            errs.append("%s row %d has no source" % (DOMAIN_TRUTH, i))
        if not quoted(r[says]):
            errs.append("%s row %d: quote the source line (\"...\", 3+ words), not a paraphrase" % (DOMAIN_TRUTH, i))
        rl = r[res].strip("` *").lower()
        if rl not in ("match", "fixed"):
            errs.append("%s row %d is %r: wrong domain content is a defect; fix it, re-check, mark fixed"
                        % (DOMAIN_TRUTH, i, rl or "blank"))
    return errs


# ---------------------------------------------------------------- 7. delivery mode
def mode_errs(root):
    p = os.path.join("validation", "05-verdict.md")
    text = rd(root, p)
    if text is None:
        return ["no %s" % p]
    errs = []
    mode = sp.field(text, "Delivery mode").lower()
    if not any(mode.startswith(m) for m in MODES):
        errs.append("%s needs `Delivery mode:` one of %s (the audit counted 4 runs built in the wrong mode)"
                    % (p, " / ".join(MODES)))
    if sp.words(sp.field(text, "Others lose")) < 8:
        errs.append("%s needs `Others lose: <the one reason the other modes lose>` (8+ words)" % p)
    return errs


# ---------------------------------------------------------------- 8. ICP walkthrough
def icp_errs(root, builder="", built=None):
    text = rd(root, ICP_WALK)
    built = last_build(root) if built is None else built
    if text is None:
        return ["no %s: a fresh agent plays the ICP and runs every SPEC.md core job on the real build "
                "(references/mvp90-gates.md #8)" % ICP_WALK]
    errs = judge_errs(text, ICP_WALK)
    if sp.words(sp.field(text, "ICP")) < 3:
        errs.append("%s needs `ICP: <who, from Stage 1/S>` (3+ words)" % ICP_WALK)
    walker = sp.field(text, "Walker")
    if not walker:
        errs.append("%s needs `Walker: <agent id>` (fresh context)" % ICP_WALK)
    elif builder and walker == builder:
        errs.append("%s walker %s is the builder; the ICP is played by a fresh agent" % (ICP_WALK, walker))
    if _stale(root, ICP_WALK, built):
        errs.append("%s predates the last build (%s); walk the current build" % (ICP_WALK, _when(built)))
    head, rows = sp.table(sp.section(text, "Jobs") or text)
    jc, rc, ec = sp.col(head, "job"), sp.col(head, "result"), sp.col(head, "evidence")
    if not (jc and rc and ec):
        return errs + ["%s needs a table: | Job | Result | Evidence |" % ICP_WALK]
    jobs = core_jobs(root)
    if not jobs:
        errs.append("SPEC.md has no `## Core jobs` (J1, J2, ...); the walkthrough has nothing to cover")
    seen = {}
    for r in rows:
        m = re.match(r"\s*\**(J\d+)", r[jc])
        if m:
            seen[m.group(1)] = r
    for j in jobs:
        r = seen.get(j)
        if r is None:
            errs.append("%s: core job %s was not walked" % (ICP_WALK, j))
            continue
        res = r[rc].strip("` *").lower()
        if res != "done":
            errs.append("%s: core job %s is %s. Stuck is a defect to fix before hand-off, not a later feature"
                        % (ICP_WALK, j, res.upper() or "BLANK"))
        elif not quoted(r[ec], 4):
            errs.append("%s: %s done with no quoted evidence (\"...\", 4+ words of what the screen/output showed)"
                        % (ICP_WALK, j))
    return errs


# ---------------------------------------------------------------- usability report (Stage 3)
def usability_errs(root, mode):
    need = 8.0 if mode == "speed-run" else 9.0
    cands = []
    for d in ("", "validation", ".planning"):
        dd = os.path.join(root, d)
        if os.path.isdir(dd):
            cands += [os.path.join(d, f) for f in os.listdir(dd) if re.search(r"usability", f, re.I) and f.endswith(".md")]
    if not cands:
        return ["no usability report (USABILITY.md or validation/*usability*.md) for Stage 3"]
    best = max(cands, key=lambda p: os.path.getmtime(os.path.join(root, p)))
    text = rd(root, best)
    m = re.search(r"(?:OVERALL_SCORE|Score)\W{0,4}(\d+(?:\.\d+)?)", text, re.I)
    errs = judge_errs(text, best)
    if not m:
        errs.append("%s has no `Score: N/10`" % best)
    elif float(m.group(1)) < need:
        errs.append("%s scores %s; the %s gate is %.0f/10" % (best, m.group(1), mode, need))
    return errs


def handoff_errs(root, st):
    """Everything the ICP needs before the first hand-off (software Stage 3, games Stage 2)."""
    built = last_build(root)
    b = st.get("builder_session", "")
    return (dead_controls_errs(root, built) + icp_errs(root, b, built) + domain_truth_errs(root, b)
            + real_target_errs(root, built))


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="run the 90%% MVP gates on a run folder (read-only)")
    ap.add_argument("root", nargs="?", default=".")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    built = last_build(root)
    checks = [("1 real target", real_target_errs(root, built)), ("2 dead controls", dead_controls_errs(root, built)),
              ("6 domain truth", domain_truth_errs(root)), ("7 delivery mode", mode_errs(root)),
              ("8 ICP walkthrough", icp_errs(root, "", built))]
    bad = 0
    for name, errs in checks:
        print("%-18s %s" % (name, "PASS" if not errs else "FAIL"))
        for e in errs:
            print("    - " + e)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
