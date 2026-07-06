# Grounding the synthetic audience — data tiers (the accuracy dial)

The single biggest lever on synthetic-audience fidelity is what the personas are built FROM. Park et al. 2024 proved it: real-data-grounded agents hit 85% of a human's own test-retest reliability; generic demographic personas only 0.70-0.71. So Forge always grounds personas in the richest signal available, in this order.

## Tier 1 — Your own customer call data (most accurate)
If the business has recorded sales/support calls, chat logs, or support email, feed the transcripts to Claude and let it extract real segments, real objections, and the customers' actual language. This is the highest-fidelity source because it's your real buyers in their own words. (Founder's path: he first used call-data analysis just to write copy and pick headlines — then realized the same grounded audience could validate PRODUCTS, not just words.)

## Tier 2 — External signal mining (no first-party data? still 80-90% there)
No call data? Have Claude research **Reddit, blogs, competitor reviews, forums, Q&A sites** — mine the real language, triggers, and objections of the category. This is the CEP external-signal method (Forge Stage 1). It gets you 80-90% of the way there — which, per the founder, still beats platforms that are just guessing, and beats generic demographic personas by the Park et al. margin.

## Tier 3 — Generic demographic personas (avoid — this is the "guessing" tier)
Prompting "act like a 35-year-old suburban mom" with no grounding. This is where the accuracy drops to ~0.70 and subgroup bias spikes. Forge does not stop here; it's the floor competitors sit on.

## Compute choice (independent of tier)
- **Local model (gemma4:12b)** if the machine has the muscle — free, private, ~$0/survey.
- **Sonnet** if not, or for a higher-fidelity pass — same method, just more tokens (still cents per survey vs $1,000s for a human panel).

## Why grounding is the moat
The survey mechanic is commodity — anyone can prompt "act like 1,000 customers." The defensible part is the research pipeline that grounds the personas in real signal (Tier 1 or 2). That's the difference between a directional read you can act on and the sycophantic guessing the accuracy research warns about.

## The honest ceiling (always state it)
Even Tier 1 is a directional filter, not truth. It surfaces objections, ranks options, and predicts relative winners — validated against real wallet-voting in the ISP case study (10). It does NOT replace real people spending real money. That's why Forge's human field test (Stage 4) is a hard gate, not optional.
