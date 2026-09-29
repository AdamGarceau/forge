---
forge_state_version: 2
project: "relay"
family: "software"
command: "/forge"
mode: "autonomous"
verdict: "Hardening: BUILD FOR SELF. Packaging: content + free lead magnet, not a product."
stage: "4"
next_action: "Maax QCs and decides the swap"
updated: "2026-09-29"
parked: null
focus: null
gates:
  "G": {"state": "waived", "since": "2026-09-29", "note": "worker run, not a market product build"}
  "H": {"state": "waived", "since": "2026-09-29", "note": "worker run, not a market product build"}
  "0": {"state": "pass", "since": "2026-09-29", "note": "00-idea.md"}
  "0A": {"state": "pass", "since": "2026-09-29", "note": "own unattended Maax seat"}
  "1": {"state": "pass", "since": "2026-09-29", "note": "05-verdict.md"}
  "2": {"state": "pass", "since": "2026-09-29", "note": "candidate built, tests/run.sh 46/46; .planning/PLAN.md (GSD-style plan, inline, not via /gsd-* commands)"}
  "2B": {"state": "waived", "since": "2026-09-29", "note": "not a brand build"}
  "3": {"state": "n/a", "since": "2026-09-29", "note": "no UI; the stub harness replaces persona walkthroughs"}
  "4": {"state": "pending", "since": "2026-09-29", "note": "Maax QC: dry-run in seat, calibrate agent regex, watch 3 relays"}
  "5": {"state": "pending", "since": "2026-09-29", "note": ""}
---

# FORGE-STATE — relay

**Resume-cold manifest** for the `/forge` run. The frontmatter above is the
machine state (`forge-state` owns it, never edit it by hand). Everything below
is for a human picking this run up with no memory of the session.

## Current position

- **Stage:** see frontmatter. `forge-state next` prints the single next action.
- **Run mode:** autonomous
- **Verdict:** pending

## Artifact checklist

| Stage | Artifact | Path | Gate |
|---|---|---|---|

## Decisions and gate overrides

(Every `waived` gate has its reason here as well as in its frontmatter note.)

## Human touchpoint

Recorded in the frontmatter `human:` list, never here by hand:
`forge-state human "<who>" --when <date> --how "<channel>" --said "<verbatim or path>"`.
`forge-state status` prints every entry; a run with none is flagged
"HUMAN: none yet, all-synthetic" (F5: flagged, not blocked).

## Graded predictions

Recorded in the frontmatter `outcomes:` list, never here by hand, at the
family's last stage (F15):
`forge-state outcome <score|ship|field|reggie> --predicted "…" --actual "…" --grade hit|partial|miss [--append <file>]`.
`forge-state status` prints the tally; a run at its last stage with none is
flagged "OUTCOMES: none graded" (flagged, not blocked). `forge-state scan
--calibration` reads them across every run, which is how a gate threshold earns
a change.

## Compute split

local / NAS / agy / Sonnet / Opus:

## Log

- 2026-09-29 — run initialized (`forge-state init --family software`).
