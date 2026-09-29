# 01 — Field audit of ~/maax/fleet/relay.log (85 lines, 2026-09-27 11:48 AM → 2026-09-29 7:04 AM, 43.2 h of OK-to-OK span)
Parsed with a python script over the log (minute resolution; the log records only the END of a relay, never its start, so time-to-relaunch is measurable only for the exit->launch leg).

| outcome | count | share of 61 attempts* |
|---|---|---|
| OK relayed | 55 | 90% |
| — of which clean /exit | 43 | 70% |
| — of which forced (TERM) after "/exit stalled" | 12 | 20% of attempts (22% of OKs) |
| ABORT input box not empty | 4 | 7% (3 on 9/27 = 3 tries in 5 min, then OK; 1 on 9/28 11:01 AM stranded the seat) |
| ABORT claude pid did not exit | 2 | 3% (9/27 3:02 PM, 4:04 PM, old version of the script, no TERM/KILL fallback) |
*attempt = OK + ABORT (12 forced are inside the OKs).

Cadence: 25 OK on 9/27, 28 on 9/28, 2 on 9/29 (so far). Median gap between relays 22 min, max 7 h (overnight).
Forced-exit -> OK-relaunch leg: 0-60 s in every one of the 12 cases (minute resolution). So forced exits cost about a minute, not a seat.

## Failure modes and root causes
1. **/exit stalled (12x, all forced exits succeeded).** Root cause PROVABLE from the log: in all 12 the pane showed the Claude Code confirm dialog "❯ 1. Exit and stop tasks / 2. Move to background and exit / 3. Stay", preceded by a live `shell ·` background task (wake.sh, sleep-poll loops, W_BUDGET worker launches). Maax always runs `wake.sh` with run_in_background, so any relay fired while it is alive hits the dialog. 43 relays did not stall because no bg task was live. The script's existing TERM/KILL fallback handles it, but (a) it burns 15 s waiting, (b) TERM to claude silently kills the bg shells, which is what option 1 does anyway, (c) at 9/28 4:32 PM the highlight was on option 2, so a blind Enter would have "moved to background" instead. Never send bare Enter into that dialog.
2. **Input box not empty (4x).** Root cause provable: Adam had typed text; the old script aborted instead of waiting. 3 aborts on 9/27 were retries; 9/28 11:01 AM abort stranded the seat and Adam relayed by hand. Current script already holds up to 45 min (fix shipped after 11:01), no field data yet on the 45-min branch and no data on a typed-but-never-sent draft.
3. **pid did not exit (2x, 9/27 pm).** Root cause provable: pre-fallback script version. Fixed by TERM/KILL. Zero recurrences since.
4. **Not in the log but in the script comment:** relaying with an in-session Agent running killed the 9/28 packaging run. No detector exists; a doc comment is the only guard.
5. **Blind spot:** `OK` is logged when `herdr agent wait --until working|idle` succeeds, which is also true if the pane is a plain shell that never launched claude. The new pid is never verified.
6. **Blind spot:** handoff arg is only checked with `-f`. The SessionStart hook injects the NEWEST handoff <18 h old, so a worker writing a later handoff hijacks the relay; an empty or fragment file relays silently.
