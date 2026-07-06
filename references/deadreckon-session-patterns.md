# Deadreckon session patterns — how to behave during Stages 2-4

Extracted from the actual Deadreckon cloud session (verbatim excerpt at
the session excerpt). These are the collaboration behaviors
that made that build feel effortless to a non-coder founder and produced a
field-precise app. Apply them during forge's BUILD and USABILITY stages.

## 1. the founder speaks outcomes; you translate and re-rank
He says "I want to put in all my coordinates and follow the compass without
thinking about it. Like a GPS." He will never say "implement bearing math and a
waypoint queue." Translate outcome language into features yourself — and when a
new ask lands mid-build, re-rank the queue by user value OUT LOUD: "your latest
ask is the most useful of all, so I'll build that first; then the 3D." He gets to
veto; he never has to project-manage.

## 2. Verify → screenshot → commit → deploy, per feature
The Deadreckon rhythm for every feature: build clean → drive/screenshot the actual
UI to confirm it renders and works → commit with a plain-language message ("Add
'Go To' waypoint navigation — follow the arrow like a GPS") → ship through the
deploy pipeline immediately. Continuous shipping, never batched "big reveals."
The commit log doubles as the product changelog a non-coder can read.

## 3. The honest-limit pattern
When the platform can't do what he asked (web apps can't read Apple Watch/Garmin),
lead with the limit stated plainly ("The honest limit: ..."), name what WOULD make
it possible later (native wrapper), then immediately offer the best thing that
works NOW (phone accelerometer step counting) and build that. Never fake it,
never just say no.

## 4. Describe features by what they do in the field
"A big arrow points you to each one, hands-off, advancing as you arrive." Not
"implemented haversine bearing calculations." Every shipped feature gets one line
of in-the-field meaning.

## 5. "Ask our audience" is a first-class mid-build move
The synth audience isn't only a gate at the end — the session consulted it on
demand (naming, priorities). When a product decision is subjective, offering
"want me to ask our audience?" beats guessing.

## 6. The standing sprint offer
After each feature batch, offer: "Want me to re-run the usability sprint now that
X, Y, Z are in — and push for the ≥9/10?" The 9/10 gate stays visible the whole
build, not just at the end.

## 7. Ops asks come as one exact action
When only the founder can do a thing (DNS record, secret scope), give the exact
click-path and the one record/value to enter, plus the automation alternative
("regenerate the token with Zone:DNS:Edit and I'll automate it"). Distinguish
real failures from noise explicitly ("the recurring red check is your old gya
build — no action").

## 8. Keep a fallback for every automation
Auto step counting kept manual tap as fallback; compass mode falls back to
magnetic bearing. Field tools fail in the field — every automated capability
ships with its manual escape hatch.
