# Relay kit — packaging SPEC (no build; for #477 lead magnet)
Verdict: free MIT kit behind an email opt-in, story-first; not a paid product (validation/05-verdict.md).
## Strip
- Persona/voice: "You are Maax, CEO", Adam-is-away lines, CARE/persona references.
- Paths: ~/maax/** (fleet/, handoffs/, FLEET.md, CONSOLE.md, reports.md, wake.sh, w), ~/forge, /Users/garceau, the Volumes/NAS path fragments that appear in relay.log.
- Console/ArtifactData/Chat-mirror/inbox/taskops steps in the kickoff; ClickUp; Sugar Pills / GYA / Axil / client names; anything from handoffs.
- relay.log contents: ship only aggregate stats and hand-scrubbed lines (pane snippets show private command text, e.g. "shell · cd /Volumes/GYA-Work ...", worker names, budgets).
- Hooks: turn-governor/session-meter specifics (model routing, $ figures, 50/80/150-turn doctrine tied to Adam's bill).
- Herdr hard-coding as the only backend.
## Keep
- relay.candidate core: idle wait, input-box safety (dim-placeholder parser), agent hold, exit-dialog handling, TERM/KILL backstop, new-pid verification, lock, abort marker, dry-run.
- Handoff convention: one file per session, kickoff fence "PASTE THIS TO START", SessionStart hook injecting newest <18 h handoff (sanitized example hook).
- The rule "detached workers survive a relay, in-session Agents do not".
- tests/run.sh + stub harness (fake pane) — the proof it works, and a good video beat.
## Add for others
- Backend adapter: `RELAY_PANE_BACKEND=herdr|tmux` (tmux send-keys/capture-pane; VNX shows tmux is the mainstream path). Config file for kickoff text and handoff dir. README with the 4 failure modes and the field table (55 relays/43 h, 12 forced exits, 0 seats lost since fix). Windows unsupported: say so.
- Honest limits section: pane-scraping depends on Claude Code UI text; regex needs recalibration on upgrades.
## Distribution
GitHub repo + email-gated zip; video #477 links it. Reddit/YouTube-comment demand check still owed (blocked in this run).
