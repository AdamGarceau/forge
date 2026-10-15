# SPEC: pause a coffee subscription
Grill rounds: 3
Open decisions: 0
Glossary: GLOSSARY.md
Grill log: GRILL-LOG.md (the questions asked and the answers)
Review: SPEC-REVIEW.md (26 findings, every one ruled; this is version 2)
Author: main-session-forge-stage-spec

## Problem
Subscribers who go travelling can only cancel. Support says most of them never come back.
They want to stop boxes for a few weeks without losing the subscription.

## Decisions
"Decided by": `founder` = the person who owns the product; `orchestrator` = the AI running this
dry run on the founder's behalf (no human was in this loop); `fact` = read from the code.

| # | Decision | Answer | Decided by |
|---|---|---|---|
| 1 | Can subscribers pause at all | Yes | founder (the brief) |
| 2 | How the length is chosen | A count of boxes to skip (prototype option C, not a calendar) | orchestrator, prototype pick |
| 3 | Longest pause | 3 boxes skipped in a row; the longest gap between two boxes is 112 days | orchestrator |
| 4 | "In a row" | Boxes skipped since the last box shipped. The count goes back to 0 when a box ships | orchestrator, from review |
| 5 | Can a subscriber pause again later | Yes, after at least one box ships. So at least 1 box in every 4 cycles is paid for | orchestrator, from review |
| 6 | Charges while paused | None: each skip moves the next box date and its charge date forward 28 days, at the moment of the skip | orchestrator |
| 7 | The nightly job | Unchanged. It never sees a skipped box, because the dates already moved | orchestrator, from review |
| 8 | Skip after the charge was taken (on or after the charge date) | That box still ships and is not refunded; the skip applies to the box after it | orchestrator |
| 9 | Skip while a declined card is being retried | Refused: a skip cannot dodge a failed payment | orchestrator, from review |
| 10 | Unskip | Allowed one box at a time; it moves the next box back 28 days; refused if that date is under 3 days away | orchestrator |
| 11 | Cancel while paused | Allowed; the skip count is cleared | orchestrator, from review |
| 12 | Gifts | Cannot skip; the refusal is in the skip rule itself, not only a hidden button | orchestrator |
| 13 | Support staff | No new screen; they guide the subscriber through the account page | orchestrator, from review |
| 14 | Email | One "paused, your next box is on <date>" email per skip. No reminder email in this build | orchestrator, from review |
| 15 | Status | Stays `active`; the skip count is stored on the subscription | orchestrator |
| 16 | Reports | A paused subscriber still counts as a subscriber; "paused now" = skip count above 0 | orchestrator, from review |
| 17 | Whose "today" | The shop's local date | orchestrator, from review |
| 18 | Charge timing today | 2 days before the box ships | fact: subscription.py advance() |
| 19 | Which subscriptions get charged | Only status `active` | fact: billing.py charge_due() |

## Worked example
Today is 2026-10-15. Next box 2026-10-29, charge 2026-10-27.

| Action | Next box | Charge | Skip count |
|---|---|---|---|
| start | 10-29 | 10-27 | 0 |
| skip | 11-26 | 11-24 | 1 |
| skip | 12-24 | 12-22 | 2 |
| skip | 01-21 | 01-19 | 3 |
| 4th skip | refused: "You can skip up to 3 boxes in a row. Your next box is on Jan 21." | | 3 |
| unskip (today 10-15) | 12-24 | 12-22 | 2 |
| box ships 12-24, nightly job runs advance() | 01-21 | 01-19 | 0 |

Skip on 10-27 (charge day): the 10-29 box still ships; the skip moves the box after it, 11-26 becomes 12-24.

## User stories
1. As a subscriber, I skip my next box so I do not get coffee while I am away.
2. As a subscriber, I am not charged for a box I skipped.
3. As a subscriber, I see my next box date right after each skip.
4. As a subscriber, I skip up to 3 boxes in a row, and a 4th skip is refused with the message in the worked example.
5. As a subscriber who skips on or after the charge date, I still get that box, and the skip moves the box after it.
6. As a subscriber whose card was declined, I cannot skip until the payment goes through, and I am told why.
7. As a subscriber, I unskip a box if my plans change and the new date is still 3+ days away.
8. As a subscriber, I can cancel while paused, and nothing more is sent to me.
9. As a subscriber, I get one email after each skip with my next box date.
10. As a gift recipient, I cannot skip a box, from any screen.

## Seams
A seam is the one place the tests poke in: here, two rules with no screen and no database
behind them, so every case in the worked example is one short test.

- `skip(sub, today) -> sub or refusal message` and `unskip(sub, today) -> sub or refusal message`:
  plain functions in `subscription.py`, today's date passed in. Stories 1-8 and 10 are tested here.
- The list of emails waiting to send (the nightly job sends it; skip() adds to it): story 9 is
  tested by reading that list after a skip.

## Out of scope
- A support staff screen (support guides the subscriber instead).
- A reminder email before the next box.
- Choosing a return date on a calendar (prototype options A and B, declined).
- Asking why they paused (survey).
- Changing coffee or box size during a pause.
- Refunds for a box already charged.

## Slices
Slices are build steps, in order. Each fits one fresh AI work session (about 150K tokens of
work); "Blocked by" means that step must be built first. The feature goes live once, after all three.

| Slice | What it does (DB to button) | Stories | Seam | Est. tokens | Blocked by |
|---|---|---|---|---|---|
| S1 | skip count column, skip() with the 3-box cap, charge-day, declined-card and gift rules, skip button showing the next box date, count reset in advance() | 1, 2, 3, 4, 5, 6, 8, 10 | skip() | 110K | none |
| S2 | unskip() with the 3-day rule, unskip button | 7 | unskip() | 50K | S1 |
| S3 | "paused, next box on <date>" email added by skip() | 9 | email list | 40K | S1 |
