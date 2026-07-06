# Forge — Pipeline Learnings

A run that doesn't write back is wasted. Append what the PIPELINE itself got right
or wrong each time forge runs.

---

## Canonical exemplar: DEADRECKON (the proof the process works)

Adam's own words, 2026-07-06: *"Deadreckon works perfectly and is exactly the way
we want it. We gave it a TM and had it run the gauntlet. We made a working app by
the end of lunch, all from my phone. It works perfectly for the audience."*

This is the gold standard forge is built to reproduce. What made it work:

1. **A single authoritative input, handed over whole.** Adam sent one photo of the
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
   cross-checked against a real CalTopo paper map; field-tested in St. George and
   precise. The field test (Stage 4) is what turns "should work" into "works."
5. **Provenance nearly lost.** The build lived in a cloud session and its repo took a
   30-minute forensic hunt to find afterward. Lesson baked into forge Stage 2/5:
   register in WORKSPACE.md, push to a durable repo, write state files — so no future
   session has to reconstruct where a working app came from.

Live: deadreckon.adamgarceau.com · repo: github.com/AdamGYA/deadreckon ·
session patterns: references/deadreckon-session-patterns.md

---

## Run log

### 2026-07-06 — forge skill smoke test (2 validation-only evals, with-skill vs baseline)
- LES pay tracker: with-skill 6/6 assertions, verdict BUILD FOR SELF (speed-run,
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
