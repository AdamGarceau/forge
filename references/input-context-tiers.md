# Input context tiers — what determines how well Forge one-shots

The single biggest factor in a clean one-shot is how much authoritative context Claude has to build from. This is the BUILD-side companion to `grounding-data-tiers.md` (which covers the AUDIENCE side). State the tier honestly at Stage 0 so expectations match reality.

## Tier 1 — An authoritative source already exists (best one-shot)
There's a manual, standard, spec, regulation, or reference that defines "correct." You hand it over whole and Claude derives requirements from it.
- Example: Deadreckon — the Army field manual TC 3-25.26 WAS the spec. One photo, and the app had a ground truth to build to and validate against (coordinate math checked against a real map).
- What to do: find and feed the source. Don't paraphrase it; give Claude the actual document.

## Tier 2 — Established domain, public knowledge (good one-shot)
No single manual, but the domain is well-documented on the open web (a common app type, a known workflow, standard best practices). Claude can research it (Forge Stage 1 does this) and build competently.
- Example: a personal compliance tracker in a regulated domain — the rules are public, so Claude researched them and built fast, but it needed usability rounds because the *edge cases* (an anxious first-timer, a screen-reader flow) were not in the public docs.
- What to do: let Stage 1 research fill the gap; expect more usability/field-test iteration than Tier 1.

## Tier 3 — Novel or proprietary, only you know how it works (needs teaching)
The idea is genuinely new, or the "correct" behavior lives only in your head or your private data. You cannot one-shot what there is no information about.
- Two paths out:
  1. **Teach it first.** Write the spec, record how it should work, give examples — turn your tacit knowledge into a document Claude can build from. (This is work, but it's the work only you can do, and it's a one-time cost.)
  2. **Give it a resource nobody else has — this is the MOAT.** Your customer call recordings, your operational data, your domain expertise written down, a proprietary dataset. Fed into Forge, it produces a result competitors literally cannot reproduce, because they don't have the input. The differentiation was never the tool — anyone can run Forge. It's the private context you feed it.

## The honest one-liner
Forge one-shots as well as its inputs allow. Rich authoritative context → clean one-shot. Thin novel context → you teach it first, or you feed it something exclusive. The tool is commodity; the context you bring is the edge.
