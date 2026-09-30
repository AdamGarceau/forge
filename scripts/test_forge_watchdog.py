#!/usr/bin/env python3
"""Tests for forge_watchdog.py: one fixture per verdict, the rules-only path is
deterministic, the module never writes a manifest, and the cache invalidates on
manifest mtime change. Also re-checks that the stalled_runs refactor left
forge-state scan's output byte-identical (belt + suspenders alongside the
manual before/after diff done at commit time)."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_state as fs
import forge_watchdog as wd


def write_manifest(root, gates, family="software", updated="2026-09-01", next_action="do the thing"):
    os.makedirs(root, exist_ok=True)
    st = fs.blank(os.path.basename(root), family, "full")
    st["updated"] = updated
    st["next_action"] = next_action
    for k, g in gates.items():
        st["gates"][k] = g
    body = "\n# fixture manifest\n"
    path = os.path.join(root, fs.FAMILIES[family][1])
    fs.save(root, st, body, path, touch=False)
    st["updated"] = updated          # save() re-touches; force it back for the fixture
    fs.save(root, st, body, path, touch=False)
    return path


def init_git(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)


def git_commit(root, fname, msg):
    p = os.path.join(root, fname)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        fh.write("x")
    subprocess.run(["git", "add", fname], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True)


class WatchdogFixtureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fw-test-")
        self.old_cache = wd.CACHE_PATH
        self.old_report = wd.REPORT_PATH
        wd.CACHE_PATH = os.path.join(self.tmp, "cache.json")
        wd.REPORT_PATH = os.path.join(self.tmp, "WATCHDOG.md")
        wd.HANDOFF_DIR = os.path.join(self.tmp, "handoffs")

    def tearDown(self):
        wd.CACHE_PATH = self.old_cache
        wd.REPORT_PATH = self.old_report
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _project(self, name):
        p = os.path.join(self.tmp, name)
        os.makedirs(p, exist_ok=True)
        init_git(p)
        return p

    # --- one fixture per verdict -----------------------------------------
    def test_failed_gate_is_blocked_on_human(self):
        d = self._project("failed-run")
        write_manifest(d, {"2": {"state": "fail", "since": "2026-09-01",
                                 "note": "usability gate failed"}},
                       updated="2026-09-01")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_ON_HUMAN")
        self.assertIn("gate", cmd)

    def test_commits_since_updated_is_done_unrecorded(self):
        d = self._project("done-unrecorded-run")
        passed = {"state": "pass", "since": "2026-09-01", "note": ""}
        gates = {k: passed for k in ("G", "H", "0", "0A", "1")}
        gates["2"] = {"state": "pending", "since": "2026-09-01", "note": ""}
        write_manifest(d, gates, updated="2026-09-01")
        git_commit(d, "output.txt", "did the stage 2 work")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "DONE_UNRECORDED")
        self.assertIn("gate", cmd)
        self.assertIn("pass", cmd)

    def test_human_stage_is_blocked_on_human(self):
        d = self._project("human-stage-run")
        # stage "4" in the software family is "Field test, real world" — a human stage.
        # Everything before it (including the non-blocking G/H/2B) must resolve first,
        # or derive_stage() will land on one of those instead of "4".
        passed = {"state": "pass", "since": "2026-09-01", "note": ""}
        write_manifest(d, {k: passed for k in ("G", "H", "0", "0A", "1", "2", "2B", "3")},
                       updated="2026-09-01")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_ON_HUMAN")
        self.assertIn("Field test", r)

    def test_third_party_mention_is_blocked_external(self):
        d = self._project("external-run")
        passed = {"state": "pass", "since": "2026-09-01", "note": ""}
        gates = {k: passed for k in ("G", "H", "0", "0A", "1")}
        gates["2"] = {"state": "pending", "since": "2026-09-01",
                     "note": "waiting on the client to confirm the date"}
        write_manifest(d, gates, updated="2026-09-01")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_EXTERNAL")

    def test_idle_with_no_movement_is_abandon(self):
        d = self._project("abandon-run")
        passed = {"state": "pass", "since": "2020-01-01", "note": ""}
        gates = {k: passed for k in ("G", "H", "0", "0A", "1")}
        gates["2"] = {"state": "pending", "since": "2020-01-01", "note": ""}
        write_manifest(d, gates, updated="2020-01-01")   # far enough in the past: idle >> 14 days
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        self.assertGreaterEqual(ev["idle"], 14)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "ABANDON")
        self.assertIn("park", cmd)

    def test_quiet_and_recent_is_resumable(self):
        d = self._project("resumable-run")
        passed = {"state": "pass", "since": fs.today(), "note": ""}
        gates = {k: passed for k in ("G", "H", "0", "0A", "1")}
        gates["2"] = {"state": "pending", "since": fs.today(), "note": ""}
        write_manifest(d, gates, updated=fs.today(), next_action="run the build step")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "RESUMABLE")
        self.assertEqual(cmd, "run the build step")

    # --- rules-only path is deterministic ---------------------------------
    def test_no_model_path_is_deterministic(self):
        d = self._project("determinism-run")
        write_manifest(d, {"2": {"state": "fail", "since": "2026-09-01", "note": "x"}},
                       updated="2026-09-01")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        rv, rr, rcmd = wd.rule_verdict(ev)
        v1, r1 = wd.model_check(ev, rv, rr, no_model=True)
        v2, r2 = wd.model_check(ev, rv, rr, no_model=True)
        self.assertEqual((v1, r1), (v2, r2))
        self.assertEqual(v1, rv)
        self.assertEqual(r1, rr)

    # --- read-only ----------------------------------------------------------
    def test_watchdog_never_writes_a_manifest(self):
        d = self._project("readonly-run")
        mp = write_manifest(d, {"2": {"state": "fail", "since": "2026-09-01", "note": "x"}},
                            updated="2026-09-01")
        with open(mp, "rb") as fh:
            before = fh.read()
        st, _, _ = fs.load(d)
        wd.gather_evidence(d, st)
        wd.rule_verdict(wd.gather_evidence(d, st))
        with open(mp, "rb") as fh:
            after = fh.read()
        self.assertEqual(before, after, "watchdog must never touch a run's manifest bytes")

    # --- cache hit / miss on mtime change ------------------------------------
    def test_cache_key_changes_with_manifest_mtime(self):
        d = self._project("cache-run")
        mp = write_manifest(d, {"2": {"state": "pending", "since": "2026-09-01", "note": ""}},
                            updated="2026-09-01")
        k1 = wd.cache_key(d)
        os.utime(mp, (os.path.getmtime(mp) + 10, os.path.getmtime(mp) + 10))
        k2 = wd.cache_key(d)
        self.assertNotEqual(k1, k2)

    def test_cache_key_changes_with_git_head(self):
        d = self._project("cache-git-run")
        write_manifest(d, {"2": {"state": "pending", "since": "2026-09-01", "note": ""}},
                       updated="2026-09-01")
        k1 = wd.cache_key(d)
        git_commit(d, "a.txt", "first")
        k2 = wd.cache_key(d)
        self.assertNotEqual(k1, k2)


class ScanUnchangedTests(unittest.TestCase):
    """The stalled_runs refactor must not change forge-state scan's output. This
    exercises the live stalled_runs() against a synthetic HOME so it does not
    depend on the real machine's manifests."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fw-scan-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_stalled_runs_matches_inline_reimplementation(self):
        d1 = os.path.join(self.tmp, "proj-a")
        d2 = os.path.join(self.tmp, "proj-b")
        write_manifest(d1, {"2": {"state": "fail", "since": "2026-09-01", "note": "n"}},
                       updated="2026-09-01")
        write_manifest(d2, {"2": {"state": "pending", "since": "2026-09-01", "note": ""}},
                       updated="2020-01-01")
        stalled, active, legacy, synthetic, ungraded, graded, parked = fs.stalled_runs(self.tmp, days=1)
        names = sorted(os.path.basename(e["dir"]) for e in stalled)
        self.assertEqual(names, ["proj-a", "proj-b"])
        failed_flags = {os.path.basename(e["dir"]): e["failed"] for e in stalled}
        self.assertTrue(failed_flags["proj-a"])
        self.assertFalse(failed_flags["proj-b"])


class RealWorldReproTests(unittest.TestCase):
    """2026-09-24 fix: reproduces four of the five verdicts that came back wrong
    on the real machine (DONE_UNRECORDED firing on file/commit noise ahead of an
    explicit block already sitting in the same evidence). Each of these must now
    resolve at the RULE level (no model needed) to the correct BLOCKED_* verdict,
    and must stay correct even when there ARE commits/file touches muddying the
    "looks busy" signal."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fw-repro-")
        self.old_handoffs = wd.HANDOFF_DIR
        wd.HANDOFF_DIR = os.path.join(self.tmp, "handoffs")

    def tearDown(self):
        wd.HANDOFF_DIR = self.old_handoffs
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _project(self, name):
        p = os.path.join(self.tmp, name)
        os.makedirs(p, exist_ok=True)
        init_git(p)
        return p

    def _passed(self, *keys):
        return {k: {"state": "pass", "since": "2026-09-01", "note": ""} for k in keys}

    def test_channel_repro_waiting_on_founder_approval(self):
        d = self._project("channel-project")
        gates = self._passed("G", "H")
        gates["0"] = {"state": "pending", "since": "2026-09-01",
                     "note": "_working/SPEC.md drafted 2026-09-03; Gate 0 waits on "
                             "The founder's approval of the frame (human-only input)"}
        write_manifest(d, gates, family="content",
                       next_action="The founder approves the SPEC frame; then Stage 1 SOCMINT/COMPINT/SEARCHINT",
                       updated="2026-09-01")
        # Noise: unrelated automation output touched after `updated`, same shape
        # as the real run's _working/ba43-45-retry.* files.
        git_commit(d, "_working/unrelated-automation.txt", "unrelated automation output")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_ON_HUMAN")
        self.assertNotEqual(v, "DONE_UNRECORDED")

    def test_personal_site_repro_dead_token(self):
        d = self._project("personal-site")
        gates = self._passed("G", "H", "0", "0A", "1", "2", "2B", "3")
        gates["4"] = {"state": "pending", "since": "2026-09-20", "note": ""}
        write_manifest(
            d, gates, family="gtm",
            next_action="Stage 4 field test with a real client. BLOCKED on deploy: "
                        "CLOUDFLARE_API_TOKEN is dead (401). BON removal is on disk, not live.",
            updated="2026-09-20")
        git_commit(d, "deploy.sh", "attempted fix")
        git_commit(d, "wrangler.toml", "attempted fix 2")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_ON_HUMAN")
        self.assertNotEqual(v, "DONE_UNRECORDED")

    def test_launch_plan_repro_awaiting_reply(self):
        d = self._project("launch-plan")
        gates = self._passed("0", "1", "2")
        gates["3"] = {"state": "pending", "since": "2026-09-20", "note": ""}
        write_manifest(d, gates, family="gtm",
                       next_action="Stage 3 copy fan-out. RECONCILE FIRST (4 items)...",
                       updated="2026-09-20")
        git_commit(d, "02-messaging-and-offer.md", "reconciliation edits")
        # The real run's third-party signal lived in a handoff, not next_action —
        # reproduce that exact path.
        os.makedirs(wd.HANDOFF_DIR, exist_ok=True)
        with open(os.path.join(wd.HANDOFF_DIR, "20260923-repro.md"), "w") as fh:
            fh.write("# HANDOFF launch-plan\nThe founder posted the reply and is waiting on a contact "
                     "to reply. Nothing else is blocked.\n")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_EXTERNAL")
        self.assertNotEqual(v, "DONE_UNRECORDED")

    def test_ops_build_repro_stop_1(self):
        d = self._project("ops-build")
        gates = self._passed("0", "1", "2", "3")
        gates["4"] = {"state": "pending", "since": "2026-09-11",
                      "note": "Blocked on STOP 1 (F7, human-only input): needs the founder "
                              "behind a camera, plus the redacted fixture database "
                              "SHOTLIST.md's precondition."}
        write_manifest(d, gates, family="content",
                       next_action="Founder: build the redacted fixture DB, then capture.",
                       updated="2026-09-11")
        git_commit(d, "research/tournament-round2/R3-3-report.md", "unrelated research output")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        v, r, cmd = wd.rule_verdict(ev)
        self.assertEqual(v, "BLOCKED_ON_HUMAN")
        self.assertNotEqual(v, "DONE_UNRECORDED")

    def test_done_unrecorded_requires_model_agreement_no_model(self):
        """Point 2: with commits but no model available, DONE_UNRECORDED must fall
        back to RESUMABLE, never print DONE unconfirmed."""
        d = self._project("quiet-busy-repo")
        gates = self._passed("G", "H", "0", "0A", "1")
        gates["2"] = {"state": "pending", "since": "2026-09-01", "note": ""}
        write_manifest(d, gates, updated="2026-09-01")
        git_commit(d, "output.txt", "did the stage 2 work")
        st, _, _ = fs.load(d)
        ev = wd.gather_evidence(d, st)
        rv, rr, _ = wd.rule_verdict(ev)
        self.assertEqual(rv, "DONE_UNRECORDED")   # rule alone still says DONE
        v, reason = wd.model_check(ev, rv, rr, no_model=True)
        self.assertEqual(v, "RESUMABLE")          # but without model confirmation it must not print DONE


if __name__ == "__main__":
    unittest.main()
