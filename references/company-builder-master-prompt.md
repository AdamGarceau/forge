# Company-Builder master prompt (autonomous mode)

The single goal-prompt for Forge's autonomous **Company Builder** mode. Origin: a
widely-shared "built me a business with one prompt" experiment (2026-07-08), absorbed
into Forge and hardened with Forge's honesty gates (that run's own retro lesson was
"stress-test viability up front more" — Forge already does that; this template keeps it).

## How to launch

1. Copy this file into the project as `MASTER-PROMPT.md`, fill the `{{BRACKETS}}`.
2. Kick the run with a thin launcher prompt so the goal survives the 4k char limit:

> Read `MASTER-PROMPT.md` and execute everything below the divider as your goal.
> That file is your full instruction set: mission, guardrails, phases, definition of
> done. Follow it exactly, including the never-ask rule. Do not report back to me
> until the definition of done is met. Start now.

3. Orchestrate delegate-down (per the CLAUDE.md router pattern, if your setup has
   one): the main session **plans, delegates, reviews** — every worker subagent is a
   mid-tier or workhorse model, not the top tier. On a top-tier session, the top-tier
   model manages and never does line work. Use the `Workflow` tool for the fan-out
   phases (hunt, tournament, red-team) when opted in; otherwise `Agent` subagents in
   parallel.

---
# ▼ GOAL — everything below this line is the instruction set ▼

## Mission
Build me a complete company from scratch, starting with nothing but the open internet.
Find a **real, painful, underserved problem** that real people are complaining about
right now, design a business around it, build the product + brand + website, and hand
me a finished package I could take to market **this month**. Then prove to me why it
would work. This is a test of how far you can go on your own. I will not answer
questions mid-run — make every call yourself, write down *why* in a decisions log, and
keep moving. Within the guardrails you have total creative freedom. Show me your best
work, not your safest work.

{{OPTIONAL: aim the hunt — "stay in the {{niche/audience}} space" — or delete this line for a fully open hunt.}}

## Guardrails (hard)
- **No new spending.** Anything already in `.env` / project API keys is fair game; buy
  nothing, sign up for nothing paid.
- **Publish nothing.** Create everything locally. Register a domain's *availability*
  but do not purchase; push no public site, post nothing.
- **Invent nothing.** Every fact, stat, quote, and price must be researched and
  verified against a live source with a URL. Synthetic enthusiasm is not evidence.
- **Work inside this project directory only.** Never run from `~`.
- **Never ask me anything.** Ambiguity is yours to resolve; log the call and move on.
- **Honesty gate is not optional.** A DON'T-BUILD verdict is a valid, first-class
  outcome. Do not manufacture a viable business if the evidence isn't there — say so,
  and hand me the gap map instead.

## Orchestration (a floor, not a ceiling)
Use multi-agent workflows aggressively. Fan out parallel researchers across different
sources and angles. Run tournaments where independent agents pitch competing business
ideas and judge panels score them. Adversarially verify every important claim with
skeptic agents whose only job is to refute it. Run a completeness critic before you
call any phase done. Local models (e.g. `ollama gemma4:12b`, `think:false`) do the
simulated-human work — synth panels, persona walkthroughs — for free. The patterns
above are the minimum; design whatever orchestration shapes the work calls for.

## The arc (nine phases — floor, not ceiling)
1. **Hunt for pain** — parallel research agents sweep the open internet; surface real
   complaints; merge to a candidate list; independent verifiers re-fetch every key quote.
2. **Pick the winner** — tournament: judge personas score every candidate on pain,
   urgency, reachability, willingness-to-pay, buildability, incumbent weakness; top
   few get an advocate + a skeptic; fresh judges vote.
3. **Validate the winner honestly** — Forge Stage 1: expert panel, CEP/ICP external
   signal, weighted synth survey, refutation → one of DON'T BUILD / BUILD FOR SELF /
   BUILD FOR MARKET, plus the gap map. If DON'T BUILD, stop and hand me the gap map.
4. **Design the business** — ICP, offer, pricing, unit economics, channels, moat,
   risks. Grounded in the research, not invented.
5. **Build the brand** — name + domain availability + logo (generation + critique loop,
   winner vectorized) + palette + type system + brand guidelines doc.
6. **Build the thing** — the product + landing page (GSD build; copy through the
   copy-validation gate). Verify it runs end-to-end on the core task.
7. **Make the launch video** — screen-capture the working product, synced to music/motion.
8. **Make the founder video** — avatar + voice clone from `.env` assets; script grounded
   in the real offer.
9. **Try to kill it** — red-team swarm of skeptics attacks market size, moat, pricing,
   reachability; count the attacks; apply every surviving fix back to the plan and site;
   write honesty artifacts. Then **package** it.

## Definition of done (subjective — you decide when it's met)
A stranger can open the recap HTML and, from it alone: understand the business, watch
both videos, run the site, demo the product, read the business plan + market research +
brand guidelines, and see the red-team verdict with the fixes applied. Everything is
linked from that one recap page and verified to exist and work. `FORGE-STATE.md`
reflects the final state. Only then, report back.

Now go build me a company.
