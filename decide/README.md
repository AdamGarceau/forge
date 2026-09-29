# decide

Local, free version of the "Jev" idea: give it a state and typed questions, get typed answers with probabilities. No prose.

The answer is the first generated token (a letter, Y/N, or a digit), so one forward pass with `logprobs` gives a real distribution. We keep the allowed tokens, renormalize, and report `confidence` (top prob) and `margin` (top minus second). Ollama on localhost only, never cloud. Stdlib Python.

## Usage

```
echo '{"state":"Task: film the homeschool intro",
 "questions":[
  {"id":"area","type":"choice","q":"Which area?","options":[{"label":"YouTube","desc":"videos"},"Home","Army"]},
  {"id":"urgent","type":"yesno","q":"Urgent?"},
  {"id":"effort","type":"score","q":"Effort?","scale":[1,5]}]}' | decide --model gemma4:e4b
```

Output: `{"answers": {id: {answer, probs, confidence, margin, valid_mass, [expected]}}, "latency_ms", "per_question_ms"}`.
Also available as `forge-lane decide` (same JSON in/out, local only, `--model`, `--in`, `--out`).
Types: `choice` (up to 26 options, letters A..Z, options may carry `desc`), `yesno`, `score` (scale spanning at most 9 values). `valid_mass` is how much raw probability landed on allowed tokens; if it is near 0 the model ignored the format, distrust the answer.
Each question is a separate short call (about 150 to 600 ms warm on e4b). The first call after a cold load costs about 4 s.
Gotcha: gemma4 emits a thinking-channel token first unless `"think": false`. decide sets it.

## Benchmark (2026-09-29)

Task: predict `tasks.area` from title + notes, `~/maax/tasks/tasks.db` read-only. 156 tasks, stratified (25 per area, all 6 Army). Same area definitions in every prompt. Script: `bench.py`, raw rows: `bench-results.json`.

| Method | Accuracy | p50 ms | p95 ms | Acc when conf >= 0.8 | Acc when conf < 0.8 |
|---|---|---|---|---|---|
| decide, gemma4:e4b | 50.6% | 602 | 723 | 56.8% (n=132) | 16.7% (n=24) |
| decide, gemma4:12b | 55.8% | 1575 | 2299 | 56.0% (n=150) | 50.0% (n=6) |
| decide, gemma4:e2b | 46.2% | 275 | 315 | 46.3% (n=147) | 44.4% (n=9) |
| forge-lane classify (e2b, free text) | 42.9% | 385 | 429 | n/a | n/a |

Excluding Inbox (0 of 25 for both decide models, see below): e4b 60.3%, 12b 66.4%, classify 45.0% (n=131).

Read this honestly:
- Ceiling is low because the labels are noisy. Most of these tasks were migrated from ClickUp and the area came from the list they lived in. Inbox is a catch-all by definition (both decide models get 0/25). Maax HQ vs GYA vs Home are fuzzy. On clean areas (YouTube, Job Hunt, Army) decide e4b hits 21/25, 21/25, 6/6, and 12b 24/25, 23/25, 6/6.
- Same-model comparison (e2b decide 46.2% vs e2b classify 42.9%) says the logprob method is worth about +3 points, within noise at n=156. The bigger win over classify is model size (e4b) plus a usable confidence.
- Calibration: only e4b is usable. Confidence >= 0.8 was right 57% of the time vs 17% below, so low confidence reliably flags a coin flip. 12b and e2b are overconfident (96% and 94% of answers above 0.8, no separation), so their confidence adds nothing. Numbers are raw, not recalibrated.
- Latency: 12b is 2.6x slower than e4b for +5 points (+6 excl. Inbox). Not worth it for routing.

Verdict: passes the kill criterion (beats classify, e4b p50 602 ms is under 1.5 s), but this is a triage tool, not an oracle. Use it where confidence gates a fallback.

## Where it fits

- Maax auto-capture: predict area and priority when Adam states a todo. Auto-file when confidence >= 0.8 and margin is wide, otherwise file to Inbox. Given the label noise, ask for area only from the 4 clean areas first.
- model-advisor hook: `yesno` "is this prompt mechanical?" instead of the regex rule table; threshold on confidence.
- Inbox and comment triage: `choice` intent (question / praise / spam / complaint / lead) plus `score` urgency, one pass.
- Pass/redo gates: `yesno` "does this draft meet the bar?" with the rubric in `state`. A score question gives an `expected` value for thresholds.
- Not for: anything needing reasoning or facts the model has to look up. Prefer stating rules in `instructions` or option `desc`s.

## Files
`decide.py` library and CLI, `~/.local/bin/decide` wrapper, `bench.py`, `bench-results.json`, `BUILD-LOG.md`.
Also edited (outside this repo): `~/.local/bin/forge-lane` gained the `decide` task.
