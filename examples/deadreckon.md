# Example: DEADRECKON — the build that proved the process

> *"We gave it a TM and had it run the gauntlet. We made a working app by the end of lunch, all from my phone. It works perfectly for the audience."* — Adam, on the build Forge was reverse-engineered from.

**Live:** deadreckon.adamgarceau.com · **What it is:** an offline Army land-navigation web app (based on field manual TC 3-25.26) that turns a photo of a paper topo map into a working navigation instrument — calibrate to the grid, drop your GPS on the photo, measure azimuth and distance, all client-side, no signal required.

## Why it's the canonical Forge run

**1. One authoritative input, handed over whole.**
The founder sent a single photo of the Army manual and said "the works." The manual *was* the spec. When a real source of truth exists, feed it in and let requirements derive from it — don't re-invent them.

**2. It ran the gauntlet (the gates ARE the quality).**
- A synthetic Army review board plus multi-manual research validated the approach *before* any building.
- Five Google-Ventures-style usability sprints with deliberately-flawed personas, plus a designer and a technical writer, drove it from a round-1 low of **4/10 to 9/10** across every reviewer.
- Coordinate math was cross-checked against a real CalTopo paper map — the app independently computed the same grid square.

**3. Built from a phone, over lunch.**
The founder never touched code or a project board. He spoke outcomes ("put in all my coordinates and follow the compass like a GPS"); Claude translated, built, screenshotted, committed, and deployed *per feature*. Speed came from continuous shipping, not corner-cutting.

**4. "Works for the audience" was verified, not asserted.**
Field-tested in the real environment and precise. That final field test (Forge Stage 4) is what turns "should work" into "works."

## The lesson that hardened the pipeline

The build lived in a cloud session and its repository took a 30-minute forensic hunt to locate afterward. That is why Forge Stage 2 and Stage 5 now *mandate* registering the project, pushing to a durable repo, and writing state files — so no future session ever has to reconstruct where a working app came from.

## The behaviors it taught

The eight collaboration patterns that made this build feel effortless to a non-coder are captured in [`references/deadreckon-session-patterns.md`](../references/deadreckon-session-patterns.md) and are read at the top of every Forge build: outcome-language translation, verify→screenshot→commit→deploy per feature, the honest-limit pattern, field-meaning feature descriptions, "ask our audience" mid-build, the standing 9/10 sprint offer, one-exact-action ops asks, and a manual fallback behind every automation.
