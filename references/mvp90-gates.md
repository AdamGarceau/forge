## The 90% MVP: the driver and the gates that enforce it (forge 1.11, 2026-10-18)

Adam, 2026-10-18: "Fix forge. I'd actually like a product to be 90% MVP." Then: "It's supposed to 'one-shot' code projects. It should be good enough for the ICP, and then I can make it perfect after that by adding or refining features." And: "Forge is supposed to act like a state machine like GSD. It hasn't done that."

The audit (`~/forge-reviews/MVP-READINESS-2026-10-18.md`) measured about 60% at first hand-off. Every check below exists because a named failure got past the old gates. Code: `scripts/forge_driver.py` (driver, stage checks), `scripts/forge_mvp.py` (gates 1, 2, 6, 7, 8), `scripts/forge_spec.py` `check_mvp90` (gate 3). Tests: `scripts/test_mvp90_gates.py`.

**What 90% means.** One build pass. At first hand-off the ICP (the run's target user, not Adam) does every core job in SPEC.md for its real job, with 0-1 small fix rounds. Anything after that is a new or refined feature, not a repair.

### The driver: `forge-state run`

The command is the step, the way GSD's execute-phase is. On a run with FORGE-STATE.md, `/forge` calls this; it does not do stage work freehand.

1. **Reconcile.** Every owed gate whose artifacts verify on disk right now is recorded as passed, with the files as evidence. One that doesn't verify is left alone. It never invents a pass.
2. **Loop.** Next stage → a fresh worker (`claude -p`, Sonnet; `FORGE_WORKER` overrides) gets that stage's section of `references/` and the gate's current refusals → the stage's checks run on the artifacts → the driver records pass or fail → on a refusal, up to 2 fix rounds, each given the exact refusals, then **BLOCKED** (gate `fail`, exit 3).
3. **Human gate.** A refusal only a person can clear (it starts `HUMAN:`), or a worker's `ASK.md` (`Stage:`, `Ask:`, `Device:`, `Pass when:`), stops the run with one exact ask: what to do, on what device, what counts as pass. The ask is recorded in the frontmatter `asks:` list and in `next_action`; `status` shows it. Exit 2. When Adam answers, Maax records it (`forge-state human Adam --stage K --passes --how … --said "…"`) and runs `forge-state run` again.
4. **Heavy stages** (1, 3) wait on `whats-running --gate ollama`; a refusal exits 5.

`--dry-run` prints the reconcile and the plan and writes nothing. `--until <gate>` stops once that gate passes.

**Only the driver, or Adam's words, move a gate to pass.** `forge-state gate K pass` by hand runs the same checks and is refused when they fail, unless `--adam-said "<his words, 3+>"` comes with it (recorded as `[ADAM OVERRIDE]`). A human gate clears only on an entry recorded with `--passes`: the 10/18 Pookemon dry run had about 40 entries at Stage V (bug reports and asks) and none was a verdict.

### Stage checks (software; games in brackets)

| Stage | Passes when |
|---|---|
| 0 | `validation/00-idea.md`, 40+ words, has kill criteria |
| 0A | `## Intended use` in 00-idea.md, and Adam's answers recorded with `--passes` (HUMAN) |
| 1 | the validation/ artifacts exist [games: compressed set], 05-verdict.md names a verdict, **gate 7** |
| S | `forge_spec.spec_check`, including **gate 3** |
| 2 | `.planning/ROADMAP.md` with every phase done, a `/gsd-*` command logged, Adam's plan approval (`--passes`; not in autonomous mode) [games: plus the hand-off bundle] |
| 2H | `HARDENING.md` (unchanged) |
| 3 | usability report at the mode's score with a cloud judge, plus the hand-off bundle: **gates 1, 2, 6, 8** |
| 4 | **gate 1** still fresh, `.planning/FIELD-TEST.md` with no open items, Adam's words with `--passes` (HUMAN). The first stop here records `handoff` |
| [T] | **gate 1** (the toolchain runs on the real hardware) |
| [P, V, 3'] | a real human's verdict recorded with `--passes` (HUMAN) |
| 5 | an outcome graded |

G, H and 2B are non-blocking: the driver records `n/a` where the mode table skips them (speed-run; no hunt; 2B on MARKET only).

### Gate 1. Real target: `REAL-TARGET.md`

```
# REAL TARGET: <name>
Target: ios | android | game | desktop | web | cli | sheet | automation
Device: iPhone 14 Pro Max          (ios/android/game/desktop: the real device, never a simulator)
URL: https://...                   (web: checked live, must answer 2xx/3xx)

## Proof
| Core job | Proof file | What it shows |
|---|---|---|
| J1 | proof/j1-log-contact.png | the saved contact on the phone |
| J2 | proof/oct-statement.csv -> proof/oct-books.csv | cli/sheet/automation: real input -> real output |
```

Device targets need screenshots or video, newer than the last build (newest source file). A missing proof is a HUMAN ask: "On <device>, install the current build, do J1..Jn, screenshot or screen-record each, drop them in proof/." CLI, sheet and automation targets need a real input and its output; a path under tests/, fixtures/, sample, mock or dummy is refused. Web and CLI cover every core job.

### Gate 2. Dead-control sweep: `DEAD-CONTROLS.md`

An agent drives the built UI: Playwright for web, XCUITest or simulator taps or a recorded device walk for iOS, every subcommand and flag for a CLI. Every control it finds gets a row; the gate reads the file.

```
# DEAD CONTROLS: <name>
Driver: playwright | xcuitest | device-walk | cli-sweep | computer-use
Controls found: 23

## Controls
| Control | Screen | Action | Result | Evidence |
|---|---|---|---|---|
| Save | Edit | click | ok | toast says Saved, row count 4 -> 5 |
```

Refused: any `dead` or `error` row, a row count that differs from `Controls found`, fewer than 3 rows, an `ok` with no evidence of what changed, a file older than the build. A control that can't be reached (pushed off-screen) is `error`.

### Gate 3. "What do you assume it does": SPEC.md, at Stage S

Before the build, list the 10-15 things a normal user of this kind of product expects (multi-select, undo, page counter, save state, error messages, empty states) and rule each in or out.

```
## Core jobs
- J1: log this week's four contacts
- J2: export them for the claim

Domain content: yes | no

## Assumed features
| Feature | In/Out | Reason | Decided by |
|---|---|---|---|
| Multi-select | in | users uninstall several apps at once | founder |
| Undo | out | the trash is the undo | Adam: "the trash is enough" |
```

Refused: fewer than 10 rows, a row with no reason, an `out` without Adam's quoted words (3+; the orchestrator may decide only in autonomous mode), no core jobs or more than 7, no `Domain content:` line.

### Gate 6. Domain truth: `DOMAIN-TRUTH.md` (when SPEC.md says `Domain content: yes`)

Rules, prices, game data, legal or tax text. Every content item cites its real source, and a fresh agent spot-checks 10 against those sources.

```
# DOMAIN TRUTH: <name>
Checker: <agent id, never the builder>
Judge: claude-sonnet-5-5
Ledger: data/pokemon.json          (.json list with "source", .csv with a source column, or a .md table)

## Spot check
| # | Item | Source | Product says | Source says | Result |
|---|---|---|---|---|---|
| 1 | Geodude type | https://bulbapedia... | Rock/Ground | "Geodude is a dual-type Rock/Ground" | match |
```

Refused: an unsourced ledger item, fewer than min(10, items) rows, a `Source says` that isn't a quote, any result other than `match` or `fixed`, a local-only judge, the builder as checker.

### Gate 7. Delivery mode: `validation/05-verdict.md`, at Stage 1

```
Delivery mode: native app | web | cli | sheet | automation | desktop | game
Others lose: <the one reason the other modes lose, 8+ words>
```

### Gate 8. ICP one-shot walkthrough: `ICP-WALKTHROUGH.md`, before hand-off

A fresh agent plays the run's ICP (from Stage 1 / SPEC.md) and runs every core job end to end on the real build.

```
# ICP WALKTHROUGH: <name>
ICP: a claimant logging four weekly job contacts
Walker: <agent id, never the builder>
Judge: claude-opus-5-5

## Jobs
| Job | Result | Evidence |
|---|---|---|
| J1 | done | "Saved 4 contacts; the list shows 4 rows dated this week" |
```

Every core job must be `done` with quoted evidence (4+ words). `stuck` or `broken` is a defect to fix before hand-off, not a later feature. Older than the build is refused.

### Gate 4. No skip without Adam's words

`waived`, `n/a` or `--force` on any blocking gate needs `--adam-said "<his words, 3+>"`. A bare `--force` is refused. Non-blocking stages still take a note.

### Gate 5. Stalls: `forge-state stalls`

Read-only. Software and games runs in `~/WORKSPACE.md` projects untouched 14+ days (`--days`), each with a FINISH line (`forge-state run`) and a KILL line (`verdict "KILLED: …" --close`). Maax surfaces it; nothing is killed automatically.

### Gate 9. Hand-off score

The first time the driver stops at Stage 4 it records `handoff: {date}` (`forge-state handoff` does it by hand for older runs). Every later Adam request is tagged: `forge-state human Adam --fix …` (broken or missing for the ICP's job) or `--feature …` (an addition or refinement). `status` prints `HAND-OFF: <date> · fix rounds since: N · features: M · 90% bar: met|MISSED`. Fix rounds count distinct days with a `--fix` entry.

### Judges

A judged file (`DOMAIN-TRUTH.md`, `ICP-WALKTHROUGH.md`, the usability report) names its judge in `Judge:`. A local model alone (gemma, llama, qwen, deepseek, e4b) is refused; the audit caught gemma4:12b fabricating. The judge quotes the evidence line it ruled on.
