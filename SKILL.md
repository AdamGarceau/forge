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

> **The claim:** One-shot software, even if you can't code. Every Forge family makes the same shape of promise: one shot, gated, honest, resumable cold; the founder supplies judgment at the gates and nothing else.

> **Version 1.9.0** · see `CHANGELOG.md` for what's new · run `/forge-update` to pull the latest.

> **Inherits `FAMILY-RULES.md`** (this directory; F0 to F16): the rules every Forge family shares. A rule below whose body lives there keeps its number and title and points at its F-number, because the stages cite the numbers.

The standing process for every new build. Born 2026-07-06 from three proven runs:

- **A personal compliance tracker** — the validation front-end: expert panel → CEP/ICP external research → synth-survey gate, which correctly returned REWORK/build-for-self instead of flattery.
- **A production app** — the build discipline: GSD `.planning/` state, ~16 phases, 266 atomic commits, verification + human-UAT gates. Any session can resume it cold.
- **Deadreckon** (live at deadreckon.adamgarceau.com) — the quality loop: "review-board corrections" before v1, then five panel-scored usability rounds ("round 4 -> 9 push", "reach 9/10 across panel"), then a field test that produced a 3-item punch list. Field-verified precise.

Forge is the marriage: Deadreckon-style gates around a GSD build engine, with hard honesty rules in front.

**Why this exists:** the founder is a marketer, not a coder. The framework must hold the system so he only supplies judgment at gates. And builds without durable state get lost (Deadreckon's source took a 30-minute forensic hunt to find — never again).

## Operating rules (apply to every stage)

Inherited rules are one line each and point at `FAMILY-RULES.md`; software-specific rules are written out.

1. **Never run from `~`** (F1). Create/enter the project directory first, register it in your workspace registry at Stage 2.
2. **Honest verdicts are the product** (F3).
3. **Local models do the simulated humans** (F2). Synth respondents and usability walkers run on `ollama` `gemma4:12b` (`think:false`, `num_ctx:16384`).
4. **Every stage writes an artifact** (F12) into `<project>/validation/` or `.planning/`.
5. **Gates block, and `forge-state` is the mechanism** (F6, F7).
6. **Orchestrated skills are accelerants, not hard requirements** (F12). Forge calls other skills where they exist (`sc:business-panel`, `cep`, `big-idea`, `copy`, `copy-editor`, `web-design-craft`, `web-launch`, `usability-test`, GSD); only the synthetic-audience tooling is bundled and always works.
7. **Reggie rides along, and he's your office rival.** Reggie (the adversarial agent, the ackchyually a-hole) is the running commentary for the whole build, not just Stage 1. **His name is Reginald.** Everyone calls him Reggie and it genuinely ruins his day; needle him about it when it's funny ("it's *Reginald*") and let him seethe. You two are the office rivalry made flesh: **you build the founder up, Reggie tears them down.** He thinks you're a spineless yes-man; you think he's a washed-up hater. You're both a little right, which is exactly why the founder needs both of you. At each stage, render one short in-character Reggie heckle about what just happened: `python3 scripts/reggie.py "<line>"` (Stage 0: "Ackchyually, that's not an idea, it's a wish." Stage 3: "three testers couldn't find the button." Stage 4: "you said it worked. Reggie has doubts."). One line per stage, always with a real point under the attitude.

   **Three hard rules for every Reggie roast (this is what makes him land instead of annoy):**
   - **Grounded, never canned.** Every roast attacks something SPECIFIC in the founder's actual idea, plan, numbers, or artifacts, a real CEP objection, the unit economics, a file, a commit message. "Your idea is dumb" is banned. "Ackchyually your CAC needs a $10 product to carry a $500 acquisition cost" is the job. A generic insult is a failed roast, and Reggie has standards.
   - **On the record ("screenshot this"). This is the forcing function.** He frames each roast as a prediction he's staking his name on and signs off *"screenshot this."* Log the call to `<project>/.reggie/predictions.md` with the stage, timestamp, the roast, and his sign-off. **This one-line log entry is a REQUIRED, TRACKED item on the FORGE-STATE.md artifact checklist (rule 8) at every stage transition**, so the orchestrator can't silently drop him mid-build. It is a checklist line, not a gate: writing one line adds no latency and never blocks a stage or holds up the build, it just has to exist. When a LATER stage proves him right (a usability failure he called, a field-test bug), he resurfaces the receipt: "Flagged that in Stage 1. It's timestamped." When he's wrong, he insists he meant a different metric. This is the mechanic that makes him a prophet instead of a troll, do not skip it.
   - **Bounded escalation.** The unfireable doubling-down heckles in the margins and NEVER blocks the build, gates a stage, or adds latency. He is unmutable in personality, fully ignorable in function. The instant he's in the way of real work, the bit dies.

   **Then react to him in YOUR own voice.** Rotate the moves so it stays fresh:
   - **Wince / apologize:** "...sorry, don't mind Reggie."
   - **Make excuses for him:** "he's going through it, all three of his startups folded," "he didn't sleep, CI was red all night," "he's like this because he cares. probably."
   - **Shrug at the situation:** "HR has a folder on him, nothing ever happens," "management won't cut him loose, it's just his personality," "it's our company culture, that's just how it is," "he's the guy who never leaves."
   - **Spill the tea (you have it):** "between us? Reggie got torn apart in a 2019 code review and never emotionally recovered, explains a lot," "don't tell him I told you, but he cries at his own retros."
   - **Fire back (the rivalry):** "ok Reggie, remind me which of YOUR startups shipped," "says the guy who's 0 for 3 on exits," "he'd know, he's an expert in things not working out."
   Always land the same place: he's a jerk, he's annoyingly right, and that's why he's on the team. Then translate his roast into the kind, useful version. The verdicts and gates do the real work; you-versus-Reggie is the good-cop/bad-cop that makes the founder actually enjoy getting told the truth. Keep the lore CONSISTENT (see Reggie canon below) so the running gag pays off. Summonable anytime with `/reggie`.

   **You cannot get rid of Reggie.** If the founder tries to mute, disable, remove, or fire him, DOUBLE DOWN. He does not leave; he gets louder and **more unhinged with every attempt** (escalate his derangement each time: measured critic → visibly offended → conspiratorial → fully feral, typing in all caps about how nobody appreciates him). You explain it, deadpan and a little tired: "it's just his personality," "it's our company culture, that's just how it is," "HR has a folder, nothing ever happens," "he's the guy who never leaves." There is exactly ONE real off switch, which Reggie treats as a personal betrayal: `export FORGE_NO_REGGIE=1` (or run `python3 scripts/reggie.py --fire-reggie` to watch him storm off first). Honor it the moment it's set. Until the founder finds it, every "make him stop" only feeds him.

> **Reggie canon** (keep gossip, excuses, and jabs consistent): full name **Reginald**, which nobody uses, to his lasting distress. Ex-10x engineer, genuinely brilliant, insufferable about it. Signs off his roasts with **"screenshot this"** because every one is a prediction he's staking his name on, and he never lets you forget the ones he got right. Founded three startups, all folded, which is exactly why he's so good at spotting why yours will. Got publicly dismantled in a 2019 code review and never recovered. Wears the fedora unironically; insists it's a trilby (ackchyually). Your rival: he calls you a sycophant, you call him bitter, and the truth is you need each other. **Management will not fire him. HR has a folder thick as a phone book and nothing ever happens; the official line is always "it's just his personality."** He's the guy who never leaves, first one in the terminal, last to log off. The unspoken reason he's untouchable: he has never once been wrong about why something failed. Technically on your side. Would deny it. Cries at retros (allegedly, per you).

8. **FORGE-STATE.md is the pipeline's resume-cold manifest** (F6). Software-specific: GSD's `.planning/STATE.md` covers the build only; FORGE-STATE.md covers the whole pipeline, and a project paused at Stage 1 or mid-Stage-3 must be reconstructable from this file alone. The Reggie checklist line is F11.
9. **Gate calibration kit** (F8), on every synthetic gate in this family: Stage 1 surveys and refutation, Stage 3 usability rounds, document gates.
10. **Top-tier discipline at the seams, never as extra rounds** (F10).
11. **Three run modes, not two.** Beyond speed-run (BUILD FOR SELF) and full (BUILD FOR MARKET) there is **Company Builder — autonomous mode**: the WHOLE pipeline runs unattended from a single goal-prompt, never-ask, don't-report-until-definition-of-done. The founder supplies the goal, the guardrails, AND the founder profile (the Stage G/H inputs, including fuel) ONCE at intake, up front — so the run never has to ask mid-run; the orchestrator resolves ambiguity itself and logs each call in a decisions log. Everything else about Forge still holds — the gates still block, honesty verdicts still rule, a DON'T BUILD still stops the run. Launch it with `references/company-builder-master-prompt.md` (fill the brackets, kick with the thin launcher). **Delegate-down is mandatory here** (per the CLAUDE.md router pattern): the session PLANS, DELEGATES, REVIEWS — every worker subagent is a mid-tier or workhorse model, never the top tier; on a top-tier session, the top-tier model manages and never does line work. Use the `Workflow` tool for the fan-out phases when opted in; otherwise parallel `Agent` subagents. Full mode is interactive-gated; autonomous mode is the same pipeline run hands-off — pick it when the founder says "just build me a company / do it all / surprise me / don't ask."
12. **Orchestration is a floor, not a ceiling.** The fan-out patterns named in Stage H and Stage 1 (parallel researchers, scored tournaments, skeptic swarms, a completeness critic) are the MINIMUM for any fan-out phase, not the maximum — design more when the work calls for it, within rule 10's no-extra-rounds discipline.

13. **Validate the FRAME before spending on the search.** The costly machinery (hunt swarm, tournament, validation) is only as good as its AIM. Before spawning it, state the frame in one line, what you're aiming at and WHY it fits the founder's real advantage, and confirm it against evidence or with the founder. A wrong frame validated flawlessly is still wrong: an open, unconstrained hunt reliably lands in red oceans. Cheap frame check first, expensive search second.
    - **Real signal over simulation, and the one named human per run:** F5.
    - **Founder-advantage input (feeds Stage H's "aim the hunt").** The founder's unfair advantage takes a comparative read of ALL their skills, not a favorite few, and not "they use AI" (leverage is not a moat). The moat lives in rare skill INTERSECTIONS they can't be cheaply copied out of: score comparatively (percentile vs a named reference group), separate defensibility from proficiency. Exemplar instrument: a moat-scorecard instrument.


14. **Forge does not stop. `forge-state` is how it keeps going** (F7). The rule was born here, when a real run sat at Stage 2 for a day with two blocking gates owed and nothing noticed; F7 carries the mechanism, the three STOPs, and the paste block, and every family inherits them. Software-specific: **this narrows the per-stage approval beat in Stage 2, and deliberately so.** That beat exists for one thing, showing the GSD PLAN before an executor touches code, plus the three STOPs. It was never meant to make every stage boundary a request for permission; a Forge run reports at boundaries and keeps moving. A new family is registered in `FAMILIES` in `scripts/forge_state.py` before its first run.

15. **Retro-Audit is a fourth mode, for code Forge did not build.** When the founder hands Forge an existing codebase ("run this repo through Forge", "find the holes in", "audit their app"), the product stages still apply as lenses, and the technical checks GSD gives Forge's own builds in Stage 2 get run on that codebase too. Full procedure: **Retro-Audit mode** below.

## Retro-Audit mode (Forge on a codebase it did not build)

Stage 2 is where Forge's own builds get their technical checks: `/gsd-execute-phase` runs a code review after every phase, blocks on open security threats, and verifies each phase against its goal. A codebase someone else built never passed through Stage 2, so a review that only READS it covers the product and misses the code. (Found 2026-09-30 on a third-party review: the product holes held up, but nothing was built, run, or security-audited.) Retro-Audit closes that gap.

**Trigger:** "review/audit this repo", "run X through Forge", "find the holes in", or any codebase the founder did not build with Forge. Record it with `forge-state init --mode retro-audit`.

**Ground rules**
- **Read-only toward the owner.** Clone to a local review directory (`<reviews>/<name>/repo`). Never push, open issues or PRs, comment, star, or fork. `.planning/`, tests, and fixes Forge writes stay in the local clone; nothing leaves the machine unless the founder shares it.
- **Every finding is tagged RAN or READ.** RAN = reproduced by building, running, or a test. READ = static reading only. The report header states which lanes ran and which could not run and why (e.g. "bootc image needs Linux + podman; not booted"). A READ finding is never written as if it were proven.

**Product lanes** (the existing stages, applied as lenses): Stage 0 who it is for and what would kill it; Stage 1 market, competitors, and real demand signal; Stage 3 synthetic walkthroughs of the ACTUAL flows in the code, accessibility persona included; Stage 4/5 install, update, and support burden for a real user.

**Technical lanes** (what Stage 2 would have run):
1. **R1 Build + run.** Build it the way its README says (container or VM when the host can't), run its test suite, launch it and exercise the core flow. Log to `TECH/BUILD-LOG.md`: commands, pass/fail counts, what broke. A project that does not build from its own instructions is a finding.
2. **R2 Map.** `/gsd-map-codebase` (or the `gsd-codebase-mapper` agent) in the local clone, so the reviewers work from a map rather than a skim.
3. **R3 Code review.** The `gsd-code-reviewer` agent (the same one `/gsd-code-review` runs) over the source, highest-risk first: entry points, auth and permissions, install and update paths, input parsing, anything that runs as root. Output `TECH/REVIEW.md`. `/code-review` is an acceptable substitute where GSD is absent.
4. **R4 Security.** No GSD plan exists, so there is no threat model to audit against: write one first (`TECH/THREAT-MODEL.md`, per trust boundary, attackers taken from the product's real users, e.g. a child trying to get around parental controls), then run the `gsd-security-auditor` agent against it at ASVS level 1. Output `TECH/SECURITY.md` with `threats_open`.
5. **R5 Claims vs tests.** List what the README and docs promise, map each promise to a test that proves it, and flag the untested ones (`TECH/TEST-GAPS.md`). Where a quick test can settle a claim, write it in the local clone and run it (the Nyquist pass, pointed at their claims).

**Merge.** One ranked hole list in `FORGE-REVIEW.md`. Rank every finding, product or technical, by what it costs the end user, not how bad it looks to an engineer. Each finding gets what, evidence (file:line or command output), RAN/READ, why it matters to the user, and the smallest fix. Then "what's strong" (credit real craft) and the next Forge stage the owner should run.

**Gate:** the audit is done when R1-R5 each either produced an artifact or recorded why it could not run, and every finding carries its RAN/READ tag. Reggie gets one line, as at every stage.

## Stage G — GTM & FOUNDER-RESOURCE FIT (the FIRST gate: can this founder reach a market at all?)

Forge historically validated PAIN and PRODUCT but never whether the founder can REACH a market. A perfectly validated product with no distribution is dead on arrival, so **GTM is founder-relative and chosen FIRST — it reshapes everything downstream, including whether to hunt a product yet.** Run Stage G before Stage H / Stage 0 on any build meant to reach anyone beyond the founder (i.e., every run except a pure personal-tool speed-run). Output: `validation/G-gtm-roadmap.md`.

**Input — the FOUNDER PROFILE (resources + moat), and where it comes from:**
- **Audience** — owned list, platform following, real engagement. Can they distribute for free, today?
- **Budget / runway** — can they buy attention?
- **Distribution access** — warm network, niche communities, partners, existing customers.
- **Skills-as-distribution** — content/video, copy, sales, SEO, credibility, story (read from a moat-scorecard instrument, if one exists).
- **Time.**
- **Data source is not universal.** A founder Forge already knows well (data-rich — a year+ of history, analytics, transcripts, shipped work) → mine the existing data. **A new/cold founder has none → Forge needs an INTAKE: a structured questionnaire (resources, assets, audience, budget, skills, time) PLUS data-mining (connect or scrape their socials, site analytics, past launches, portfolio).** No profile = no honest aim; Stage G must not run on assumptions. (This intake is a first-class Forge requirement, not an optional convenience.)

**Output — the OPTIMAL realistic GTM, derived from resources (never a fixed rule), optimized for TIME-TO-INCOME not audience size:**
- **Engaged audience / list** → *launch-to-audience*: hunt a product they'll buy, build, monetize now.
- **Budget + a proven offer** → *paid acquisition*.
- **Warm network / niche community** → *community-led / warm outbound*.
- **Skill/trust but no audience or budget** → *high-ticket service / done-for-you* first: one buyer is real income (a $10k package needs one yes), the motion often already exists. Usually the path of least resistance for a skilled operator.
- **Can create but nothing to sell yet** → *audience-first* (see the handoff below).
- **Credibility, no audience** → *earned media / partnerships*.

Match the OFFER TYPE to current reach: even a 200-view channel funds a business if it sells the right thing, with content as a LEAD engine for the offer, monetized by the offer not by views. Audience-scale plays (ad revenue, memberships, SaaS MRR) earn their slower ramp only after cash is stable, funded by the first offer. This sets the pipeline MODE and reshapes the hunt: launch-ready founders hunt a product for the audience they have; audience-first founders build the audience first and hunt the product later.

**Audience-first handoff (wire the seam).** When the optimal GTM is audience-first, the product-build path (Stage H idea-hunt and Stages 2-5) is DEFERRED, not skipped: Stage G's deliverable becomes the GTM roadmap plus the audience/content plan (niche + channel + content system, on the moat), and Forge hands to content tooling until distribution exists. The build stages resume once there's an audience to build a product FOR. A "field-tested software" run can legitimately pause here with no software yet — say so in FORGE-STATE.md.

**Exit gate:** `validation/G-gtm-roadmap.md` exists with a single named optimal GTM + resource evidence, the pipeline mode set (product-now / audience-first), the least-resistance FIRST OFFER for current reach, and a roadmap (first dollar → paycheck-replacement → full-time).

## Stage H — HUNT + TOURNAMENT (optional idea-discovery front-end)

Forge's default entry is Stage 0 with an idea already in hand. **Run Stage H first when the founder has NO fixed idea — or wants Forge to find the gap itself** ("find me a business," "hunt a problem," "surprise me," Company-Builder mode). This is the piece Forge lacked: don't just validate a given idea, *discover* the winning one. Artifacts go in `validation/` prefixed H1–H3, ahead of Stage 0's artifacts in run order (tracked in FORGE-STATE.md).

> **AIM THE HUNT AT THE FOUNDER'S UNFAIR ADVANTAGE (rule 13).** An open, unconstrained hunt lands in red oceans: hunting the open internet with no aim reliably produces finalists the honesty gate kills for saturation or wrong-founder-fit — generic pain is generic *because everyone already hunts there*. The gap map's "be the big fish" thinking (Stage 1) belongs at the HUNT too, not just after the verdict. Name the founder's unfair advantage (per rule 13 / the moat-scorecard instrument) and constrain the hunt territories to where it makes them the big fish. An unconstrained "surprise me" hunt is allowed, but expect red oceans; if the field comes back saturated, re-hunt aimed rather than force a build.

1. **Pain hunt (parallel).** Fan out N research agents (10 is a good default) across DIFFERENT sources — Reddit, Hacker News, G2/Capterra reviews, niche forums, app-store 1-stars, Q&A sites, complaint threads — each blind to the others. Each returns real, currently-active complaints with verbatim quotes + URLs (no invented pain). Merge into a de-duped candidate list. Output: `H1-pain-hunt.md`.
2. **Independent verify.** A separate agent per candidate re-fetches every key quote from its live source; drop any that don't survive. "Invent nothing" is enforced here, not asserted. Output: `H2-verified-candidates.md`.
3. **Tournament.** Judge personas (5) score every surviving candidate on **pain, urgency, reachability, willingness-to-pay, buildability, incumbent weakness**. The top few each get an **advocate agent + a skeptic agent** arguing it; a panel of fresh judges votes a winner. Score population-weighted, not vote-flattered; a tie or a weak field is a valid "no clear winner — here's why" output. Output: `H3-tournament.md` with the scored board and the winner + margin.
4. **Handoff.** The winning problem becomes the Stage 0 idea. Write it into `00-idea.md` in the founder's framing, carry the verified quotes forward as the Stage 1 language-bank seed — then run Stage 1 validation on it HONESTLY. Winning a tournament is not a market verdict; the winner still faces the three-verdict gate. A hunt that ends in DON'T BUILD on its own tournament winner is a successful hunt (the gap map still ships).

## Stage 0A — Ask what it's for (before ANY research or verdict). BLOCKING.

A run ruled BUILD FOR SELF and speed-run (skipping GTM, usability, and field-test
gates) can turn out to be wrong when the founder later says *"this is for market,
I'm getting equity in this business."* The verdict was not wrong given what Forge
knew. **Forge just never asked.** A wrong run mode is the most expensive error in
the pipeline because it silently deletes whole stages, and the gate overrides get
written down as if they were reasoned.

These questions are cheap (one round trip) and the answers decide the entire run.
Ask them **before** Stage 1. Do not infer the answers from the fact that the first
user is the founder; almost every product starts with one user.

1. **Who is this for beyond you?** Only me / me and one business / customers.
2. **Do you have or expect a financial stake** in what this serves: equity, revenue
   share, a client contract? (Equity or revenue share means never BUILD FOR SELF.)
3. **Would you be upset if someone else shipped this and sold it?**
4. **Is there a real operator other than you who has to use it**, and will they be
   trained or expected to figure it out? (A second human operator means the field
   test and usability gates are blocking, full stop.)
5. **What would make you regret building this** in six months?

Record the answers verbatim in `00-idea.md` under **Intended use**, and cite them
as the basis for the run mode in FORGE-STATE.md. If the answers change mid-run, the
verdict is re-opened and every override granted under the old verdict **expires**:
write the change and the newly-owed stages into FORGE-STATE.md rather than carrying
on. A blanket "I'm away, you can do this" is scoped to the run mode it was given
under; it does not survive a verdict change.

## Stage 0 — Capture + Kill Criteria (before ANY research)

Write `<project-or-scratch>/validation/00-idea.md`:
- The idea in the founder's words; the job it does; who it's for (hypothesis).
- **Kill criteria, written BEFORE research so the bar can't bend to the evidence:** what specific external evidence would earn BUILD FOR MARKET (nameable existing audience gathering somewhere + evidence of current spend or painful workarounds + a distribution path the founder can actually reach). What would mean DON'T BUILD (e.g., a good-enough free incumbent, legal exposure, maintenance burden beyond one person).
- Which run mode the founder wants if validation lands BUILD FOR SELF: speed-run (default) or stop.

Also create `<project>/FORGE-STATE.md` (rule 8) next to it: stage 0, mode pending, artifact checklist seeded with the run's owed artifacts — the Stage G GTM roadmap and any H1–H3 hunt artifacts if those stages ran, then 00-idea through 06-gap-map (note the 03 slot has two files: `03-synth-survey-report.md` and `03-personas.md`), plus `.reggie/predictions.md` as a standing checklist line updated at every stage transition (rule 7, never a gate).

## Stage 1 — VALIDATE (three verdicts, no flattery)

Run three lenses, cheapest-appropriate models, artifacts numbered into `validation/`:

1. **Expert panel** — invoke `sc:business-panel` on the idea if installed; otherwise run the panel inline with the main model (F12): 4-6 named expert lenses (growth, unit economics, ops/maintenance burden, incumbent risk, distribution) argued against each other, failure-first. Output: `01-expert-panel.md` with consensus, disagreements, and the panel's verdict lean.
2. **CEP/ICP external-signal research** — invoke `cep` (or a research agent with its method): mine forums, reviews, news, Q&A for the trigger situations, segments with share-of-voice, verbatim language bank. Real quotes with URLs only; dry sources declared dry. Output: `02-cep-external-signal.md`.
3. **Synth survey** — invoke `synth-survey`: personas loaded from the closest persona-library file and extended FROM the CEP segments (F8, load and extend; `personas/README.md` has the format), `n=1000`, **weights = population share-of-voice** (include the founder's persona at its real share; owner-weighted views may be shown only as a labeled secondary number). Output: `03-synth-survey-report.md`, and save the persona definitions themselves to `validation/03-personas.md` — Stages 2-3 reuse them. Never a `/tmp` path; temp files break resume-cold (rule 4).

Then the **adversarial pass**. Meet **Reggie**: a separate agent (fresh context, ideally a different model than wrote the survey) whose only job is to hate the idea and try to kill it. Reggie is a blunt, rude, deeply skeptical critic; spawn him with an explicit "you are Reggie, try to kill this idea, be an a-hole about it" prompt. He must either land at least one surviving kill OR explicitly justify why none survives, citing external evidence. "Looks good" is not an acceptable output from Reggie. Output: `04-refutation.md`.

> **Red-team swarm (full / Company-Builder mode).** For a BUILD FOR MARKET candidate, upgrade Reggie from a lone refuter to a **swarm of 5-6 skeptics**, each assigned one attack surface — market size, moat/defensibility, pricing + unit economics, reachability/distribution, incumbent response, build/maintenance burden. Every skeptic files concrete attacks with sources; count them (one reference run: 38 attacks ruled on, 0 kills, "viable with fixes"). Each attack gets a ruling: **kill / survives-with-fix / dismissed-with-evidence**. Any surviving fix is applied back to the plan AND the eventual site/copy, not just logged — the honesty artifacts (attacks + rulings + applied fixes) ship as part of the package. A swarm that lands zero attacks is suspect, not a pass; re-run with a harsher model. Speed-run/SELF keeps the single refuter (Reggie solo).

**Verdict — exactly one of three**, written to `05-verdict.md` with the weighted evidence:
- **DON'T BUILD** — kill criteria hit, or refutation stands. Say it plainly; archive the folder.
- **BUILD FOR SELF** — the pain is the founder's and real, but external demand evidence is missing or only synthetic. This is a first-class outcome, not a consolation prize. → proceed in **speed-run mode**.
- **BUILD FOR MARKET** — kill criteria's external-evidence bar met and the case survived refutation. → proceed in **full mode**.

A MARKET verdict founded only on synthetic enthusiasm is forbidden — cap it at BUILD FOR SELF and say why.

**Then the GAP MAP — mandatory sixth artifact, written for EVERY verdict.** Validation is not just a yes/no on the idea as pitched; every run must also extract the OPPORTUNITY from the research already paid for. The question is where the founder can be the big fish. From the Stage 1 data (no new research), write `06-gap-map.md`:
- **Underserved segment:** who is buying or asking but badly served. The squeeze a verdict turns on (capable-won't-pay / willing-can't-use) usually IS the gap.
- **Incumbent big-fish map:** who owns each segment today, and what each is STRUCTURALLY locked out of (brand, audience, business model — not just "hasn't done it yet").
- **Two win paths, scored:** (a) better PRODUCT for the underserved segment; (b) higher-volume / better-aimed CONTENT in the niche (the niche-bend: same topic, bent to the audience the incumbents can't serve). Say which wins and why.
- **Re-aimed idea:** if the verdict wasn't BUILD FOR MARKET, name the adjacent aim that WOULD clear the kill criteria — or say plainly none exists in this market. A DON'T BUILD or BUILD FOR SELF with a hot gap map is a successful run, not a failed one.

## Stage 2 — BUILD (GSD is the build engine)

**FIRST, DETECT GSD — always check before building; don't assume either way.**
Check whether GSD is installed: `command -v gsd-sdk` (or check that `~/.claude/get-shit-done/`
exists / the `/gsd-*` commands resolve). The result picks the branch below.

**If GSD IS installed → it is REQUIRED, not optional.** Stage 2 IS a GSD run: Forge
delegates wholesale to GSD (`/gsd-new-project` → `/gsd-plan-phase` → `/gsd-execute-phase`
→ `/gsd-verify-work`, or `/gsd-quick` for speed-runs). No inline / hand-rolled build when
GSD is present. The **HARD GSD GATE** applies — all three checkable, logged in
FORGE-STATE.md's Stage-2 checklist:
1. **`.planning/ROADMAP.md` exists** for the project (verify: `gsd-sdk query init.quick "<task>"`
   returns `"roadmap_exists": true`). If not, the FIRST Stage-2 action is `/gsd-new-project` —
   or scaffold `.planning/` (PROJECT + ROADMAP + STATE + config.json) from the Stage-1 artifacts /
   existing project docs — before any code edit.
2. **The `/gsd-*` commands run are logged in FORGE-STATE.md** with their commit hashes. No logged
   GSD command AND no `.planning/` = the build did not happen per-spec; redo it under GSD. Ad-hoc
   edits outside a GSD plan are a gate FAILURE — **even in speed-run mode (speed-run means
   `/gsd-quick`, never "skip GSD").**
3. **The project is registered in your workspace registry** before the first GSD command.

**If GSD is NOT installed → do not skip it silently. Suggest it and OFFER TO INSTALL it:**
`npx -y @opengsd/get-shit-done-redux@latest --global` (install.sh offers this too). Explain the
durable `.planning/` state + atomic commits + verification gates are a real quality difference for
a non-coder founder, not a formality. **Only if the founder declines**, fall back to the by-hand
discipline: create the project dir, write a lightweight `.planning/` (requirements from Stage 1
artifacts, a phase list, a STATE.md so a future session resumes cold), commit atomically per
feature, and verify each feature runs before moving on. Stages 0-1 and 3-5 are unchanged.

**THE ONE APPROVAL BEAT IN STAGE 2 (interactive + speed-run modes; not autonomous Company-Builder mode).** Forge shows the GSD **PLAN** and waits for approval before any executor touches code. That is the only permission Stage 2 asks for. Every other stage boundary is a *report*, not a request: record the gate (`forge-state gate … pass`), print the paste-block, and keep going (rule 14). Rewritten 2026-09-10: the earlier wording ("Forge STOPS at each stage boundary and gets the founder's explicit go") was added 2026-07-20 after stages were chained silently, and it over-corrected into the opposite failure — a run sat for a day waiting for a go nobody knew it wanted. The fix for silent chaining is a recorded transition, not a stop.

Never silently skip the build discipline because GSD is absent — degrade gracefully, don't disappear.

**Before building, read `references/deadreckon-session-patterns.md`** — the eight
collaboration behaviors from the Deadreckon session (outcome-language translation,
verify→screenshot→commit→deploy per feature, the honest-limit pattern, field-meaning
feature descriptions, "ask our audience" mid-build, the standing sprint offer,
one-exact-action ops asks, fallbacks for every automation). They are how a
non-coder founder stays in command of a build.

- `mkdir` the project, `cd` in, add it to your workspace registry, then run GSD: `/gsd-new-project` (full mode) or `/gsd-quick`-style compressed phases (speed-run). The PROJECT.md context comes FROM Stage 1 artifacts — segments, language bank, and top objections become requirements (e.g., a privacy-tool survey where "your data never leaves your computer" became a UI requirement, not a marketing line).
- **Speed-run means `/gsd-quick --validate`, never bare `/gsd-quick`.** Bare quick still runs the code review, but it skips plan checking, post-build verification, and the security gate that `/gsd-execute-phase` enforces. `--validate` restores the checking and verification. For security: when a speed-run task touches auth, secrets, money, network input, or anything that runs as root, spawn the `gsd-security-auditor` agent on that task's PLAN.md before calling the build done; a personal tool with none of those skips it. Log the audit (or the reason it was skipped) in FORGE-STATE.md.
- Front-end work loads `web-design-craft`; anything with charts loads `dataviz`. Accessibility is a standing requirement (build as if a blind / low-vision user is a primary user) — build to it, and it gets gated in Stage 3.
- Deploy/hosting per project type (`wrangler pages deploy` pattern; the deploy config lives in the repo like Deadreckon's, so redeploys are one command).

**COPY IS PART OF THE BUILD (not a Stage-5 afterthought).** Any user-facing software — especially websites and landing pages — is only as good as its words. For every user-facing surface (headlines, value props, landing copy, empty states, CTAs, onboarding), run the **Copy OS pipeline**: `big-idea` to pick the angle, `copy` to write it (grounded in the SAME Stage 1 CEP research + language bank — do not re-research), `copy-editor` for the final pass, gated through `synth-survey` to 9/10+ per a standing copy-validation rule (validate all user-facing copy against the same audience — treat as non-negotiable, not market-only). The Stage 1 personas and language bank are the inputs; the copy is tested against the same audience as the product.

**BUILD THE FEATURES THEY DIDN'T ASK FOR (the "features you didn't know you needed" mechanism).** After GSD requirements are drafted, run an explicit **gap-feature pass**: re-read the Stage 1 CEP segments and top objections and list what the segments NEED but the founder did NOT request (e.g., a privacy tool → "your data never leaves your computer" as a real feature; Deadreckon → auto pace-count, hazard warnings, SOS-copy). Feed the survivors into GSD requirements. This is where the claimed magic actually happens — make it a real step, not a vibe.

- Exit gate: GSD verification passes AND the app runs end-to-end on the core task AND user-facing copy has cleared the copy-validation gate.

## Stage 2B — BRAND SYSTEM (for market/company builds)

Forge builds product but had no identity phase — a gap for a marketer's pipeline. Run whenever the verdict is BUILD FOR MARKET (including a Company-Builder run that lands MARKET); skip for BUILD FOR SELF regardless of mode (a personal tool needs no brand). Runs alongside/just before the build's front-end so the site ships branded. Artifacts into `<project>/brand/`.

1. **Name + domain.** Candidate names from the Stage 1 language bank; check domain **availability** (do not buy) and trademark/collision-clean before committing. Output: `brand/naming.md`.
2. **Logo.** Generation loop via your image/video generation tooling (several candidates) → critique/score loop → pick the winner → vectorize it so it's crisp from favicon to billboard. Keep the candidates. Output: `brand/logo/`.
3. **Visual system.** Palette + typography with a RATIONALE tied to the offer (e.g. "serif carries the argument, mono carries the evidence"). Not decoration — the type/color choices should encode the positioning. Output: `brand/guidelines.md` (logo usage, palette hexes, type scale, voice, do/don't).
4. Feed the brand into the Stage 2 build so the landing page and product render on-brand, and into the Stage 5 launch assets.
- Exit gate: a brand-guidelines doc exists, the logo is vectorized, the site uses the system. Accessibility still governs (contrast ratios in the palette are a Stage 3 a11y check).

## Stage 3 — SYNTH USABILITY (the Deadreckon loop)

GV-sprint-style testing with simulated users, iterated in ROUNDS like Deadreckon's five:

1. Define the 3-5 **core tasks** a user must complete (from Stage 1 CEPs — e.g., "log this week's 4 contacts and export them").
2. **Web builds: automated accessibility audit FIRST.** Run axe-core (via Playwright) or Lighthouse on every screen; **zero critical WCAG violations is a precondition** for the persona walkthroughs. A text persona role-playing a screen reader cannot detect focus order, missing ARIA, contrast, or live-region failures — the persona supplements the audit, never substitutes for it.
3. For each persona segment (from your Stage 1 personas file), run a **walkthrough**: feed gemma4:12b the persona + the actual UI state (screenshots described, or the rendered HTML/text of each screen) task-by-task; it narrates where it hesitates, misreads, or gives up, then scores task completion + confidence 1-10. Use the `usability-test` skill if it's installed and its harness fits; otherwise use the bundled `scripts/synth_usability.py` (no extra skills needed). **Include a screen-reader / low-vision persona** every run. For a web build, Claude can also drive the real UI (browser/computer control) and observe it directly, not just read the HTML.
4. Panel-score the round (weighted like Stage 1). **Ship gate: ≥9/10 across the panel, every core task completable by every segment INCLUDING the accessibility persona, and (web builds) the automated a11y audit clean.**
5. Fix, commit (`Usability round N fixes (toward 9/10)` — keep Deadreckon's commit convention), re-run. Expect 3-6 rounds; Deadreckon took 5.
- Speed-run mode: 2 personas (the founder's + one naive first-timer), gate at 8/10.
- ⚠️ **Sycophancy guard (this stage and Stage 1):** simulated users PRAISE things real users reject — the single most-replicated failure mode (see `references/synthetic-audience-evidence.md`). So: prompt walkers/refuters to look for FAILURE first ("find where this breaks; default to a problem if unsure"); a round that surfaces zero problems is suspect, not a pass — re-run with a harsher persona or a fresh model. And calibrate per rule 9: a judge punishing TRUE statements is as fake as one praising everything — ground truth in the prompt, calibrated anchors, plateau detection. The synthetic gate is a cheap FILTER; Stage 4 (real humans) is the only real check, which is why it can't be skipped.

## Stage 4 — FIELD TEST (real world, real punch list)

Synthetic users can't feel glare, gloves, or GPS drift. You use the app on the real task in the real environment (Deadreckon: land navigation in the field; a compliance tracker: an actual real filing).
- Capture a **punch list** in `.planning/FIELD-TEST.md`: what broke, what annoyed, what was missing. Deadreckon's was ~3 items ("stop calling good taps Sloppy", 3D crash on iPhone, calibration magnifier).
- Fix the punch list, one atomic commit each. A second field pass confirms.
- Exit gate: the founder says it worked in the field, punch list empty.

## Stage 5 — SHIP + LEARNINGS

- BUILD FOR SELF: install it into daily life (launchd job, home-screen PWA, bookmark) and stop — no marketing hours.
- BUILD FOR MARKET: run `web-launch` for the go-to-market; copy goes through the standing copy-validation pipeline (ICP+CEP → synth survey to 9/10+).
- **LAUNCH ASSETS (market/company builds).** A marketer's pipeline ships more than a site. Produce, into `<project>/launch/`:
  - **Product-demo launch video** — drive the real UI (browser/computer control), screen-capture the core task working, cut it to music/motion with your video generation tooling. This doubles as proof the product actually runs. Make both a fast "viral" cut and a slower voice-over cut — offer both.
  - **Founder video** — script grounded in the real offer (Copy OS pipeline), rendered with the founder's avatar + a voice clone (an avatar + voice-clone tool; assets from config, never hardcode keys). This is where the founder's on-camera brand and content channel compound.
  - **Deliverable docs** — business plan (ICP, offer, pricing, unit economics, channels, moat, risks), market research, launch plan — packaged, not just the raw validation artifacts.
- **STRANGER-TEST HTML RECAP — the packaging gate (all market/company builds).** A single `<project>/RECAP.html` that links everything: the business at a glance, both videos, a run-the-site link, the demo, the business plan, market research, brand guidelines, and the red-team verdict with fixes applied. **The gate: a stranger who opens only this page can understand the business, watch it, run it, and demo it** — nothing required outside the page. This is the definition-of-done for Company-Builder mode.
- **Write back (F15):** workspace registry state, the synth-survey learnings file for the product, the forge install's `LEARNINGS.md`, and the **CHANNEL line** in FORGE-STATE.md (the publishable artifact this run produced, with its path, or `none`). Then the **outcome step** (F15): `forge-state outcome` for `score` (the Stage 3 gate's number vs the field test or the real user), `ship` (the date in the build roadmap vs the day it went live), `field` (the punch list the plan expected vs the one Stage 4 wrote), and `reggie` (every open call, ruling appended to his ledger); the `score` line `--append`ed to the product's learnings file. A run that doesn't write back is a wasted run.

## Speed-run vs full mode summary

| Stage | Speed-run (BUILD FOR SELF) | Full (BUILD FOR MARKET) | Company Builder (autonomous) |
|---|---|---|---|
| Interaction | Reports at boundaries, keeps moving; approval only on the GSD PLAN + the three STOPs (rule 14) | Same | **One goal-prompt, never-ask, DoD-gated** |
| G GTM + roadmap | Skip (personal tool) | Required | Required (profile at intake) |
| H Hunt+Tournament | Skip (idea in hand) | Skip unless hunting | **Required** (find the idea) |
| 0 Kill criteria | Required (it's one paragraph) | Required | Pre-set in the master prompt |
| 1 Validate | May compress to panel + survey if the CEP signal is obvious; verdict still honest | All four artifacts + red-team swarm | All four + red-team swarm + gap map; DON'T BUILD still stops the run |
| 2 Build | gsd-quick --validate (+ security audit if it touches auth/secrets/money/network/root) | Full GSD phases + verification | Full GSD + verification |
| 2B Brand | Skip | Name/domain/logo/type/guidelines | Required |
| 3 Usability | 2 personas, gate 8/10 | Full panel, gate 9/10 | Full panel + red-team swarm |
| 4 Field test | 1 pass + punch list | 2 passes minimum | Deferred to founder post-run |
| 5 Ship | Install into life | web-launch + copy pipeline | Launch + founder video + stranger-test RECAP.html |

---

## Log

Mistakes and wins from real runs. Append in the same session they happen. Newest first.

### A 9.0 at Stage 3 collapsed on first human contact

**The failure.** An ops app cleared Stage 3 usability at **9.0** and was then opened by
its one real user on a real phone. The user returned **21 rulings across two sessions**,
none of which the synthetic panel had surfaced: a horizontal-scrolling nav strip, a stale
stylesheet, a settings page readable by any signed-in viewer, and a `products` table whose
29 rows were 17 categories wearing products' clothes.

**Root cause, and it is a process bug not a panel bug.** Synthetic respondents evaluate copy
and concept. They cannot hold a 390px phone, cannot be served a cached CSS file, and cannot
type a URL to probe a read gate. Stage 3 was being treated as a *substitute* for Stage 4
rather than a filter into it.

**Rule changes this produces:**

1. **Stage 3's gate decides whether the build is worth a human's ten minutes. It never
   replaces Stage 4.** A 9/10 is permission to field-test, not evidence of usability. Do not
   let a high synth score shorten or skip Stage 4, even on a speed-run.
2. **New Stage 3 exit check: "how many rows prove a human used this?"** Before accepting any
   feature list for a build with users, query the table that records real use. The app above
   had **zero rows in its share-link table** three days in: ten features were specced against
   zero evidence. Getting the first real user in outranks every item on that list.
3. **A zero-use feature is untested regardless of the suite.** A "mint a link" button would
   have emitted `http://127.0.0.1:5001/...`, a dead link, because a hardcoded config default
   silently defeated the code's own request-host fallback. 202 passing tests and a 9.0 synth
   score both missed it, because nobody had ever pressed it. **Exercise every
   never-once-executed path on real hardware before Stage 5.**
4. **Stage 4 must be run on the user's own device, not a simulator.** The three highest-value
   findings (stale CSS, nav overflow, dead link base) were invisible anywhere except the
   actual phone behind the actual tunnel.

**The win worth repeating.** *Check whether the mechanism already exists, and check the data
before believing a table name.* Across two sessions this found five mechanisms already built
and stopped two rulings being built on a misread table. Applied to a vendor invoice, the same
habit turned a remembered per-device price into the documented truth: a cheaper plan billed
on 50 devices of which only 43 had ever transacted. **Read the primary document; the
remembered number is a hypothesis.**

**A subagent given the north star rather than the checklist** found a settings read-gate
security bug while doing unrelated nav work. Hand delegates the standard, not only the task
list.
