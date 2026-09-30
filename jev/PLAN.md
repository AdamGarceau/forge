# Jev plan (2026-09-29)

Jev = TypeSafe's "System One" model (typesafe.ai). No text output: it answers typed questions about a state (yes/no, choice, score) with calibrated probabilities, in one parallel call. `pip jev` 0.3.0 is the `@jev.fn` decorator: a function signature + docstring + Pydantic return model becomes the query. Hosted API only (https://api.typesafe.ai/v1/systemone). Our `~/forge/decide` is the local clone of the same idea.

## Step 0: install (DONE 9/29 8:15 PM)
`~/forge/jev`: uv project, Python 3.14.7, jev 0.3.0 + typesafe_sdk 0.7.2, `import jev` verified. Run with `cd ~/forge/jev && uv run python ...`.

## Step 1: key (ADAM, 5 min)
Make an account at console.typesafe.ai, put `TYPESAFE_API_KEY=...` in `~/forge/jev/.env`, log the path in ~/brain/SECRETS.md. Check pricing and data retention while there. Nothing calls the cloud until this exists.

## Step 2: local shim (DONE 9/29 8:24 PM, QC PASS: test_shim.py; e4b calibration check still owed)
The SDK honors `TYPESAFE_BASE_URL`. Build `~/forge/jev/shim.py`: a localhost server that answers `/v1/systemone` and `/v1/models` in TypeSafe's schema, backed by `decide` on Ollama (gemma4:e4b, the only calibrated one). Result: the same `@jev.fn` code runs either way.
- `TYPESAFE_BASE_URL=http://127.0.0.1:8766` means local, $0, private (default for anything sensitive).
- Unset it and the call goes to real Jev (public data only).

### Step 2 calibration + Step 4.1 result (9/29 ~8:50 PM): NOT WIRED into `t`
`calibrate.py` (n=75: 12/area from done+open rows, seed 7, e4b via shim, `calibrate-results.json`), module `autotag.py` built.
- Area: 58.7% overall. Right-rate at conf>=0.8: 62% (n=69) vs 17% below (n=6). decide e4b baseline was 50.6%, 57% vs 17%. Confidence barely separates (only 6 rows fall below 0.8; the 0.9 cut gives 62% vs 42%).
- Per-label precision at >=0.8: YouTube 8/8, Job Hunt 10/14, GYA 8/13, Army 6/10, Home 5/9, Maax HQ 5/14. Top confusions: Inbox->Maax HQ/GYA, YouTube->Maax HQ, Home->Job Hunt.
- Priority: 41% overall, at/below the majority-class baseline (P2 = 48%); conf>=0.8 gives 50% vs 29%. Useless.
- Verdict: ~38% silent wrong tags in the system of record is not acceptable; `t add --auto` NOT wired, tasks/README untouched. Revisit with a bigger sample or per-label thresholds (YouTube looks safe but n=8) or a stronger e4b prompt.

### Step 4.2 result (9/29 ~9:00 PM): fleet report triage NOT WIRED (below baseline); key-independent, all local
`triage.py` (Choice DONE/BLOCKED/NEEDS-ADAM + Noul outward-facing) and `calibrate_triage.py` built; results in `triage-results.json` (n=76 worker DONE/BLOCKED lines from reports.md: 50 DONE sampled seed 7 + all 26 BLOCKED, e4b via shim, p50 655 ms).
- Verdict vs the line's own status: 25% right, majority baseline (always DONE) is 66%. Confidence does not separate (conf>=0.9: 27%, n=59). Model calls 43/76 lines NEEDS-ADAM (28 DONE, 15 BLOCKED), which is defensible in many cases (DONE lines often carry "needs Adam check"), but the gold status can't score that; 14 DONE lines were called BLOCKED (noise: BLOCKED called on 42% of BLOCKED vs 28% of DONE).
- Outward-facing: P(yes) ~0.00 on nearly everything. Eyeballed 30 random lines: 2 real outward actions (ClickUp comments) both scored 0.00. Missed. A keyword rule (sent/posted/uploaded/commented/submitted/pushed) beats it.
- Verdict: not wired into Maax's QC. The status field the worker writes already IS DONE/BLOCKED; the QC value is judging NEEDS-ADAM and outward-facing, and neither is reliable on e4b. Use a regex for outward-facing if anything; keep NEEDS-ADAM as human QC. Real Jev (needs #502 key, public data only, reports contain client/SP data so must be scrubbed) is BLOCKED-on-key: rerun `calibrate_triage.py` with JEV_ALLOW_CLOUD=1 after scrub to see if a bigger model separates NEEDS-ADAM. Not worth doing before Step 3.

### Step 6: native Ollama /v1/systemone + nimble / tev1 recalibration (9/30 ~6:20 AM): NOTHING CLEARS, still NOT WIRED
Ollama upgraded 0.34.4 -> 0.35.0 (`brew upgrade --cask ollama-app`; the CLI is a symlink into Ollama.app; service came back, gemma4:e4b still loads). Pulled `nimble` (9.0B Q8, qwen35 family, 9.5 GB) and `tev1` (4.5 GB, the 4B). Native endpoint `POST localhost:11434/v1/systemone` works with the SDK unchanged (`TYPESAFE_BASE_URL=http://127.0.0.1:11434`, `model=` passed through, any key). Scripts take `JEV_NATIVE_MODEL=<model>` (skips the shim, writes `*-results-<model>.json`) and `JEV_TIMEOUT`. Same seed 7, 12/area; tasks.db/reports.md grew slightly, so n differs by 1-11 (noted per row). Native `confidence` is NOT the shim's: it is not the top probability (p=0.83 gave conf 0.33). Original e4b results kept as `*-e4b-orig.json`. The e4b column was not rerun today.

| Use (baseline) | e4b shim (9/29) | nimble native | tev1 native |
|---|---|---|---|
| Area acc (n=75/76/76) | 58.7% | 56.6% | 52.6% |
| Area right at conf>=0.8 | 62% (n=69) vs 17% below | 62% (n=37) vs 51% below | 68% (n=28) vs 44% below |
| Area right at conf>=0.9 | 62% vs 42% | 64% (n=25) | 73% (n=15) |
| Priority acc (majority P2 = 46-48%) | 41% | 53.9% | 46.1% |
| Priority conf separation | 50% vs 29% at 0.8 | none (0% at >=0.7, n=4) | none (conf never >=0.6) |
| Triage verdict acc (n=76/86/87; always-DONE baseline 66% / 58% / 57%) | 25% | 43% | 39% |
| Triage right at conf>=0.8 | 27% (at 0.9) | 29% (n=14) | 30% (n=10) |
| p50 latency | 655 ms triage | 1.8 s area, 1.4 s triage | 0.9 s area, 0.8 s triage |

Verdicts against the existing gates:
- **Area autotag: NO.** Best case tev1 at conf>=0.9 is 73% on 15 rows: more than 1 in 4 silent wrong tags on a tiny sample. Neither decision model beat gemma4:e4b on overall accuracy. Stays unwired.
- **Priority: NO.** nimble beats the majority class by ~8 pts (53.9% vs 46%) but confidence does not separate right from wrong, so there is nothing to gate on.
- **Fleet triage: NO.** Both beat e4b (43% / 39% vs 25%) but both sit below the always-DONE baseline (58%), and conf>=0.8 is worse than overall. Keep the worker-written status plus human QC; regex for outward-facing.
- No model clears a gate, so no wiring proposal. If one later does, the change is small: set `JEV_NATIVE_MODEL`, point `TYPESAFE_BASE_URL` at :11434, and gate `t add --auto` on a threshold measured on the native confidence scale, with human confirm below it.
- **shim.py is redundant for serving** (native /v1/systemone exists on 0.35+ for any local model). Not deleted: it is the only path giving gemma4 the calibrated `decide` logprob confidence, and test_shim.py covers it.
- **A TypeSafe account / API key (#502) is no longer needed if native wins.** The native endpoint accepts any key and nothing leaves the machine. Step 1 and Step 3 (cloud Jev head-to-head) only matter as a ceiling reference, which these numbers do not justify.

## Step 3: head-to-head bench (after the key)
Rerun the 156-task area benchmark from `~/forge/decide/bench.py` on real Jev and compare accuracy, latency, and calibration (right-rate above vs below 0.8 confidence) with decide e4b (50.6%, 57% vs 17%). OPSEC: GYA/client and Sugar Pills rows get scrubbed or skipped before anything goes to the cloud.

## Step 4: where it earns a place (confidence-gated: act when sure, ask when not)
1. `t add` auto-tag: area + priority, and ask only when confidence is low. Local shim.
2. Fleet report triage: every reports.md line gets DONE / BLOCKED / NEEDS-ADAM / outward-facing? That's the QC gate Maax runs by hand now. Local shim.
3. Job matches: apply yes/no + fit score on new-matches.md postings. Public data, so real Jev is fine.
4. Title/hook pre-screen before synth-survey: cut 20 candidates to 5 fast. Public data.
5. Console inbox: urgent? needs a reply tonight? Local shim.

## Step 5: the video (YouTube-first)
Build-with-me channel episode: "I tested an AI that isn't allowed to talk." Hook beat already proven in decide's build log: the bigger model was slower and its confidence was useless; the tiny model knew when it was guessing. Jev vs local clone is the showdown. Test line: TBD with data-scientist once the bench numbers exist.

## Not doing
Rewriting existing forge-lane lanes onto Jev before Step 3 shows it beats decide.

## Own model (9/30): local System One trained on Adam's own labels: SHIP as a suggester, NOT silent auto-tag
Built `own_model.py` (train/eval/predict) + `own-area`/`own-priority` Choice routes in `shim.py` + `test_own_model.py` (PASS). Multinomial logistic regression (sklearn, C=10) on nomic-embed-text embeddings of `title + notes`, all 507 tasks.db rows (incl. backlog), stratified 5-fold CV seed 7, out-of-fold predictions. Fully local, no LLM call at inference (one ~10 ms embed). Not wired into `t add`. Results: `own-model-results.json`. Ran under a gated-lite check: `whats-running --gate ollama` said NOT SAFE for a 12b-class load (RAM), but nomic-embed-text is 274 MB, so I ran it anyway.

**Area, same n=75 seed-7 sample as calibrate.py (12/area, done+open): accuracy 50.7% vs e4b 58.7%.** Raw accuracy on that class-balanced sample does NOT beat e4b (it is the harder sample: Inbox/Home/Army are 1/6 of it but only ~25% of the natural data). On the natural distribution (all 507): **60.4%** (majority baseline 31.8%, ECE 0.068). The win is calibration:

| conf cut | own, n=75 sample | own, all 507 | e4b, n=75 |
|---|---|---|---|
| >=0.8 | 78% right (n=9) vs 47% below | 82% (n=100, 20% coverage) vs 55% | 62% (n=69) vs 17% (n=6) |
| >=0.7 | 75% (n=16) vs 44% | 81% (n=176, 35%) | n/a |
| >=0.9 | 100% (n=1) | 89% (n=27, 5%) | 62% vs 42% |

e4b says >=0.8 on 92% of rows and is right 62%; own says >=0.8 on 12-20% and is right ~80%: the confidence means something. Sample at >=0.8 is only 9 rows, so the natural-distribution 507-row numbers are the trustworthy ones.

**Per-label (OOF, all 507; precision / recall / precision at conf>=0.8):** YouTube 77/84/86% (n=29); GYA 70/79/77% (n=52); Job Hunt 68/78/90% (n=10); Maax HQ 53/53/89% (n=9); Home 38/17/never >=0.8; Inbox 28/24/never >=0.8; Army 0/0 (only 6 rows, can't learn it). Inbox is a catch-all of vague items with no signal, so it is inherently unpredictable from text; that is a property of the labels, not the model.

**Safe-to-auto-tag threshold:** nothing reaches 95% and there is no free lunch. Right-rate curve (precision/coverage): 0.7 -> 81%/35%, 0.8 -> 82%/20%, 0.85 -> 89%/11%, 0.9 -> 89%/5%. Recommendation: use as a **suggester** in `t add` (prefill the area, show conf, Adam one-key confirms). If Maax wants silent tagging, only `conf>=0.85` AND predicted in {YouTube, Job Hunt, Maax HQ}: ~89% right, ~10% coverage, i.e. still 1 in 9 silently wrong, so only worth it if wrong tags are cheap to fix (`t` edit). Never auto-tag to Inbox/Home/Army.

**Priority: useless, drop it.** OOF accuracy on all 507 is 52.3% vs a 56.8% majority baseline (always-P4), and on the n=75 sample it is 13% (the sample is done+open rows, which are P1-3; the model learned "backlog = P4" from 288 P4 rows, a status confound, not a text signal). Priority is not predictable from the title; it depends on deadlines and status, which are not in the text.

**Ranking vs the field (area):** own 60.4% natural / 78-82% at conf>=0.8; e4b 58.7% (62% at >=0.8, bad calibration); decide e4b 50.6%. jev-systemone's nimble/tev1 numbers are logged separately (PLAN.md Step 3 section); compare on the same n=75 sample using `own-model-results.json` `calibrate_sample_n75`.

**Caveats:** 507 rows, one labeler, labels drifted (ClickUp list names became areas); C=10 was picked once, not tuned on a held-out set (a light sweep would be inside-CV optimism). Retrain (`uv run python own_model.py train`) as labels grow; the embedding cache makes it seconds. Kill test: if OOF acc at >=0.85 drops below 85% after retrain, stop suggesting.

**What a tev1 LoRA fine-tune would add (plan only, not trained):** tev1 (the Jev/TypeSafe native decision model on Ollama 0.35+) already emits calibrated choice probabilities with an LLM prior, so it should handle the low-signal middle (Maax HQ vs GYA vs YouTube, where text semantics matter) better than a linear probe on a 768-d embedding. A LoRA on the 507 rows (plus done-task history) would teach it Adam's private taxonomy (what "Maax HQ" vs "Inbox" mean here), which zero-shot cannot know. Expected gain: raise the 60% natural accuracy toward ~70% and lift coverage at 85%+ precision from ~11% to 25-35%. Limits: 507 rows is tiny (needs a held-out split of ~100, and 5-fold LoRA is expensive); it will not fix Inbox (label noise) or priority (no signal); the LoRA + tev1 inference costs ~10-100x the latency and RAM of this 10 ms model. Plan: (1) build the JSONL from tasks.db with the same CV folds, (2) train LoRA (rank 8, 3 epochs) on the 4 training folds, (3) score OOF on the 5th, (4) accept only if it beats own model's precision at matched coverage; (5) then an ensemble (average own + tev1 probs) is the likely best ship, since the two err differently. Do this only if the suggester proves useful in practice for a couple of weeks.
