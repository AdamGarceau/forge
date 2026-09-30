"""Calibration: area+priority on done+open tasks from tasks.db, via autotag (local shim). Read-only DB.
Run: uv run python calibrate.py [n_per_area] ; writes calibrate-results.json"""
import json, os, random, sqlite3, sys, threading, time
NATIVE = os.environ.get("JEV_NATIVE_MODEL")  # e.g. nimble:latest -> native /v1/systemone on Ollama 0.35+, no shim
os.environ["TYPESAFE_BASE_URL"] = "http://127.0.0.1:11434" if NATIVE else "http://127.0.0.1:8766"
os.environ.setdefault("TYPESAFE_API_KEY", "local")
import shim, autotag
model = os.environ.get("JEV_SHIM_MODEL", "gemma4:e4b")
assert NATIVE or model == "gemma4:e4b"
NATIVE or threading.Thread(target=shim.serve(8766, model).serve_forever, daemon=True).start()
n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
db = sqlite3.connect("file:" + os.path.expanduser("~/maax/tasks/tasks.db") + "?mode=ro", uri=True)
rows = db.execute("select id,title,coalesce(notes,''),area,priority from tasks where status in ('done','open') and area in (%s)" % ",".join("?" * 7), list(autotag.AREAS)).fetchall()
by = {}
for r in rows: by.setdefault(r[3], []).append(r)
rnd = random.Random(7); sample = []
for a, rs in by.items():
    rnd.shuffle(rs); sample += rs[:n]
rnd.shuffle(sample)
res = []
for r in sample:
    t0 = time.time(); o = autotag.autotag(r[1], r[2])
    res.append({"id": r[0], "gold": r[3], "gold_pri": r[4], **o, "ms": int((time.time() - t0) * 1000)})
json.dump(res, open(f"calibrate-results{'-' + NATIVE.replace(':','_') if NATIVE else ''}.json", "w"), indent=1)
def rep(key, goldk, confk, label, subset=None):
    xs = [x for x in res if (subset is None or x[goldk] is not None)]
    acc = sum(str(x[key]) == str(x[goldk]) for x in xs) / len(xs)
    print(f"{label}: n={len(xs)} acc={acc:.1%}")
    for th in (.5, .6, .7, .8, .9):
        hi = [x for x in xs if x[confk] >= th]; lo = [x for x in xs if x[confk] < th]
        f = lambda s: f"{sum(str(x[key]) == str(x[goldk]) for x in s) / len(s):.0%} (n={len(s)})" if s else "n/a"
        print(f"  conf>={th}: right {f(hi)} | below: {f(lo)}")
rep("area", "gold", "area_conf", "AREA")
rep("priority", "gold_pri", "priority_conf", "PRIORITY", subset=True)
print("p50 ms", sorted(x["ms"] for x in res)[len(res) // 2])
