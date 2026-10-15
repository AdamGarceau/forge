# Stage S dry run: pause a coffee subscription (2026-10-15)

Proof for Forge 1.10.0's Stage S (spec + spec review), run on Matt Pocock's demo toy against a
tiny fixture codebase (`toy-app/`). No human was in the loop, so the orchestrator answered its own
frontier and logged each answer (Company-Builder style); in a real run the rounds in
`GRILL-LOG.md` go to the founder exactly as written.

| Step | Artifact | What happened |
|---|---|---|
| Facts | `GRILL-LOG.md` (Facts) | A helper agent (haiku) read the code and answered 7 fact questions. None were asked of the founder. |
| Grill | `GRILL-LOG.md` | 3 frontier rounds, 13 questions, each with a recommended answer. Round 2's Q11 answer opened a new decision (Q13) in round 3. |
| Prototype | `prototype/pause-options.html` | Q2 was ungrillable (dates or boxes?). A fresh agent built 3 throwaway options; C (skip boxes) won because it matches the 28-day cycle; the pick went back into the grill. |
| Glossary | `GLOSSARY.md` | 8 terms with words to avoid. |
| Spec | `SPEC.md` | v1 then v2 after review: 19 decisions (who decided each), a worked example, 10 user stories, 2 seams, 6 out-of-scope items, 3 slices (110K / 50K / 40K tokens). |
| Review | `SPEC-REVIEW.md` | 3 fresh reviewers in parallel (2 Sonnet, 1 Haiku): 26 findings, 24 fixed, 2 dismissed with reasons. All three independently found the same hole (no reset rule for the skip count). |
| Reggie | `.reggie/predictions.md` | One prediction logged, open until Stage 2. |
| Gate | `GATE-PROOF.txt` | The thin copy (`thin/`) was refused on 12 counts. Stage 2 was blocked while S was open. The reviewed spec passed `forge-state gate S pass`. |

## What the review changed (why the stage exists)

Version 1 looked finished to its author and passed every structural check. The reviewers still
found a double-shift bug in the date logic (decision 8 against decision 13 against `advance()`), a
slice that could not ship alone, a missing declined-card rule, an undefined cap ("in a row") that
decided how much revenue the feature protects, and two features nobody asked for (a support
screen and a reminder email, both cut). None of that would have surfaced until code review, or
until a subscriber hit it.

## Retro (F17), from this run

- **Mistake a machine could spot, so it became a check:** the first `forge_spec.py` run flagged
  the required `## User stories` heading because the glossary said to avoid "user". Fixed in the
  checker (headings are skipped) with a regression test, `test_avoid_word_in_a_required_heading_is_not_flagged`.
- **Suggested, not applied:** the generic refusal "Resolve it first (pass / waived --note / n/a)"
  offers n/a, which Stage S refuses. A per-stage hint would be clearer. Left for the maintainer to pick.
- **Suggested, not applied:** reviewer C (the founder reader, on Haiku) found 8 real plain-words
  problems. Worth keeping a smaller model on that lens: it reads more like a non-coder.
