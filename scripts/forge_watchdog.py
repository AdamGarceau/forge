"""forge_watchdog — WHY a stopped Forge run stopped, not just that it did.

THE PROBLEM THIS FIXES
-----------------------
`forge-state scan` says a run is "idle 14 days" but never says why. Runs sit stalled because nobody re-reads the evidence — scan is a list,
this is a verdict.

For every non-parked run `forge_state.stalled_runs()` flags (stalled or FAILED),
gather cheap evidence (frontmatter, git log scoped to the run dir, .planning/
STATE.md, recently-touched files, a matching handoff) and turn it into one of six
deterministic VERDICTs. The rules run first and always win; a local model
(`forge-lane`) only supplies a one-line human-readable reason/ask, and only when
it AGREES do we print its wording without the "(model: X)" suffix. Model output
is display text only — it is never executed.

Read-only: this module never writes a manifest. `--refresh` recomputes verdicts
into `~/.cache/forge-watchdog.json`; without it, fresh cache entries are reused.
Cache key per run = manifest mtime + `git rev-parse HEAD` of the run's own repo
(or "nogit" if the run dir is not inside a git work tree).

stdlib only, matches forge_state.py's style.
"""
import json
import os
import re
import subprocess
import sys
import time

import forge_state as fs

CACHE_PATH = os.path.expanduser("~/.cache/forge-watchdog.json")
REPORT_PATH = os.environ.get("FORGE_WATCHDOG_REPORT",
                             os.path.expanduser("~/.cache/forge-watchdog-report.md"))
HANDOFF_DIR = os.environ.get("FORGE_HANDOFF_DIR", os.path.expanduser("~/.forge/handoffs"))
MAX_BLOCK_BYTES = 6 * 1024

VERDICTS = ("BLOCKED_ON_HUMAN", "DONE_UNRECORDED", "BLOCKED_EXTERNAL", "ABANDON",
            "RESUMABLE")

HUMAN_STAGE_HINTS = ("field test", "capture", "film", "real world", "real couch",
                     "playtest", "shoot")

# Split into two tiers (2026-09-24 fix): "reply"/"awaiting"/"waiting on" already
# mean waiting-on-someone by themselves. Bare named parties ("client", "apple",
# "google"...) are common in totally unrelated boilerplate ("field test with a
# real client" is a stage NAME, not a third-party wait) so they only count when
# they co-occur with actual wait/response language.
THIRD_PARTY_STRONG_HINTS = ("reply", "awaiting", "waiting on", "support ticket")
THIRD_PARTY_NAMED = ("client", "apple", "vendor", "app store", "google", "irs", "payer")
THIRD_PARTY_CONTEXT_RE = re.compile(r"\bwait|\breply|\brespon(d|se)|\bget back\b", re.I)

# 2026-09-24 fix: an explicit block signal in the run's own next_action/gate note/
# handoff (BLOCKED, waiting/waits, STOP, a dead credential) must win over
# DONE_UNRECORDED — a repo can be busy (commits, file touches) while the actual
# next action is stuck on exactly one of these. Checked BEFORE the "looks like
# output" check, not after.
BLOCK_SIGNAL_RE = re.compile(
    r"\bblocked\b|\bwaits?\b|\bwaiting\b|\bstop\b|"
    r"\bdead (?:token|credential|key|api[ _-]?token)\b|"
    r"\bexpired (?:token|credential|key)\b",
    re.I)

# Conservative ranking for tie-breaking a rule/model disagreement (point 3 of the
# 2026-09-24 fix): lower rank = more conservative = wins the disagreement.
# BLOCKED_* always beats ABANDON/RESUMABLE, which always beat DONE_UNRECORDED.
# DONE_UNRECORDED itself is handled separately (it needs model agreement to be
# printed at all; see model_check).
_VERDICT_RANK = {"BLOCKED_ON_HUMAN": 0, "BLOCKED_EXTERNAL": 0,
                 "ABANDON": 1, "RESUMABLE": 1, "DONE_UNRECORDED": 2}


# --------------------------------------------------------------------------
# Evidence gathering (cheap, capped, read-only)
# --------------------------------------------------------------------------
def _run(cmd, cwd=None, timeout=5):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.stdout.strip()
    except Exception:
        return ""


def _cap(text, n=MAX_BLOCK_BYTES):
    b = text.encode("utf-8", "ignore")
    if len(b) <= n:
        return text
    return b[:n].decode("utf-8", "ignore") + "\n…(truncated)"


def _is_git_repo(d):
    return _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=d) == "true"


def repo_head(d):
    """git rev-parse HEAD of the run's own repo, or 'nogit'. Used as a cache key
    component so a commit invalidates the cached verdict."""
    if not _is_git_repo(d):
        return "nogit"
    return _run(["git", "rev-parse", "HEAD"], cwd=d) or "nogit"


def git_log_since(d, since):
    """git log scoped to the run dir path only, so the homedir repo's unrelated
    commits elsewhere never count as evidence for this run."""
    if not since or not _is_git_repo(d):
        return ""
    out = _run(["git", "log", "--since=%s" % since, "--oneline", "-n", "15",
                "--", "."], cwd=d)
    return out


def state_md_status(d):
    """.planning/STATE.md frontmatter status + stopped_at, if present."""
    p = os.path.join(d, ".planning", "STATE.md")
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        return {}
    st, _ = fs.parse_frontmatter(text) if False else (None, None)
    out = {}
    for key in ("status", "stopped_at"):
        for line in text.splitlines()[:60]:
            s = line.strip()
            if s.lower().startswith(key + ":"):
                out[key] = s.split(":", 1)[1].strip().strip('"')
    return out


SKIP_DIRS = {".git", "node_modules", ".build", "__pycache__", ".venv", "venv"}


def newest_files_since(d, since_epoch, cap=8):
    """Newest files touched since the manifest's `updated` timestamp. The manifest
    itself is excluded at the root — every gate transition rewrites it, so its own
    mtime is not evidence of stage output, it is bookkeeping."""
    hits = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".")]
        for f in files:
            if root == d and f in fs.MANIFESTS:
                continue
            p = os.path.join(root, f)
            try:
                mt = os.path.getmtime(p)
            except OSError:
                continue
            if mt >= since_epoch:
                hits.append((mt, os.path.relpath(p, d)))
    hits.sort(reverse=True)
    return [rel for _, rel in hits[:cap]]


def matching_handoff(run_dirname):
    """Newest handoff mentioning the run's dir name, first 40 lines, if any."""
    if not os.path.isdir(HANDOFF_DIR):
        return None
    cands = []
    for f in os.listdir(HANDOFF_DIR):
        if not f.endswith(".md"):
            continue
        p = os.path.join(HANDOFF_DIR, f)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except Exception:
            continue
        if run_dirname in text:
            cands.append((os.path.getmtime(p), p, text))
    if not cands:
        return None
    cands.sort(reverse=True)
    _, p, text = cands[0]
    return {"path": p, "excerpt": "\n".join(text.splitlines()[:40])}


def since_epoch(since):
    try:
        import datetime as dt
        return dt.datetime.fromisoformat(str(since)).timestamp()
    except Exception:
        return 0


def gather_evidence(d, st):
    f = fs.family(st)
    fl, o = fs.failed(st), fs.owed(st)
    gate_key, gate = (fl[0] if fl else (o[0] if o else (None, {})))
    # The stage that matters here is the one actually stalled/FAILED (gate_key),
    # not derive_stage()'s cursor — those differ whenever a non-blocking stage
    # (G, H, 2B) sits unresolved ahead of the real blocking gate.
    stage = gate_key or fs.derive_stage(st)
    updated = st.get("updated")
    ev = {
        "dir": d,
        "family": f["name"],
        "stage": stage,
        "stage_name": f["names"].get(stage, stage),
        "gate_key": gate_key,
        "gate_state": gate.get("state") if gate else None,
        "gate_note": gate.get("note", "") if gate else "",
        "next_action": st.get("next_action", ""),
        "updated": updated,
        "idle": fs.age_days(updated),
        "failed": bool(fl),
    }
    ev["git_log"] = _cap(git_log_since(d, updated))
    ev["state_md"] = state_md_status(d)
    ev["new_files"] = newest_files_since(d, since_epoch(updated))
    ho = matching_handoff(os.path.basename(d.rstrip("/")))
    ev["handoff"] = _cap(ho["excerpt"]) if ho else ""
    ev["handoff_path"] = ho["path"] if ho else ""
    return ev


# --------------------------------------------------------------------------
# Deterministic rules (run first, always win)
# --------------------------------------------------------------------------
def cmd_for(verdict, ev):
    """The one deterministic, copy-pasteable command per verdict. Used regardless
    of whether the verdict came from the rule or won a conservative tie-break
    against the model (point 3, 2026-09-24) — the command must always match the
    FINAL printed verdict, never a stale one from a different branch."""
    d, k = ev["dir"], ev["gate_key"]
    if verdict == "BLOCKED_ON_HUMAN":
        if ev["failed"]:
            return ("fix + forge-state gate %s pending --note \"...\", "
                    "or waive with a reason, or verdict --close to end it" % json.dumps(k))
        return "The founder resolves the block, then forge-state -C %s next" % d
    if verdict == "BLOCKED_EXTERNAL":
        return "follow up externally; nothing to do on this machine yet"
    if verdict == "DONE_UNRECORDED":
        return ("forge-state -C %s gate %s pass --note \"watchdog: evidence of completed work found\""
                % (d, json.dumps(k) if k else '"?"'))
    if verdict == "ABANDON":
        return "forge-state -C %s park --reason \"idle %d days, no movement\"" % (d, ev["idle"])
    return ev["next_action"] or "forge-state -C %s next" % d   # RESUMABLE


def rule_verdict(ev):
    """Returns (verdict, reason, ask_or_command). Rule order, fixed 2026-09-24
    after 5/8 real verdicts came back wrong (DONE_UNRECORDED was firing on file
    noise ahead of an explicit block in the same evidence):

        failed gate
        -> explicit block signal (BLOCKED/waiting/STOP/dead credential in the
           run's own next_action/gate note/handoff) -> BLOCKED_ON_HUMAN, or
           BLOCKED_EXTERNAL if it also names a third party / awaits a reply
        -> human-only stage
        -> DONE_UNRECORDED (commits only, not just file touches — model must
           agree or this never gets printed; see model_check)
        -> ABANDON (idle, quiet)
        -> else RESUMABLE
    """
    d = ev["dir"]
    hay = " ".join([ev["gate_note"], ev["next_action"], ev["handoff"]])
    hay_l = hay.lower()
    has_commits = bool(ev["git_log"].strip())

    strong_hit = next((h for h in THIRD_PARTY_STRONG_HINTS if h in hay_l), None)
    named_hit = next((h for h in THIRD_PARTY_NAMED if h in hay_l), None)
    has_third_party = bool(strong_hit) or (named_hit and THIRD_PARTY_CONTEXT_RE.search(hay_l))
    third_party_hit = strong_hit or named_hit

    if ev["failed"]:
        note = ev["gate_note"] or "(no note recorded)"
        return ("BLOCKED_ON_HUMAN", "Stage %s FAILED: %s" % (ev["gate_key"], note),
                cmd_for("BLOCKED_ON_HUMAN", ev))

    m = BLOCK_SIGNAL_RE.search(hay)
    if m:
        if has_third_party:
            return ("BLOCKED_EXTERNAL",
                    "explicit block (%r) naming a third party (%r)" % (m.group(0), third_party_hit),
                    cmd_for("BLOCKED_EXTERNAL", ev))
        return ("BLOCKED_ON_HUMAN", "explicit block signal: %r in the evidence" % m.group(0),
                cmd_for("BLOCKED_ON_HUMAN", ev))

    sm = ev["state_md"]
    stopped_at = (sm.get("stopped_at") or "").lower()
    stage_name_l = ev["stage_name"].lower()
    if any(h in stopped_at for h in ("human-verify", "checkpoint", "owed by the founder")):
        return ("BLOCKED_ON_HUMAN", "STATE.md stopped_at: %s" % sm.get("stopped_at"),
                cmd_for("BLOCKED_ON_HUMAN", ev))
    if any(h in stage_name_l for h in HUMAN_STAGE_HINTS):
        return ("BLOCKED_ON_HUMAN", "Stage %s is a human-only stage (%s)" % (ev["gate_key"], ev["stage_name"]),
                cmd_for("BLOCKED_ON_HUMAN", ev))

    # Third-party/reply-awaited mention with no explicit BLOCK_SIGNAL word still
    # counts as BLOCKED_EXTERNAL — it just isn't phrased as a "block".
    if has_third_party:
        return ("BLOCKED_EXTERNAL", "evidence names a third party (%r)" % third_party_hit,
                cmd_for("BLOCKED_EXTERNAL", ev))

    if has_commits:
        bits = ["%d commit(s) since %s" % (len(ev["git_log"].splitlines()), ev["updated"])]
        if ev["new_files"]:
            bits.append("%d file(s) touched since" % len(ev["new_files"]))
        return ("DONE_UNRECORDED", "; ".join(bits), cmd_for("DONE_UNRECORDED", ev))

    if ev["idle"] >= 14:
        return ("ABANDON", "idle %d days, no commits since updated" % ev["idle"],
                cmd_for("ABANDON", ev))

    return ("RESUMABLE", "no blocker found in the evidence", cmd_for("RESUMABLE", ev))


# --------------------------------------------------------------------------
# Model confirmation (forge-lane analyze). Never executed, display text only.
# --------------------------------------------------------------------------
def _done_fallback(rule_reason, why):
    return "RESUMABLE", "%s; falling back to RESUMABLE, never an unconfirmed DONE. rule read: %s" % (
        why, rule_reason)


def model_check(ev, rule_v, rule_reason, no_model):
    """Returns (verdict, reason). The verdict CAN differ from rule_v — 2026-09-24
    fix, point 2 and 3:

    - DONE_UNRECORDED is never printed without the model's agreement. No model
      available, the call fails, or the model disagrees -> RESUMABLE, never DONE.
    - For every other rule verdict, a disagreeing model can only make the result
      MORE conservative (BLOCKED_* beats ABANDON/RESUMABLE beats DONE_UNRECORDED,
      see _VERDICT_RANK): if the model's verdict outranks the rule's, the model's
      verdict and reason win; otherwise the rule verdict stands and the model's
      dissent is appended for visibility.

    ask_or_command is never taken from the model; cmd_for() regenerates it from
    whatever verdict this function returns, in cmd_watchdog."""
    if no_model:
        if rule_v == "DONE_UNRECORDED":
            return _done_fallback(rule_reason, "no model available to confirm")
        return rule_v, rule_reason
    lane = os.environ.get("FORGE_LANE", os.path.expanduser("~/.local/bin/forge-lane"))
    if not os.path.exists(lane):
        if rule_v == "DONE_UNRECORDED":
            return _done_fallback(rule_reason, "forge-lane not found")
        return rule_v, rule_reason
    data = {
        "family": ev["family"], "stage": ev["stage"], "stage_name": ev["stage_name"],
        "gate_state": ev["gate_state"], "gate_note": ev["gate_note"],
        "next_action": ev["next_action"], "idle_days": ev["idle"],
        "git_log": ev["git_log"], "new_files": ev["new_files"],
        "state_md": ev["state_md"], "handoff_excerpt": ev["handoff"],
    }
    prompt = (
        "A stopped software-project run has this evidence. A rules engine already "
        "computed the verdict %s (%s). Confirm or refute in one JSON object: "
        '{"verdict": one of %s, "reason": "<=20 words", "ask_or_command": "one line"}. '
        "Respond with JSON only.\n\nDATA_START\n%s\nDATA_END"
        % (rule_v, rule_reason, list(VERDICTS), json.dumps(data)[:4000])
    )
    try:
        p = subprocess.run([lane, "analyze", "--sensitive", "--json", prompt],
                            capture_output=True, text=True, timeout=90)
    except Exception:
        if rule_v == "DONE_UNRECORDED":
            return _done_fallback(rule_reason, "model call raised an exception")
        return rule_v, rule_reason
    if p.returncode != 0:
        if rule_v == "DONE_UNRECORDED":
            return _done_fallback(rule_reason, "model call failed (exit %d)" % p.returncode)
        return rule_v, rule_reason
    out = p.stdout.strip()
    try:
        parsed = json.loads(out)
        if isinstance(parsed, dict) and "response" in parsed and isinstance(parsed["response"], str):
            parsed = json.loads(parsed["response"])
        mv = parsed.get("verdict")
        mreason = parsed.get("reason", "")
    except Exception:
        if rule_v == "DONE_UNRECORDED":
            return _done_fallback(rule_reason, "model response was not parseable JSON")
        return rule_v, rule_reason

    if mv not in VERDICTS:               # model returned garbage: ignore it, rule stands
        if rule_v == "DONE_UNRECORDED":
            return _done_fallback(rule_reason, "model returned an unrecognized verdict %r" % mv)
        return rule_v, rule_reason

    if rule_v == "DONE_UNRECORDED":
        if mv == "DONE_UNRECORDED":
            return "DONE_UNRECORDED", (mreason or rule_reason)
        return _done_fallback(rule_reason, "model disagreed (said %s: %s)" % (mv, mreason))

    if mv == rule_v:
        return rule_v, (mreason or rule_reason)
    if _VERDICT_RANK.get(mv, 9) < _VERDICT_RANK.get(rule_v, 9):
        # Model is more conservative than the rule: it wins (point 3).
        return mv, "%s (rule said %s: %s)" % (mreason or ("model: " + mv), rule_v, rule_reason)
    return rule_v, "%s (model: %s — %s)" % (rule_reason, mv, mreason)


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------
def load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=1, sort_keys=True)


def cache_key(d):
    mp = fs.manifest_path(d)
    mtime = os.path.getmtime(mp) if mp and os.path.exists(mp) else 0
    return "%s|%s" % (mtime, repo_head(d))


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def write_report(results):
    lines = ["# Forge Watchdog", "", fs.today() + " (12-hour times, AM/PM only)", ""]
    for r in results:
        lines.append("## %s" % os.path.basename(r["dir"].rstrip("/")))
        lines.append("- **verdict:** %s" % r["verdict"])
        lines.append("- **reason:** %s" % r["reason"])
        lines.append("- **ask/command:** %s" % r["ask_or_command"])
        for b in r.get("evidence_bullets", []):
            lines.append("  - %s" % b)
        lines.append("")
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return REPORT_PATH


def evidence_bullets(ev):
    out = ["stage %s (%s), idle %d day(s)" % (ev["gate_key"], ev["stage_name"], ev["idle"])]
    if ev["gate_note"]:
        out.append("gate note: %s" % ev["gate_note"])
    if ev["git_log"].strip():
        out.append("commits since updated: %d" % len(ev["git_log"].splitlines()))
    if ev["new_files"]:
        out.append("files touched since: %s" % ", ".join(ev["new_files"][:5]))
    if ev["state_md"]:
        out.append("STATE.md: %s" % ev["state_md"])
    if ev["handoff_path"]:
        out.append("handoff: %s" % ev["handoff_path"])
    return out


# --------------------------------------------------------------------------
# Main entry, called from forge_state.main()
# --------------------------------------------------------------------------
def cmd_watchdog(args):
    home = os.path.expanduser("~")
    stalled, *_ = fs.stalled_runs(home, days=1)
    cache = load_cache()

    if args.hook_lines:
        # CACHE ONLY: no evidence gathering, no forge-lane call. This runs on every
        # session start, so it must stay well under 200ms regardless of cache size.
        # Same sort + WIP_CAP as cmd_scan's shown list, so a watchdog line only ever
        # follows a scan line the hook actually printed. Exactly one line per shown run
        # (blank on a cache miss) so the hook can pair them with scan's lines by position.
        stalled.sort(key=lambda e: (not e["focus"], not e["failed"], -e["idle"], e["rel"]))
        for e in stalled[:fs.WIP_CAP]:
            hit = cache.get(e["dir"])
            if hit and hit.get("result"):
                r = hit["result"]
                print("   ↳ WATCHDOG: %s — %s → %s" % (
                    r["verdict"], r["reason"], r["ask_or_command"]))
            else:
                print("")
        return 0

    results = []
    for e in stalled:
        d = e["dir"]
        st, _, _ = fs.load(d)
        if not st:
            continue
        key = cache_key(d)
        cached = cache.get(d)
        if not args.refresh and cached and cached.get("key") == key:
            results.append(cached["result"])
            continue
        ev = gather_evidence(d, st)
        rv, rr, _ = rule_verdict(ev)
        v, reason = model_check(ev, rv, rr, args.no_model)
        # cmd_for() is re-derived from the FINAL verdict `v` (which may differ
        # from the rule's rv per the DONE-needs-agreement and conservative
        # tie-break rules), never from the rule's own, possibly stale, command.
        result = {"dir": d, "rel": e["rel"], "verdict": v, "reason": reason,
                  "ask_or_command": cmd_for(v, ev), "evidence_bullets": evidence_bullets(ev),
                  "computed": fs.today()}
        results.append(result)
        cache[d] = {"key": key, "result": result}
    save_cache(cache)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    report = write_report(results)
    for r in results:
        print("%s: %s — %s → %s" % (os.path.basename(r["dir"].rstrip("/")),
                                              r["verdict"], r["reason"], r["ask_or_command"]))
    print("\nwrote %s" % report)
    return 0


def add_subparser(sub):
    w = sub.add_parser("watchdog", help="verdict on every stalled/FAILED run: why it stopped")
    w.add_argument("--refresh", action="store_true", help="recompute every verdict (ignore cache)")
    w.add_argument("--json", action="store_true", help="print results as JSON")
    w.add_argument("--no-model", dest="no_model", action="store_true",
                   help="rules only, no forge-lane call")
    w.add_argument("--hook-lines", dest="hook_lines", action="store_true",
                   help="cache-only indented lines for the session-start hook (no model call)")
    return w
