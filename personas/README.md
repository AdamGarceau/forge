# Persona library

One sourced synthetic-audience panel per file, kept outside any single run so every
Forge family loads and extends the same people instead of inventing a fresh panel
each time. Default location `~/personas/`; set `PERSONA_LIBRARY` to move it.
`scripts/synth_survey.py --personas <audience>` resolves a bare name to
`<library>/<audience>.md`.

## The rule (FAMILY-RULES F8)

**Load and extend, never rebuild.** A run copies the closest library file into its
run directory, extends it (a new segment carries its own `Sources:` line; a
re-weighting names the evidence it came from), and adds itself to the index at the
run's ship stage. A new audience file is created only when nothing in the library
covers the audience, and it is written into the library, not only into the run.
Extrapolating a persona from a handful of comments is banned; a segment with no
`Sources:` line does not load into a gate.

## File format

Exactly what `parse_personas()` reads, plus one required line per segment.

```
# <Audience> panel

<!-- library: <path>
     library entry: YYYY-MM-DD
     source panel dated: YYYY-MM-DD
     origin: <path(s) the panel was built from>
     provenance: SOURCED | PARTIAL (why)
     weights basis: population share | ICP-priority | veto-shaped | working estimate
     loaded by: <runs> -->

## About this panel
Who this is, the corpora with counts, what the weights mean, how to extend it.
Bias warnings, retirement flags, and variant pointers go here, above the segments.
Sourcing caveats about a real person go here too, never inside that person's
segment (a persona built from "no public source links this person" rows scored a
thesis 4.2 for citing him).

## Segment 1: <Name> (n=<X>, weight=<Y>)
**Profile:** ...
**Psychographics:** ...
**Decision Factors:** ...
**Language Patterns:** ...
**Top Objections:** ...
**Sources:** <corpus, counts, path>
```

Constraints the parser imposes: the only `## ` headers are `## About this panel` and
`## Segment N: ...`; everything after the last segment header belongs to that
segment; `n` sums to 1000 (or 1 per person when the panel is real named people);
weights sum to 1.00. Extra bold fields inside a segment (population share, ground
truth, hunger, trigger quote) are fine and reach the prompt.

## Index

`INDEX.md` in the library lists every file with audience, panel type, segment count,
n, weights basis, sources, source date, provenance, and which runs loaded it, plus
the panels deliberately kept out and why. A file the index does not list does not
exist as far as the families are concerned.

## Two house standards

- **The owner persona rides at its real share.** When the founder is in the market,
  the founder's segment is included at its true small weight and reported as a
  labeled secondary number, never as the market basis.
- **The accessibility gate persona is appended, never weighted in.** A screen-reader
  or low-vision persona joins every usability round on every build at weight 1.0
  standalone, after the automated audit (a text persona cannot detect focus order,
  missing ARIA, contrast, or live regions).

The maintainer's own panel files are private and not in this repo; this README and
the rule are the portable part.
