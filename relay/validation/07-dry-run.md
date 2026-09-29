# 07 Dry run of relay.candidate (2026-09-29, worker relay-dryrun, pane w29:p1)

Scope: `--dry-run` only. Production `~/maax/fleet/relay` was never run or touched; no swap, no push. Scratch: /tmp/relay-dryrun/.

## Results

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Clean dry run (valid handoff, kickoff block) | PASS | `DRY: checks passed; would /exit pid 55778 in w29:p1, then launch fresh claude with kickoff for …0900-dryrun.md`, rc=0; no lock, kickoff or abort file written (`ls -a` clean) |
| 2 | Agent running: must HOLD | PASS (after fix) | `DRY-LOG: WAIT in-session agents running, holding:   ◯ general-purpose  Sleep 150 harmless` / `DRY: would hold`, rc=0 |
| 3 | Agent finished: must not hold | PASS | final re-run: `checks passed`, rc=0 |
| 4a | Empty handoff refuses | PASS | `ABORT handoff too small (0 bytes)`, rc=1, before any pane wait |
| 4b | Handoff older than newest refuses | **FAIL vs dispatch, PASS vs design** | see below |
| 5 | tests/run.sh | PASS | 51/51 (46 before, +5 new T16 agent-regex tests) |

## Finding 1: the agent regex was wrong (the UNVERIFIED part)

Real pane text while a background Agent ran (tests/fixtures/pane-agent-running.txt):
`  ◯ general-purpose  Sleep 90 harmless agent      3s · ↓ 59.7k tokens` (native agent-list row), plus the
transcript line `⏺ Agent(Sleep 90 harmless agent)` and the footer `2 shells · ← for agents`.

- Before: `[0-9]+ (local )?(agents?|subagents?) (running|working)|Running [0-9]+ (agents?|subagents?)|⏺ *Agent\(`
  Nothing in the real UI says "N agents running". The only match was `⏺ Agent(`, a transcript line: it holds by accident,
  and keeps holding after the agent finished for as long as that line stays on screen (false hold, up to the 90-try abort 4).
  It also missed the case where the line had scrolled away while the agent still ran: the first dry run that fired while the
  agent was alive reported `checks passed; would /exit` (i.e. would have killed a live agent).
- After: `^ *[◯●◉] .*[0-9]+[smh] · [↓↑] [0-9.]+[kM]? tokens|[0-9]+ (local )?(agents?|subagents?) (running|working)`
  Anchored to the agent-list row; dropped `⏺ Agent(`; `← for agents` is NOT a signal (appears whenever shells exist, verified with no agent running).
- Tests T16: running fixture matches; finished fixture (transcript line still visible) does not; footer alone does not; whole-script hold (abort 4, /exit never sent) on the running capture; relays on the finished capture.
- Live: with the agent running the new regex held; after it finished the same command passed.

Caveat: only the `◯` (running) glyph was observed. If a blocked/errored agent row uses another glyph, `●◉` are a guess. Also the dry run fires only once the pane is idle (`herdr agent wait --until idle` blocks while the turn is working), so from inside a turn you run it in the background and end the turn, which is exactly how production runs it.

## Finding 2: "handoff older than newest" warns, it does not refuse

`relay.candidate` prints `WARN handoff is not the newest … the SessionStart hook will inject that one instead` and continues to the idle/agent checks (T10 asserts this: "not newest: WARN but relays"). It never exits nonzero for it. The dispatch expected a refusal, so against the dispatch this check FAILS. Against PLAN H3 it is as designed: the kickoff names the handoff path explicitly ("Resume $HANDOFF and delete it"), so the new seat resumes the right file; the hook just also injects the newest one.

The rc=143 Maax saw was not the script: that dry run blocked at the idle wait (correct, it had passed the WARN), and I `pkill`ed it, SIGTERM = 143. The script's own behaviour is "WARN, continue".

Recommendation: keep it a WARN for the swap (a refusal could strand a legitimate relay when another worker wrote a newer handoff mid-run), or if Adam wants the strict reading, make it `die 1` unless `RELAY_ALLOW_STALE=1` (one line + test). Decision belongs to Maax/Adam; I did not change it.

## Swap recommendation

Ready to swap after Adam accepts Finding 2 as WARN (or asks for the strict variant). Still owed per FORGE-STATE: watch 3 real relays. A live (non-dry) `/exit` path was not exercised here by design.

## Update (9:35 AM): not-newest handoff now refuses (Maax decision)

Maax ruled the WARN wrong: the hook injects the newest handoff, so relaying a stale one boots the next seat on the wrong context.
Change: `relay.candidate` now `die 1` on a handoff that is not the newest in the handoff dir, unless `RELAY_ALLOW_STALE=1` (then WARN and relay).
- T10 updated: not-newest exits 1, `/exit` never sent, ABORT logged, abort marker written. New test: `RELAY_ALLOW_STALE=1` warns and relays.
- Live dry-run re-check (/tmp/relay-dryrun/step6-notnewest-refuse.txt): `DRY-LOG: ABORT handoff is not the newest in /tmp/relay-dryrun/handoffs (newest: 20260929-0910-newer.md); … RELAY_ALLOW_STALE=1 overrides`, rc=1, before any pane wait. **Check 4b now PASS.**
- tests/run.sh: 53/53.
