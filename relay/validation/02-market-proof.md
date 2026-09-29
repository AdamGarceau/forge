# 02 — Market proof (searched 2026-09-29)
Tools: WebSearch + WebFetch. Firecrawl search errored on every call; reddit.com is blocked for WebSearch/WebFetch, so Reddit and YouTube-comment mining were NOT possible. Do it by hand or via Adam's browser before publishing claims about "what people say".

## Claude Code's own features
- Built-in /compact and /clear (lossy summary / wipe). Anthropic guidance: compact at ~60% and keep sessions under ~120k tokens — https://www.sitepoint.com/claude-code-context-management/ ; https://claude.com/blog/using-claude-code-session-management-and-1m-context
- Auto-continue in new conversation on context limit: requested, **closed "not planned"** (stale) — https://github.com/anthropics/claude-code/issues/43404 ("each context switch costs ~5 minutes... manual intervention 3-4 times per task")
- Context awareness + graceful handoff before session death: **closed "not planned"** — https://github.com/anthropics/claude-code/issues/27914 ("flying a rocket plane at Mach 9 with no fuel gauge")
- Hooks cannot trigger /clear (feature request #9118, closed not planned; per https://vincentvandeth.nl/blog/context-rot-claude-code-automatic-rotation)

## Existing third-party tools (handoff-document layer; mostly manual trigger)
- 392fyc/claude-handoff — /handoff writes doc, optionally launches fresh session (wt on Windows); **1 star**; "Handoff runs when you type /handoff. No automatic triggers" — https://github.com/392fyc/claude-handoff
- Sting25/claude-code-handoff — auto-snapshot at context boundaries — https://github.com/Sting25/claude-code-handoff
- who96/claude-code-context-handoff — hooks around compact/clear — https://github.com/who96/claude-code-context-handoff
- shiyu9/relay — diary + knowledge injected next session — https://github.com/shiyu9/relay
- Manavarya09/relay — hands off to Codex/Gemini/Aider at rate limit — https://github.com/Manavarya09/relay
- thepushkarp/handoff — HANDOFF.md plugin — https://github.com/thepushkarp/handoff
- REMvisual/claude-handoff, Sonovore/claude-code-handoff, justinboggs0/claude-handoff (fork) — same category
- Blog/how-to: https://www.jdhodges.com/blog/ai-session-handoffs-keep-context-across-conversations/ (manual HANDOVER.md)

## Closest to Maax's relay: unattended rotation
- VNX context rotation (Vincent van Deth): PreToolUse blocks at 65% context, PostToolUse launches an external rotator that `tmux send-keys /clear`, SessionStart re-injects. Needs tmux + Bash 4+. Failure modes he reports: 1-2 s race after /clear, vague handover under pressure, skills reload from scratch. https://vincentvandeth.nl/blog/context-rot-claude-code-automatic-rotation
- Eva Khmelinskaya, "Running Claude Code Autonomously Overnight — What Breaks and How to Fix It" (Medium) — same problem space, not fetched.

## Reading
Demand: confirmed by Anthropic-repo issues (unattended runs "hit the context limit and just stop"). Supply: crowded but manual/doc-centric and low-adoption. Differentiator Maax has: unattended, idle-safe, input-box-safe, relaunches a fresh process (picks up a new binary/model), 55 field relays in 43 h. Weakness: Herdr-specific pane control (Herdr is niche; tmux is the mainstream analog, as VNX shows).
