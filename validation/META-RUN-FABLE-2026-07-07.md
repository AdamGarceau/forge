# Forge through Forge — self-audit meta-run, 2026-07-07

Forge's own rules, applied to Forge. Method: reference-integrity audit of the
skill + a failure-first synthetic panel (6 personas on local gemma4:12b,
`think:false`, `num_ctx:16384`, sycophancy guard on) + an adversarial refuter,
with every panel claim verified against the actual files before being kept.
A prior smoke-test pass (2026-07-06) eval'd the validation front-end only
(Stages 0-1, with-skill vs baseline); this pass covers what that one didn't:
Stages 2-5, resume-cold behavior, and reference integrity.

Raw panel outputs are retained in the maintainer's local archive (they contain
machine-specific context); this report carries everything that mattered.

---

## Headline finding (from the audit, not the panel)

**The skill had forked.** The maintainer's live installed copy and this repo's
`SKILL.md` diverged within a day of each other — fixes (graceful degradation for
missing skills, bundled synth scripts, a real citation for the sycophancy
research) landed in one copy and never reached the other, with no sync
mechanism between them. Bonus irony: the workspace registry pointed at a
`validation/` self-audit folder that had never been committed — the previous
meta-run's artifacts were simply lost, the exact provenance failure Forge was
built to prevent. This file restores the location; both copies now carry a
mutual sync note.

## Reference integrity

Every skill, file, and citation the pipeline invokes was checked on disk. Found
and fixed: two invoked skills that had been archived (`sc:business-panel`,
`big-idea` — now replaced with inline equivalents per the degradation rule), one
citation pointing at a nonexistent research file (now
`references/synthetic-audience-evidence.md`), and a Stage 3 personas file living
in volatile `/tmp` (now a durable `validation/03-personas.md` artifact).

## Panel results (failure-first prompting; scores are attack-mode — read the findings, not the numbers)

| Persona | Score | Core finding | Verdict after verification |
|---|---|---|---|
| Founder-on-phone | 3/10 | The skill never states up front that the AI drives everything and the founder only speaks outcomes (buried in a reference file); no in-field punch-list capture path | CONFIRMED (doc gap + feature gap) |
| Cold session, 3 wks later | 4/10 | No machine-readable pipeline state manifest — a project killed at Stage 1 or paused mid-Stage-3 was unreconstructable; no Stage 3 protocol for CLI/backend (UI-less) builds | CONFIRMED — matched the audit's independent finding |
| Skeptical engineer | 3/10 | 9/10 panel gate gameable; proposed failure-mode mapping (walker names 3 concrete ways a user could fail each task; founder reproduces them pre-field) | CONFIRMED as upgrade |
| Tiny-tool speed-run | 2/10 | Even speed-run over-taxes a 30-line utility → the founder will bypass Forge entirely, eroding the system | CONFIRMED — erosion risk is real |
| Accessibility specialist | 2/10 | A text persona role-playing a screen reader cannot catch ARIA / focus-order / contrast / live-region failures; the gate was theater without an automated audit | CONFIRMED |
| Adversarial refuter | 3/10 | "Validation is redundant ritual" — REFUTED by the 07-06 eval evidence (skill vs baseline produced materially different verdicts). But "cap the usability rounds" and "add a feasibility check before the build" survive | PARTIAL |

## Fixes applied same-day (P0)

1. **De-forked** — mutual sync notes in both copies; portable fixes backported
   both directions.
2. **FORGE-STATE.md** (operating rule 8) — a pipeline-wide resume-cold manifest
   created at Stage 0 and updated at every stage transition. GSD's build state
   only starts at Stage 2; this covers the whole pipeline.
3. **Real accessibility gate** — Stage 3 web builds now require a clean
   axe-core/Lighthouse pass on critical WCAG rules BEFORE persona walkthroughs,
   and the audit is part of the ship gate. The screen-reader persona supplements
   the audit, never substitutes.
4. All broken/fragile references repaired (see Reference integrity above).

## Open backlog (P1/P2)

- **Utility mode** — a third run mode for sub-1-hour single-user tools:
  kill-paragraph → build → one real-use field pass; copy gate scoped to copy
  other humans actually read.
- **Early-kill short-circuit in Stage 1** — if a pre-registered kill criterion
  is conclusively hit by any artifact, write the DON'T BUILD verdict then;
  don't run the remaining lenses.
- **Failure-mode mapping + round cap in Stage 3** — walkers name 3 concrete
  ways to fail each task (reproduced manually pre-field); if a round's score
  doesn't improve on the previous, stop iterating synthetically and go to field.
- **In-field punch-list capture** — name a voice-note capture path so field
  notes don't wait for a desk session.
- **Ideas graveyard + Stage 0 registration** — DON'T BUILD folders archive to a
  named home; the project registers in the workspace registry at Stage 0, not
  Stage 2.
- **Per-type field-test definitions** — website = live-traffic smoke test;
  automation = one real scheduled run; script = run on real data.
- **Wider refuter scope for SELF verdicts** — also attack build-at-all
  (good-enough free incumbent, maintenance burden), not just the market case;
  prefer a different model family to dodge shared-weights convergence.
- **Feasibility paragraph in the Stage 1 verdict** — platform blockers named
  before the build starts, so a doomed build dies at verdict.

## Verdict on Forge itself, Forge-style

**BUILD FOR MARKET — already validated by use.** The pipeline's discriminating
value (kill criteria before research, three honest verdicts, mandatory
adversarial refutation) survived its own refuter with external evidence: the
smoke-test evals showed the skill and a bare baseline reach materially
different verdicts on the same ideas. But at audit time it failed its own
Stage 3 gate — resume-cold broke before Stage 2, the accessibility gate was
synthetic-only, and the installed copy was a stale fork. P0 fixed; the backlog
above is the next round.
