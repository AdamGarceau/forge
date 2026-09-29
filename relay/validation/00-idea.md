# 00 — Idea + kill criteria (written before the verdict)
Idea: harden the Maax self-relay (~/maax/fleet/relay), and separately decide whether a sanitized "relay kit" is worth packaging (YouTube #477, due 10/3).
Mode: autonomous (worker run). Scope: verdict + GSD plan + tested CANDIDATE. No swap into production.

Kill criteria, hardening (DON'T BUILD if ALL true):
- K1 forced/aborted relays < 5% of relays, AND
- K2 no failure has stranded a seat or lost work in the last 48h, AND
- K3 the current script already covers the observed failure modes.
Kill criteria, packaging (DON'T PACKAGE if ANY true):
- P1 an existing tool already does unattended, idle-safe, exit-and-relaunch rotation for Claude Code with real adoption.
- P2 the mechanism depends on Herdr/persona/Console so heavily that a kit is not portable.
- P3 no evidence people want the unattended part (vs. just a /handoff prompt).
