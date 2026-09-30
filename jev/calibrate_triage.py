"""Calibrate triage on reports.md worker lines. Gold for verdict = the line's own DONE/BLOCKED status
(stripped from the text before asking). Writes triage-results.json. Run: uv run python calibrate_triage.py"""
import json, os, random, threading, time
NATIVE = os.environ.get("JEV_NATIVE_MODEL")  # e.g. nimble:latest -> native /v1/systemone on Ollama 0.35+, no shim
os.environ["TYPESAFE_BASE_URL"] = "http://127.0.0.1:11434" if NATIVE else "http://127.0.0.1:8766"
os.environ.setdefault("TYPESAFE_API_KEY", "local")
import shim, triage
NATIVE or threading.Thread(target=shim.serve(8766, "gemma4:e4b").serve_forever, daemon=True).start()
rows = [p for p in map(triage.parse, open(os.path.expanduser("~/maax/fleet/reports.md"))) if p and p["status"] in ("DONE", "BLOCKED") and p["worker"] != "maax"]
rnd = random.Random(7)
done = [r for r in rows if r["status"] == "DONE"]; blk = [r for r in rows if r["status"] == "BLOCKED"]
rnd.shuffle(done); sample = done[:50] + blk
res = []
for r in sample:
    t0 = time.time(); o = triage.triage(r["text"])
    res.append({"worker": r["worker"], "ts": r["ts"], "gold": r["status"], "text": r["text"][:300], **o, "ms": int((time.time() - t0) * 1000)})
json.dump(res, open(f"triage-results{'-' + NATIVE.replace(':','_') if NATIVE else ''}.json", "w"), indent=1)
ok = lambda x: x["verdict"] == x["gold"] or (x["gold"] == "DONE" and x["verdict"] == "NEEDS-ADAM" and False)
print("n", len(res), "verdict acc", sum(map(ok, res)) / len(res))
for th in (.5, .7, .8, .9):
    hi = [x for x in res if x["verdict_conf"] >= th]
    print(f" conf>={th}: n={len(hi)} right={sum(map(ok, hi)) / max(len(hi), 1):.0%}")
from collections import Counter
print(Counter((x["gold"], x["verdict"]) for x in res))
print("p50 ms", sorted(x["ms"] for x in res)[len(res) // 2])
