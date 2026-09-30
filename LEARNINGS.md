# Forge — Pipeline Learnings

A run that doesn't write back is wasted. Append what the PIPELINE itself got right
or wrong each time forge runs.

---

## Canonical exemplar: DEADRECKON (the proof the process works)

The founder, verbatim, 2026-07-06: *"Deadreckon works perfectly and is exactly the way
we want it. We gave it a TM and had it run the gauntlet. We made a working app by
the end of lunch, all from my phone. It works perfectly for the audience."*

This is the gold standard forge is built to reproduce. What made it work:

1. **A single authoritative input, handed over whole.** The founder sent one photo of the
   Army manual TC 3-25.26 and said "the works." The manual WAS the spec. When a real
   source of truth exists, feed it in and let the build derive requirements from it.
2. **"Run the gauntlet."** Synthetic Army review board + multi-TM research validated
   the approach BEFORE building; then 5 GV-style usability sprints with flawed
   personas + a designer + a technical writer drove it from a round-1 low of 4/10 to
   9/10 across all reviewers. The gates are the quality.
3. **Built from his phone, over lunch.** The non-coder founder never touched code or
   project management. He spoke outcomes ("follow the compass like a GPS"), Claude
   translated, built, screenshotted, committed, deployed, per feature. Speed came
   from continuous shipping, not corner-cutting.
4. **"Works perfectly for the audience" was VERIFIED, not asserted.** Coordinate math
   cross-checked against a real CalTopo paper map; field-tested on real terrain and
   precise. The field test (Stage 4) is what turns "should work" into "works."
5. **Provenance nearly lost.** The build lived in a cloud session and its repo took a
   30-minute forensic hunt to find afterward. Lesson baked into forge Stage 2/5:
   register in the workspace registry, push to a durable repo, write state files — so no future
   session has to reconstruct where a working app came from.

Live: deadreckon.adamgarceau.com ·
session patterns: references/deadreckon-session-patterns.md

---

## Run log

### 2026-07-06 — forge skill smoke test (2 validation-only evals, with-skill vs baseline)
- Military drill-pay (LES) audit tool: with-skill 6/6 assertions, verdict BUILD FOR SELF (speed-run,
  scoped to a back-catalog audit). Baseline 4/6: correct NO-GO instinct but no kill
  criteria, no three-verdict vocabulary.
- Franchise ads grader: with-skill 6/6, verdict DON'T BUILD (panel 4/4 against,
  synth 3.95/10 with hypothesized buyer LOWEST, structural refutation). Baseline 4/6:
  also killed it, but landed on "conditional GO as lead magnet" with no refutation
  artifact and no test of the buyer hypothesis.
- TAKEAWAY: forge's discriminating value is the front-end DISCIPLINE — kill criteria
  before research, the three honest verdicts, and a mandatory adversarial refutation.
  Raw Claude reaches good instincts but skips the structure that makes a verdict
  defensible months later. Cost: ~7-9 min vs ~2 min. Worth it for build/don't-build
  decisions; the speed-run mode keeps small self-tools from over-paying.
- PIPELINE FIX FOR NEXT TIME: baselines defaulted to GO/NO-GO vocabulary; that's fine
  (they're the baseline). No skill change needed from this run — the three-verdict
  framing and refutation pass are already the differentiators and they fired correctly.

---

## Run: a generated party-kit site (2026-08)

Verdict BUILD FOR SELF (speed-run). 5 GSD phases, 4 quick-task gap closures, 4 usability rounds,
191 tests. Shipped green.

### 1. Automated verification passed three phases that a human failed on sight

| Phase | Programmatic score | What a human saw |
|---|---|---|
| 2 — asset generation | 4/4 must-haves | The OG card was a **blank cream rectangle**, 6KB |
| 3 — site generation | 5/5 success criteria | The landing page was a **blank void** below the age pill |
| 3 (again, after fix) | all green | Age pill read **"turning 7TH"**; story read **"with an puppy party theme"** |

Every one passed exit codes, file assertions, dimension checks and full test suites. The blank
OG card was a *valid* 1200×630 JPEG. The blank landing page had all its markup present.

**The rule:** these checks verify that files and strings exist, not that a human can see anything.
Any phase whose output is judged by eye needs either a human gate or a rendering assertion
(screenshot the page with JS disabled and count distinct colours below the fold). The verifier
was RIGHT to mark those phases `human_needed` rather than pass them; do not tune that away.

### 2. `gsd-sdk auto` picks the next phase from the ROADMAP checkbox, not STATE.md

Marking a phase's verification `passed` and advancing `.planning/STATE.md` is **not enough**. The
run re-planned a phase twice before the roadmap checkbox turned out to be the actual pointer.
Advancing a phase by hand means all three: verification frontmatter, the roadmap checkbox (and its
trailing plan boxes), and STATE. A phase stuck at `human_needed` makes `auto` exit with
`success: false` and no work done; that looks like a crash and is not one.

### 3. A test can encode the bug it should have caught

A test asserted the hero alt text *starts with the child's name*. That assertion is exactly why a
label-shaped alt survived: the test was actively protecting the defect. When fixing a defect, read
the tests that were green while it existed. One of them is often specifying it.

### 4. Fixing one instance of a class leaves the others

A helper inlined in one template fixed "turning SEVEN" on one surface while three others kept
"turning 7TH". A pronoun fix removed one error and introduced a hardcoded article ("an puppy").
**Rule:** after fixing a copy or template defect, grep the *generated output* for the pattern
across every surface, and prefer removing a failure mode over approximating it ("with a theme of
X" cannot have article agreement errors; a vowel heuristic can).

### 5. Stale gitignored build output can make a broken pipeline look green

A build script never ran one of its steps; the broken-reference guard only fired because a stale
output file from an earlier manual run happened to be on disk. A fresh clone would have passed
because the breaking file had not been generated yet. **Verify a pipeline after clearing its
gitignored output.** "Passes" on a dirty tree means nothing.

### 6. A synthetic-usability harness can misrepresent the product to its own judges

A usability round dropped 6.7 to 5.3 because two personas named the same worst problem: the image
description "at the very bottom of the page, after the footer." It was not; the linearisation
script matched only paired tags, so self-closing `<img/>` never matched. The judges reasoned
correctly about a false input. **Before treating a score drop as a regression, verify the harness
still represents the artefact.**

### 7. GROUND_TRUTH blocks fix false negatives and can over-correct into praise

After the GROUND_TRUTH block went in, the next round came back with two 10/10s and "none
material", which the sycophancy guard says to distrust. What saved it was the third persona
holding at 8/10 with the same concrete objection filed in all four rounds. **Trust a panel's
consistent dissenter over its consensus.** A persona that repeats one concrete objection across
rounds is signal; one that flips about unchanged text is noise.

### 8. The plateau rule earned its keep

Four rounds, three shapes for one control, and the oldest persona stayed nervous through all of
them: a structural ceiling, not a quality gap. Declaring it and routing the question to the real
field test is cheaper than a fifth round.

### 9. Process notes that worked

- **Executor reports numbers, orchestrator does the looking.** Telling every executor to run the
  checks, report actual values, and STOP without self-approving caught the blank card, the blank
  page, "turning 7TH", a 320px clip, and a doubled alt text.
- **Keep long GSD runs alive** (`caffeinate` + `nohup`); plain background jobs died at turn boundaries.
- **Quick tasks are the right tool for gap closure.** `gsd-sdk auto` will not reopen a completed
  phase, so a UAT failure written after the fact is ignored; a `/gsd-quick` against the UAT
  document closes it properly.

## Run: a founder's portfolio site (2026-08)

Verdict BUILD FOR MARKET on real but thin evidence. Shipped same day.

### PIPELINE BUG: validation artifacts live inside the deploy root
Forge writes `validation/`, `.planning/`, `.reggie/` and `FORGE-STATE.md` into the project
directory. For a WEBSITE project the project directory IS the deploy root, so a deploy of `.`
publishes buyer personas, pricing rationale, internal strategy and private notes to the open
internet. This was caught by hand at the deploy step, not by the pipeline.

**Fix:** any web/deployable build must produce a deploy filter (staging dir or ignore file) as a
Stage 2 requirement, with a leak check that FAILS the deploy rather than warning.

### PIPELINE BUG: no version-control precondition before editing live assets
The site had been live for months and was never in git. The build was one command away from
overwriting a live homepage with no way back.

**Fix:** Stage 2 checks `git rev-parse` in the project dir BEFORE the first edit. If the project
is not under version control, initialize it and commit a baseline snapshot first.

### The synth-survey harness saturates as copy grows
Round scores: 6.85, 8.08, 7.99, 7.93, 7.73, 7.69. The last two rounds added a written policy and
a collaboration workflow, both answering objections the panel raised, and the overall score fell
each time. Per-segment data showed the truth: one segment hit its joint best in the final round
while the average dropped. Longer copy dilutes absolute resonance scoring.

**Fix:** the plateau rule works, but absolute score should not be the only signal. Track
per-segment deltas and whether specific objections were closed. A falling average with a rising
target segment is a PASS, not a regression.

### What worked
- **Real signal over simulation (rule 13) was decisive.** The CEP came from a live group text with
  an actual buyer; the winning promise came verbatim from the buyer's own words.
- **The two-sided in-house veto earned its place.** The panel repeatedly demanded a published
  recurring discount. Refusing it cost score and protected the business.
- **The accessibility gate caught a real defect no persona could have:** white on the brand accent
  measured 2.61:1 in dark mode across every button, including two pre-existing failures.
- **The blind persona then caught what the automated audit could not:** every proof element and
  the revision workflow were visual. Automated tools score markup; only the persona asked whether
  a blind buyer could evaluate the work.
- **Founder-in-the-loop reversals improved the product.** The founder struck a policy, reversed
  mid-build, and that produced a written 4-point policy instead of a vague claim. They also
  volunteered a collaboration workflow, the strongest differentiator on the page, which appeared
  in no draft. Neither came from research. Ask the founder what they actually do before writing
  what they sell.

## A setup run for a desktop app (BUILD FOR SELF, full mode)

1. **A founder can override the ICP to themselves.** Population of one: mitigate with
   state-variance personas (the founder's operating states), not clones. The survey plateaued at
   8.13 to 8.19. Treat roughly 8.1-8.2 as a small local model's ceiling for honest technical
   concept docs; declare the plateau, don't chase it.
2. **A planner hallucinated a prerequisite** that the vendor manual contradicts. The orchestrator
   must fact-check plan `user_setup` blocks against primary docs before execution.
3. **An executor called an API method on the wrong object** and reported the plan's canned
   diagnostic instead of probing. When an API call returns None, getattr the method on every
   candidate object before concluding "not installed."
4. **Sandboxed executors can't edit global settings or do recursive deletes.** Route those steps
   to the orchestrator explicitly in the plan.
5. **Free lanes die mid-run** (quota exhausted on call 1). Put the fallback order in every run's
   routing table up front.
6. **A red team earns its keep even at 0 kills** when it changes the build. Metric: number of
   survives-with-fix items that became requirements.
7. **"Committed green" is not working for config artifacts.** A config shipped with an unparseable
   filter AND its source folder excluded; both invisible until a human opened the window. Exit
   criterion for any UI-rendered config: a screenshot with a non-zero result count, not a file diff.
8. **Stage 3 for a desktop-app setup:** drive it once with computer-use (ground truth), then a
   local persona panel judges the observed reality. Every judge at 9 and none at 10 is the honest
   ceiling when the design deliberately keeps one human rule.

## Forge ruled on a build without ever asking what it was for

**What happened.** An ops app was validated and ruled **BUILD FOR SELF**, which put it in
speed-run: Stage G (GTM) skipped as "internal tool for one client business," Stage 1 compressed,
per-stage approval waived on a blanket "I'm away, you can do this." Hours later: *"This is for
market. This is business. I'm going to get equity in this business."*

**The failure is upstream of the verdict.** The verdict was defensible on what Forge knew. Forge
never asked the one question that decides the run mode: what is this for, and do you have a
stake in it. It inferred "personal tool" from "the founder is the only user today," which is true
of essentially every product at the start.

**Why it is expensive.** A wrong run mode does not produce a wrong artifact you can spot and fix.
It **silently deletes whole stages**, then writes the deletions into FORGE-STATE.md as reasoned
gate overrides, so the next session inherits them as settled.

**Fix, shipped in SKILL.md as Stage 0A (blocking):** five intake questions before any research or
verdict, answers recorded in `00-idea.md` under **Intended use**. A verdict change re-opens the
run and **expires every override granted under the old verdict**, including blanket away-approval.

## Audit of the whole Forge family

The idea (a rule that Forge does not stop, a state machine, a hook) had shipped in a shape that
could not do the job:

1. **The stop was still in the file.** The rule said Forge does not stop; Stage 2 still said
   "Forge STOPS at each stage boundary and gets the founder's explicit go." A skill that says
   both does whichever it read last. Stage 2 now has exactly one approval beat: show the GSD PLAN
   before code. Everything else is a report.
2. **The state machine could not advance.** `stage` and `next_action` were never updated by
   `gate`; out-of-order passes were accepted silently; a FAILED gate looked like a pending one;
   non-blocking stages were never reported, so a run "finished" with nothing shipped.
3. **Two files for one run.** A JSON sidecar beside the markdown manifest is the same disease as
   two SKILL.md copies: they drift. The manifest is now YAML frontmatter plus prose in one file.
4. **The scan could not see most families**: it looked one level down for a single manifest name,
   and called every active project "stalled." It now walks to depth 5, knows each family's
   manifest name, and stalls only after a day idle or on a FAILED gate.
5. **The hook announced itself every session.** `scan` is now silent when clean and the hook just
   relays output.
6. **Pasted, not integrated.** Siblings carried a pasted rule with the wrong number, cited rules
   they did not have, and told you to `init` in a directory that would put one state file over
   many packages.

**Pattern:** when a fix adds a mechanism, grep the skill for the sentence the mechanism replaces.
If the old sentence is still there, the fix is a second opinion, not a fix.

## FAMILY-RULES.md: the shared rulebook

Every family SKILL.md opens with "inherits FAMILY-RULES.md" and carries only its deltas. Rule
numbers inside each family stayed stable; a moved rule keeps its number and title and points at
its F-number, because stage sections and siblings cite those numbers. Renumbering would have
recreated the drift class the rulebook exists to kill.

**The verification is a grep, and it caught something.** Sentences that must exist only in the
rulebook; the first pass found one survivor (a stage restating the GROUND_TRUTH and plateau
rules inline). A stage restating an operating rule is the same bug as a sibling restating it.
Run the grep at the end of any session that edits a family file.

**Pattern:** when a family has an exemplar failure on disk, the family's rules are that verdict
file's findings, one rule each, with the date. A rule with a scar is obeyed; a rule from
principle is skimmed.

## The persona library

One sourced panel per file, an index of audience/sources/n/date/loaded-by, and F8 reading "load
and extend, never rebuild." Seeding only from disk held: an inventory sorted sourced panels from
cheat sheets from well-formed-but-unsourced panels before anything was written.

**Mistake avoided.** The first design put two panels in one file; `parse_personas` would have
loaded both and summed weights to 2.00. One panel per file; the audience name carries the panel.
**Rule the parser imposes:** anything after the last `## Segment` header is that segment's body,
so bias warnings and retirement flags live in `## About this panel`, above the segments, or they
end up inside the last persona's prompt. Also: a tool that writes its persona file to `/tmp`
breaks resume-cold (F12); a panel died that way.

## First calibration read on Reggie (25 graded predictions, 9 runs)

`forge-state scan --calibration`: 13 hit / 4 partial / 8 miss. The pattern from the first three
runs held at nine: **he hits on scope and human behavior** (feature-parity count, a
customer-acquisition-cost gate, why a 7-year-old quit, a dummy-deck field test) and **he misses
on tooling and model failure rates** (a toolchain twice, a predicted 10-20% ledger-id failure
rate that came in at 1.5%). Use: weight his Stage 0/2 scope calls, discount his toolchain and
validator-rate calls, and make him stake a NUMBER on those so the miss is gradable.

## The scan line's WIP cap, and why it then silenced the pipeline

`forge-state scan` had grown to 16 lines at every session start. Every one was true. That was the
problem: nobody can act on 16 owed gates, so the block trained the reader to scroll past it. A
monitor that is always red is not a monitor. `scan` now prints at most 3 (focused, then FAILED,
then stalest) and one line counting the rest. New states: `park` (no nag, reversible) and
`focus` (pin to the WIP 3). Three things worth repeating on any nag mechanism:

1. **A gate transition unparks automatically.** Work happened, so the run is live again.
2. **Bookkeeping must not touch the clock.** `save()` unconditionally set `updated: today`, so
   `focus` would have reset a run's idle count and *hidden* it. Fixed with `save(..., touch=False)`
   on park/unpark/focus. Any status field that doubles as a staleness clock has this bug in it.
3. **The overflow is parked, not deleted.** `--all` still lists everything.

**The follow-up failure.** `--park-overflow` was then used as a bulk silencer: twelve runs went
dark in one move with no triage, all with the identical reason string, and none moved in a week.
The cap fixed the *symptom* by hiding most runs and advanced none of them. Structural lesson:
every line a session-start hook prints is a request for the human's judgment, and a list of
requests with no actions is triage work, not an advance mechanism. Candidate fixes: a park needs
a review date (twelve identical reason strings is the signature of a silencer); the scan line
must name an action, never "Pick."; a FAILED gate should print its options so the reply is one
word; a prose manifest should be impossible (auto-`init` on first write), paired with `init`
never silently resetting an existing run's state. Also: **a monitor whose remediation command
does not run is worse than no monitor.** The scan's printed hints had `-C <dir>` after the
subcommand; `-C` is a top-level flag and must precede it.

## `forge-state watchdog`: WHY a run stopped, not just that it did

`scan` says idle; it never says why. `forge-state watchdog` runs deterministic rules first and
uses a model only to phrase the reason, never to pick the verdict. Findings from the first real
run (5 of 8 verdicts were wrong on first review, so it was not shippable):

1. **Rule order was the bug.** `DONE_UNRECORDED` was checked before the human-stage and
   third-party rules, so any commit or file touch since `updated` won over an explicit block in the
   same evidence. Fixed order: failed gate, explicit block signal (BLOCKED / waits / waiting /
   STOP / dead credential, checked against next_action + gate note + handoff), human-only stage,
   `DONE_UNRECORDED`, `ABANDON`, `RESUMABLE`. `DONE_UNRECORDED` now also requires commits (not
   just file touches) AND the model's explicit agreement; no model, a failed call, or a
   disagreeing model all fall back to `RESUMABLE`. For every other verdict the model can only push
   the result to something MORE conservative.
2. **Substring matching is fragile.** Bare nouns ("client", "google") in the third-party hint
   list fired on ordinary stage names ("field test with a real client"). Split the list:
   "reply" / "awaiting" / "waiting on" mean waiting by themselves; bare named parties only count
   alongside actual wait/reply language. The same goes for `HUMAN_STAGE_HINTS`: "capture" also
   matches the software family's Stage 0 ("Capture + kill criteria"), an intake stage.
3. **Use the owed gate's stage, not the run's cursor.** `gather_evidence` used the cursor, which
   can land on an unresolved non-blocking stage ahead of the real blocker.

**Lesson:** a session-start line that says "done" when a run is actually blocked is worse than no
verdict at all, because it tells the human to stop looking. Run the honest per-run table BEFORE
calling something shippable, not after.
