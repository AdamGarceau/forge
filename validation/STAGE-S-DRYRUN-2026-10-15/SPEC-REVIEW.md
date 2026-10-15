# SPEC REVIEW: pause a coffee subscription
Author: main-session-forge-stage-spec
Spec reviewed: SPEC.md version 1 (rulings applied in version 2)
Date: 2026-10-15

Each reviewer was a fresh agent that did not write the spec, given only SPEC.md, GLOSSARY.md and
the brief (A also got the toy code). They ran in parallel. A and B ran on Sonnet, C on Haiku (a
different model on purpose). Raw reports: the agent ids below, summarised in the findings table.

## Reviewers
| Reviewer | Lens | Agent id | Model | Findings |
|---|---|---|---|---|
| A | completeness and edge cases ("the packed bag") | a27e288e51064515c | sonnet | 10 |
| B | Reggie: scope and over-build | a3f1c24c0ef9a6f5a | sonnet | 8 |
| C | non-coder founder reader: plain words | a566ad972fa82c731 | haiku | 8 |

**Convergent finding:** all three reviewers, without seeing each other, hit the same hole: the
skip count had no reset rule and "in a row" was undefined (A5, B6, C6). That one gap would have
decided how much revenue the 3-box cap protects, and it was invisible to the author.

## Findings
| # | Reviewer | Finding | Ruling | Why / fix |
|---|---|---|---|---|
| 1 | A | Declined card while paused or at skip time is unspecified; retries collide with skips | fixed | decision 9: skip refused while a declined card is being retried; story 6 |
| 2 | A | "Charge was taken" has no test: on the charge day itself, before or after the nightly job? | fixed | decision 8 says "on or after the charge date"; worked example shows a skip on 10-27 |
| 3 | A | S1 is not shippable alone: its button would skip an already-charged box until S2 lands | fixed | charge-day rule merged into S1 (old S2 removed) |
| 4 | A | Charged-then-skipped box: refund or not is ambiguous | fixed | decision 8: the box ships, no refund; refunds listed out of scope |
| 5 | A | skips_used has no reset rule; "3 in a row" conflicts with a lifetime counter | fixed | decisions 4 and 5: count resets when a box ships; S1 adds the reset in advance() |
| 6 | A | Decision 8 (original date + 28 per skip) and decision 13 (move dates at skip) double-shift with advance(); 84 days is wrong | fixed | decisions 6 and 7 rewritten; advance() unchanged and never sees a skipped box; longest gap is 112 days; worked example |
| 7 | A | Cancel while paused leaves skip count and pending reminder behind | fixed | decision 11 clears the count; reminder email cut; story 8 |
| 8 | A | Gift refusal only hides a button; support could bypass it | fixed | decision 12: refusal is inside skip(); story 10 "from any screen" |
| 9 | A | S4 reminder needs an undefined nightly hook; S5 blocked-by wrong; story 4 display not testable at the seam; "today" timezone undefined | fixed | reminder and support screen cut; decision 17 sets the shop's local date; the shown date is skip()'s return value, so it is tested at the seam |
| 10 | A | Unskip 3-day check: against which date, current or original? | fixed | decision 10: checked against the date the box moves back to; glossary Unskip updated |
| 11 | B | S2 is one branch of skip(), not a slice | fixed | merged into S1 (same fix as 3) |
| 12 | B | S5 support screen adds a permissions surface nobody asked for | fixed | cut; decision 13: support guides the subscriber; out of scope |
| 13 | B | Stories 1, 3, 4 are one behaviour; story 7 restates decision 10 | dismissed | stories are what gets tested and decisions are what was chosen; "not charged" gets its own test because it is the part subscribers care about most |
| 14 | B | Unskip is gold-plating; cut S3 | dismissed | a traveller who comes home early and cannot unskip waits or cancels, which is the exact loss the feature exists to stop; kept at 50K |
| 15 | B | Reminder email is unrequested and needs a new nightly hook | fixed | reminder cut (out of scope); the per-skip email already states the next box date |
| 16 | B | Cap, "in a row" and skips_used loosely specified | fixed | same fix as 5 |
| 17 | B | Token estimates uneven and padded; 300K for a toy | fixed | re-sliced to 3 slices: 110K, 50K, 40K (200K) |
| 18 | B | Prediction: the build gets the charge-already-taken arithmetic wrong; prose, no worked example | fixed | worked example table added (every row is a test at the skip() seam); prediction logged in .reggie/predictions.md |
| 19 | C | "seam" is never defined | fixed | one plain sentence added at the top of ## Seams |
| 20 | C | "outbox" is code-speak; what if an email fails? | fixed | renamed "the list of emails waiting to send"; failed sends are unchanged existing behaviour |
| 21 | C | Token counts and "blocked by" have no plain meaning | fixed | plain line added above the Slices table |
| 22 | C | Revenue/churn effect of staying `active` not stated | fixed | decision 16: paused subscribers still count; "paused now" = skip count above 0 |
| 23 | C | "Resume early" and "gift recipient" undefined | fixed | "resume early" replaced by Unskip everywhere; Gift recipient added to the glossary |
| 24 | C | Cap loophole: skip 3, take one, skip 3 again? Decides how much revenue the cap protects | fixed | decision 5 states it: allowed; at least 1 paid box in every 4 cycles |
| 25 | C | Process jargon: grill rounds, prototype option C, orchestrator | fixed | "Decided by" values explained above the table; grill log linked |
| 26 | C | Refusal text never given; field names with no plain meaning | fixed | refusal message in the worked example; decisions say "next box date" and "charge date" instead of field names |

Totals: 26 findings, 24 fixed, 2 dismissed with reasons, 0 open.
