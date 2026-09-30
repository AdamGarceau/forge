"""Own System One: multinomial logistic regression on nomic-embed-text embeddings of Adam's own
task labels (~/maax/tasks/tasks.db, read-only). Predicts area (and priority) with calibrated confidence.

  uv run python own_model.py eval    # stratified 5-fold CV, prints metrics, writes own-model-results.json
  uv run python own_model.py train   # fits on all rows, saves models/own-{area,priority}.joblib
  uv run python own_model.py predict "title" [notes]

Served through shim.py as model `own-area` / `own-priority` (a Choice question, no LLM call).
Fully local: embeddings from Ollama on localhost:11434; nothing leaves the machine."""
import hashlib, json, os, sqlite3, sys, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.expanduser("~/maax/tasks/tasks.db")
OLLAMA = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
EMBED_MODEL = "nomic-embed-text"
CACHE = os.path.join(HERE, "models", "embed-cache.json")
MODELS = os.path.join(HERE, "models")
C = float(os.environ.get("OWN_MODEL_C", "10"))
TARGETS = {"area": "area", "priority": "priority"}


def text_of(title, notes=""):
    return f"classification: {title or ''}\n{(notes or '').strip()}"[:2000]


def embed(texts):
    """Embed via Ollama /api/embed, cached by text hash so retraining costs nothing."""
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    key = lambda t: hashlib.sha1((EMBED_MODEL + t).encode()).hexdigest()
    need = [t for t in dict.fromkeys(texts) if key(t) not in cache]
    for i in range(0, len(need), 32):
        chunk = need[i:i + 32]
        req = urllib.request.Request(OLLAMA + "/api/embed", json.dumps({"model": EMBED_MODEL, "input": chunk}).encode(),
                                     {"Content-Type": "application/json"})
        vecs = json.load(urllib.request.urlopen(req, timeout=120))["embeddings"]
        for t, v in zip(chunk, vecs):
            cache[key(t)] = v
    if need:
        os.makedirs(MODELS, exist_ok=True)
        json.dump(cache, open(CACHE, "w"))
    X = np.array([cache[key(t)] for t in texts], dtype=np.float64)
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def load_rows():
    db = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
    return db.execute("select id,title,coalesce(notes,''),area,priority,status from tasks").fetchall()


def make_clf():
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=C, max_iter=2000)


def train(save=True):
    import joblib
    rows = load_rows()
    X = embed([text_of(r[1], r[2]) for r in rows])
    out = {}
    for name, col in (("area", 3), ("priority", 4)):
        idx = [i for i, r in enumerate(rows) if r[col] is not None]
        y = np.array([str(rows[i][col]) for i in idx])
        clf = make_clf().fit(X[idx], y)
        out[name] = clf
        if save:
            os.makedirs(MODELS, exist_ok=True)
            joblib.dump(clf, os.path.join(MODELS, f"own-{name}.joblib"))
    return out


_loaded = {}


def predict_probs(target, title, notes=""):
    """-> {label: prob}. Loads (training on first use if no saved model) the target's classifier."""
    import joblib
    if target not in _loaded:
        path = os.path.join(MODELS, f"own-{target}.joblib")
        _loaded[target] = joblib.load(path) if os.path.exists(path) else train()[target]
    clf = _loaded[target]
    p = clf.predict_proba(embed([text_of(title, notes)]))[0]
    return {str(k): float(x) for k, x in zip(clf.classes_, p)}


def predict(title, notes=""):
    out = {}
    for t in TARGETS:
        p = predict_probs(t, title, notes)
        k = max(p, key=p.get)
        out[t] = k
        out[t + "_conf"] = round(p[k], 4)
    return out


def ece(conf, ok, bins=10):
    conf, ok = np.asarray(conf), np.asarray(ok, float)
    e = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        m = (conf > lo) & (conf <= lo + 1 / bins)
        if m.any():
            e += m.mean() * abs(ok[m].mean() - conf[m].mean())
    return float(e)


def cv_eval():
    from sklearn.model_selection import StratifiedKFold
    rows = load_rows()
    X = embed([text_of(r[1], r[2]) for r in rows])
    calib_ids = [x["id"] for x in json.load(open(os.path.join(HERE, "calibrate-results.json")))]
    result = {"C": C, "n_rows": len(rows)}
    for name, col in (("area", 3), ("priority", 4)):
        idx = np.array([i for i, r in enumerate(rows) if r[col] is not None])
        y = np.array([str(rows[i][col]) for i in idx])
        oof = np.empty(len(idx), dtype=object); conf = np.zeros(len(idx))
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=7).split(idx, y):
            clf = make_clf().fit(X[idx[tr]], y[tr])
            p = clf.predict_proba(X[idx[te]])
            oof[te] = clf.classes_[p.argmax(1)]; conf[te] = p.max(1)
        ok = oof == y
        ids = np.array([rows[i][0] for i in idx])
        sub = np.isin(ids, calib_ids)
        maj = max((y == c).mean() for c in set(y))
        def block(m):
            d = {"n": int(m.sum()), "acc": float(ok[m].mean()), "ece": ece(conf[m], ok[m]), "thresholds": {}}
            for th in (.5, .6, .7, .8, .9):
                hi, lo = m & (conf >= th), m & (conf < th)
                d["thresholds"][str(th)] = {"hi_right": float(ok[hi].mean()) if hi.any() else None, "hi_n": int(hi.sum()),
                                            "lo_right": float(ok[lo].mean()) if lo.any() else None, "lo_n": int(lo.sum()),
                                            "coverage": float(hi.sum() / m.sum())}
            return d
        per = {}
        for c in sorted(set(y)):
            pm = oof == c
            per[c] = {"support": int((y == c).sum()), "predicted": int(pm.sum()),
                      "precision": float(ok[pm].mean()) if pm.any() else None,
                      "recall": float((oof[y == c] == c).mean()),
                      "precision_at_0.8": float(ok[pm & (conf >= .8)].mean()) if (pm & (conf >= .8)).any() else None,
                      "n_at_0.8": int((pm & (conf >= .8)).sum())}
        result[name] = {"majority_baseline": float(maj), "all": block(np.ones(len(idx), bool)),
                        "calibrate_sample_n75": block(sub), "per_label": per,
                        "curve": [{"th": th, "precision": float(ok[conf >= th].mean()), "coverage": float((conf >= th).mean())}
                                  for th in (.5, .6, .7, .75, .8, .85, .9, .95) if (conf >= th).any()]}
    json.dump(result, open(os.path.join(HERE, "own-model-results.json"), "w"), indent=1)
    return result


def report(r):
    print(f"C={r['C']} rows={r['n_rows']}")
    for name in ("area", "priority"):
        d = r[name]; print(f"\n{name.upper()} (majority baseline {d['majority_baseline']:.1%})")
        for k in ("all", "calibrate_sample_n75"):
            b = d[k]; print(f" [{k}] n={b['n']} acc={b['acc']:.1%} ECE={b['ece']:.3f}")
            for th, t in b["thresholds"].items():
                f = lambda v, n: f"{v:.0%} (n={n})" if v is not None else "n/a"
                print(f"   conf>={th}: right {f(t['hi_right'], t['hi_n'])} | below {f(t['lo_right'], t['lo_n'])} | cov {t['coverage']:.0%}")
        for c, p in d["per_label"].items():
            pr = "n/a" if p["precision"] is None else f"{p['precision']:.0%}"
            p8 = "n/a" if p["precision_at_0.8"] is None else f"{p['precision_at_0.8']:.0%}"
            print(f"   {c:9} support={p['support']:3} prec={pr} rec={p['recall']:.0%} prec@.8={p8} (n={p['n_at_0.8']})")
        print("   curve:", " ".join(f"{c['th']}:{c['precision']:.0%}/{c['coverage']:.0%}cov" for c in d["curve"]))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "eval"
    if cmd == "eval": report(cv_eval())
    elif cmd == "train": train(); print("saved", MODELS)
    elif cmd == "predict": print(json.dumps(predict(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")))
    else: sys.exit(__doc__)
