# Changelog

All notable changes to Forge. Format follows [Keep a Changelog](https://keepachangelog.com); versioning is [SemVer](https://semver.org). Run `/forge-update` to pull the latest.

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
