# GSD plan — relay hardening (Phase 1, single phase)
Goal: relay.candidate is a drop-in for ~/maax/fleet/relay that cannot silently lose work or strand a seat, and is testable without a live claude. Status: items H1-H8 BUILT in relay.candidate; tests/run.sh 46/46. Field test (Stage 4) is Maax's QC.
Run: `tests/run.sh [script]` (defaults to relay.candidate; pass ~/maax/fleet/relay to see what production fails).

| # | Item | Why (field evidence) | Acceptance test (tests/run.sh) |
|---|---|---|---|
| H1 | Exit dialog: detect "Exit and stop tasks", send number `1`, TERM/KILL backstop; never bare Enter | 12 stalls; 9/28 4:32 PM highlight on option 2 | T2 number honored → no force; T3 number ignored → TERM; T4 TERM ignored → KILL |
| H2 | Hold while in-session agents run (regex on pane), abort 4 after hold, never /exit | 9/28 packaging run killed by /exit | T8 hold+abort 4, /exit never sent; T9 proceeds when agents finish. **Regex UNVERIFIED on a live pane; calibrate (see below)** |
| H3 | Handoff integrity: exists, >=200 B, has PASTE THIS TO START fence; WARN if not newest in handoffs dir | hook injects newest handoff; empty/foreign handoff relays silently | T10 four cases |
| H4 | `--dry-run` / RELAY_DRY_RUN=1: run checks, print plan, no sends/log/lock | no way to try the relay without risking the seat | T11 |
| H5 | OK requires a NEW claude pid in the pane; else ABORT 6 | agent-wait passes on a bare shell | T12 |
| H6 | mkdir lock, stale-lock recovery | 3 aborts in 5 min 9/27 | T13 |
| H7 | Abort marker file (~/maax/fleet/.relay-abort) surfaced as NOTE on next relay | 9/28 11:01 abort stranded the seat unseen | T7, T8, T12 marker assertions |
| H8 | Duration in OK log line; test seams via RELAY_* env | log has no start times | T1 |
| H9 | Test harness with stub herdr + fake claude, never touches real pane/~/maax | zero tests today | T15 isolation, whole suite |

Calibration owed before swap (cannot be done from a worker run): (a) during a live in-session Agent run, `herdr pane read $HERDR_PANE_ID --source visible` and set RELAY_AGENT_RE / the default to the real status text; (b) confirm the dialog accepts the `1` key (if not, T3 path applies, no regression); (c) `relay.candidate --dry-run <handoff>` from the real pane.
Out of scope / not built: tmux adapter (packaging phase), auto-writing the handoff, context-threshold trigger (turn-governor owns it).
Swap steps for Maax: run tests; diff relay vs relay.candidate; dry-run in seat; `cp ~/maax/fleet/relay ~/maax/fleet/relay.bak-<date>; cp relay.candidate ~/maax/fleet/relay`; watch the next 3 relays in relay.log.
