# GRILL LOG: pause a coffee subscription (Stage S dry run, 2026-10-15)

Toy from Matt Pocock's demo ("let subscribers pause instead of cancel"), run against the
fixture code in `toy-app/`. **This is a dry run with no human in the loop**, so it runs
Company-Builder style: the orchestrator (this session) answers its own frontier and logs
each answer as `Decided by: orchestrator`. In a real run these rounds go to the founder
as written below, and they reply in one line.

## Facts (helper agent, haiku, id a6b9ba1e2df2fb2db; never asked of the founder)

| # | Fact | Source |
|---|---|---|
| F1 | A box ships every 28 days; the card is charged 2 days before the ship date | subscription.py CYCLE_DAYS, advance() |
| F2 | Statuses today: `active`, `cancelled` (plain string) | subscription.py Subscription.status |
| F3 | The nightly job runs charge_due() then advance() after a box ships | README.md, advance() docstring |
| F4 | Gifts are prepaid for N boxes (`boxes_left`), decremented by advance() | subscription.py |
| F5 | Declined card: 3 daily retries then cancel + email (docstring only; body is a stub) | billing.py on_card_declined() |
| F6 | Emails named: shipped, card declined, cancelled (no sending code in the fixture) | README.md |
| F7 | No way to skip or delay a box today; only cancel() | subscription.py, README.md |
| F8 | charge_due() only picks `status == "active"` | billing.py charge_due() |

## Decision tree

```
D0 subscribers can pause (settled by the brief: README "Ask: let people pause instead")
├── D1 how long can a pause be ─┬── D7 when does the next box ship after a pause
├── D2 how is the length chosen ┘   ├── D8 resume early?
├── D3 does billing stop             └── D10 extend a pause while paused?
├── D4 gift subscriptions?           D9 pause asked inside the 2-day charge window?
├── D5 who can pause                 D11 status name (needs D3 + F8)
└── D6 emails ── D12 reminder before the next box
```

## Round 1 (frontier: every decision whose parent D0 is settled)

```
Q1. Longest pause? Recommend: 3 months. (yes = 3 months)
Q2. How is the length chosen: a resume date, or a number of boxes? Recommend: a resume date.
Q3. Do charges stop while paused? Recommend: yes, no charge for a box that does not ship.
Q4. Can gift subscriptions pause? Recommend: no, out of scope (the gift buyer prepaid; the
    recipient does not manage billing).
Q5. Who can pause? Recommend: the subscriber on the account page; support uses the same action.
Q6. Email when a pause starts? Recommend: yes, one "paused, next box on <date>" email.
```

Answers (orchestrator): **Q1 yes. Q2 UNGRILLABLE: send to a prototype** (how the control looks
decides whether people think in dates or boxes). Q3 yes. Q4 yes. Q5 yes. Q6 yes.

### Prototype for Q2 (fresh agent, haiku, id acaf7d22856837c0c)

`prototype/pause-options.html`, marked THROWAWAY: (A) pause 1/2/3 months buttons,
(B) "resume on" date picker, (C) "skip next box" pressed up to 3 times. **Pick: C.** A and B
produce ship dates that fight the 28-day cycle (F1): a "1 month" pause lands mid-cycle and needs
a second rule for the charge date. C moves whole cycles, which is exactly what advance() already
does. The pick returns to the grill: **D2 = count of boxes, D1 restated = up to 3 boxes**
(84 days, close to the recommended 3 months).

## Round 2 (frontier after round 1 + the prototype pick)

```
Q7.  After a pause, the next box ships on the original date + 28 days per skipped box, charged
     2 days before. Recommend: yes.
Q8.  Can a subscriber resume early? Recommend: yes, "unskip" boxes one at a time from the
     account page, as long as the next ship date is still 3+ days away.
Q9.  Pause asked inside the 2-day charge window (box already charged)? Recommend: that box still
     ships; the skip starts from the box after it.
Q10. Extend while paused? Recommend: yes, up to 3 skipped boxes in total per pause.
Q11. New status `paused`? Recommend: yes; charge_due() already ignores anything not `active` (F8).
Q12. Reminder email 3 days before the first box after a pause? Recommend: yes.
```

Answers (orchestrator): Q7 yes. Q8 yes. Q9 yes. **Q10 no**: the cap is 3 skipped boxes per
pause, and extending is just skipping again (same rule, no new decision). Q11 **no**: keep the
status `active` and store `skips_left`; a third status means every query that checks `active`
has to learn it, which is a bigger blast radius than the feature (see F8, F2). Charges are skipped
because next_charge moves, not because the status changes. Q12 yes.

## Round 3

Frontier recomputed after Q11 = no: one new decision appeared.

```
Q13. With status staying `active`, the nightly job must not ship a skipped box. Recommend:
     skipping moves next_ship and next_charge forward by 28 days per box at the moment of the
     skip (so the nightly job never sees the skipped dates). yes = move the dates up front.
```

Answer (orchestrator): Q13 yes.

Frontier: **empty**. 3 rounds, 13 decisions, 1 prototype.
