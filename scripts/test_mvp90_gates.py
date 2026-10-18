#!/usr/bin/env python3
"""Tests for forge 1.11, the 90% MVP release (Adam 2026-10-18: "Fix forge. I'd actually like a
product to be 90% MVP." / "Forge is supposed to act like a state machine like GSD.").

PART A, the driver (forge_driver.py, `forge-state run`): the loop records passes only when the
artifacts verify, fixes up to 2 rounds then BLOCKS, stops at a human gate with one ask, --until and
--dry-run; a hand-called pass is refused unless it verifies; reconcile records what verifies and
nothing else.
PART B, the gates (forge_mvp.py, forge_spec.check_mvp90): real target, dead controls, assumed
features, no bare --force / waive, stalls, domain truth, delivery mode, ICP walkthrough, hand-off.

Run:  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pytest -q test_mvp90_gates.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import forge_driver as drv  # noqa: E402
import forge_mvp as mvp  # noqa: E402
import forge_spec as sp  # noqa: E402
import forge_state as fst  # noqa: E402
import test_spec_gate as ts  # noqa: E402  (the good SPEC / GLOSSARY / REVIEW fixtures)

PY = sys.executable
FORGE_STATE = os.path.join(HERE, "forge_state.py")
ADAM = "test fixture, not under test"
OLD = time.time() - 3600          # an hour ago: the build
NEW = time.time()                 # now: proof shot after the build

# A fake stage worker: reads the stage from the prompt, writes the files the test planned for it.
FAKE = r'''
import json, os, re, sys
prompt = sys.stdin.read()
k = re.search(r"Do Stage (\S+),", prompt).group(1)
with open(".fake-calls", "a") as fh:
    fh.write(k + "\n")
plan = json.load(open(".fake-plan.json")).get(k, {})
for rel, text in plan.items():
    if rel == "+FORGE-STATE.md":
        open("FORGE-STATE.md", "a").write(text)
        continue
    os.makedirs(os.path.dirname(rel) or ".", exist_ok=True)
    open(rel, "w").write(text)
'''


def fs(root, *args, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([PY, FORGE_STATE, "-C", root] + list(args), capture_output=True, text=True, env=e)


def ok(root, *args, env=None):
    r = fs(root, *args, env=env)
    assert r.returncode == 0, "forge-state %s failed:\n%s\n%s" % (" ".join(args), r.stdout, r.stderr)
    return r


def new_run(mode="speed-run", family="software"):
    root = tempfile.mkdtemp(prefix="forge-mvp90-")
    ok(root, "init", "--family", family, "--mode", mode)
    return root


def w(root, rel, text, mtime=None):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write(text)
    if mtime:
        os.utime(p, (mtime, mtime))
    return p


def state(root):
    return fst.load(root)[0]


def worker_env(root, plan):
    w(root, ".fake-plan.json", json.dumps(plan))
    script = w(root, ".fake_worker.py", FAKE)
    return {"FORGE_WORKER": "%s %s" % (PY, script), "FORGE_GATE_CMD": "true"}


def calls(root):
    p = os.path.join(root, ".fake-calls")
    return open(p).read().split() if os.path.exists(p) else []


IDEA = "# Idea\n" + "A tool that logs the four weekly job contacts for a claim. " * 4 + \
       "\n\n## Kill criteria\nA free incumbent that does it already kills it.\n"
INTENDED = "\n## Intended use\n" + "Only me for now, no money stake, a second operator never, regret wasted hours. " * 2
VERDICT = ("# Verdict\nBUILD FOR SELF\nDelivery mode: web\n"
           "Others lose: a native app needs the App Store and a CLI is too hard for the operator\n")
STAGE1 = {"validation/%s" % f: "# %s\nartifact body\n" % f for f in (
    "01-expert-panel.md", "02-cep-external-signal.md", "03-synth-survey-report.md", "03-personas.md",
    "04-refutation.md", "06-gap-map.md")}
STAGE1["validation/05-verdict.md"] = VERDICT


# ============================================================ PART A: the driver
def test_driver_loop_runs_workers_records_passes_and_stops_at_the_human_gate():
    root = new_run()
    env = worker_env(root, {"0": {"validation/00-idea.md": IDEA}})
    r = fs(root, "run", env=env)
    assert r.returncode == 2, r.stdout + r.stderr                    # waiting on Adam
    st = state(root)
    assert st["gates"]["G"]["state"] == "n/a" and "speed-run" in st["gates"]["G"]["note"]
    assert st["gates"]["0"]["state"] == "pass" and "verified by forge-state run" in st["gates"]["0"]["note"]
    assert st["gates"]["0A"]["state"] == "pending"
    assert st["asks"][0]["stage"] == "0A" and "five intended-use questions" in st["asks"][0]["ask"]
    assert "WAITING ON ADAM" in st["next_action"] and "Do:" in r.stdout and "Where:" in r.stdout
    assert calls(root) == ["0"]                                   # 0A is Adam's: no worker spun at it


def test_worker_ask_md_stops_the_run_with_its_ask():
    root = new_run()
    w(root, "validation/00-idea.md", IDEA + INTENDED)
    ok(root, "human", "Adam", "--stage", "0A", "--passes", "--how", "chat", "--said", "just me, no stake, nobody else")
    env = worker_env(root, {"1": {"ASK.md": "Stage: 1\nAsk: is the claim weekly or biweekly?\nDevice: chat\n"
                                            "Pass when: Adam answers\n"}})
    r = fs(root, "run", env=env)
    assert r.returncode == 2, r.stdout + r.stderr
    a = state(root)["asks"][0]
    assert a["stage"] == "1" and "weekly or biweekly" in a["ask"] and a["device"] == "chat"
    assert calls(root) == ["1"]


def test_driver_continues_after_adam_answers_and_stops_at_until():
    root = new_run()
    env = worker_env(root, {"0": {"validation/00-idea.md": IDEA},
                            "0A": {"validation/00-idea.md": IDEA + INTENDED},
                            "1": STAGE1,
                            "S": {"SPEC.md": ts.SPEC, "GLOSSARY.md": ts.GLOSSARY, "SPEC-REVIEW.md": ts.REVIEW}})
    w(root, "ASK.md", "Stage: 0A\nAsk: answer the five questions\n")
    ok(root, "human", "Adam", "--stage", "0A", "--passes", "--how", "chat", "--said", "just me, no stake, no second operator")
    r = fs(root, "run", "--until", "S", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    st = state(root)
    for k in ("0", "0A", "1", "S"):
        assert st["gates"][k]["state"] == "pass", (k, st["gates"][k])
    assert st["gates"]["2"]["state"] == "pending"                   # --until S stopped before the build
    assert not os.path.exists(os.path.join(root, "ASK.md"))         # the answered ask was archived
    assert not st.get("asks")


def test_driver_fix_loop_blocks_after_two_rounds():
    root = new_run()
    env = worker_env(root, {"0": {"validation/00-idea.md": "# Idea\ntoo short\n"}})
    r = fs(root, "run", env=env)
    assert r.returncode == 3, r.stdout + r.stderr
    assert calls(root) == ["0", "0", "0"]                          # first try + 2 fix rounds
    g = state(root)["gates"]["0"]
    assert g["state"] == "fail" and g["note"].startswith("BLOCKED after 2 fix rounds")
    assert fs(root, "next").returncode == 3


def test_driver_fix_round_gets_the_errors():
    root = new_run()
    env = worker_env(root, {"0": {"validation/00-idea.md": "# Idea\nshort\n"}})
    fs(root, "run", env=env)
    st = state(root)
    p = drv.worker_prompt(root, st, "0", drv.stage_errors(root, st, "0"), 1)
    assert "FIX ROUND 1 of 2" in p and "00-idea.md" in p and "Never run `forge-state gate`" in p


def test_driver_waits_when_the_machine_is_busy():
    root = new_run()
    w(root, "validation/00-idea.md", IDEA + INTENDED)
    ok(root, "human", "Adam", "--stage", "0A", "--passes", "--how", "chat", "--said", "just me, no stake, nobody else")
    env = worker_env(root, {})
    env["FORGE_GATE_CMD"] = "false"
    r = fs(root, "run", env=env)
    assert r.returncode == 5 and "BUSY  Stage 1" in r.stdout
    assert calls(root) == []


def test_dry_run_changes_nothing_and_prints_the_plan():
    root = new_run()
    w(root, "validation/00-idea.md", IDEA)
    p = os.path.join(root, "FORGE-STATE.md")
    before = open(p).read()
    r = fs(root, "run", "--dry-run")
    assert r.returncode == 0, r.stderr
    assert open(p).read() == before
    assert "RECONCILE  Stage 0" in r.stdout and "dry-run: not written" in r.stdout
    assert "PLAN (dry-run" in r.stdout and "HUMAN GATE" in r.stdout and "Stage 0A" in r.stdout


def test_run_refuses_other_families():
    root = tempfile.mkdtemp()
    ok(root, "init", "--family", "gtm")
    r = fs(root, "run")
    assert r.returncode != 0 and "software and games" in r.stderr


# ---- A2: a hand pass must verify
def test_hand_pass_refused_unless_artifacts_verify():
    root = new_run()
    ok(root, "gate", "G", "n/a", "--note", "speed-run")
    ok(root, "gate", "H", "n/a", "--note", "idea in hand")
    r = fs(root, "gate", "0", "pass")
    assert r.returncode != 0 and "does not verify on disk" in r.stderr and "00-idea.md" in r.stderr
    w(root, "validation/00-idea.md", IDEA)
    ok(root, "gate", "0", "pass")


def test_hand_pass_with_adams_words_is_recorded_as_override():
    root = new_run()
    ok(root, "gate", "G", "n/a", "--note", "x")
    ok(root, "gate", "H", "n/a", "--note", "x")
    assert fs(root, "gate", "0", "pass", "--adam-said", "ok").returncode != 0      # 1 word is not his call
    ok(root, "gate", "0", "pass", "--adam-said", "I wrote the idea on paper")
    assert state(root)["gates"]["0"]["note"].startswith('[ADAM OVERRIDE] "I wrote the idea on paper"')


def test_human_gate_cannot_be_passed_by_a_model():
    root = new_run()
    for k in ("G", "H"):
        ok(root, "gate", k, "n/a", "--note", "x")
    w(root, "validation/00-idea.md", IDEA + INTENDED)
    ok(root, "gate", "0", "pass")
    r = fs(root, "gate", "0A", "pass")                         # the worker wrote answers; Adam never said them
    assert r.returncode != 0 and "HUMAN:" in r.stderr


# ---- A3: reconcile
def test_reconcile_records_what_verifies_and_nothing_else():
    root = new_run()
    w(root, "validation/00-idea.md", IDEA + INTENDED)
    ok(root, "human", "Adam", "--stage", "0A", "--passes", "--how", "chat", "--said", "only me, no stake, no operator")
    for rel, text in STAGE1.items():
        if "05-verdict" not in rel:
            w(root, rel, text)
    st = state(root)
    done, _ = drv.reconcile(root, st, out=lambda s: None)
    assert [k for k, _ in done] == ["0", "0A"]                      # Stage 1 lacks 05-verdict: left alone
    st = state(root)
    assert st["gates"]["0"]["note"].startswith("reconciled by forge-state run: artifacts verify")
    assert st["gates"]["1"]["state"] == "pending"


def test_reconcile_passes_a_failed_gate_whose_artifacts_now_verify():
    root = new_run()
    w(root, "validation/00-idea.md", IDEA)
    ok(root, "gate", "0", "fail", "--note", "thin idea")
    done, _ = drv.reconcile(root, state(root), out=lambda s: None)
    assert ("0" in [k for k, _ in done]) and state(root)["gates"]["0"]["state"] == "pass"


# ============================================================ PART B: the gates
# ---- 4. no bare --force / waive on a blocking gate
def test_bare_force_and_waive_refused_on_blocking_gates():
    root = new_run()
    r = fs(root, "gate", "1", "pass", "--force")
    assert r.returncode != 0 and "bare --force" in r.stderr
    r = fs(root, "gate", "0", "waived", "--note", "skip")
    assert r.returncode != 0 and "Adam's call" in r.stderr
    r = fs(root, "gate", "0", "n/a", "--note", "skip")
    assert r.returncode != 0
    ok(root, "gate", "G", "n/a", "--note", "non-blocking stays a note")
    ok(root, "gate", "0", "waived", "--note", "idea is a one-liner", "--adam-said", "skip the write up")


# ---- 1. real target
def _src(root):
    w(root, "app.py", "print('hi')\n", mtime=OLD)


def test_real_target_device_missing_is_a_human_ask():
    root = tempfile.mkdtemp()
    e = mvp.real_target_errs(root)
    assert e and e[0].startswith("HUMAN:")


def test_real_target_device_rules():
    root = tempfile.mkdtemp()
    _src(root)
    base = "# REAL TARGET\nTarget: ios\nDevice: %s\n\n## Proof\n| Core job | Proof file | What it shows |\n|---|---|---|\n| J1 | %s | home |\n"
    w(root, mvp.REAL_TARGET, base % ("iPhone 16 Simulator", "proof/j1.png"))
    w(root, "proof/j1.png", "x", mtime=NEW)
    assert any("simulator is not the target" in e for e in mvp.real_target_errs(root))
    w(root, mvp.REAL_TARGET, base % ("iPhone 14 Pro Max", "proof/j1.png"))
    assert mvp.real_target_errs(root) == []
    os.utime(os.path.join(root, "proof/j1.png"), (OLD - 600, OLD - 600))      # shot before the build
    assert any("predates the last build" in e for e in mvp.real_target_errs(root))
    w(root, mvp.REAL_TARGET, base % ("iPhone 14 Pro Max", "proof/j1.txt"))
    assert any("not a screenshot or video" in e for e in mvp.real_target_errs(root))


def test_real_target_cli_needs_real_input_and_fresh_output():
    root = tempfile.mkdtemp()
    _src(root)
    w(root, sp.SPEC, "## Core jobs\n- J1: convert the statement\n")
    t = "Target: cli\n\n## Proof\n| Core job | Proof file | What it shows |\n|---|---|---|\n| J1 | %s | ran |\n"
    w(root, mvp.REAL_TARGET, t % "tests/fixtures/in.csv -> proof/out.csv")
    w(root, "tests/fixtures/in.csv", "a")
    w(root, "proof/out.csv", "b", mtime=NEW)
    assert any("test fixture" in e for e in mvp.real_target_errs(root))
    w(root, "proof/oct-statement.csv", "a")
    w(root, mvp.REAL_TARGET, t % "proof/oct-statement.csv -> proof/out.csv")
    assert mvp.real_target_errs(root) == []
    w(root, mvp.REAL_TARGET, t % "proof/out.csv")
    assert any("real input -> real output" in e for e in mvp.real_target_errs(root))


def test_real_target_web_checks_the_live_url(monkeypatch):
    root = tempfile.mkdtemp()
    _src(root)
    w(root, mvp.REAL_TARGET, "Target: web\nURL: https://example.test\n\n## Proof\n| Core job | Proof file | x |\n"
                             "|---|---|---|\n| J1 | proof/home.png | home |\n")
    w(root, "proof/home.png", "x", mtime=NEW)
    monkeypatch.setattr(mvp, "http_status", lambda url, timeout=10: 503)
    assert any("returned 503" in e for e in mvp.real_target_errs(root))
    monkeypatch.setattr(mvp, "http_status", lambda url, timeout=10: 200)
    assert mvp.real_target_errs(root) == []


# ---- 2. dead controls
DEAD = """# DEAD CONTROLS
Driver: playwright
Controls found: 3

## Controls
| Control | Screen | Action | Result | Evidence |
|---|---|---|---|---|
| Save | Edit | click | ok | toast says Saved |
| Export | List | click | %s | downloaded export.csv |
| Delete | List | click | ok | row removed from list |
"""


def test_dead_control_sweep():
    root = tempfile.mkdtemp()
    _src(root)
    assert mvp.dead_controls_errs(root)                           # no file
    w(root, mvp.DEAD_CONTROLS, DEAD % "ok", mtime=NEW)
    assert mvp.dead_controls_errs(root) == []
    w(root, mvp.DEAD_CONTROLS, DEAD % "dead", mtime=NEW)
    assert any("'Export' is DEAD" in e for e in mvp.dead_controls_errs(root))
    w(root, mvp.DEAD_CONTROLS, (DEAD % "ok").replace("found: 3", "found: 9"), mtime=NEW)
    assert any("driver found 9" in e for e in mvp.dead_controls_errs(root))
    w(root, mvp.DEAD_CONTROLS, DEAD % "ok", mtime=OLD - 600)
    assert any("predates the last build" in e for e in mvp.dead_controls_errs(root))
    w(root, mvp.DEAD_CONTROLS, (DEAD % "ok").replace("playwright", "vibes"), mtime=NEW)
    assert any("Driver:" in e for e in mvp.dead_controls_errs(root))


# ---- 3. what do you assume it does (Stage S)
def test_assumed_features_round():
    good = ts.SPEC
    assert sp.check_mvp90(good) == []
    rows = [l for l in good.splitlines() if l.startswith("| ") and "| in |" in l]
    thin = good.replace("\n".join(rows[:3]) + "\n", "")
    assert any("lists 7" in e for e in sp.check_mvp90(thin))
    cut = good.replace('founder: "one at a time is fine"', "orchestrator")
    assert any("out without Adam's words" in e for e in sp.check_mvp90(cut))
    assert sp.check_mvp90(cut, mode="autonomous") == []
    assert any("Core jobs" in e for e in sp.check_mvp90(good.replace("## Core jobs", "## Jobs")))
    assert any("Domain content" in e for e in sp.check_mvp90(good.replace("Domain content: no", "")))


# ---- 6. domain truth
def _domain(root, judge="claude-sonnet-5-5", result="match", n=10, unsourced=0):
    w(root, sp.SPEC, "Domain content: yes\n")
    items = [{"name": "card %d" % i, "source": "" if i < unsourced else "https://rules.test/%d" % i} for i in range(n)]
    w(root, "data/cards.json", json.dumps(items))
    rows = "".join('| %d | card %d | https://rules.test/%d | 3 dmg | "deals three damage to a target" | %s |\n'
                   % (i, i, i, result) for i in range(min(n, 10)))
    w(root, mvp.DOMAIN_TRUTH, "# DOMAIN TRUTH\nChecker: agent-9f\nJudge: %s\nLedger: data/cards.json\n\n## Spot check\n"
      "| # | Item | Source | Product says | Source says | Result |\n|---|---|---|---|---|---|\n%s" % (judge, rows))


def test_domain_truth():
    root = tempfile.mkdtemp()
    w(root, sp.SPEC, "Domain content: no\n")
    assert mvp.domain_truth_errs(root) == []                      # nothing to check
    _domain(root)
    assert mvp.domain_truth_errs(root, builder="agent-1") == []
    assert any("is the builder" in e for e in mvp.domain_truth_errs(root, builder="agent-9f"))
    _domain(root, judge="gemma4:12b")
    assert any("local model alone" in e for e in mvp.domain_truth_errs(root))
    _domain(root, result="wrong")
    assert any("wrong domain content is a defect" in e for e in mvp.domain_truth_errs(root))
    _domain(root, unsourced=2)
    assert any("2 of 10 content items" in e for e in mvp.domain_truth_errs(root))


# ---- 7. delivery mode
def test_delivery_mode_check():
    root = tempfile.mkdtemp()
    w(root, "validation/05-verdict.md", "BUILD FOR SELF\n")
    e = mvp.mode_errs(root)
    assert any("Delivery mode" in x for x in e) and any("Others lose" in x for x in e)
    w(root, "validation/05-verdict.md", VERDICT)
    assert mvp.mode_errs(root) == []


# ---- 8. ICP walkthrough
ICP = """# ICP WALKTHROUGH
ICP: a claimant logging four weekly job contacts
Walker: agent-icp-1
Judge: claude-opus-5-5

## Jobs
| Job | Result | Evidence |
|---|---|---|
| J1 | done | "Paused until 12/01, banner shows the date" |
| J2 | %s | "Resumed, next box ships on 11/03 cycle" |
"""


def test_icp_walkthrough():
    root = tempfile.mkdtemp()
    _src(root)
    w(root, sp.SPEC, ts.SPEC)
    w(root, mvp.ICP_WALK, ICP % "done", mtime=NEW)
    assert mvp.icp_errs(root, builder="main") == []
    w(root, mvp.ICP_WALK, ICP % "stuck", mtime=NEW)
    assert any("J2 is STUCK" in e and "defect" in e for e in mvp.icp_errs(root))
    w(root, mvp.ICP_WALK, (ICP % "done").replace("| J2 |", "| J9 |"), mtime=NEW)
    assert any("J2 was not walked" in e for e in mvp.icp_errs(root))
    w(root, mvp.ICP_WALK, (ICP % "done").replace("claude-opus-5-5", "gemma4:12b"), mtime=NEW)
    assert any("local model alone" in e for e in mvp.icp_errs(root))
    w(root, mvp.ICP_WALK, ICP % "done", mtime=NEW)
    assert any("is the builder" in e for e in mvp.icp_errs(root, builder="agent-icp-1"))


def test_stage_3_needs_the_whole_handoff_bundle():
    root = new_run()
    st = state(root)
    errs = drv.stage_errors(root, st, "3")
    for name in ("usability report", mvp.DEAD_CONTROLS, mvp.ICP_WALK, mvp.REAL_TARGET):
        assert any(name in e for e in errs), name


# ---- 5. stalls
def test_stalls_lists_old_runs_read_only():
    home = tempfile.mkdtemp()
    old, fresh = os.path.join(home, "oldrun"), os.path.join(home, "freshrun")
    for d in (old, fresh):
        os.makedirs(d)
        ok(d, "init", "--mode", "speed-run")
    p = os.path.join(old, "FORGE-STATE.md")
    text = open(p).read().replace('updated: "%s"' % fst.today(), 'updated: "2026-09-01"')
    open(p, "w").write(text)
    ws = w(home, "WORKSPACE.md", "- oldrun: ~/%s\n- fresh: ~/%s\n" % (
        os.path.relpath(old, os.path.expanduser("~")), os.path.relpath(fresh, os.path.expanduser("~"))))
    r = ok(home, "stalls", "--workspace", ws)
    assert "oldrun" in r.stdout and "freshrun" not in r.stdout
    assert "FINISH:" in r.stdout and "KILL:" in r.stdout and "nothing is killed" in r.stdout
    assert open(p).read() == text                                  # read-only


# ---- 9. hand-off score
def test_handoff_recorded_at_stage_4_and_fix_rounds_counted():
    root = new_run()
    st = state(root)
    for k in ("G", "H", "0", "0A", "1", "S", "2", "2H", "3"):
        st["gates"][k] = {"state": "pass", "since": fst.today(), "note": "fixture"}
    fst.save(root, st, fst.load(root)[1], os.path.join(root, "FORGE-STATE.md"))
    r = fs(root, "run", env={"FORGE_GATE_CMD": "true", "FORGE_WORKER": "false"})
    assert r.returncode == 2, r.stdout + r.stderr                  # Stage 4 is Adam's: a human gate
    st = state(root)
    assert st["handoff"]["date"] == fst.today() and st["asks"][0]["stage"] == "4"
    assert "already recorded" in ok(root, "handoff").stdout
    ok(root, "human", "Adam", "--fix", "--how", "text", "--said", "export button does nothing", "--when", "2099-01-01")
    ok(root, "human", "Adam", "--feature", "--how", "text", "--said", "add a dark mode please", "--when", "2099-01-01")
    assert "fix rounds since: 1 · features: 1" in ok(root, "status").stdout and "met" in ok(root, "status").stdout
    ok(root, "human", "Adam", "--fix", "--how", "text", "--said", "save loses the last row", "--when", "2099-01-02")
    assert "MISSED" in ok(root, "status").stdout
    assert fs(root, "human", "Adam", "--fix", "--feature", "--how", "x", "--said", "a b c").returncode != 0


def test_games_build_needs_the_handoff_bundle_and_P_is_human():
    root = new_run(family="games")
    st = state(root)
    assert drv.stage_errors(root, st, "P")[0].startswith("HUMAN:")
    errs = drv.stage_errors(root, st, "2")
    assert any(mvp.ICP_WALK in e for e in errs) and any(mvp.DEAD_CONTROLS in e for e in errs)


def test_only_a_passes_entry_clears_a_human_gate():
    # Pookemon 10/18 dry run: ~40 entries at Stage V, all bug reports and asks, none a verdict.
    root = new_run(family="games")
    ok(root, "human", "Adam", "--stage", "V", "--how", "text", "--said", "sound does not work from the phone")
    assert drv.stage_errors(root, state(root), "V")[0].startswith("HUMAN:")
    ok(root, "human", "Adam", "--stage", "V", "--passes", "--how", "text", "--said", "the slice is fun, build it")
    assert drv.stage_errors(root, state(root), "V") == []


def test_stage_2_needs_every_roadmap_phase_done():
    root = new_run(mode="autonomous")
    w(root, ".planning/ROADMAP.md", "- [x] **Phase 1: Core** - done\n- [ ] **Phase 2: Release** - sign\n")
    with open(os.path.join(root, "FORGE-STATE.md"), "a") as fh:
        fh.write("\n- /gsd-execute-phase 1 -> abc123\n")
    errs = drv.stage_errors(root, state(root), "2")
    assert any("1 phase(s) not complete" in e and "Phase 2" in e for e in errs)
    w(root, ".planning/ROADMAP.md", "- [x] **Phase 1: Core** - done\n- [x] **Phase 2: Release** - sign\n")
    assert drv.stage_errors(root, state(root), "2") == []
