#!/usr/bin/env python3
"""forge-state — make Forge advance like GSD instead of stopping like a memo.

THE PROBLEM THIS FIXES
----------------------
Adam, 2026-09-10: "Forge isn't supposed to stop. Why did it stop!"

Because nothing could advance it. GSD keeps its machine state in the YAML
frontmatter of `.planning/STATE.md` (`stopped_at`, `status`, progress) and its
prose underneath, in ONE file, and a runner reads the frontmatter to decide what
is next. Forge kept a prose narrative that nothing could parse.

This does the same thing GSD does, for every Forge family:

    <manifest>.md        one file per run: YAML frontmatter (machine) + prose (human)
    forge-state next     the single next action; exit code says whether a gate blocks
    forge-state gate     records a transition (and refuses out-of-order passes)
    forge-state scan     every run that has gone idle with a gate owed (session-start hook)

The manifest is whatever the family already calls its resume-cold document:
FORGE-STATE.md (software, games), LAUNCH-STATE.md (gtm, either lens),
RESEARCH-STATE.md (research), CONTENT-STATE.md (content). (yt folded into gtm 2026-09-10.) The frontmatter is
the authority; the prose is the human's. `forge-state` never touches the prose.

v2 (2026-09-10, late): replaced the v1 FORGE-STATE.json sidecar. Two files that
describe one run drift, which is the exact disease this pipeline already had
with its two SKILL.md copies. `init` folds a leftover v1 JSON into the
frontmatter and removes it.

EXIT CODES (branch on these; they are the gate)
    0   nothing blocks: next stage is non-blocking work, or the run is complete
    1   usage / not a Forge project / refused transition
    2   a blocking gate is owed -- that is the next thing to run
    3   a gate FAILED -- a STOP: needs a decision (fix + re-run, waive with a
        reason, or end the run), not more work
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

VERSION = 2
LEGACY_JSON = "FORGE-STATE.json"

# Every Forge family: slash command, manifest filename, pipeline in order.
# `blocking` = the run may not be called done while this stage is unresolved,
# and a LATER stage may not be passed while this one is pending or failed
# (without --force). Non-blocking stages still have to be resolved before the
# run is complete; they just don't hold a later stage hostage.
FAMILIES = {
    "software": ("/forge", "FORGE-STATE.md", [
        ("G",  "GTM & founder-resource fit",   False),
        ("H",  "Hunt + tournament",            False),
        ("0",  "Capture + kill criteria",      True),
        ("0A", "Intended-use intake",          True),
        ("1",  "Validate (three verdicts)",    True),
        ("2",  "Build (GSD is the engine)",    True),
        ("2B", "Brand system",                 False),
        ("3",  "Synth usability to the gate",  True),
        ("4",  "Field test, real world",       True),
        ("5",  "Ship + learnings",             False),
    ]),
    "games": ("/forge-games", "FORGE-STATE.md", [
        ("G",  "GTM (skip for personal games)",     False),
        ("H",  "Hunt (rare)",                       False),
        ("0",  "Capture + FUN criteria",            True),
        ("1",  "Validate",                          True),
        ("T",  "TOOLCHAIN GATE",                    True),
        ("P",  "PROTOTYPE, find the fun",           True),
        ("V",  "VERTICAL SLICE (the Cerny gate)",   True),
        ("2",  "BUILD (GSD, gated behind V)",       True),
        ("3'", "PLAYTEST, real humans",             True),
        ("4",  "FIELD TEST (the real couch)",       True),
        ("5",  "SHIP + LEARNINGS",                  False),
    ]),
    "gtm": ("/forge-gtm", "LAUNCH-STATE.md", [
        ("0", "Intake (the brief)",                 True),
        ("1", "Category entry points and ICPs",     True),
        ("2", "Strategy fan-out",                   True),
        ("3", "Copy fan-out (after Gate 2)",        True),
        ("4", "Assembly + adam-voice pass",         True),
        ("5", "Review and ship",                    False),
    ]),
    "research": ("/forge-research", "RESEARCH-STATE.md", [
        ("0", "Frame and question bank",            True),
        ("1", "Source map: all the SINTs",          True),
        ("2", "Evidence ledger + verification",     True),
        ("3", "Sourced personas and synth panel",   True),
        ("4", "The paper",                          True),
        ("5", "Downstream fix list and ship",       False),
    ]),
    "content": ("/forge-content", "CONTENT-STATE.md", [
        ("0", "Brief",                              True),
        ("1", "Research digest",                    True),
        ("2", "Hook and title tournament",          True),
        ("3", "Script, shot list, b-roll",          True),
        ("4", "Capture and edit",                   True),
        ("5", "Packaging and publish",              True),
        ("6", "Measure and learn (72h / 28d)",      True),
    ]),
    "offer": ("/forge-offer", "OFFER-STATE.md", [
        ("0", "Brief and the money step",           True),
        ("1", "CEP from the audience's own words",  True),
        ("2", "Offer, two-sided",                   True),
        ("3", "Build the thing",                    True),
        ("4", "Landing page and email sequence",    True),
        ("5", "Launch, money step first",           True),
        ("6", "Measure at 28 days",                 True),
    ]),
    "client": ("/forge-client", "CLIENT-STATE.md", [
        ("0", "Discovery and the money step",        True),
        ("1", "Proposal, two-sided, signed, paid",   True),
        ("2", "Shoot and edit spec, shoot, cut",     True),
        ("3", "Delivery, capped",                    True),
        ("4", "Invoice, then paid",                  True),
        ("5", "Testimonial, case study, write-back", False),
    ]),
    "ads": ("/forge-ads", "ADS-STATE.md", [
        ("0", "Intake and the measurement gate",          True),
        ("1", "Plan, kill rules written first",          True),
        ("2", "Creative and destination, two-sided",     True),
        ("3", "Launch, paused first, go recorded",       True),
        ("4", "7-day read: kill or scale by the rules",  True),
        ("5", "28-day read and write-back",              True),
    ]),
    "job": ("/job-apply", "JOB-STATE.md", [
        ("1",  "Source the jobs",                        True),
        ("1A", "Read the form first (Check 7)",          True),
        ("2",  "Research (/job-cep)",                    True),
        ("3",  "Tailor in Adam's voice",                 True),
        ("4",  "Synth gate, both documents, 9/10",       True),
        ("5",  "Assemble the packet",                    True),
        ("6",  "Submit on explicit go, log outcome",     True),
    ]),
}
MANIFESTS = sorted({v[1] for v in FAMILIES.values()})
RESOLVED = ("pass", "waived", "n/a")          # counts as done
STATES = ("pass", "fail", "pending", "waived", "n/a")


def family(st):
    fam = (st or {}).get("family", "software")
    cmd, manifest, stages = FAMILIES.get(fam, FAMILIES["software"])
    return {
        "name": fam, "cmd": cmd, "manifest": manifest,
        "order": [s[0] for s in stages],
        "names": {s[0]: s[1] for s in stages},
        "blocking": {s[0]: s[2] for s in stages},
    }


def today():
    return dt.date.today().isoformat()


def age_days(since):
    try:
        return (dt.date.today() - dt.date.fromisoformat(str(since))).days
    except Exception:
        return 0


# --------------------------------------------------------------------------
# Frontmatter. Values are JSON-encoded on the right of `key:`, which is valid
# YAML and round-trips with the stdlib alone (no PyYAML in the public repo).
# --------------------------------------------------------------------------
FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
TOP_KEYS = ("forge_state_version", "project", "family", "command", "mode",
            "verdict", "stage", "next_action", "updated")


def parse_frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return None, text
    st, gates = {}, {}
    in_gates = False
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and in_gates:
            k, _, v = line.strip().partition(":")
            gates[json.loads(k) if k.startswith('"') else k] = json.loads(v.strip())
            continue
        in_gates = False
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if k == "gates":
            in_gates = True
            continue
        try:
            st[k] = json.loads(v) if v else None
        except ValueError:
            st[k] = v
    st["gates"] = gates
    if "forge_state_version" not in st:      # someone else's frontmatter (title/date/status)
        return None, text
    return st, text[m.end():]


def foreign_frontmatter(text):
    """Top-level keys of a non-forge frontmatter block, so init can carry them along."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    extra = {}
    for line in m.group(1).splitlines():
        if line.startswith(" ") or not line.strip():
            continue
        k, _, v = line.partition(":")
        extra[k.strip()] = v.strip()
    return extra, text[m.end():]


def render_frontmatter(st):
    out = ["---"]
    for k in TOP_KEYS:
        out.append("%s: %s" % (k, json.dumps(st.get(k))))
    for k, v in st.items():
        if k not in TOP_KEYS and k != "gates":
            out.append("%s: %s" % (k, json.dumps(v)))
    out.append("gates:")
    for k in family(st)["order"]:
        g = st["gates"].get(k, {"state": "pending", "since": today(), "note": ""})
        out.append("  %s: %s" % (json.dumps(k), json.dumps(g)))
    out.append("---")
    return "\n".join(out) + "\n"


def manifest_path(root, st=None, fam=None):
    if fam:
        return os.path.join(root, FAMILIES[fam][1])
    if st:
        return os.path.join(root, family(st)["manifest"])
    for name in MANIFESTS:                      # tracked manifest wins
        p = os.path.join(root, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                if parse_frontmatter(fh.read())[0] is not None:
                    return p
    for name in MANIFESTS:                      # then any legacy prose manifest
        p = os.path.join(root, name)
        if os.path.exists(p):
            return p
    return None


def load(root):
    """(state, body, path). state is None when untracked."""
    p = manifest_path(root)
    if not p:
        return None, "", None
    with open(p, encoding="utf-8") as fh:
        st, body = parse_frontmatter(fh.read())
    return st, body, p


def derive_stage(st):
    f = family(st)
    for k in f["order"]:
        if st["gates"].get(k, {}).get("state", "pending") not in RESOLVED:
            return k
    return "DONE"


def save(root, st, body, path):
    st["forge_state_version"] = VERSION
    st["command"] = family(st)["cmd"]
    st["stage"] = derive_stage(st)
    st["updated"] = today()
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_frontmatter(st))
        fh.write(body)


def blank(project, fam, mode):
    f = family({"family": fam})
    return {
        "forge_state_version": VERSION,
        "project": project,
        "family": fam,
        "command": f["cmd"],
        "mode": mode,
        "verdict": None,
        "stage": f["order"][0],
        "next_action": "Run Stage %s: %s." % (f["order"][0], f["names"][f["order"][0]]),
        "updated": today(),
        "gates": {k: {"state": "pending", "since": today(), "note": ""} for k in f["order"]},
    }


BODY_TEMPLATE = """
# {manifest_title} — {project}

**Resume-cold manifest** for the `{cmd}` run. The frontmatter above is the
machine state (`forge-state` owns it, never edit it by hand). Everything below
is for a human picking this run up with no memory of the session.

## Current position

- **Stage:** see frontmatter. `forge-state next` prints the single next action.
- **Run mode:** {mode}
- **Verdict:** pending

## Artifact checklist

| Stage | Artifact | Path | Gate |
|---|---|---|---|

## Decisions and gate overrides

(Every `waived` gate has its reason here as well as in its frontmatter note.)

## The one real-human touchpoint this run used

(Forge rule 13: all-synthetic is a flagged risk, not a clean pass.)

## Compute split

local / NAS / agy / Sonnet / Opus:

## Log

- {date} — run initialized (`forge-state init --family {family}`).
"""


# --------------------------------------------------------------------------
# Queries
# --------------------------------------------------------------------------
def owed(st):
    """Blocking stages not resolved, in order: (stage, gate)."""
    f = family(st)
    return [(k, st["gates"].get(k, {})) for k in f["order"]
            if f["blocking"][k] and st["gates"].get(k, {}).get("state", "pending") not in RESOLVED]


def failed(st):
    return [(k, g) for k, g in st["gates"].items() if g.get("state") == "fail"]


def pending_any(st):
    f = family(st)
    return [(k, st["gates"].get(k, {})) for k in f["order"]
            if st["gates"].get(k, {}).get("state", "pending") not in RESOLVED]


def paste_block(root, st, stage):
    f = family(st)
    home = os.path.expanduser("~")
    shown = "~" + root[len(home):] if root.startswith(home) else root
    ending = "a DON'T BUILD" if f["name"] in ("software", "games") else "a verdict that ends the run"
    return ("\n▶ CLEAR, THEN PASTE:\n\n"
            "  cd %s && %s\n"
            "  Resume at Stage %s. Do not stop at stage boundaries; STOP means only a\n"
            "  human-only input, an irreversible/outward action, or %s.\n"
            % (shown, f["cmd"], stage, ending))


def cmd_status(root, st, body, path, args):
    f = family(st)
    print("%s  [%s · %s mode]" % (st["project"], f["cmd"], st.get("mode", "?")))
    if st.get("verdict"):
        print("verdict: %s" % st["verdict"])
    stage = derive_stage(st)
    print("stage:   %s%s" % (stage, " — " + f["names"][stage] if stage in f["names"] else ""))
    print("updated: %s (%d days ago)\n" % (st.get("updated", "?"), age_days(st.get("updated"))))
    for k in f["order"]:
        g = st["gates"].get(k, {})
        state = g.get("state", "pending")
        mark = {"pass": "✅", "waived": "⏭", "n/a": "—", "fail": "❌"}.get(state, "⬜")
        flag = ""
        if state == "fail":
            flag = "  ← FAILED: needs a decision"
        elif f["blocking"][k] and state not in RESOLVED:
            d = age_days(g.get("since", today()))
            flag = "  ← BLOCKING%s" % (", owed %d days" % d if d else "")
        print("  %s  %-3s %-36s %-8s%s" % (mark, k, f["names"][k], state, flag))
        if g.get("note"):
            print("        %s" % g["note"])
    o, fl = owed(st), failed(st)
    print("\n%d blocking gate%s outstanding%s." % (
        len(o), "" if len(o) == 1 else "s", ", %d FAILED" % len(fl) if fl else ""))
    print("next action: %s" % st.get("next_action", "—"))
    return 0


def cmd_next(root, st, body, path, args):
    f = family(st)
    fl = failed(st)
    if fl:
        k, g = fl[0]
        print("STOP — Stage %s (%s) FAILED." % (k, f["names"][k]))
        if g.get("note"):
            print("Note: %s" % g["note"])
        print("\nThis is one of the three real stops: it needs a decision, not more work.")
        print("  fix and re-run:   forge-state gate %s pending --note \"…\"" % json.dumps(k))
        print("  waive (recorded): forge-state gate %s waived --note \"why\"" % json.dumps(k))
        print("  end the run:      forge-state verdict \"DON'T BUILD: …\"")
        return 3
    p = pending_any(st)
    if p:
        k, g = p[0]
        blocking = f["blocking"][k]
        d = age_days(g.get("since", today()))
        print("NEXT%s: Stage %s — %s%s" % (
            " OWED" if blocking else "", k, f["names"][k],
            "  (owed %d day%s)" % (d, "" if d == 1 else "s") if d else ""))
        if not blocking:
            print("(non-blocking: do it, or `forge-state gate %s n/a --note \"why\"` if it does not apply)"
                  % json.dumps(k))
        if g.get("note"):
            print("Note: %s" % g["note"])
        print("Project next action: %s" % st.get("next_action", "—"))
        print(paste_block(root, st, k))
        return 2 if owed(st) else 0
    print("RUN COMPLETE — every stage resolved. Verdict: %s" % (st.get("verdict") or "(none recorded)"))
    print("Write the learnings back (skill LEARNINGS.md + ~/maax/context/learnings.md) if not done.")
    return 0


def cmd_gate(root, st, body, path, args):
    f = family(st)
    k = args.stage
    if k not in st["gates"]:
        sys.exit("unknown stage %r for %s (expected one of %s)"
                 % (k, f["cmd"], ", ".join(f["order"])))
    if args.state == "waived" and not args.note:
        sys.exit("a waived gate is an override; record why: --note \"…\"")
    if args.state in RESOLVED and not args.force:
        earlier = [e for e in f["order"][:f["order"].index(k)]
                   if f["blocking"][e] and st["gates"].get(e, {}).get("state", "pending") not in RESOLVED]
        if earlier:
            sys.exit("refused: Stage %s cannot pass while earlier blocking stage%s %s "
                     "%s unresolved. Resolve %s first (pass / waived --note / n/a), or --force "
                     "to record an out-of-order pass."
                     % (k, "" if len(earlier) == 1 else "s", ", ".join(earlier),
                        "is" if len(earlier) == 1 else "are", "it" if len(earlier) == 1 else "them"))
    prev = st["gates"][k].get("state")
    note = args.note or ""
    if args.force and args.state in RESOLVED:
        note = "[out of order] " + note
    st["gates"][k] = {"state": args.state, "since": today(), "note": note}
    if args.next:
        st["next_action"] = args.next
    save(root, st, body, path)
    print("Stage %s: %s -> %s" % (k, prev, args.state))
    if args.state == "fail":
        print("A failed gate is a STOP. `forge-state next` now exits 3 until it is decided.")
        return 0
    print()
    cmd_next(root, st, body, path, args)   # show what is next; the write itself succeeded
    return 0


def cmd_set_next(root, st, body, path, args):
    st["next_action"] = args.text
    save(root, st, body, path)
    print("next action: %s" % args.text)
    return 0


def cmd_verdict(root, st, body, path, args):
    st["verdict"] = args.text
    if args.close:
        for k, g in st["gates"].items():
            if g.get("state", "pending") not in RESOLVED:
                st["gates"][k] = {"state": "n/a", "since": today(),
                                  "note": "run ended: %s" % args.text}
        st["next_action"] = "Run ended (%s). Write back learnings." % args.text
    save(root, st, body, path)
    print("verdict: %s%s" % (args.text, "  (remaining stages marked n/a)" if args.close else ""))
    return 0


def cmd_init(root, st, body, path, args):
    if st:
        sys.exit("%s is already tracked (frontmatter present)" % path)
    fam = args.family
    mp = manifest_path(root, fam=fam)
    project = os.path.basename(root)
    new = blank(project, fam, args.mode)

    # v1 sidecar: fold it in, then remove it. One run, one file.
    legacy = os.path.join(root, LEGACY_JSON)
    folded = False
    if os.path.exists(legacy):
        with open(legacy, encoding="utf-8") as fh:
            old = json.load(fh)
        for key in ("mode", "verdict", "next_action"):
            if old.get(key):
                new[key] = old[key]
        for k, g in old.get("gates", {}).items():
            if k in new["gates"]:
                new["gates"][k] = {"state": g.get("state", "pending"),
                                   "since": g.get("since", today()), "note": g.get("note", "")}
        folded = True

    if os.path.exists(mp):                      # existing prose manifest: prepend
        with open(mp, encoding="utf-8") as fh:
            existing = fh.read()
        extra, existing = foreign_frontmatter(existing)
        for k, v in extra.items():
            new.setdefault(k, v)
        body_out = "\n" + existing if not existing.startswith("\n") else existing
    else:
        body_out = BODY_TEMPLATE.format(
            manifest_title=os.path.splitext(os.path.basename(mp))[0], project=project,
            cmd=new["command"], mode=new["mode"], family=fam, date=today())
    save(root, new, body_out, mp)
    if folded:
        os.remove(legacy)
    print("tracked: %s  [%s, %s mode]%s" % (mp, new["command"], new["mode"],
                                            "  (folded and removed %s)" % LEGACY_JSON if folded else ""))
    return 0


# --------------------------------------------------------------------------
# scan: the session-start line. Quiet unless something has actually stalled.
# --------------------------------------------------------------------------
PRUNE = {"node_modules", "Library", "Applications", "Music", "Pictures", "Movies",
         "venv", ".venv", "__pycache__", "dist", "build", "brain",   # ~/brain mirrors ~
         "skills-archive"}


def find_manifests(home, maxdepth=5):
    hits = []
    for root, dirs, files in os.walk(home):
        depth = root[len(home):].count(os.sep)
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in PRUNE]
        if depth >= maxdepth:
            dirs[:] = []
        for f in files:
            if f in MANIFESTS:
                hits.append(os.path.join(root, f))
    return sorted(hits)


def cmd_scan(root, st, body, path, args):
    home = os.path.expanduser("~")
    stalled, active, legacy = [], [], []
    for mp in find_manifests(home):
        d = os.path.dirname(mp)
        s, _, _ = load(d)
        rel = "~" + d[len(home):]
        if not s:
            legacy.append(rel)
            continue
        f = family(s)
        fl, o = failed(s), owed(s)
        idle = age_days(s.get("updated"))
        if fl:
            k = fl[0][0]
            stalled.append("FORGE: %s — Stage %s (%s) FAILED, decision owed → cd %s && forge-state next"
                           % (os.path.basename(d), k, f["names"][k], rel))
        elif o and idle >= args.days:
            k = fl[0][0] if fl else o[0][0]
            stalled.append("FORGE: %s — Stage %s (%s) owed, idle %d day%s → cd %s && forge-state next"
                           % (os.path.basename(d), k, f["names"][k], idle, "" if idle == 1 else "s", rel))
        elif o:
            active.append("%s: Stage %s owed, touched today" % (rel, o[0][0]))
        else:
            active.append("%s: nothing blocking (stage %s)" % (rel, derive_stage(s)))
    for line in stalled:
        print(line)
    if args.all:
        for a in active:
            print("ok     %s" % a)
        for l in legacy:
            print("legacy %s (prose only; track it: cd %s && forge-state init --family …)" % (l, l))
    elif not stalled and args.verbose:
        print("FORGE: nothing stalled (%d tracked, %d legacy)" % (len(active) + len(stalled), len(legacy)))
    return 2 if stalled else 0


def main():
    ap = argparse.ArgumentParser(prog="forge-state", description=__doc__.split("\n\n")[0])
    ap.add_argument("-C", dest="root", default=".", help="run directory (where the manifest lives)")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status", help="every gate, what blocks, how long owed")
    sub.add_parser("next", help="the single next action; exit 2 = blocking gate owed, 3 = a gate FAILED")
    g = sub.add_parser("gate", help="record a stage transition")
    g.add_argument("stage")
    g.add_argument("state", choices=STATES)
    g.add_argument("--note", default="")
    g.add_argument("--next", default="", help="set the project's next action in the same write")
    g.add_argument("--force", action="store_true", help="allow an out-of-order pass (recorded as such)")
    n = sub.add_parser("set-next", help="set the single next action")
    n.add_argument("text")
    v = sub.add_parser("verdict", help="record the verdict")
    v.add_argument("text")
    v.add_argument("--close", action="store_true", help="the verdict ends the run: mark remaining stages n/a")
    i = sub.add_parser("init", help="track this run (new manifest, or frontmatter onto an existing one)")
    i.add_argument("--family", default="software", choices=sorted(FAMILIES) + ["yt"])
    i.add_argument("--mode", default="full", help="full | speed-run | autonomous")
    sc = sub.add_parser("scan", help="every run idle with a gate owed (session-start hook)")
    sc.add_argument("--all", action="store_true", help="also list active and legacy runs")
    sc.add_argument("--days", type=int, default=1, help="idle days before a run counts as stalled")
    sc.add_argument("--verbose", action="store_true", help="print a line even when nothing stalled")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    cmd = args.cmd or "status"
    st, body, path = (None, "", None) if cmd == "scan" else load(root)

    if cmd == "scan":
        return cmd_scan(root, None, None, None, args)
    if cmd == "init":
        if args.family == "yt":
            sys.exit("yt was folded into gtm on 2026-09-10: use --family gtm and set "
                     "`--lens youtube` in SPEC.md")
        return cmd_init(root, st, body, path, args)
    if st is None:
        sys.exit("not a tracked Forge run: no manifest with frontmatter in %s%s\n"
                 "  track it: forge-state init --family %s"
                 % (root, " (prose-only %s found)" % os.path.basename(path) if path else "",
                    "|".join(sorted(FAMILIES))))
    return {"status": cmd_status, "next": cmd_next, "gate": cmd_gate,
            "set-next": cmd_set_next, "verdict": cmd_verdict}[cmd](root, st, body, path, args)


if __name__ == "__main__":
    sys.exit(main())
