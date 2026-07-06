# Quickstart (5 minutes)

Assumes Ollama is installed and `gemma4:12b` is pulled — see [SETUP.md](SETUP.md)
if not.

## 1. Run a synthetic audience survey on the example concept

```bash
cd scripts
python3 synth_survey.py \
  --personas personas.example.md \
  --concept "TaskFlow is a free, offline-first task and habit tracker. No login wall, no forced account creation - open it and start adding tasks immediately. It works fully offline, syncs nothing to the cloud by default, and lets you export or import your data as JSON any time." \
  --concept-label "TaskFlow" \
  --out /tmp/synth-survey-report.md
```

This sends the concept to 3 simulated audience segments (defined in
`personas.example.md`: a busy parent, a solo freelancer, and a screen-reader
user), one at a time, and prints progress as each segment finishes:

```
Parsed 3 segment(s) from personas.example.md. Model: gemma4:12b @ http://localhost:11434

[1/3] Busy Parent Organizer complete - resonance 7.2
[2/3] Solo Freelancer / Side-Hustler complete - resonance 8.8
[3/3] Screen-Reader / Low-Vision User (accessibility) complete - resonance 4.8

Report written to /tmp/synth-survey-report.md
OVERALL_SCORE: 7.2
```

`OVERALL_SCORE` is the population-weighted average across segments (weights
come from the `weight=` value in each segment's header). Open
`/tmp/synth-survey-report.md` for the full per-segment breakdown: first
impressions, objections, what resonates, a call-to-action read, a competitive
comparison, and — the useful part — "what would make this a 10/10" for each
segment.

Notice the low score from the screen-reader segment (~4.8 in a real run):
that's the survey doing its job — a concept that says nothing about
accessibility reads as a red flag to that audience, and the report will spell
out exactly why.

**To test your own concept:** write your own personas file (copy the
example's format — segments with `n=`/`weight=` headers), then either pass
your concept text inline or as `--concept @path/to/concept.md`.

## 2. Run a synthetic usability test on the example UI

```bash
python3 synth_usability.py \
  --personas personas.example.md \
  --ui ui.example.md \
  --tasks tasks.example.md \
  --out /tmp/usability-report.md
```

This walks each of the 3 personas through each of the 4 example tasks (12
walkthroughs total), instructing the model to hunt for failure rather than be
polite. You'll see progress like:

```
[1/12] Busy Parent Organizer     See what's due today          -> yes     conf 8
[2/12] Busy Parent Organizer     Add a repeating task           -> yes     conf 7
...
OVERALL_SCORE: 7.1  |  incomplete task-runs: 2/12
```

Open `/tmp/usability-report.md` for the ranked punch list — every task a
persona couldn't complete (or completed with low confidence), worst first,
with the specific problems that persona hit.

## Next steps

- Swap in your own personas, UI description, and task list to test a real
  concept or interface.
- See [SETUP.md](SETUP.md) for model choices (bigger/smaller than
  `gemma4:12b`) and using a hosted model instead of local.
- Both tools are plain Python + curl — read the source in `scripts/` to see
  exactly what prompt is sent and adapt it if you need a different question
  set.
