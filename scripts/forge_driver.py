#!/usr/bin/env python3
"""forge-state run: the driver. The command IS the step, the way GSD's execute-phase is.

Adam, 2026-10-18: "Forge is supposed to act like a state machine like GSD. It hasn't done that."
The watchdog that morning: 7 runs DONE_UNRECORDED (work happened, state never moved), ~6
RESUMABLE with nobody running them, 6 sugar-pills-ops runs parked on a failed gate 3 with no
re-run. forge-state was a ledger plus a nag: it said what was next, then advancing depended on
a model remembering SKILL.md and calling `gate pass` itself.

The driver closes that loop:

    reconcile   every owed gate whose artifacts verify on disk is recorded as passed, with the
                evidence. One that doesn't verify is left alone: it never invents a pass.
    loop        next stage -> a fresh worker runs it with that stage's prompt from references/
                -> the stage's checks run on the artifacts -> the DRIVER records pass or fail
                -> on fail, up to 2 fix rounds, then BLOCKED (gate fail, exit 3)
    human gate  a check that only a person can clear ("HUMAN: ...") or a worker's ASK.md stops
                the run with ONE exact ask (what, on what device, what counts as pass), recorded
                in the frontmatter `asks:` list. Exit 2.

The same checks guard `forge-state gate K pass` by hand (forge_state.cmd_gate): a pass that
doesn't verify is refused unless Adam's words come with it (--adam-said, 3+ words).

Exit codes: 0 complete / --until reached, 1 usage, 2 waiting on a human, 3 BLOCKED,
5 the machine is busy (whats-running --gate refused a heavy stage).
"""
import datetime as dt
import fcntl
import os
import re
import shlex
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import forge_mvp as mvp  # noqa: E402
import forge_spec as sp  # noqa: E402

FIX_ROUNDS = 2
ASK = "ASK.md"
VERDICTS = ("DON'T BUILD", "DONT BUILD", "BUILD FOR SELF", "BUILD FOR MARKET")

# stage -> (reference file, section heading) the worker reads. Games stages live in /forge-games.
GAMES_SKILL = os.path.join(os.path.dirname(SKILL), "forge-games", "SKILL.md")
REFS = {
    "software": {
        "G": ("references/stages-front.md", "Stage G"), "H": ("references/stages-front.md", "Stage H"),
        "0": ("references/stages-front.md", "Stage 0"), "0A": ("references/stages-front.md", "STAGE 0A"),
        "1": ("references/stages-front.md", "Stage 1"), "S": ("references/stage-spec.md", "Stage S"),
        "2": ("references/stages-build.md", "Stage 2"), "2H": ("references/stage-hardening.md", "Stage 2H"),
        "2B": ("references/stages-build.md", "Stage 2B"), "3": ("references/stages-build.md", "Stage 3"),
        "4": ("references/stages-build.md", "Stage 4"), "5": ("references/stages-build.md", "Stage 5"),
    },
    "games": {k: (GAMES_SKILL, "Stage " + k) for k in ("0", "1", "T", "P", "S", "V", "2", "3'", "4", "5")},
}
REFS["games"].update({"G": REFS["software"]["G"], "H": REFS["software"]["H"]})
MVP_REF = "references/mvp90-gates.md"

# heavy stages wait for the machine (CLAUDE.md compute rule 6)
LANES = {"1": "ollama", "3": "ollama"}


def today():
    return dt.date.today().isoformat()


def _fs():
    import forge_state
    return forge_state


def rd(root, rel):
    return sp.rd(os.path.join(root, rel))


def humans_at(st, stage, passing=True):
    """Human entries at a stage. A gate clears only on one recorded with `human --passes`: the
    2026-10-18 Pookemon dry run had ~40 entries at Stage V (bug reports, asks) and none was a verdict."""
    return [h for h in _fs().humans(st) if h.get("stage") == stage and sp.words(h.get("said", "")) >= 3
            and (h.get("passes") or not passing)]


def _exists(root, rel, what, min_words=0):
    t = rd(root, rel)
    if t is None:
        return ["no %s (%s)" % (rel, what)]
    if sp.words(t) < min_words:
        return ["%s is under %d words (%s)" % (rel, min_words, what)]
    return []


def _gsd_logged(root, body):
    errs = []
    if not os.path.exists(os.path.join(root, ".planning", "ROADMAP.md")):
        errs.append("no .planning/ROADMAP.md: Stage 2 is a GSD run (HARD GSD GATE 1)")
    if not re.search(r"/gsd-[a-z]", body or ""):
        errs.append("FORGE-STATE.md logs no /gsd-* command with its commits (HARD GSD GATE 2)")
    rm = rd(root, os.path.join(".planning", "ROADMAP.md")) or ""
    open_ = re.findall(r"^\s*- \[ \]\s*\**(Phase[^*\n-]*)", rm, re.M) + \
        re.findall(r"^#{1,4}\s*(Phase[^\n]*?)\s*(?:\u25fb|\u2b1c|\u25a1)", rm, re.M)
    if open_:
        errs.append(".planning/ROADMAP.md has %d phase(s) not complete: %s" % (
            len(open_), "; ".join(x.strip()[:40] for x in open_[:4])))
    return errs


def _field_test(root, st, stage):
    errs = mvp.real_target_errs(root)
    ft = rd(root, os.path.join(".planning", "FIELD-TEST.md"))
    if ft is None:
        errs.append(("" if humans_at(st, stage) else "HUMAN: ")
                    + "no .planning/FIELD-TEST.md (the punch list from Adam's real use)")
    elif re.search(r"^\s*[-*]\s*\[ \]", ft, re.M):
        errs.append(".planning/FIELD-TEST.md still has open punch-list items")
    if not humans_at(st, stage):
        errs.append("HUMAN: Adam has not said it worked for its real job (forge-state human Adam --stage %s "
                    "--passes --how ... --said \"<his words>\")" % stage)
    return errs


def stage_errors(root, st, k, body=None):
    """Problems with stage k's artifacts; [] means the gate may pass. "HUMAN:" ones need a person."""
    fam = st.get("family", "software")
    mode = st.get("mode", "full")
    if body is None:
        body = _fs().load(root)[1]
    v = "validation/"
    if k == "G":
        return _exists(root, v + "G-gtm-roadmap.md", "Stage G GTM roadmap", 40)
    if k == "H":
        return _exists(root, v + "H3-tournament.md", "Stage H tournament result", 40)
    if k == "0":
        errs = _exists(root, v + "00-idea.md", "the idea and its kill criteria", 40)
        if not errs and not re.search(r"kill criteria", rd(root, v + "00-idea.md"), re.I):
            errs.append("validation/00-idea.md has no kill criteria (written before research)")
        return errs
    if k == "0A":
        t = rd(root, v + "00-idea.md") or ""
        said = humans_at(st, "0A") or st.get("mode") == "autonomous"
        if sp.words(sp.section(t, "Intended use")) < 20:
            if said:
                return ["validation/00-idea.md has no `## Intended use`: write Adam's recorded 0A answers there"]
            return ["HUMAN: validation/00-idea.md has no `## Intended use` answers from Adam (the five 0A questions)"]
        if not said:
            return ["HUMAN: the 0A answers are Adam's, not a worker's: record them (forge-state human Adam "
                    "--stage 0A --passes --how chat --said \"<his answers>\")"]
        return []
    if k == "1":
        errs = []
        for f in ("01-expert-panel.md", "02-cep-external-signal.md", "03-synth-survey-report.md",
                  "03-personas.md", "04-refutation.md", "05-verdict.md", "06-gap-map.md"):
            if fam == "games" and f in ("01-expert-panel.md", "02-cep-external-signal.md", "06-gap-map.md",
                                        "03-synth-survey-report.md"):
                continue                       # games compress Stage 1 (forge-games Stage 1)
            errs += _exists(root, v + f, "Stage 1 artifact")
        verdict = (rd(root, v + "05-verdict.md") or "").upper().replace("’", "'")
        if verdict and not any(x in verdict for x in VERDICTS):
            errs.append("validation/05-verdict.md names none of the three verdicts")
        return errs + mvp.mode_errs(root)
    if k == "S":
        return sp.spec_check(root, mode, fam)
    if k == "2H":
        import forge_verify as fv
        return fv.hardening_check(root, mode, builder=st.get("builder_session", ""))
    if k == "2B":
        return _exists(root, "brand/guidelines.md", "brand guidelines", 40)
    if k == "5":
        return [] if _fs().outcomes(st) else ["no graded outcome (forge-state outcome score|ship|field ...)"]
    if fam == "software":
        if k == "2":
            errs = _gsd_logged(root, body)
            if mode != "autonomous" and not humans_at(st, "2"):
                errs.append("HUMAN: Adam has not approved the GSD plan (the one approval beat in Stage 2)")
            return errs
        if k == "3":
            return mvp.usability_errs(root, mode) + mvp.handoff_errs(root, st)
        if k == "4":
            return _field_test(root, st, "4")
    if fam == "games":
        if k == "T":
            return mvp.real_target_errs(root)          # the toolchain runs on the real hardware
        if k in ("P", "V", "3'"):
            return [] if humans_at(st, k) else [
                "HUMAN: Stage %s is a real-human call (%s); record it: forge-state human <who> --stage \"%s\" "
                "--passes --how ... --said \"...\"" % (k, {"P": "is the core loop fun?", "V": "would you play this slice?",
                                                  "3'": "a real playtest"}[k], k)]
        if k == "2":
            return _gsd_logged(root, body) + mvp.handoff_errs(root, st)
        if k == "4":
            return _field_test(root, st, "4")
    return ["the driver has no check for stage %r; ask Adam (--adam-said)" % k]


def evidence(root, k):
    """The artifact files behind a pass, newest first, for the gate note."""
    names = {"G": ["validation/G-gtm-roadmap.md"], "H": ["validation/H3-tournament.md"],
             "0": ["validation/00-idea.md"], "0A": ["validation/00-idea.md"],
             "1": ["validation/05-verdict.md", "validation/04-refutation.md"],
             "S": ["SPEC.md", "SPEC-REVIEW.md", "GLOSSARY.md"], "2": [".planning/ROADMAP.md"],
             "2H": ["HARDENING.md"], "2B": ["brand/guidelines.md"],
             "3": [mvp.ICP_WALK, mvp.DEAD_CONTROLS, mvp.REAL_TARGET, mvp.DOMAIN_TRUTH],
             "4": [".planning/FIELD-TEST.md", mvp.REAL_TARGET], "T": [mvp.REAL_TARGET]}.get(k, [])
    out = []
    for n in names:
        p = os.path.join(root, n)
        if os.path.exists(p):
            out.append("%s (%s)" % (n, dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m/%d")))
    return ", ".join(out) or "human record"


# --------------------------------------------------------------------------- state writes
def write(root, fn):
    """Lock the run, re-read the state under the lock, apply fn(st, body), save. Returns st."""
    fs = _fs()
    with open(os.path.join(root, ".forge-state.lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        st, body, path = fs.load(root)
        fn(st, body)
        fs.save(root, st, body, path)
        return st


def record(root, k, state, note, next_action=None):
    def fn(st, body):
        st["gates"][k] = {"state": state, "since": today(), "note": note}
        if state in ("pass", "n/a"):
            st["asks"] = [a for a in (st.get("asks") or []) if a.get("stage") != k] or None
        if next_action:
            st["next_action"] = next_action
        if st.get("parked"):
            st["parked"] = None
    return write(root, fn)


# --------------------------------------------------------------------------- reconcile (A3)
def reconcile(root, st, dry=False, out=print):
    """Record a pass for every owed gate whose artifacts verify right now; stop at the first
    blocking one that doesn't. Never invents a pass."""
    fs = _fs()
    f = fs.family(st)
    body = fs.load(root)[1]
    done = []
    for k in f["order"]:
        g = st["gates"].get(k, {})
        if g.get("state", "pending") in fs.RESOLVED:
            continue
        errs = stage_errors(root, st, k, body)
        if errs:
            if f["blocking"][k]:
                break
            continue
        ev = evidence(root, k)
        done.append((k, ev))
        out("RECONCILE  Stage %-3s %s -> pass   (artifacts verify: %s)%s"
            % (k, g.get("state", "pending"), ev, "  [dry-run: not written]" if dry else ""))
        if not dry:
            st = record(root, k, "pass", "reconciled by forge-state run: artifacts verify (%s)" % ev)
        else:
            st["gates"][k] = dict(g, state="pass")      # in memory only, so later stages plan right
    return done, st


# --------------------------------------------------------------------------- policy
def skip_reason(root, st, k):
    """Non-blocking stages the mode table skips. The driver may record n/a on these only."""
    mode, verdict = st.get("mode", "full"), (st.get("verdict") or "").upper()
    if k in ("G", "H", "2B") and mode == "speed-run":
        return "speed-run skips Stage %s (SKILL.md mode table)" % k
    if k == "H" and not os.path.exists(os.path.join(root, "validation", "H1-pain-hunt.md")):
        return "no hunt: the idea was in hand"
    if k == "2B" and "MARKET" not in verdict:
        return "Stage 2B runs on BUILD FOR MARKET only"
    if k == "G" and "SELF" in verdict:
        return "Stage G skipped for a personal tool"
    return ""


def pending_ask(root, st, k):
    """A worker's ASK.md for stage k with no human answer recorded since it was written."""
    t = rd(root, ASK)
    if t is None:
        return None
    if sp.field(t, "Stage").strip("` ") not in ("", k):
        return None
    since = dt.date.fromtimestamp(os.path.getmtime(os.path.join(root, ASK))).isoformat()
    if any(h.get("when", "") >= since for h in humans_at(st, k, passing=False)):
        return None
    return {"stage": k, "ask": sp.field(t, "Ask") or t.strip()[:300], "device": sp.field(t, "Device") or "chat",
            "pass": sp.field(t, "Pass when") or "Adam answers; the worker continues"}


def human_ask(root, st, k, errs):
    """The ONE exact ask for a human gate: what to do, on what device, what counts as pass."""
    a = pending_ask(root, st, k)
    if a:
        return a
    fs = _fs()
    name = fs.family(st)["names"].get(k, k)
    jobs = ", ".join(mvp.core_jobs(root)) or "the core jobs in SPEC.md"
    mode = sp.field(rd(root, "validation/05-verdict.md") or "", "Delivery mode")
    dev = sp.field(rd(root, mvp.REAL_TARGET) or "", "Device") or (
        "the real device it ships on (%s)" % mode if mode else "the real device or real data it is for")
    first = errs[0][len("HUMAN:"):].strip()
    if k == "0A":
        return {"stage": k, "device": "chat", "ask": "Answer the five intended-use questions (who it's for beyond "
                "you; any money stake; upset if someone else sold it; a second operator; what you'd regret in six "
                "months). One line each.", "pass": "the answers are under ## Intended use in validation/00-idea.md"}
    if k == "2":
        return {"stage": k, "device": "Mac", "ask": "Read the GSD plan (.planning/ROADMAP.md and the current "
                "PLAN.md) and say approve, or what to change.", "pass": "your words recorded: forge-state human "
                "Adam --stage 2 --passes --how chat --said \"<your words>\""}
    if k == "4":
        return {"stage": k, "device": dev, "ask": "Use it for its real job (%s) on %s. Screenshot or screen-record "
                "each job into %s/proof/. Tell Maax what broke or is missing for the job (a fix) and what you'd add "
                "later (a feature)." % (jobs, dev, os.path.basename(root)),
                "pass": "proof newer than the last build, FIELD-TEST.md punch list empty, and your words recorded "
                        "with forge-state human Adam --stage 4 --passes"}
    if any("REAL-TARGET" in e or "proof" in e.lower() or "device" in e.lower() for e in errs):
        return {"stage": k, "device": dev, "ask": "On %s, install the current build, do %s, and screenshot or "
                "screen-record each one; drop the files in %s/proof/." % (dev, jobs, os.path.basename(root)),
                "pass": "proof files newer than the last build, listed in REAL-TARGET.md (%s)" % first[:80]}
    return {"stage": k, "device": "in person", "ask": "Stage %s (%s): %s" % (k, name, first), "pass": first}


def stop_human(root, st, k, errs, dry=False, out=print):
    a = human_ask(root, st, k, errs)
    a["since"] = today()
    out("\nWAITING ON ADAM  Stage %s" % k)
    out("  Do:      %s" % a["ask"])
    out("  Where:   %s" % a["device"])
    out("  Pass:    %s" % a["pass"])
    if dry:
        return 2

    def fn(s, body):
        asks = [x for x in (s.get("asks") or []) if x.get("stage") != k]
        s["asks"] = asks + [a]
        s["next_action"] = "WAITING ON ADAM (Stage %s): %s" % (k, a["ask"])
        if k == "4" and not s.get("handoff"):            # the first time Adam gets it for real
            s["handoff"] = {"date": today(), "stage": k}
    write(root, fn)
    return 2


# --------------------------------------------------------------------------- the worker
def worker_prompt(root, st, k, errs, rnd, answer=""):
    fs = _fs()
    f = fs.family(st)
    ref, head = REFS.get(f["name"], REFS["software"]).get(k, ("SKILL.md", "Stage " + k))
    ref = ref if os.path.isabs(ref) else os.path.join(SKILL, ref)
    if not os.path.exists(ref):              # the product copy keeps its stages inline in SKILL.md
        ref = os.path.join(SKILL, "SKILL.md")
    lines = [
        "[FORGE STAGE WORKER] run %s  (%s family, %s mode)" % (root, f["name"], st.get("mode", "full")),
        "Do Stage %s, %s, and nothing else. You are one step of the forge-state run state machine." % (k, f["names"][k]),
        "Read first: %s (section \"%s\"), %s/references/operating-rules.md, and %s/%s for the gate formats."
        % (ref, head, SKILL, SKILL, MVP_REF),
        "The driver checks your artifacts on disk and records the gate. Never run `forge-state gate`.",
        "If you need a decision or a physical action only Adam can give, write %s/%s with `Stage: %s`, "
        "`Ask: <one exact ask>`, `Device: <where>`, `Pass when: <what counts>`, then stop." % (root, ASK, k),
    ]
    if errs:
        lines.append("The gate currently refuses with:" if rnd == 0 else
                     "FIX ROUND %d of %d. The last attempt left these problems; fix exactly these:" % (rnd, FIX_ROUNDS))
        lines += ["  - " + e for e in errs[:20]]
    if answer:
        lines.append("Adam answered the open ask: %s" % answer)
    return "\n".join(lines) + "\n"


def run_worker(root, prompt):
    cmd = os.environ.get("FORGE_WORKER") or (
        "claude -p --model sonnet --dangerously-skip-permissions --max-budget-usd %s"
        % os.environ.get("FORGE_WORKER_BUDGET", "8"))
    timeout = int(os.environ.get("FORGE_WORKER_TIMEOUT", "5400"))
    try:
        r = subprocess.run(shlex.split(cmd), input=prompt, cwd=root, capture_output=True, text=True, timeout=timeout)
        return r.returncode
    except subprocess.TimeoutExpired:
        return 124


def lane_free(k):
    lane = LANES.get(k)
    if not lane:
        return True
    gate = os.environ.get("FORGE_GATE_CMD") or (shutil.which("whats-running") and "whats-running --gate")
    if not gate:
        return True
    return subprocess.run(shlex.split(gate) + [lane], capture_output=True).returncode == 0


def latest_answer(st, k):
    hs = humans_at(st, k, passing=False)
    return hs[-1].get("said", "") if hs else ""


def archive_ask(root):
    p = os.path.join(root, ASK)
    if os.path.exists(p):
        d = os.path.join(root, ".forge", "asks")
        os.makedirs(d, exist_ok=True)
        os.replace(p, os.path.join(d, "ASK-%s-%d.md" % (today(), int(os.path.getmtime(p)))))


def next_stage(st):
    fs = _fs()
    fl = fs.failed(st)
    if fl:
        return fl[0][0]
    p = fs.pending_any(st)
    return p[0][0] if p else None


# --------------------------------------------------------------------------- the loop (A1)
def plan(root, st, until=None, out=print):
    """--dry-run: what the driver would do from here. Changes nothing."""
    fs = _fs()
    f = fs.family(st)
    body = fs.load(root)[1]
    out("\nPLAN (dry-run, nothing written)")
    stop = False
    for k in f["order"]:
        g = st["gates"].get(k, {})
        state = g.get("state", "pending")
        if state in fs.RESOLVED:
            continue
        if not f["blocking"][k] and skip_reason(root, st, k):
            out("  Stage %-3s SKIP n/a   %s" % (k, skip_reason(root, st, k)))
            continue
        errs = stage_errors(root, st, k, body)
        hum = [e for e in errs if e.startswith("HUMAN:")]
        ask = pending_ask(root, st, k)
        tag = "NEXT" if not stop else "then"
        if ask or (errs and len(hum) == len(errs)):
            out("  %s Stage %-3s HUMAN GATE%s" % (tag, k, " (the run stops here)" if not stop else ""))
            stop_human(root, st, k, hum or ["HUMAN: " + (ask or {}).get("ask", "")], dry=True,
                       out=lambda s: out("    " + s.strip()) if s.strip() and not s.startswith("\nWAITING") else None)
        else:
            ref = REFS.get(f["name"], REFS["software"]).get(k, ("SKILL.md", ""))
            out("  %s Stage %-3s %s worker <- %s \"%s\"; verify; up to %d fix rounds; then %s if still refused"
                % (tag, k, "RETRY (failed)" if state == "fail" else "WORKER", os.path.basename(ref[0]), ref[1],
                   FIX_ROUNDS, "a HUMAN ask" if hum else "BLOCKED"))
            if state == "fail" and g.get("note"):
                out("        was: %s" % g["note"][:140])
            for e in errs[:6]:
                out("        needs: %s" % e)
            if len(errs) > 6:
                out("        ... %d more" % (len(errs) - 6))
            if LANES.get(k):
                out("        heavy: waits on whats-running --gate %s" % LANES[k])
        stop = stop or f["blocking"][k]
        if until and k == until:
            out("  (--until %s: stop)" % until)
            break
    return 0


def cmd_run(root, st, body, path, args, out=print):
    fs = _fs()
    fam = st.get("family", "software")
    if fam not in fs.SPEC_FAMILIES:
        sys.exit("forge-state run drives software and games runs; %s runs keep their own gates" % fam)
    f = fs.family(st)
    until = getattr(args, "until", None)
    if until and until not in f["order"]:
        sys.exit("--until %r is not a stage of %s (%s)" % (until, f["cmd"], ", ".join(f["order"])))
    dry = getattr(args, "dry_run", False)
    out("forge-state run  %s  [%s · %s mode]" % (st.get("project"), f["cmd"], st.get("mode", "?")))
    _, st = reconcile(root, st, dry=dry, out=out)
    if dry:
        return plan(root, st, until, out)
    for _ in range(getattr(args, "max_steps", 40)):
        st, body, _p = fs.load(root)
        if until and st["gates"].get(until, {}).get("state") in fs.RESOLVED:
            out("--until %s reached." % until)
            return 0
        k = next_stage(st)
        if k is None:
            out("RUN COMPLETE: every stage resolved.")
            return 0
        if not f["blocking"][k] and skip_reason(root, st, k):
            record(root, k, "n/a", "driver: " + skip_reason(root, st, k))
            out("Stage %s: n/a (%s)" % (k, skip_reason(root, st, k)))
            continue
        errs = stage_errors(root, st, k, body)
        rnd = 0
        while True:
            if not errs:
                record(root, k, "pass", "verified by forge-state run: %s" % evidence(root, k),
                       next_action="forge-state run")
                out("Stage %s: pass  (verified: %s)" % (k, evidence(root, k)))
                break
            hum = [e for e in errs if e.startswith("HUMAN:")]
            if pending_ask(root, st, k) or len(hum) == len(errs):
                return stop_human(root, st, k, hum or errs, out=out)
            if rnd > FIX_ROUNDS:
                record(root, k, "fail", "BLOCKED after %d fix rounds: %s" % (FIX_ROUNDS, " | ".join(errs[:3])),
                       next_action="BLOCKED at Stage %s: see the gate note; fix by hand or Adam decides" % k)
                out("BLOCKED  Stage %s after %d fix rounds:" % (k, FIX_ROUNDS))
                for e in errs[:10]:
                    out("  - " + e)
                return 3
            if not lane_free(k):
                out("BUSY  Stage %s needs the %s lane; whats-running --gate refused. Re-run later." % (k, LANES[k]))
                return 5
            answer = latest_answer(st, k) if os.path.exists(os.path.join(root, ASK)) else ""
            archive_ask(root) if answer else None
            out("Stage %s: worker%s ..." % (k, "" if rnd == 0 else " (fix round %d)" % rnd))
            run_worker(root, worker_prompt(root, st, k, errs, rnd, answer))
            st, body, _p = fs.load(root)
            errs = stage_errors(root, st, k, body)
            rnd += 1
        if until and k == until:
            out("--until %s reached." % until)
            return 0
    out("max steps reached; re-run forge-state run")
    return 0


# --------------------------------------------------------------------------- stalls (gate 5)
def workspace_dirs(path=None):
    path = path or os.path.expanduser("~/WORKSPACE.md")
    home = os.path.expanduser("~")
    text = sp.rd(path) or ""
    out = []
    for m in re.findall(r"~/[A-Za-z0-9_.\-/]+", text):
        d = os.path.join(home, m[2:]).rstrip("/")
        if os.path.isdir(d) and d != home and d not in out:
            out.append(d)
    return out


def cmd_stalls(args, out=print):
    """Read-only: runs in ~/WORKSPACE.md projects untouched 14+ days, each with finish-or-kill."""
    fs = _fs()
    home = os.path.expanduser("~")
    seen, rows = set(), []
    for d in workspace_dirs(getattr(args, "workspace", None)):
        for mp in fs.find_manifests(d, maxdepth=3):
            run = os.path.dirname(mp)
            if run in seen:
                continue
            seen.add(run)
            st, _, _ = fs.load(run)
            if not st or st.get("family", "software") not in fs.SPEC_FAMILIES:
                continue
            stage = fs.derive_stage(st)
            idle = fs.age_days(st.get("updated"))
            if stage == "DONE" or idle < args.days:
                continue
            rows.append((idle, run, st, stage))
    rows.sort(key=lambda r: -r[0])
    out("FORGE STALLS: %d run%s untouched %d+ days (read-only; nothing is killed)"
        % (len(rows), "" if len(rows) == 1 else "s", args.days))
    for idle, run, st, stage in rows:
        rel = "~" + run[len(home):] if run.startswith(home) else run
        f = fs.family(st)
        out("  %3dd  %-34s Stage %s (%s)%s" % (idle, rel, stage, f["names"].get(stage, "?"),
                                                "  [parked]" if st.get("parked") else ""))
        out("        FINISH: cd %s && forge-state run    KILL: forge-state -C %s verdict \"KILLED: <why>\" --close"
            % (rel, rel))
    return 0


# --------------------------------------------------------------------------- hand-off score (gate 9)
def handoff_lines(st):
    h = st.get("handoff")
    if not h:
        return []
    after = [x for x in _fs().humans(st) if x.get("when", "") >= h.get("date", "")]
    fixes = [x for x in after if x.get("kind") == "fix"]
    feats = [x for x in after if x.get("kind") == "feature"]
    rounds = len({str(x.get("when", ""))[:10] for x in fixes})     # one round per day with a --fix
    return ["  🤝  HAND-OFF: %s · fix rounds since: %d · features: %d · 90%% bar (0-1 small fix rounds): %s"
            % (h.get("date"), rounds, len(feats), "met" if rounds <= 1 else "MISSED")]


def ask_lines(st):
    return ["  ⏳  WAITING ON ADAM (Stage %s, since %s): %s  [%s]  pass: %s"
            % (a.get("stage"), a.get("since"), a.get("ask"), a.get("device"), a.get("pass"))
            for a in (st.get("asks") or [])]
