#!/usr/bin/env python3
"""Stage S (SPEC) gate check: is SPEC.md + GLOSSARY.md + SPEC-REVIEW.md complete enough to build from?

`forge-state gate S pass` calls spec_check(); an empty list means the gate may pass.
Run it by hand before the gate:  python3 forge_spec.py <project root> [--mode speed-run|full|autonomous]

Stdlib only, so both copies of the skill (the live one and the product) carry the same file.
The format each file must follow is in the Stage S section of the skill (references/stage-spec.md
in the live copy). Mechanics adapted from Matt Pocock's skills (grilling, domain-modeling, to-spec,
to-tickets, code-review; github.com/mattpocock/skills, MIT).
"""
import os
import re
import sys

SPEC, GLOSSARY, REVIEW = "SPEC.md", "GLOSSARY.md", "SPEC-REVIEW.md"
SESSION_TOKENS = 150_000          # one slice must fit one fresh session
REVIEWERS = {"speed-run": 2, "full": 3, "autonomous": 3}
RULINGS = ("fixed", "dismissed")
OPEN = {"", "?", "tbd", "todo", "open", "pending", "-", "—"}
_SEP = re.compile(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?")


def rd(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def section(text, heading):
    """Body of `## <heading>` (case-insensitive prefix match) up to the next heading of level 1-3."""
    head = re.compile(r"#{1,3}\s*%s" % re.escape(heading), re.I)
    out, found, fenced = [], False, False
    for line in (text or "").splitlines():
        if re.match(r"\s*(```|~~~)", line):
            fenced = not fenced
        elif not fenced and found and re.match(r"#{1,3}\s", line):
            break
        elif not fenced and not found and head.match(line):
            found = True
            continue
        if found:
            out.append(line)
    return "\n".join(out).strip()


def field(text, name):
    m = re.search(r"^\**%s\**[ \t]*:([^\n]*)$" % re.escape(name), text or "", re.M | re.I)
    return m.group(1).strip().strip("*").strip() if m else ""


def _cells(s):
    return [c.strip() for c in s.strip().strip("|").split("|")]


def table(text):
    """(header cells lowercased, rows as dicts keyed by header) for the first markdown table in text."""
    lines = [l.strip() for l in (text or "").splitlines()]
    for i, s in enumerate(lines):
        if s.startswith("|") and i + 1 < len(lines) and _SEP.fullmatch(lines[i + 1]):
            head = [c.lower() for c in _cells(s)]
            rows = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                c = _cells(r)
                if any(x for x in c):
                    rows.append(dict(zip(head, c + [""] * (len(head) - len(c)))))
            return head, rows
    return [], []


def col(head, *names):
    """First header cell that starts with any of names (so `Decided by (who)` matches `decided by`)."""
    for h in head:
        if any(h.startswith(n) for n in names):
            return h
    return None


def bullets(text):
    return [l.strip()[2:].strip() for l in (text or "").splitlines() if re.match(r"^\s*[-*]\s+\S", l)]


def items(text):
    """Bullets and numbered lines."""
    return bullets(text) + [l.strip() for l in (text or "").splitlines() if re.match(r"^\s*\d+[.)]\s+\S", l)]


def words(s):
    return len(re.findall(r"[^\W_]+", s or ""))


def tokens(s):
    """'120K' / '~90k' / '140,000' / '0.1M' -> int, None if unreadable."""
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*([km]?)", (s or "").lower())
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return int(n * {"k": 1_000, "m": 1_000_000}.get(m.group(2), 1))


def _ids(cell):
    return [x for x in re.split(r"[,;\s]+", cell or "") if x]


def check_spec(root):
    text = rd(os.path.join(root, SPEC))
    if text is None:
        return ["%s is missing: grill, then write it at the project root" % SPEC], None
    errs = []

    if words(section(text, "Problem")) < 10:
        errs.append("## Problem is missing or under 10 words: say whose pain, in their words")

    rounds = re.search(r"\d+", field(text, "Grill rounds"))
    if not rounds or int(rounds.group()) < 1:
        errs.append("`Grill rounds:` is missing: the number of frontier rounds asked (1 or more)")
    opened = re.search(r"\d+", field(text, "Open decisions"))
    if not opened:
        errs.append("`Open decisions:` is missing: it must read 0 (the frontier is empty)")
    elif int(opened.group()):
        errs.append("`Open decisions: %s`: the grill is not done until the frontier is empty" % opened.group())

    head, rows = table(section(text, "Decisions"))
    d, a, w = col(head, "decision"), col(head, "answer"), col(head, "decided by", "who")
    if not (d and a and w):
        errs.append("## Decisions needs a table with columns: Decision | Answer | Decided by")
    elif not rows:
        errs.append("## Decisions table has no rows: a spec with no settled decisions was not grilled")
    else:
        for i, r in enumerate(rows, 1):
            if r[a].lower() in OPEN:
                errs.append("## Decisions row %d (%s) has no answer" % (i, r[d][:50]))
            if r[w].lower() in OPEN:
                errs.append("## Decisions row %d (%s) does not say who decided (Adam, founder, orchestrator, or fact: <source>)"
                            % (i, r[d][:50]))

    stories = [s for s in items(section(text, "User stories")) if re.search(r"\bAs an?\b.+\bI\b", s, re.I)]
    if not stories:
        errs.append("## User stories has no story in the form \"As a <who>, I ...\"")

    seams = items(section(text, "Seams"))
    if not seams:
        errs.append("## Seams lists none: name where the tests poke in (ideal is one per feature)")

    if not items(section(text, "Out of scope")):
        errs.append("## Out of scope lists nothing: name at least one thing this build will NOT do")

    head, rows = table(section(text, "Slices"))
    s, t, b, sm = col(head, "slice"), col(head, "est", "tokens"), col(head, "blocked by"), col(head, "seam")
    if not (s and t and b and sm):
        errs.append("## Slices needs a table with columns: Slice | ... | Seam | Est. tokens | Blocked by")
    elif not rows:
        errs.append("## Slices table has no rows: cut the build into vertical slices (DB to button)")
    else:
        ids = [r[s].split()[0].strip("`*") if r[s].split() else "" for r in rows]
        deps = {}
        for i, (sid, r) in enumerate(zip(ids, rows), 1):
            n = tokens(r[t])
            if n is None:
                errs.append("## Slices row %d (%s): `Est. tokens` is unreadable (write e.g. 90K)" % (i, sid))
            elif n > SESSION_TOKENS:
                errs.append("## Slices row %d (%s) is %s tokens: over one fresh session (%dK). Split it"
                            % (i, sid, r[t], SESSION_TOKENS // 1000))
            if r[sm].lower() in OPEN:
                errs.append("## Slices row %d (%s) names no seam: every slice is tested somewhere" % (i, sid))
            blk = [] if r[b].lower() in OPEN | {"none", "nothing", "n/a"} else _ids(r[b])
            for x in blk:
                if x not in ids:
                    errs.append("## Slices row %d (%s) is blocked by %r, which is not a slice in the table" % (i, sid, x))
                elif x == sid:
                    errs.append("## Slices row %d (%s) blocks itself" % (i, sid))
            deps[sid] = [x for x in blk if x in ids and x != sid]
        if _cycle(deps):
            errs.append("## Slices `Blocked by` links form a loop: no slice in the loop can ever start")
    return errs, text


def _cycle(deps):
    seen, stack = set(), set()

    def visit(n):
        if n in stack:
            return True
        if n in seen:
            return False
        seen.add(n)
        stack.add(n)
        hit = any(visit(m) for m in deps.get(n, []))
        stack.discard(n)
        return hit
    return any(visit(n) for n in deps)


def check_glossary(root, spec_text):
    text = rd(os.path.join(root, GLOSSARY))
    if text is None:
        return ["%s is missing: write the terms the grill settled (Term | Meaning | Avoid)" % GLOSSARY]
    head, rows = table(text)
    tm, mn, av = col(head, "term"), col(head, "meaning"), col(head, "avoid")
    if not (tm and mn and av):
        return ["%s needs a table with columns: Term | Meaning | Avoid" % GLOSSARY]
    if not rows:
        return ["%s table has no terms" % GLOSSARY]
    errs = []
    # Headings are the required template ("## User stories"), not the author's words: skip them.
    body = "\n".join(l for l in (spec_text or "").splitlines() if not re.match(r"\s*#", l))
    for r in rows:
        if words(r[mn]) < 3:
            errs.append("%s: %r has no meaning (one plain line)" % (GLOSSARY, r[tm]))
        for bad in [x.strip(" `*\"'") for x in re.split(r"[,;/]", r[av])]:
            if bad and bad.lower() not in OPEN | {"none", "n/a"} and \
                    re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(bad), body, re.I):
                errs.append("%s says avoid %r (use %r), but %s still says it" % (GLOSSARY, bad, r[tm], SPEC))
    return errs


def check_review(root, need):
    text = rd(os.path.join(root, REVIEW))
    if text is None:
        return ["%s is missing: %d fresh-context reviewers read SPEC.md, findings get rulings" % (REVIEW, need)]
    errs = []
    author = field(text, "Author").strip("` ").lower()
    if not author:
        errs.append("`Author:` is empty: the agent or session that wrote SPEC.md (reviewers must not be it)")

    head, rows = table(section(text, "Reviewers"))
    rv, ag, ln = col(head, "reviewer"), col(head, "agent"), col(head, "lens")
    names = set()
    if not (rv and ag and ln):
        errs.append("## Reviewers needs a table with columns: Reviewer | Lens | Agent id")
    else:
        if len(rows) < need:
            errs.append("## Reviewers lists %d, this run needs %d fresh-context reviewers" % (len(rows), need))
        agents = [r[ag].strip("` ").lower() for r in rows]
        for r, a in zip(rows, agents):
            names.add(r[rv].lower())
            if a in OPEN:
                errs.append("## Reviewers: %r has no agent id (proof it was a separate fresh agent)" % r[rv])
            elif author and a == author:
                errs.append("## Reviewers: %r is the spec's author (%s). The author never reviews its own spec" % (r[rv], a))
        dup = sorted({a for a in agents if a not in OPEN and agents.count(a) > 1})
        if dup:
            errs.append("## Reviewers: agent id %s appears twice; each reviewer is its own fresh agent" % ", ".join(dup))

    head, rows = table(section(text, "Findings"))
    fr, fd, ru, why = col(head, "reviewer"), col(head, "finding"), col(head, "ruling"), col(head, "why", "fix", "reason")
    if not (fr and fd and ru and why):
        errs.append("## Findings needs a table with columns: # | Reviewer | Finding | Ruling | Why / fix")
    elif not rows:
        errs.append("## Findings is empty. A review that finds nothing is suspect: re-run it harsher, "
                    "or a different model, and record what it found")
    else:
        for i, r in enumerate(rows, 1):
            rl = r[ru].strip("` *").lower()
            if not any(rl.startswith(x) for x in RULINGS):
                errs.append("## Findings row %d has no ruling (fixed | dismissed): %s" % (i, r[fd][:60]))
            elif words(r[why]) < 3:
                errs.append("## Findings row %d is %s with no reason: say what changed in SPEC.md, or why it is wrong"
                            % (i, rl))
            if names and r[fr].lower() not in names:
                errs.append("## Findings row %d names reviewer %r, who is not in ## Reviewers" % (i, r[fr]))
    return errs


ASSUMED_MIN, ASSUMED_MAX = 10, 15


def check_mvp90(text, mode="full"):
    """forge 1.11 (90% MVP): core jobs, the domain-content line, and the "what do you assume it does" round.

    The audit found 6 runs missing a feature Adam took for granted (multi-select, a page counter).
    So before the build, list the 10-15 things a normal user of this kind of product expects and
    rule each in or out. An expected feature left out needs Adam's own words; nobody else can drop it.
    """
    errs = []
    jobs = re.findall(r"^\s*[-*\d.)\s]*\**(J\d+)\b", section(text, "Core jobs"), re.M)
    if not jobs:
        errs.append("## Core jobs lists none: the 1-7 jobs the ICP must finish on first hand-off (- J1: ...)")
    elif len(jobs) > 7:
        errs.append("## Core jobs lists %d; core means the few the ICP can't live without (7 max)" % len(jobs))
    dom = field(text, "Domain content").lower()
    if not (dom.startswith("yes") or dom.startswith("no")):
        errs.append("`Domain content: yes|no` is missing: does the product hold rules, prices, game data or "
                    "legal/tax text? yes means every item gets a source and a spot check (DOMAIN-TRUTH.md)")
    head, rows = table(section(text, "Assumed features"))
    f, io, why, by = col(head, "feature"), col(head, "in"), col(head, "reason", "why"), col(head, "decided by", "who")
    if not (f and io and why and by):
        return errs + ["## Assumed features needs a table: Feature | In/Out | Reason | Decided by "
                       "(the %d-%d things a normal user of this kind of product expects)" % (ASSUMED_MIN, ASSUMED_MAX)]
    if len(rows) < ASSUMED_MIN:
        errs.append("## Assumed features lists %d; list %d-%d (multi-select, undo, page counter, save state, "
                    "error messages, empty states...)" % (len(rows), ASSUMED_MIN, ASSUMED_MAX))
    for i, r in enumerate(rows, 1):
        v = r[io].strip("` *").lower()
        if v not in ("in", "out"):
            errs.append("## Assumed features row %d (%s): In/Out must be in or out" % (i, r[f][:40]))
            continue
        if words(r[why]) < 3:
            errs.append("## Assumed features row %d (%s) has no reason" % (i, r[f][:40]))
        if v == "out":
            who = r[by]
            ok = re.match(r"\s*(adam|founder)\b", who, re.I) and re.search(r"[\"\u201c].*\w+\W+\w+\W+\w+.*[\"\u201d]", who)
            if mode == "autonomous" and re.match(r"\s*orchestrator", who, re.I):
                ok = True
            if not ok:
                errs.append("## Assumed features row %d (%s) is out without Adam's words: a feature a normal user "
                            "expects is cut only by Adam (Decided by: Adam \"<3+ words>\")" % (i, r[f][:40]))
    return errs


def spec_check(root, mode="full", family="software"):
    """List of problems with the Stage S artifacts under root (empty list = gate S may pass)."""
    if family == "games":
        need = REVIEWERS["speed-run"]                 # the games family keeps Stage S light
    elif mode in REVIEWERS:
        need = REVIEWERS[mode]
    else:
        return ["unknown mode %r: Stage S runs as speed-run, full or autonomous" % (mode,)]
    errs, text = check_spec(root)
    if text is not None:
        errs += check_glossary(root, text) + check_mvp90(text, mode)
    return errs + check_review(root, need)


def main(argv):
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--mode", default="full", choices=sorted(REVIEWERS))
    p.add_argument("--family", default="software", choices=("software", "games"))
    a = p.parse_args(argv)
    errs = spec_check(a.root, a.mode, a.family)
    for e in errs:
        print("- " + e)
    print("STAGE S: %s" % ("READY" if not errs else "%d problem(s)" % len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
