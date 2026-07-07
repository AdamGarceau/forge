---
name: forge
description: >
  the founder's complete idea-to-field-tested-software pipeline — "GSD for building
  anything software, run by a non-coder founder." Forge builds ANY software:
  websites, web apps, native apps, tools, automations, dashboards, scripts,
  SaaS — not just "apps." Use this skill WHENEVER the founder wants to build any new
  software — even if he never says "forge": trigger on "build me a website/app/
  tool," "make me a landing page," "I have an idea for," "make me a tool that,"
  "should I build," "is this worth building," "productize," "turn this into a
  product," "build X for me," or any moment a new software build is about to
  start ad-hoc. It REPLACES /product-sprint (which now redirects here). Pipeline:
  kill criteria → honest 3-verdict validation (BUILD FOR SELF / BUILD FOR MARKET
  / DON'T BUILD) → GSD build → panel-scored synthetic usability rounds to 9/10 →
  real-world field test punch list → ship + learnings. Also use it when the founder asks
  whether an EXISTING personal tool should become a product (start at Stage 1).
---

# /forge — Idea to Field-Tested App

The standing process for every new build. Born 2026-07-06 from three proven runs:

- **A personal compliance tracker** — the validation front-end: expert panel → CEP/ICP external research → synth-survey gate, which correctly returned REWORK/build-for-self instead of flattery.
- **A production app** — the build discipline: GSD `.planning/` state, ~16 phases, 266 atomic commits, verification + human-UAT gates. Any session can resume it cold.
- **Deadreckon** (live at deadreckon.adamgarceau.com) — the quality loop: "review-board corrections" before v1, then five panel-scored usability rounds ("round 4 -> 9 push", "reach 9/10 across panel"), then a field test that produced a 3-item punch list. Field-verified precise.

Forge is the marriage: Deadreckon-style gates around a GSD build engine, with hard honesty rules in front.

**Why this exists:** the founder is a marketer, not a coder. The framework must hold the system so he only supplies judgment at gates. And builds without durable state get lost (Deadreckon's source took a 30-minute forensic hunt to find — never again).

## Operating rules (apply to every stage)

1. **Never run from `~`.** Create/enter the project directory first, register it in your workspace registry at Stage 2.
2. **Honest verdicts are the product.** Never tell the founder what he wants to hear . Population-share weights, external evidence for market claims, adversarial refutation before verdicts.
3. **Local models do the simulated humans.** Synth respondents/usability walkers run on `ollama` `gemma4:12b` (`think:false`, `num_ctx:16384`) — free, per the CLAUDE.md router.
4. **Every stage writes an artifact** into `<project>/validation/` or `.planning/` so any future session resumes cold.
5. **Gates block.** A stage's exit criteria unmet = the next stage does not start. the founder can override any gate explicitly; record the override in STATE.md.
6. **Orchestrated skills are accelerants, not hard requirements.** Forge calls other skills where they exist (`sc:business-panel`, `cep`, `big-idea`, `copy`, `copy-editor`, `web-design-craft`, `web-launch`, `usability-test`, GSD). Only the synthetic-audience tooling is bundled (`scripts/synth_survey.py`, `scripts/synth_usability.py`) and always works. If a called skill isn't installed, **do its job directly with the main model instead of erroring or hanging** — e.g. no `sc:business-panel` → run the expert-panel reasoning inline; no `cep` → do the forum/review research with a research agent; no `copy`/`copy-editor` → write and edit the copy directly against the Stage 1 language bank. Tell the founder which skill would have helped and how to add it, then continue. Never let a missing optional skill stall the pipeline.

## Stage 0 — Capture + Kill Criteria (before ANY research)

Write `<project-or-scratch>/validation/00-idea.md`:
- The idea in the founder's words; the job it does; who it's for (hypothesis).
- **Kill criteria, written BEFORE research so the bar can't bend to the evidence:** what specific external evidence would earn BUILD FOR MARKET (nameable existing audience gathering somewhere + evidence of current spend or painful workarounds + a distribution path the founder can actually reach). What would mean DON'T BUILD (e.g., a good-enough free incumbent, legal exposure, maintenance burden beyond one person).
- Which run mode the founder wants if validation lands BUILD FOR SELF: speed-run (default) or stop.

## Stage 1 — VALIDATE (three verdicts, no flattery)

Run three lenses, cheapest-appropriate models, artifacts numbered into `validation/`:

1. **Expert panel** — invoke `sc:business-panel` on the idea (main-model judgment work). Output: `01-expert-panel.md` with consensus, disagreements, and the panel's verdict lean.
2. **CEP/ICP external-signal research** — invoke `cep` (or a research agent with its method): mine forums, reviews, news, Q&A for the trigger situations, segments with share-of-voice, verbatim language bank. Real quotes with URLs only; dry sources declared dry. Output: `02-cep-external-signal.md`.
3. **Synth survey** — invoke `synth-survey`: personas built FROM the CEP segments, `n=1000`, **weights = population share-of-voice** (include the founder's persona at its real share; owner-weighted views may be shown only as a labeled secondary number). Output: `03-synth-survey-report.md`.

Then the **adversarial pass**: a separate agent (fresh context, ideally a different model than wrote the survey) whose only job is to refute the market case (spawn with an explicit "try to kill this" prompt). It must either land at least one surviving kill OR explicitly justify why none survives, citing external evidence — "looks good" is not an acceptable refutation output. Output: `04-refutation.md`.

**Verdict — exactly one of three**, written to `05-verdict.md` with the weighted evidence:
- **DON'T BUILD** — kill criteria hit, or refutation stands. Say it plainly; archive the folder.
- **BUILD FOR SELF** — the pain is the founder's and real, but external demand evidence is missing or only synthetic. This is a first-class outcome, not a consolation prize. → proceed in **speed-run mode**.
- **BUILD FOR MARKET** — kill criteria's external-evidence bar met and the case survived refutation. → proceed in **full mode**.

A MARKET verdict founded only on synthetic enthusiasm is forbidden — cap it at BUILD FOR SELF and say why.

## Stage 2 — BUILD (GSD strongly recommended)

**GSD is Forge's recommended build engine — highly encouraged, not required.**
When it's installed, Stage 2 IS a GSD run: Forge delegates wholesale to GSD
(`/gsd-new-project` → `/gsd-plan-phase` → `/gsd-execute-phase` → `/gsd-verify-work`,
or `/gsd-quick` for speed-runs). GSD gives the build durable `.planning/` state,
atomic commits, and verification gates so any session can resume it cold — the
discipline a non-coder founder needs. Forge's own contribution is the gates AROUND
the build (Stages 0-1 in front, 3-5 behind).

**If GSD isn't installed, don't stop — recommend it, then fall back gracefully:**
- Offer to add it first (it's a public npm package):
  `npx -y @opengsd/get-shit-done-redux@latest --global` (install.sh offers this too).
  Encourage it — the durable-state + verification discipline is a real quality
  difference, not a formality.
- If the founder declines or it's unavailable, build directly with Claude Code while
  keeping GSD's disciplines by hand: create the project dir, write a lightweight
  `.planning/` (requirements from Stage 1 artifacts, a phase list, a STATE.md so a
  future session resumes cold), commit atomically per feature, and verify each
  feature runs before moving on. Stages 0-1 and 3-5 are unchanged.

Never silently skip the build discipline because GSD is absent — degrade
gracefully, don't disappear.

**Before building, read `references/deadreckon-session-patterns.md`** — the eight
collaboration behaviors from the Deadreckon session (outcome-language translation,
verify→screenshot→commit→deploy per feature, the honest-limit pattern, field-meaning
feature descriptions, "ask our audience" mid-build, the standing sprint offer,
one-exact-action ops asks, fallbacks for every automation). They are how a
non-coder founder stays in command of a build.

- `mkdir` the project, `cd` in, add it to your workspace registry, then run GSD: `/gsd-new-project` (full mode) or `/gsd-quick`-style compressed phases (speed-run). The PROJECT.md context comes FROM Stage 1 artifacts — segments, language bank, and top objections become requirements (e.g., a privacy-tool survey where "your data never leaves your computer" became a UI requirement, not a marketing line).
- Front-end work loads `web-design-craft`; anything with charts loads `dataviz`. Accessibility is a standing requirement (build as if a blind / low-vision user is a primary user) — build to it, and it gets gated in Stage 3.
- Deploy/hosting per project type (`wrangler pages deploy` pattern; the deploy config lives in the repo like Deadreckon's, so redeploys are one command).

**COPY IS PART OF THE BUILD (not a Stage-5 afterthought).** Any user-facing software — especially websites and landing pages — is only as good as its words. For every user-facing surface (headlines, value props, landing copy, empty states, CTAs, onboarding), run the **Copy OS pipeline**: `big-idea` to pick the angle, `copy` to write it (grounded in the SAME Stage 1 CEP research + language bank — do not re-research), `copy-editor` for the final pass, gated through `synth-survey` to 9/10+ per a standing copy-validation rule (validate all user-facing copy against the same audience — treat as non-negotiable, not market-only). The Stage 1 personas and language bank are the inputs; the copy is tested against the same audience as the product.

**BUILD THE FEATURES THEY DIDN'T ASK FOR (the "features you didn't know you needed" mechanism).** After GSD requirements are drafted, run an explicit **gap-feature pass**: re-read the Stage 1 CEP segments and top objections and list what the segments NEED but the founder did NOT request (e.g., a privacy tool → "your data never leaves your computer" as a real feature; Deadreckon → auto pace-count, hazard warnings, SOS-copy). Feed the survivors into GSD requirements. This is where the claimed magic actually happens — make it a real step, not a vibe.

- Exit gate: GSD verification passes AND the app runs end-to-end on the core task AND user-facing copy has cleared the copy-validation gate.

## Stage 3 — SYNTH USABILITY (the Deadreckon loop)

GV-sprint-style testing with simulated users, iterated in ROUNDS like Deadreckon's five:

1. Define the 3-5 **core tasks** a user must complete (from Stage 1 CEPs — e.g., "log this week's 4 contacts and export them").
2. For each persona segment (from your Stage 1 personas file), run a **walkthrough**: feed gemma4:12b the persona + the actual UI state (screenshots described, or the rendered HTML/text of each screen) task-by-task; it narrates where it hesitates, misreads, or gives up, then scores task completion + confidence 1-10. Use the `usability-test` skill if it's installed and its harness fits; otherwise use the bundled `scripts/synth_usability.py` (no extra skills needed). **Include a screen-reader / low-vision persona** every run — accessibility is gated here, not assumed. For a web build, Claude can also drive the real UI (browser/computer control) and observe it directly, not just read the HTML.
3. Panel-score the round (weighted like Stage 1). **Ship gate: ≥9/10 across the panel, and every core task completable by every segment INCLUDING the accessibility persona.**
4. Fix, commit (`Usability round N fixes (toward 9/10)` — keep Deadreckon's commit convention), re-run. Expect 3-6 rounds; Deadreckon took 5.
- Speed-run mode: 2 personas (the founder's + one naive first-timer), gate at 8/10.
- ⚠️ **Sycophancy guard (this stage and Stage 1):** simulated users PRAISE things real users reject — the single most-replicated failure mode (see validation/07 accuracy research). So: prompt walkers/refuters to look for FAILURE first ("find where this breaks; default to a problem if unsure"); a round that surfaces zero problems is suspect, not a pass — re-run with a harsher persona or a fresh model. The synthetic gate is a cheap FILTER; Stage 4 (real humans) is the only real check, which is why it can't be skipped.

## Stage 4 — FIELD TEST (real world, real punch list)

Synthetic users can't feel glare, gloves, or GPS drift. You use the app on the real task in the real environment (Deadreckon: land navigation in the field; a compliance tracker: an actual real filing).
- Capture a **punch list** in `.planning/FIELD-TEST.md`: what broke, what annoyed, what was missing. Deadreckon's was ~3 items ("stop calling good taps Sloppy", 3D crash on iPhone, calibration magnifier).
- Fix the punch list, one atomic commit each. A second field pass confirms.
- Exit gate: the founder says it worked in the field, punch list empty.

## Stage 5 — SHIP + LEARNINGS

- BUILD FOR SELF: install it into daily life (launchd job, home-screen PWA, bookmark) and stop — no marketing hours.
- BUILD FOR MARKET: run `web-launch` for the go-to-market; copy goes through the standing copy-validation pipeline (ICP+CEP → synth survey to 9/10+).
- Either way, write back: update WORKSPACE.md state, append run learnings to the synth-survey learnings file for the product, and record what the pipeline itself got wrong in `~/.claude/skills/forge/LEARNINGS.md` (create on first run). A run that doesn't write back is a wasted run.

## Speed-run vs full mode summary

| Stage | Speed-run (BUILD FOR SELF) | Full (BUILD FOR MARKET) |
|---|---|---|
| 0 Kill criteria | Required (it's one paragraph) | Required |
| 1 Validate | May compress to panel + survey if the CEP signal is obvious; verdict still honest | All four artifacts |
| 2 Build | gsd-quick / few phases | Full GSD phases + verification |
| 3 Usability | 2 personas, gate 8/10 | Full panel, gate 9/10 |
| 4 Field test | 1 pass + punch list | 2 passes minimum |
| 5 Ship | Install into life | web-launch + copy pipeline |
