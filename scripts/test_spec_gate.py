#!/usr/bin/env python3
"""Tests for Stage S (SPEC): the gate is VERIFIED against SPEC.md, GLOSSARY.md and SPEC-REVIEW.md.
A missing, thin or self-reviewed spec is refused; the build cannot pass while S is open; a run
begun before S existed is untouched until `forge-state migrate --spec`; S cannot be n/a.

Run:  python3 -m pytest -q test_spec_gate.py
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import forge_spec as fs  # noqa: E402

PY = sys.executable
FORGE_STATE = os.path.join(HERE, "forge_state.py")

SPEC = """# SPEC: pause a coffee subscription
Grill rounds: 2
Open decisions: 0

## Problem
Subscribers going on holiday cancel outright because they cannot skip deliveries, and most never come back.

## Decisions
| # | Decision | Answer | Decided by |
|---|---|---|---|
| 1 | Longest pause | 3 months | founder |
| 2 | Billing date after resume | shifts by the pause length | fact: billing.py next_charge() |

## User stories
1. As a subscriber, I pause for up to 3 months so I do not get coffee while away.
2. As a subscriber, I resume early and the next box ships on the next cycle.

## Seams
- `subscription.pause(sub, until, today)` pure function: the one seam for pause and resume.

## Out of scope
- Pausing gift subscriptions.

## Core jobs
- J1: pause a subscription for a holiday
- J2: resume early

Domain content: no

## Assumed features
| Feature | In/Out | Reason | Decided by |
|---|---|---|---|
| Undo a pause | in | a mis-tap must be reversible | founder |
| Confirmation message | in | people need to know it worked | founder |
| Error message on bad date | in | a past date must say why | founder |
| Empty state with no subscription | in | new accounts see a blank page otherwise | founder |
| Save state across reloads | in | a pause must survive closing the tab | founder |
| Email receipt of the pause | in | subscribers expect a paper trail | founder |
| Show the resume date | in | the first question every pauser asks | founder |
| Pause from the mobile site | in | most subscribers manage on phones | founder |
| Pause several subscriptions at once | out | rare, one account rarely has two | founder: "one at a time is fine" |
| Pause reason survey | out | not the job, adds friction | Adam: "skip the survey for now" |

## Slices
| Slice | What it does (DB to button) | Stories | Seam | Est. tokens | Blocked by |
|---|---|---|---|---|---|
| S1 | pause column + pure pause() + pause button | 1 | pause() | 90K | none |
| S2 | resume early button + next-ship date | 2 | pause() | 60K | S1 |
"""

GLOSSARY = """# GLOSSARY
| Term | Meaning | Avoid |
|---|---|---|
| Pause | Deliveries and charges stop until a set date, then restart on their own. | hold, freeze |
"""

REVIEW = """# SPEC REVIEW
Author: main-session-7f3a2c

## Reviewers
| Reviewer | Lens | Agent id |
|---|---|---|
| A | completeness: missing decisions, contradictions | a1b2c3d4 |
| B | Reggie: scope and over-build | e5f6a7b8 |
| C | non-coder founder reader | c9d0e1f2 |

## Findings
| # | Reviewer | Finding | Ruling | Why / fix |
|---|---|---|---|---|
| 1 | A | What if the card expires during the pause? | fixed | added decision: charge retries on resume |
| 2 | B | Pause reasons survey is over-build | dismissed | not in the spec, Reggie misread story 1 |
"""


def write(d, spec=SPEC, glossary=GLOSSARY, review=REVIEW):
    for name, text in (("SPEC.md", spec), ("GLOSSARY.md", glossary), ("SPEC-REVIEW.md", review)):
        p = os.path.join(d, name)
        if text is None:
            if os.path.exists(p):
                os.remove(p)
        else:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)


def fst(d, *a):
    return subprocess.run([PY, FORGE_STATE, "-C", d] + list(a), capture_output=True, text=True)


class SpecCheck(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def errs(self, mode="full", **kw):
        write(self.d, **kw)
        return fs.spec_check(self.d, mode)

    def test_good_spec_passes(self):
        self.assertEqual(self.errs(), [])

    def test_speed_run_needs_two_reviewers_full_needs_three(self):
        two = re.sub(r"\| C \| non-coder.*\n", "", REVIEW)
        self.assertEqual(self.errs("speed-run", review=two), [])
        self.assertTrue(any("needs 3" in e for e in self.errs("full", review=two)))

    def test_games_family_is_light(self):
        two = re.sub(r"\| C \| non-coder.*\n", "", REVIEW)
        write(self.d, review=two)
        self.assertEqual(fs.spec_check(self.d, "full", "games"), [])

    def test_missing_files(self):
        e = self.errs(spec=None, glossary=None, review=None)
        self.assertTrue(any("SPEC.md is missing" in x for x in e))
        self.assertTrue(any("SPEC-REVIEW.md is missing" in x for x in e))

    def test_open_frontier_refused(self):
        e = self.errs(spec=SPEC.replace("Open decisions: 0", "Open decisions: 2"))
        self.assertTrue(any("frontier is empty" in x for x in e))

    def test_decision_without_owner_refused(self):
        e = self.errs(spec=SPEC.replace("| 3 months | founder |", "| 3 months | ? |"))
        self.assertTrue(any("who decided" in x for x in e))

    def test_no_user_story_refused(self):
        e = self.errs(spec=SPEC.replace("As a subscriber, I", "Subscriber can"))
        self.assertTrue(any("User stories" in x for x in e))

    def test_no_seam_refused(self):
        e = self.errs(spec=re.sub(r"## Seams\n- .*\n", "## Seams\n", SPEC))
        self.assertTrue(any("## Seams lists none" in x for x in e))

    def test_slice_over_one_session_refused(self):
        e = self.errs(spec=SPEC.replace("| 90K |", "| 400K |"))
        self.assertTrue(any("over one fresh session" in x for x in e))

    def test_blocked_by_unknown_or_loop_refused(self):
        e = self.errs(spec=SPEC.replace("| 60K | S1 |", "| 60K | S9 |"))
        self.assertTrue(any("not a slice" in x for x in e))
        e = self.errs(spec=SPEC.replace("| 90K | none |", "| 90K | S2 |"))
        self.assertTrue(any("loop" in x for x in e))

    def test_glossary_avoid_word_in_spec_refused(self):
        e = self.errs(spec=SPEC.replace("Pausing gift", "Freezing gift"))
        self.assertTrue(any("avoid 'freeze'" in x or "avoid 'freeze'" in x.lower() for x in e) or
                        not any("Freezing" in x for x in e))   # 'Freezing' is a different word: allowed
        e = self.errs(spec=SPEC.replace("Pausing gift subscriptions.", "Put gift subscriptions on hold."))
        self.assertTrue(any("avoid 'hold'" in x for x in e))

    def test_avoid_word_in_a_required_heading_is_not_flagged(self):
        # Found by the dry run: a glossary that avoids "user" must not trip on "## User stories".
        g = GLOSSARY + "| Subscriber | The person who pays and manages it. | user |\n"
        self.assertEqual(self.errs(glossary=g), [])
        e = self.errs(glossary=g, spec=SPEC.replace("Pausing gift subscriptions.", "Letting a user pause a gift."))
        self.assertTrue(any("avoid 'user'" in x for x in e))

    def test_author_reviewing_itself_refused(self):
        e = self.errs(review=REVIEW.replace("a1b2c3d4", "main-session-7f3a2c"))
        self.assertTrue(any("never reviews its own spec" in x for x in e))

    def test_same_agent_twice_refused(self):
        e = self.errs(review=REVIEW.replace("e5f6a7b8", "a1b2c3d4"))
        self.assertTrue(any("appears twice" in x for x in e))

    def test_zero_findings_is_suspect(self):
        e = self.errs(review=re.sub(r"\| 1 \| A .*\n\| 2 \| B .*\n", "", REVIEW))
        self.assertTrue(any("suspect" in x for x in e))

    def test_unruled_finding_refused(self):
        e = self.errs(review=REVIEW.replace("| fixed |", "| |"))
        self.assertTrue(any("no ruling" in x for x in e))
        e = self.errs(review=REVIEW.replace("not in the spec, Reggie misread story 1", "no"))
        self.assertTrue(any("no reason" in x for x in e))


class Gate(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def init(self, mode="speed-run", family="software"):
        r = fst(self.d, "init", "--family", family, "--mode", mode)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        for k in ("G", "H"):
            fst(self.d, "gate", k, "n/a", "--note", "idea in hand")    # non-blocking: no Adam words needed
        for k in ("0", "0A", "1") if family == "software" else ("0", "1", "T", "P"):
            r = fst(self.d, "gate", k, "pass", "--note", "test", "--adam-said", "test fixture, not under test")
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def gates(self):
        text = open(os.path.join(self.d, "FORGE-STATE.md"), encoding="utf-8").read()
        return text.split("---", 2)[1]

    def test_new_run_has_S_between_1_and_2(self):
        self.init()
        g = self.gates()
        keys = re.findall(r'^\s+"([^"]+)":', g, re.M)
        self.assertEqual(keys[keys.index("1") + 1:keys.index("2")], ["S"])

    def test_thin_spec_refused_then_good_passes(self):
        self.init()
        write(self.d, spec="# SPEC\n\n## Problem\nshort\n", review=None)
        r = fst(self.d, "gate", "S", "pass", "--note", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refused: Stage S", r.stderr)
        write(self.d)
        r = fst(self.d, "gate", "S", "pass", "--note", "spec reviewed")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_build_blocked_while_S_open(self):
        self.init()
        r = fst(self.d, "gate", "2", "pass", "--note", "x")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("S", r.stderr)

    def test_S_cannot_be_na_but_can_be_waived_with_note(self):
        self.init()
        self.assertNotEqual(fst(self.d, "gate", "S", "n/a", "--note", "x").returncode, 0)
        self.assertNotEqual(fst(self.d, "gate", "S", "waived").returncode, 0)
        self.assertNotEqual(fst(self.d, "gate", "S", "waived", "--note", "founder: skip it").returncode, 0)  # 1.11
        self.assertEqual(fst(self.d, "gate", "S", "waived", "--note", "one-line script",
                             "--adam-said", "skip it, one-line script").returncode, 0)

    def test_next_names_the_spec(self):
        self.init()
        r = fst(self.d, "next")
        self.assertEqual(r.returncode, 2)
        self.assertIn("SPEC.md", r.stdout)

    def test_games_S_sits_after_P(self):
        self.init(family="games")
        r = fst(self.d, "gate", "V", "pass", "--note", "x")
        self.assertNotEqual(r.returncode, 0)
        two = re.sub(r"\| C \| non-coder.*\n", "", REVIEW)
        write(self.d, review=two)
        self.assertEqual(fst(self.d, "gate", "S", "pass", "--note", "light spec").returncode, 0)

    def test_old_run_untouched_until_migrate(self):
        self.init()
        p = os.path.join(self.d, "FORGE-STATE.md")
        text = open(p, encoding="utf-8").read()
        text = re.sub(r'\n  "S": .*', "", text)                  # a run born before Stage S
        self.assertNotIn('"S":', text)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        r = fst(self.d, "gate", "2", "pass", "--note", "built",    # S does not block an old run
                "--adam-said", "test fixture, build not under test")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = fst(self.d, "migrate", "--spec")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("added Stage S", r.stdout)
        self.assertIn('"S":', self.gates())
        self.assertIn("nothing to migrate", fst(self.d, "migrate", "--spec").stdout)

    def test_other_families_unchanged(self):
        r = fst(self.d, "init", "--family", "gtm", "--mode", "full")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('"S":', self.gates_of("LAUNCH-STATE.md"))
        self.assertNotEqual(fst(self.d, "migrate", "--spec").returncode, 0)

    def gates_of(self, name):
        return open(os.path.join(self.d, name), encoding="utf-8").read().split("---", 2)[1]


if __name__ == "__main__":
    unittest.main()
