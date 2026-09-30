# Changelog

All notable changes to Forge. Format follows [Keep a Changelog](https://keepachangelog.com); versioning is [SemVer](https://semver.org). Run `/forge-update` to pull the latest.

## [1.8.0] — 2026-09-30

Sync with the maintainer's live skill: the stall monitor learns to triage, Forge asks what a build is for before it rules on it, and two months of run learnings land in the public tree.

### Added
- **Stage 0A, "ask what it's for" (blocking).** Five intake questions before any research or verdict (who it's for beyond you, any equity or revenue stake, would you mind a competitor shipping it, a second human operator, what you'd regret). Answers go in `00-idea.md` under Intended use and are the recorded basis for the run mode. A verdict change re-opens the run and expires every override granted under the old verdict. Born when a run was ruled BUILD FOR SELF and speed-run, then turned out to be a business.
- **`forge-state park "why"` / `unpark` / `focus [--off]` / `scan --park-overflow`.** A run can be parked (scan never prints it; recording any gate unparks it) or focused (pinned first in the scan). Bookkeeping never touches the `updated` idle clock.
- **The scan's WIP cap: `scan` prints at most 3 stalled runs** (focused, then FAILED, then stalest) plus one counted line; `--cap N` and `--all` override. Sixteen always-red lines trained everyone to scroll past them.
- **`forge-state watchdog [--refresh] [--json] [--no-model] [--hook-lines]`** (`scripts/forge_watchdog.py`, with `scripts/test_forge_watchdog.py`, 16 tests). Says why each stalled run stopped: `BLOCKED_ON_HUMAN`, `BLOCKED_EXTERNAL`, `DONE_UNRECORDED`, `ABANDON`, or `RESUMABLE`, from deterministic rules. An optional local model (`FORGE_LANE`) only phrases the reason and can only make a verdict more conservative. Read-only. Report and handoff paths are `FORGE_WATCHDOG_REPORT` and `FORGE_HANDOFF_DIR`.
- **`cfo` family** registered in `forge_state.py` (`forge-state init --family cfo`).
- **F4: standard external-signal sources.** Every research stage that mines real voices includes YouTube comments (Data API) and Reddit through a grounded search lane, or declares them dry with the queries tried.
- **`SKILL.md` Log**: a Stage 3 score of 9.0 collapsed on first human contact. Stage 3 decides whether a build is worth a human's ten minutes and never replaces Stage 4; ask "how many rows prove a human used this"; exercise every never-executed path; run Stage 4 on the user's own device.

### Changed
- `LEARNINGS.md` gains the run and instrument learnings from two months of real runs, genericized: verification that passes what a human fails, the deploy-root leak, the version-control precondition, the synth-survey saturation, the WIP-cap-as-silencer failure, and the watchdog's rule-order bug.
- `SKILL.md` Stage 1 expert panel falls back to running the panel inline when `sc:business-panel` is not installed (F12).
- `FAMILY-RULES.md` F7 documents the WIP cap, the idle-clock rule, and the watchdog.
- `forge_state.py`: the tracked-run scan is factored into `stalled_runs()` so the watchdog reuses the same walk; output is unchanged.

## [1.7.0] — 2026-09-11

The predictions get graded. Reggie wrote one at every stage and every gate scored every artifact; nobody scored either, so the gates stayed where they were first set.

### Added
- **`forge-state outcome <what> --predicted "…" --actual "…" --grade hit|partial|miss [--stage] [--when] [--note] [--append <file>]`** appends an entry to an `outcomes:` list in the manifest frontmatter (F15). The vocabulary is `score`, `ship`, `field`, `reggie`; any short label is accepted. `--stage` is the stage the prediction was MADE at (default: current). Empty `--predicted` or `--actual` is refused: if nothing was predicted there is nothing to grade. `--append` writes one line to a file (a panel's learnings file); `reggie` defaults to `.reggie/predictions.md` when it exists, so the ruling lands where the call was made.
- **`forge-state status`** prints the tally (`OUTCOMES: 3 hit · 1 partial · 1 miss`) and one line per entry under the human entries. A run at its last stage with none prints `OUTCOMES: none graded` in the same style as BLOCKING. Flagged, never blocked: `next` and its exit codes are unchanged. `next` on a complete run and `verdict --close` each add one reminder line when nothing was graded.
- **`forge-state scan --calibration`** tallies every graded prediction across every run by family and kind, and lists what was not a hit. This is the read that moves a gate threshold (F8). `scan --verbose` adds one line counting runs at their last stage with nothing graded; the plain scan is unchanged.

### Changed
- `FAMILY-RULES.md` F15 item 2 is the outcome step; F11 names how Reggie gets graded. `init`'s body template carries a "Graded predictions" pointer at the field.
- `SKILL.md` Stage 5 names the four outcomes for a software run.

## [1.6.0] — 2026-09-11

The persona library: panels are loaded and extended, never rebuilt per run.

### Added
- **`personas/README.md`**: the library rule (F8) and the file format one sourced panel per file, an `About this panel` section for bias warnings and retirement flags, and a required `Sources:` line on every segment. Default location `~/personas/`, `PERSONA_LIBRARY` to move it.
- **`synth_survey.py --personas <audience>`** resolves a bare name against the library (`<library>/<audience>.md`); a path still wins. One small stdlib function, `resolve_personas()`.

### Changed
- `FAMILY-RULES.md` F8 carries the load-and-extend rule and the index. `SKILL.md` Stage 1 loads from the library and extends from the CEP segments instead of building from scratch.

## [1.5.0] — 2026-09-11

The human touchpoint is a field the state machine prints, not a sentence in the prose.

### Added
- **`forge-state human "<who>" --when <date> --how "<channel>" --said "<verbatim or path>"`** appends an entry to a `human:` list in the manifest frontmatter (F5, one named real human per run; a run can have several entries). `--stage` defaults to the run's current stage; `--said` may be the verbatim or the path to the file that holds it, and an empty `--said` is refused because an empty record is not a touchpoint.
- **`forge-state status`** prints every human entry under the gate table (date, who, channel, stage, the quoted verbatim). A run with none prints `HUMAN: none yet, all-synthetic` in the same style as BLOCKING. Flagged, never blocked: `next` and its exit codes are unchanged.
- **`forge-state scan --verbose`** adds one line counting tracked runs past Stage 1 with no human entry. Quiet otherwise, so the session-start hook is unchanged.

### Changed
- `init`'s body template: the "one real-human touchpoint" prose section is now a "Human touchpoint" pointer at the field and the command, so the prose and the frontmatter cannot disagree.
- `FAMILY-RULES.md` F5 carries the command and what `status`, `next`, and `scan` do with it.

## [1.4.0] — 2026-09-11

Two families in one release: the ads pipeline, and the job pipeline registered as-is.

### Added
- **The `ads` family** registered in `FAMILIES` in `scripts/forge_state.py` and in the family table of `FAMILY-RULES.md`: `/forge-ads`, manifest `ADS-STATE.md`, run directory `<property or client root>/ads/<slug>`, six stages (intake and a measurement gate that refuses to start until the conversion event fires on the destination page and is proven from the raw source; plan with the kill and scale rules written before any creative; creative and destination gated two-sided with an in-house veto on claims and policy; launch built paused with the go recorded; the 7-day read that executes the plan's own rules; the 28-day read and write-back). The claim: one-shot paid acquisition, even if you can't buy media. The family's SKILL.md is maintainer-side; this repo ships the registration so `forge-state init --family ads` works.
- **The `job` family** registered the same way: `/job-apply`, manifest `JOB-STATE.md`, run directory `<job-search root>/output/<slug>`, seven stages taken from the existing skill unchanged (source, read the form first, research, tailor, synth gate on both documents, packet, submit on an explicit go). The claim: one-shot ready-to-send application, even if you can't write about yourself. No rewrite; the pipeline already had the Forge shape and only lacked state.

### Changed
- `FAMILY-RULES.md`: the family table carries nine families; the routing paragraph sends ad spend to `/forge-ads` and applications to `/job-apply`; F0 lists both claims. The "planned" line is gone because the queue of families is empty.

## [1.3.2] — 2026-09-10

### Added
- **The `client` family** registered in `FAMILIES` in `scripts/forge_state.py` and in the family table of `FAMILY-RULES.md`: `/forge-client`, manifest `CLIENT-STATE.md`, run directory `<clients root>/<slug>`, six stages (discovery and the money step; proposal gated two-sided with an in-house veto, then signed and paid; shoot and edit spec, the shoot, the cut; delivery under a revision cap; invoice, then paid; testimonial, case study, write-back). The claim: one-shot paid client work, even if you've never run an agency. The family's SKILL.md is maintainer-side; this repo ships the registration so `forge-state init --family client` works.

## [1.3.1] — 2026-09-10

### Added
- **The `offer` family** registered in `FAMILIES` in `scripts/forge_state.py` and in the family table of `FAMILY-RULES.md`: `/forge-offer`, manifest `OFFER-STATE.md`, run directory `<project>/offers/<slug>`, seven stages (brief and the money step, CEP from the audience's own words, offer with a two-sided gate, build the thing, landing page and email sequence, launch with the payment path test-purchased first, measure at 28 days). The claim: one-shot owned revenue, even if you can't sell. The family's SKILL.md is maintainer-side; this repo ships the registration so `forge-state init --family offer` works.

## [1.3.0] — 2026-09-10

One rulebook, deltas per family.

### Added
- **`FAMILY-RULES.md`**: the rules every Forge family inherits, written once (F0 to F16: the claim, never run from `~`, compute and delegate-down, honest verdicts, first-party is a hypothesis, real signal over simulation with one named human per run, gates and the manifest, the run does not stop, the gate calibration kit, the copy gate, seam discipline, Reggie, artifacts, confidentiality, numbers, Stage 5 write-back, session economics). Each family's SKILL.md now says "inherits FAMILY-RULES.md" and carries only what differs; a rule whose body moved keeps its number and points at its F-number, so every existing cross-reference still resolves. The file ends with a grep that proves no family has grown its own copy back.
- **The channel line (F15).** Stage 5 of every family carries one tracked checklist line: the publishable artifact this run produced (for the maintainer, the AI channel), or an explicit `none`. Never a gate.

### Changed
- `SKILL.md` operating rules 1 to 7, 9, 10, and 14 are one-line pointers into the rulebook; Reggie's canon, the run modes, the frame check, and the Stage 2 approval narrowing stay here because they are software-specific.

## [1.2.0] — 2026-09-10

Forge advances like GSD instead of stopping like a memo.

### Added
- **`forge-state`** (`scripts/forge_state.py`): the pipeline's machine state lives in YAML frontmatter at the top of `FORGE-STATE.md`, exactly like GSD's `.planning/STATE.md`. `next` prints the single next stage and exits 2 while a blocking gate is owed, 3 when a gate has FAILED and needs a decision. `gate` records every transition and refuses to pass a later stage while an earlier blocking one is unresolved; a waiver needs a reason. `scan` names any run idle a day or more with a gate owed (wire it into a session-start hook). `init` adds frontmatter to an existing prose manifest. Families for the sibling pipelines (gtm, yt, research, content, games) are registered in `FAMILIES`.
- **Rule 14 — Forge does not stop.** STOP means exactly three things: a human-only input, an irreversible or outward-facing action, or a verdict that ends the run. Everything else is work, and Forge does the work. Every stage ends with a GSD-style paste-block.
- **Stage 0A — intended-use intake (blocking).** Five questions before any research or verdict, because a wrong run mode silently deletes whole stages.

### Changed
- Stage 2's approval beat is now exactly one thing: show the GSD PLAN before an executor touches code. The 2026-07-20 wording ("Forge STOPS at each stage boundary") over-corrected into a run that waited a day for a go nobody knew it wanted.
- Rule 5 ("gates block") now names its mechanism.

## [1.1.0] — 2026-07-09

First self-updating release. Forge now carries a changelog and an in-place updater (`/forge-update`), and gained a full go-to-market front end.

### Added
- **Stage G — GTM & Founder-Resource Fit** (the new first gate). Choose the optimal go-to-market from the founder's real resources *before* hunting a product: audience, budget, distribution, skills-as-distribution, time. Optimizes for time-to-income (match the offer type to current reach — high-ticket-first when there's no audience), outputs a roadmap to full-time income, and wires an audience-first handoff so a "build software" run can honestly pause on a content play when that's the faster path. Includes a founder-profile intake (questionnaire + data-mining) for cold users.
- **Stage H — Hunt + Tournament.** Discover the winning idea across the open internet instead of only validating one you already have: parallel pain-hunt, independent quote verification, and a scored tournament with advocate/skeptic judges. Aim the hunt at the founder's unfair advantage — an open hunt lands in red oceans.
- **Company-Builder autonomous mode.** The whole pipeline from a single goal-prompt: never-ask, done-when-the-definition-of-done-is-met. Delegate-down (the session plans/delegates/reviews; workers are cheaper models). Ships with a master-prompt reference.
- **Stage 2B — Brand system.** Name + domain-availability check, logo generation loop, type system, and brand guidelines.
- **Stage 5 launch assets + stranger-test recap.** Product-demo video, founder video, packaged docs, and a single recap page a stranger can open to understand, run, and demo the whole thing.
- **Stage 1 red-team swarm** for market candidates (skeptics by attack surface; surviving fixes applied back).
- **Operating rule — validate the frame before spending; real-signal over simulation; founder-advantage input.** The moat lives in rare skill intersections, not in "uses AI" (leverage is not a moat).
- **`/forge-update`, `VERSION`, and this changelog** — Forge can now update itself and tell you what changed.
- **SessionStart update nudge** — `scripts/forge-update-check.sh` prints a one-line "update available" notice at session start when you're behind (throttled to one network fetch per day, silent on any failure). `install.sh` offers to register it as an opt-in hook.

### Fixed
- Self-review pass (Forge run through Forge before release): resolved a contradiction between autonomous "never-ask" and the founder-fuel input (the profile is now captured at intake), fixed broken cross-references and a false artifact-sort claim, added missing mode-table and state-seed rows, wired the dangling audience-first branch, and cut ~15% bloat.

## [1.0.0] — 2026-07-06 → 2026-07-07

Initial Forge. Honest 3-verdict validation (BUILD FOR SELF / BUILD FOR MARKET / DON'T BUILD) in front of a GSD build engine, panel-scored synthetic usability rounds to 9/10, a real-world field test, and ship + learnings. Gate-calibration kit (ground-truth block, calibrated anchors, plateau rule), the FORGE-STATE.md resume-cold manifest, five-gate seam discipline, and Reggie the adversarial agent.
