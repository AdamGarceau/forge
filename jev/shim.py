#!/usr/bin/env python3
"""Local TypeSafe/Jev shim: /v1/systemone and /v1/models on 127.0.0.1:8766, backed by
~/forge/decide (Ollama on localhost only, think:false). Never touches the internet.

Mapping: noul -> yesno (noul = P(yes)); choice -> choice (max 26 labels);
score -> score (criteria[i] is level i; max 9 levels, more is a 422 error, no bucketing).
Any API key is accepted. Model: JEV_SHIM_MODEL (default gemma4:e4b); the request's
"model" is honored only if it names a local Ollama model (contains ':'), else default.

Run: python3 shim.py [--port 8766] [--model gemma4:e4b]
"""
import argparse, json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.expanduser("~/forge/decide"))
import decide  # noqa: E402  (imported only, never modified)

DEFAULT_MODEL = os.environ.get("JEV_SHIM_MODEL", "gemma4:e4b")
HOST = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")
_lock = threading.Lock()  # one Ollama call at a time


class BadRequest(Exception):
    def __init__(self, loc, msg, typ="value_error"):
        self.detail = [{"loc": ["body"] + list(loc), "msg": msg, "type": typ}]


def _txt(v):
    return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)


def to_decide_question(name, q):
    t = q.get("type")
    instr = q.get("instructions")
    text = _txt(instr) if instr is not None else name.replace("_", " ")
    crit = q.get("criteria")
    if t == "noul":
        c = crit or {}
        extra = []
        if c.get("true") is not None:
            extra.append("Yes means: " + _txt(c["true"]))
        if c.get("false") is not None:
            extra.append("No means: " + _txt(c["false"]))
        return {"id": name, "type": "yesno", "q": text + (" " + " ".join(extra) if extra else "")}
    if t == "choice":
        if not isinstance(crit, dict) or not crit:
            raise BadRequest(["questions", name, "criteria"], "choice needs nonempty criteria", "missing")
        if len(crit) > 26:
            raise BadRequest(["questions", name, "criteria"], f"shim supports at most 26 choices, got {len(crit)}", "too_long")
        opts = [{"label": k, "desc": "" if v is None else _txt(v)} for k, v in crit.items()]
        return {"id": name, "type": "choice", "q": text, "options": opts}
    if t == "score":
        if not isinstance(crit, list) or not crit:
            raise BadRequest(["questions", name, "criteria"], "score needs nonempty criteria", "missing")
        if len(crit) > 9:
            raise BadRequest(["questions", name, "criteria"], f"shim supports at most 9 score levels, got {len(crit)}", "too_long")
        rubric = "; ".join(f"{i}={_txt(c)}" for i, c in enumerate(crit))
        return {"id": name, "type": "score", "q": f"{text} Levels: {rubric}", "scale": [0, len(crit) - 1]}
    raise BadRequest(["questions", name, "type"], f"unknown question type {t!r}", "literal_error")


def to_wire(name, q, out):
    t = q["type"]
    p = out["probs"]
    if t == "noul":
        return {"type": "noul", "noul": p["yes"]}
    if t == "choice":
        return {"type": "choice", "choice": out["answer"], "confidence": out["confidence"], "probabilities": p}
    legend = {str(i): c for i, c in enumerate(q["criteria"])}
    return {"type": "score", "score": out["expected"], "confidence": out["confidence"],
            "legend": legend, "probabilities": {str(k): v for k, v in p.items()}}


OWN_MODELS = {"own-area": "area", "own-priority": "priority"}


def own_systemone(req, target):
    """Answer choice questions from the own logistic-regression model (own_model.py): no LLM call.
    Probabilities are restricted to the question's criteria labels and renormalised."""
    import own_model
    state = _txt(req["state"])
    title, _, notes = state.partition("\n")
    answers = {}
    for name, q in req["questions"].items():
        if q.get("type") != "choice":
            raise BadRequest(["questions", name, "type"], f"model own-{target} only answers choice questions", "literal_error")
        crit = q.get("criteria")
        if not isinstance(crit, dict) or not crit:
            raise BadRequest(["questions", name, "criteria"], "choice needs nonempty criteria", "missing")
        raw = own_model.predict_probs(target, title, notes)
        p = {k: raw.get(str(k), 0.0) for k in crit}
        z = sum(p.values())
        if z <= 0:
            raise BadRequest(["questions", name, "criteria"], f"no criteria label matches own-{target} classes {sorted(raw)}", "value_error")
        p = {k: v / z for k, v in p.items()}
        best = max(p, key=p.get)
        answers[name] = {"type": "choice", "choice": best, "confidence": p[best], "probabilities": p}
    return {"model": f"own-{target}", "answers": answers,
            "usage": {"input_tokens": len(state) // 4, "output_tokens": len(answers)}}


def systemone(req, default_model):
    if not isinstance(req, dict):
        raise BadRequest([], "body must be an object", "model_attributes_type")
    for f in ("state", "questions"):
        if f not in req:
            raise BadRequest([f], "Field required", "missing")
    qs = req["questions"]
    if not isinstance(qs, dict) or not qs:
        raise BadRequest(["questions"], "questions must be a nonempty object", "too_short")
    model = req.get("model")
    if model in OWN_MODELS:
        for name, q in qs.items():
            if not isinstance(q, dict):
                raise BadRequest(["questions", name], "question must be an object", "model_attributes_type")
        return own_systemone(req, OWN_MODELS[model])
    model = model if isinstance(model, str) and ":" in model else default_model
    state = _txt(req["state"])
    dq = {name: to_decide_question(name, q) for name, q in qs.items()}  # validate all first
    answers, tokens = {}, len(state) // 4
    with _lock:
        for name, q in qs.items():
            out, _ = decide.decide_one(model, state, dq[name], host=HOST)
            answers[name] = to_wire(name, q, out)
            tokens += len(json.dumps(dq[name])) // 4
    return {"model": model, "answers": answers,
            "usage": {"input_tokens": tokens, "output_tokens": len(qs)}}


def make_handler(default_model):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            if self.path.split("?")[0] == "/v1/models":
                return self._send(200, {"models": [
                    {"name": "jev-latest", "description": f"Local shim over decide ({default_model}, Ollama).",
                     "release_date": "2026-09-29"},
                    {"name": default_model, "description": "Direct local Ollama model via decide.",
                     "release_date": "2026-09-29"},
                    {"name": "own-area", "description": "Own logistic regression on nomic-embed-text, trained on tasks.db areas (choice only).",
                     "release_date": "2026-09-30"},
                    {"name": "own-priority", "description": "Own logistic regression on tasks.db priorities (choice only, weak).",
                     "release_date": "2026-09-30"}]})
            self._send(404, {"detail": "not found"})

        def do_POST(self):
            if self.path.split("?")[0] != "/v1/systemone":
                return self._send(404, {"detail": "not found"})
            try:
                n = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(n) or b"{}")
                self._send(200, systemone(req, default_model))
            except BadRequest as e:
                self._send(422, {"detail": e.detail})
            except json.JSONDecodeError:
                self._send(422, {"detail": [{"loc": ["body"], "msg": "invalid JSON", "type": "json_invalid"}]})
            except Exception as e:  # Ollama down, etc.
                self._send(500, {"detail": f"shim error: {e}"})

        def log_message(self, *a):
            pass
    return H


def serve(port=8766, model=DEFAULT_MODEL):
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(model))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    a = ap.parse_args()
    print(f"jev shim on http://127.0.0.1:{a.port} model={a.model}", flush=True)
    serve(a.port, a.model).serve_forever()
