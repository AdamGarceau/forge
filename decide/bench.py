#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""Benchmark: predict tasks.area from title+notes. Read-only on tasks.db.
Usage: bench.py [--n-per-area 25] ; results -> bench-results.json"""
import sqlite3, random, json, time, subprocess, sys, os, statistics as st
sys.path.insert(0, os.path.dirname(__file__))
import decide as D

AREAS = {"YouTube": "video ideas, scripts, filming, editing, publishing, channel, thumbnails, Etsy/homeschool content business",
         "Job Hunt": "job applications, resumes, interviews, unemployment/work-search filings, recruiters",
         "GYA": "Grab Your Assets: client video/marketing work, gigs, invoices, proposals, gear for client shoots",
         "Maax HQ": "the AI assistant system itself: Claude, agents, automations, the console, tooling and infrastructure",
         "Home": "house, family, kids, errands, vehicles, health, personal life",
         "Army": "Army Reserves: board, warrant packet, drill, military paperwork",
         "Inbox": "unsorted catch-all: vague or miscellaneous items that fit nowhere else"}
LABELS = list(AREAS)

def sample(n, seed=7):
    db = sqlite3.connect("file:" + os.path.expanduser("~/maax/tasks/tasks.db") + "?mode=ro", uri=True)
    rows = db.execute("select id,title,coalesce(notes,''),area from tasks where area in (%s)" % ",".join("?" * 7), LABELS).fetchall()
    by = {}
    for r in rows: by.setdefault(r[3], []).append(r)
    rnd = random.Random(seed); out = []
    for a, rs in by.items():
        rnd.shuffle(rs); out += rs[:n]
    rnd.shuffle(out); return out

def state(r): return f"Task title: {r[1]}\nNotes: {r[2][:400]}"

def run_decide(rows, model):
    q = {"id": "area", "type": "choice", "q": "Which life/work area does this task belong to?",
         "options": [{"label": k, "desc": v} for k, v in AREAS.items()]}
    D.decide_one(model, "warmup", q)  # exclude cold load from latency
    res = []
    for r in rows:
        o, ms = D.decide_one(model, state(r), q)
        res.append({"id": r[0], "gold": r[3], "pred": o["answer"], "conf": o["confidence"], "ms": ms})
    return res

def run_classify(rows):
    defs = "\n".join(f"- {k}: {v}" for k, v in AREAS.items())
    res = []
    subprocess.run(["forge-lane", "classify", "Reply OK"], capture_output=True, text=True)  # warm
    for r in rows:
        p = (f"Classify this task into exactly one area. Areas:\n{defs}\n\n{state(r)}\n\n"
             f"Reply with only the area name, one of: {', '.join(LABELS)}.")
        t0 = time.time()
        out = subprocess.run(["forge-lane", "classify", "--sensitive", p], capture_output=True, text=True).stdout.strip()
        ms = int((time.time() - t0) * 1000)
        low = out.lower(); pred = None
        for k in sorted(LABELS, key=lambda k: low.find(k.lower()) if k.lower() in low else 9999):
            if k.lower() in low: pred = k; break
        res.append({"id": r[0], "gold": r[3], "pred": pred or "??", "conf": None, "ms": ms})
    return res

def summarize(res):
    n = len(res); acc = sum(x["pred"] == x["gold"] for x in res) / n
    ms = sorted(x["ms"] for x in res)
    s = {"n": n, "acc": round(acc, 3), "p50_ms": ms[n // 2], "p95_ms": ms[int(n * .95) - 1]}
    if res[0]["conf"] is not None:
        hi = [x for x in res if x["conf"] >= .8]; lo = [x for x in res if x["conf"] < .8]
        f = lambda g: round(sum(x["pred"] == x["gold"] for x in g) / len(g), 3) if g else None
        s.update(hi_n=len(hi), hi_acc=f(hi), lo_n=len(lo), lo_acc=f(lo))
    return s

if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--n-per-area") + 1]) if "--n-per-area" in sys.argv else 25
    rows = sample(n); print("tasks:", len(rows), flush=True)
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else ["e4b", "e2b", "classify", "12b"]
    path = os.path.join(os.path.dirname(__file__), "bench-results.json")
    allr = json.load(open(path)) if os.path.exists(path) else {}
    for name in only:
        res = run_classify(rows) if name == "classify" else run_decide(rows, "gemma4:" + name)
        allr[name] = {"summary": summarize(res), "rows": res}
        print(name, allr[name]["summary"], flush=True)
        json.dump(allr, open(path, "w"))
