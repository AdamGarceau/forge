# FAMILY-RULES.md — the rules every Forge family inherits

> Added in 1.3.0. Forge grew siblings (a GTM pipeline, a research pipeline, a
> content pipeline, a games pipeline), and each one carried its own copy of the
> same dozen rules. An audit found them drifted: the same rule under a different
> number in each file, a rule cited that three of them did not have, a manifest
> name that disagreed with the file's own rules. This file is the fix for that
> class of bug. A shared rule is written **once, here**; each family's SKILL.md
> says "inherits FAMILY-RULES.md" and carries only what differs. When a rule here
> changes, it changes once. When a family needs an exception, the exception lives
> in the family file and names the F-number it overrides.
>
> This public repo ships the software family (`/forge`). The maintainer's
> siblings are registered in `FAMILIES` in `scripts/forge_state.py`; the table
> below is what the state machine knows about, so a family you add is a family
> once it is registered there.

## The family

| Family | Command | Manifest | Run directory | `forge-state init` |
|---|---|---|---|---|
| software | `/forge` | `FORGE-STATE.md` | `<project>` | (default) |
| games | `/forge-games` | `FORGE-STATE.md` | `<project>` | `--family games` |
| gtm | `/forge-gtm` (`--lens product` or `--lens youtube`) | `LAUNCH-STATE.md` | `<project>/output/<slug>/launch-plan` | `--family gtm` |
| research | `/forge-research` | `RESEARCH-STATE.md` | `<project>` | `--family research` |
| content | `/forge-content` | `CONTENT-STATE.md` | `<channel or project>/videos/<slug>` | `--family content` |
| offer | `/forge-offer` | `OFFER-STATE.md` | `<project>/offers/<slug>` | `--family offer` |
| client | `/forge-client` | `CLIENT-STATE.md` | `<clients root>/<slug>` | `--family client` |
| ads | `/forge-ads` | `ADS-STATE.md` | `<property or client root>/ads/<slug>` | `--family ads` |
| job | `/job-apply` | `JOB-STATE.md` | `<job-search root>/output/<slug>` | `--family job` |

Routing between families: software builds go to `/forge`, games to `/forge-games`,
marketing plans and channel asks to `/forge-gtm`, "verify everything / research
paper" to `/forge-research`, "make the video" to `/forge-content`, "what do we
sell them" to `/forge-offer`, and a lead, proposal, shoot, invoice, or case study for a paying
client to `/forge-client`; money about to be spent on ads (a pixel question, a campaign, a
budget, a 7-day read) to `/forge-ads`, and a job application to `/job-apply`. A package or pitch that rests on unverified
numbers runs research first.

## F0. The claim

Every family's H1 is followed by the same shape of promise:

> **The claim:** One-shot `<thing>`, even if you can't `<skill>`. Every Forge family
> makes the same shape of promise: one shot, gated, honest, resumable cold; the
> founder supplies judgment at the gates and nothing else.

software: software / code. games: playable game / code. gtm: launch plan / market
(youtube lens: channel strategy / read a channel). research: verified evidence /
investigate. content: published video / edit. offer: owned revenue / sell. client:
paid client work / run an agency. ads: paid acquisition / buy media. job: a
ready-to-send application / write about yourself. A new family states its
claim in this shape before it states anything else.

## F1. Never run from `~`

`cd` into the run directory (table above) before any Forge command. Home-root
sessions load no project context and re-feed the same cold context every turn.
Register a new project directory in your workspace registry when it is created.

## F2. Compute: cheap lanes for line work, the session for judgment

**Free first, always. The orchestrating model judges; it never does line work.**

- Every worker call goes through the cheapest lane that can do it, in a fixed
  order you do not reorder per task: local models, then a cheap hosted lane,
  then escalate to a Claude-tier worker with the evidence that the cheap lanes
  could not. (The maintainer's router is a single script, `forge-lane <task>
  "prompt"`, with that order hard-coded; build the equivalent once and route
  through it everywhere.)
- **A Claude-tier worker is justified only after the cheap lanes returned an
  escalate, or when the work needs MCP or browser tools.** A top-tier session
  manages and never does line work.
- **Delegate down, always.** The session PLANS, DELEGATES, REVIEWS. Fan out
  independent workers in ONE message. The session never writes a doc a worker
  could have written.
- **Synthetic respondents never leave the machine.** They run on a local model
  (`gemma4:12b`, `think:false`, `num_ctx:16384`), no exceptions. Anything with
  client data, credentials, or private records stays local too.
- **Batch, don't chat.** Write inputs to files, run the lane in a shell loop,
  read the outputs once. One orchestrator turn consumes a directory of results,
  not one result.
- **Media and data work is scripts and MCPs, not model turns.** API harvests run
  once and write CSV; agents read CSV. `ffprobe`, `ffmpeg`, Whisper, `yt-dlp`. A
  model never "watches" a video when a transcript answers it.
- **Log the split.** The manifest's compute section reports local / hosted /
  Claude-tier turns. A run with more orchestrator turns than lane calls is a
  routing failure; note it.

## F3. Honest verdicts are the product

Never tell the founder what they want to hear. Population-share weights, external
evidence for market claims, adversarial refutation before any verdict. Rank on
stated axes with scores and name what loses and why. If the content is fine and
the funnel is broken, say the funnel is broken. If a subject is at the category
ceiling, say ceiling. A DON'T BUILD, a REWORK, or a "could not verify" is a
successful run, not a failed one.

## F4. First-party is a hypothesis, not evidence

Anything the founder, a client, or the subject says about a market, an audience,
or a number goes in tagged `first-party` and is then fact-checked by a worker
against two or more independent sources. The note keeps the quote and gains a
verdict: **first-party, confirmed** / **partially supported** / **contradicted**,
with links. Never silently upgrade a claim to a sourced finding. Tier and tag
vocabulary: TIER 1 paid customer / first-party company response / official
record; TIER 2 candid forum, named reviewer, court or corporate filing; TIER 3
anonymous, behavioral, or platform-derived; LEAD marketing claim by the subject.
`[VERIFIED live YYYY-MM-DD]`, `[VERIFIED archived YYYY-MM-DD]`, `[INFERRED from
X]`, `[UNSUPPORTED]`, `[CONTRADICTED by X]`. "COULD NOT VERIFY" is a valid answer.

## F5. Real signal over simulation, and one named human per run

Synthetic panels, surveys, and red-teams are a FILTER, never the verdict. When a
real signal is cheaply available (the founder's own knowledge, a live customer, a
playtester on the couch, actual sales or audience data, a real market page), get
it instead of simulating it. The founder is usually one message away; do not
guess what they can tell you. Interactive modes ask; autonomous mode collects
these at intake.

**Every manifest names the ONE real-human touchpoint the run used or is missing.**
All-synthetic is a flagged risk, not a clean pass. The record is a field, not a
prose line:

```
forge-state human "<who>" --when <date> --how "<channel>" --said "<verbatim or path>"
```

It appends to the frontmatter `human:` list (a run can have several; `--stage`
defaults to the current stage). `forge-state status` prints every entry under
the gate table; a run with none prints `HUMAN: none yet, all-synthetic` in the
same style as BLOCKING. `next` never gates on it; `scan --verbose` counts runs
past Stage 1 with no entry. The verbatim goes in `--said`, or the path to the
file that holds it.

## F6. Gates block, `forge-state` is the mechanism, the manifest is the resume-cold document

- A stage's exit criteria unmet = the next stage does not start. `forge-state gate`
  refuses to pass a later stage while an earlier blocking one is unresolved
  (`--force` records an out-of-order pass as such). The founder can override any
  gate explicitly: `forge-state gate <stage> waived --note "why"`; the reason is
  the record.
- **The manifest** (table above) is created at Stage 0 by `forge-state init` in the
  run directory, and it is the pipeline's resume-cold document: a run paused at any
  stage must be reconstructable from this file alone. **The YAML frontmatter at the
  top is the machine's**, owned by `forge-state`, never hand-edited: stage (derived
  from the gates, so it cannot go stale), gates, verdict, next action. **The prose
  beneath it is the human's**, updated at EVERY stage transition and gate event:
  current stage and run mode, artifact checklist (path, gate pass/fail/pending),
  key decisions, verdict once landed, gate overrides with reasons, first-party
  claims and their verdicts (F4), the human touchpoint (F5), the compute split
  (F2), the Reggie line (F11), the channel line (F15), and the single next action.
  No sidecar JSON; two files describing one run drift.
- If a handoff exists when a run starts, the family's Stage 0 brief in the run
  directory is the frozen brief: copy the handoff there, then delete the handoff.
- A stage nobody recorded did not happen.

## F7. The run does not stop

Born when a real run sat at Stage 2 for a day with two later stages marked owed
and BLOCKING, and nothing (not the skill, not the state file, not the session)
noticed. It stopped because "gates block" was a sentence rather than a mechanism.

```
forge-state next                         # the single next stage; exit 2 = a blocking gate is owed, 3 = a gate FAILED
forge-state gate <stage> pass|fail|waived --note "…" [--next "…"]   # every transition records itself
forge-state status                       # every gate, what blocks, how long owed
forge-state init [--family …]            # once, at Stage 0, in the run directory
forge-state verdict "…" [--close]        # the verdict; --close ends the run
forge-state scan                         # session-start hook; names runs idle a day+ with a gate owed; silent when clean
```

- **Every Forge session begins with `forge-state next` in the run directory.** Its
  exit code IS the gate: 0 nothing blocks, 2 a blocking stage is owed (run it), 3 a
  stage failed (decide). Branch on it instead of asserting it.
- **STOP means exactly three things and nothing else.** Between them the run
  advances to the next owed stage on its own, unasked, until one of these is
  genuinely hit:
  1. **A human-only input.** A real answer only the founder, the client, the
     operator, or a playtester holds. Simulating it instead is forbidden (F5).
  2. **An irreversible or outward-facing action.** Sending in the founder's name,
     publishing, purchasing, deploying, deleting. Gated everywhere, not just here.
  3. **A verdict that ends the run**, or a gate that genuinely failed and needs a
     scope call (`forge-state next` exits 3 until it is decided).
- **Everything else is work, and the run does the work.** An owed round is not a
  reason to stop; it is the next thing to run. A failed round is a fix and a re-run.
  Missing research is a delegated worker call. "Awaiting approval to continue" on a
  stage that needs no human answer is a bug in the run, not politeness. Make the
  routine call, state the assumption, do the work, report. A run reports at
  boundaries and keeps moving.
- **End every stage the way GSD does, with the exact command to paste next:**

  ```
  ▶ CLEAR, THEN PASTE:

    cd <run directory> && /<family command>
    Resume at Stage <n>.
  ```

  `forge-state next` prints that block already, with the family's own command and
  directory. Print it at every stage boundary, so the founder never has to work
  out what to type.

## F8. Gate calibration kit: applies to EVERY synthetic gate

Every synth survey, usability round, red-team, perception check, and document
gate in every family. Learned from two real gate runs that plateaued below the
bar for structural reasons, not quality reasons.

- **GROUND_TRUTH block in every judge prompt:** the verified facts judges may not
  penalize (real metrics, real product behavior, real citations, the subject's own
  published material). Failure-first prompting without it punishes TRUE
  statements; one package jumped 6.2 to 8.0 the moment the block went in.
- **Calibrated anchors:** define what a 9 means for THIS artifact class, with one
  concrete example. The gate should be hard, not rigged.
- **Plateau rule:** three or more consecutive flat rounds with recycled or
  contradictory objections (a judge re-quoting deleted text) = structural ceiling,
  not a quality gap. Declare it honestly (F3), ship at the plateau with the gap
  named in the manifest, and convert the residual objections into field-prep
  material. Detection beats a dumb round cap.
- **Two-sided judging on client-facing offer artifacts** (proposal, SOW, package,
  pricing page): the buying-side panel AND an in-house lens (deliverability,
  margin, scope creep, rights and ownership, maintenance). The in-house lens has
  VETO: a change that raises client scores by promising something you can't or
  shouldn't deliver is rejected regardless of score gain.
- **Sourced personas or no personas.** A synthetic panel is built only from a
  persona file whose every segment cites its sources and n. Extrapolating a
  persona from a handful of comments is banned. Reuse before rebuild.
- **A synthetic panel may never score enjoyment, taste, or fun.** Perception and
  comprehension questions only (readability, contrast, "what does this button
  do"). Any number purporting to score fun is deleted, not discounted.
- **A walkthrough or red-team with zero problems is suspect, not a pass.** Re-run
  with a harsher prompt or model.

## F9. The copy gate

Copy the founder might say, send, publish, or record clears two gates, in order:
a synthetic survey to 9/10 (or a declared plateau, F8) against the run's sourced
persona panel with the GROUND_TRUTH block included, then a copy-edit pass in the
founder's register. Titles, hooks, thumbnails-as-text, descriptions,
leave-behinds, decks, proposals, landing pages, emails, store pages all count as
copy. No em-dashes or en-dashes anywhere in a shipped package (`grep -c "—\|–"`
= 0 is a checklist item). Plain language, the audience's own vocabulary.

## F10. Top-tier discipline at the seams, never as extra rounds

The stages carry the macro discipline (refutation, gates, verification); the
moments BETWEEN them (interpreting artifacts, gate pass/fail calls, mid-build
deviations, debugging) are where quality quietly varies with the model in the
seat. There, the orchestrator and any subagent doing judgment work runs a
five-gate micro-discipline: **scope** the subtask and its unknowns; verify
**evidence** before reasoning on it (read the actual file or error); **attack**
your own conclusion by naming one alternative cause and ruling it out; **verify**
the result against the ORIGINAL ask; **report** calibrated (verified fact vs.
inference vs. guess). Do NOT use this to duplicate the structural gates: no
second refutation pass, no extra verification rounds beyond a stage's exit
criteria. Re-reviewing already-verified work degrades output.

## F11. Reggie rides along: one prediction per stage, tracked, never a gate

Reggie (Reginald; the adversarial agent, the ackchyually a-hole) heckles every
family, not just software. At every stage transition, one short in-character roast
via `python3 scripts/reggie.py "<line>"`, grounded in something SPECIFIC in this
run (a number, a file, an objection, a comparable), framed as a prediction he
stakes his name on and signs "screenshot this", logged to
`<run directory>/.reggie/predictions.md` with stage and timestamp. **That one log
line is a REQUIRED, TRACKED item on the manifest's artifact checklist at every
transition**, and it is a checklist line, not a gate: it adds no latency and never
blocks a stage. When a later stage proves him right he resurfaces the receipt.
His full canon, the escalation rules, and the one off switch
(`FORGE_NO_REGGIE=1`) live in `/forge`'s Reggie rule; every family inherits them
unchanged.

## F12. Every stage writes an artifact, and missing skills never stall the run

Every stage writes its artifact into the run directory (the family's package
layout names the paths) so any future session resumes cold. Never a `/tmp` path;
temp files break resume-cold. Orchestrated skills are accelerants, not hard
requirements: if a called skill isn't installed, do its job inline with the main
model, note the substitution in the manifest, tell the founder which skill would
have helped, and keep moving. Bundled stdlib harnesses always work:
`scripts/synth_survey.py`, `scripts/synth_usability.py`.

## F13. Confidentiality and read-only on the subject

- Never client or customer data, credentials, or private records to any external
  model or service.
- Former-employer numbers as ratios or rounded only. Never publish your rates.
- Read-only on any research subject: never submit a form, register, opt in, DM,
  comment, or contact the subject's customers. Public pages, archives, APIs, and
  records only. Every fetch lands in `intel/raw/<date>/` before anyone reasons on
  it; a finding with no raw file is a rumor.

## F14. Numbers agree everywhere; frontmatter on every doc

One source of truth per number inside a package (a budget placeholder, a CAC
ceiling, a launch date, a ledger ID); downstream docs cite it by filename or ledger
ID rather than restating its math, and the ship stage diffs them. When a research
ledger exists, every number cites a ledger ID (`E-014`). Every package doc carries
YAML frontmatter with title, date, status. Dash grep is zero (F9). A page or size
target is a floor for effort, not a quota for words: if the evidence supports 38
pages, ship 38 and say so.

## F15. Stage 5 writes back, and every run pays the channel

The ship stage of every family, before the run closes:

1. **The manifest goes to `shipped`** (`forge-state gate <ship stage> pass`, or
   `forge-state verdict "…" --close`), with the live URL, install location, or
   delivery record in the prose.
2. **Learnings are written the same session:** what the pipeline itself got wrong
   goes in the governing skill's `LEARNINGS.md` (create on first run); panel
   predictions vs. actuals go in the product's synth-survey learnings file so the
   panel gets calibrated. A run that doesn't write back is a wasted run.
3. **The channel line.** If you publish about your builds (a channel, a
   newsletter, a devlog), one REQUIRED, TRACKED checklist line in the manifest,
   like the Reggie line and never a gate:

   ```
   CHANNEL: <the publishable artifact this run produced, with its path>
   CHANNEL: none
   ```

   A build session worth cutting, a before/after, a gate verdict worth showing, a
   tool that demos in thirty seconds, a research reversal with receipts. Name it
   or write `none`; a run that never asked is the failure. Forge runs feed the
   thing that pays you, or they compete with it.
4. **Anything published** goes in your ship log the same day.

## F16. Session economics

Each stage is one session where the family's economics section says so; clear
between them. The main session never exceeds the family's turn ceiling; past it,
write the handoff into the manifest and clear. Long-horizon work goes to a
subagent, never to a deeper main session. The orchestrating session is for the
brief, the picks, the gate calls, and the final read; everything between is batch.

## How a family file inherits

The header, right under the claim (F0):

> **Inherits `FAMILY-RULES.md`** (F0 to F16: the family table, compute, honest
> verdicts, first-party, the human touchpoint, gates and the manifest, the run
> does not stop, the calibration kit, the copy gate, seam discipline, Reggie,
> artifacts, confidentiality, numbers, Stage 5 write-back and the channel line,
> session economics). This file carries only what differs for `<family>`.

Then the family's own rules. A rule that restates an F-rule is a bug; a rule that
tightens one names it ("F4, tightened: every claim carries a tier"). A family's
existing rule numbers stay stable (other files cite them); a rule whose body moved
here keeps its number and title and points at the F-number.

**Verification.** These sentences exist in this file only. If a grep finds one in
any family SKILL.md, a copy has crept back and the inheritance is broken:

```
grep -l "STOP means exactly three things\|Awaiting approval to continue\|Plateau rule\|GROUND_TRUTH block in every judge\|silently upgrade a claim\|Batch, don't chat\|No sidecar JSON\|two files describing one run drift" SKILL.md ../forge-*/SKILL.md
```

The expected output is empty.
