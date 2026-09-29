#!/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
"""decide: local typed-decision model. State + typed questions in, typed answers out
(choice / yesno / score) with probabilities, confidence and margin. No prose.

Method: the answer is the FIRST generated token (a letter A/B/C.., Y/N, or a digit),
so one forward pass with logprobs gives a distribution. We take top_logprobs, keep only
tokens that map to allowed options, and renormalize. Local Ollama only. Never cloud.

Input JSON (stdin or --in):
 {"state": "...", "instructions": "optional",
  "questions": [
   {"id":"area","type":"choice","q":"Which area?","options":["YouTube",{"label":"Home","desc":"house, family"}]},
   {"id":"urgent","type":"yesno","q":"Is this urgent?"},
   {"id":"quality","type":"score","q":"Rate quality","scale":[1,5]} ]}
Output JSON: {"answers": {id: {answer, probs, confidence, margin, [expected]}}, "model", "latency_ms", "per_question_ms"}
"""
import json, math, sys, time, argparse, urllib.request

HOST = "http://localhost:11434"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TOPK = 20


def _norm(tok):
    return tok.strip().upper()


def build_prompt(state, q, instructions=""):
    t = q.get("type", "choice")
    head = "You are a precise classifier. Read the state, then answer the question with a single character and nothing else."
    if instructions:
        head += "\n" + instructions
    parts = [head, "", "STATE:", state.strip(), "", "QUESTION: " + q.get("q", q["id"])]
    if t == "choice":
        keys, labels = [], []
        for i, o in enumerate(q["options"]):
            lab, desc = (o, "") if isinstance(o, str) else (o["label"], o.get("desc", ""))
            keys.append(LETTERS[i]); labels.append(lab)
            parts.append(f"{LETTERS[i]}) {lab}" + (f" - {desc}" if desc else ""))
        parts.append("Answer with one letter (" + "/".join(keys) + ").")
    elif t == "yesno":
        keys, labels = ["Y", "N"], ["yes", "no"]
        parts.append("Answer Y for yes or N for no.")
    elif t == "score":
        lo, hi = q.get("scale", [1, 5])
        if hi - lo > 8:
            raise ValueError("score scale must span at most 9 values (single-digit tokens)")
        keys = [str(v) for v in range(lo, hi + 1)]
        labels = list(range(lo, hi + 1))
        parts.append(f"Answer with one digit from {lo} to {hi} ({lo}=lowest, {hi}=highest).")
    else:
        raise ValueError("unknown type " + t)
    parts.append("Answer:")
    return "\n".join(parts), keys, labels


def call(model, prompt, host=HOST, keep_alive="10m"):
    body = {"model": model, "prompt": prompt, "stream": False, "think": False,
            "logprobs": True, "top_logprobs": TOPK, "keep_alive": keep_alive,
            "options": {"temperature": 0, "num_predict": 1, "num_ctx": 4096}}
    req = urllib.request.Request(host + "/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode())
    lp = d.get("logprobs") or []
    if not lp:
        raise RuntimeError("no logprobs returned")
    return lp[0]["top_logprobs"]


def decide_one(model, state, q, instructions="", host=HOST):
    t0 = time.time()
    prompt, keys, labels = build_prompt(state, q, instructions)
    top = call(model, prompt, host)
    mass = {k: 0.0 for k in keys}
    for e in top:
        k = _norm(e["token"])
        if k in mass:
            mass[k] += math.exp(e["logprob"])
    tot = sum(mass.values())
    if tot <= 0:  # answer token was outside the allowed set
        probs = {str(l): 1.0 / len(keys) for l in labels}
        raw_mass = 0.0
    else:
        probs = {str(l): mass[k] / tot for k, l in zip(keys, labels)}
        raw_mass = tot
    ranked = sorted(probs.items(), key=lambda kv: -kv[1])
    ans = ranked[0][0]
    if q.get("type") == "score":
        ans = int(ans)
    out = {"answer": ans, "probs": {k: round(v, 4) for k, v in probs.items()},
           "confidence": round(ranked[0][1], 4),
           "margin": round(ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0), 4),
           "valid_mass": round(raw_mass, 4)}
    if q.get("type") == "score":
        out["expected"] = round(sum(float(k) * v for k, v in probs.items()), 3)
    return out, int((time.time() - t0) * 1000)


def decide(spec, model="gemma4:e4b", host=HOST):
    t0 = time.time()
    res, per = {}, {}
    for q in spec["questions"]:
        res[q["id"]], per[q["id"]] = decide_one(model, spec.get("state", ""), q, spec.get("instructions", ""), host)
    return {"answers": res, "model": model, "latency_ms": int((time.time() - t0) * 1000), "per_question_ms": per}


def main():
    ap = argparse.ArgumentParser(description="local typed decisions with logprob probabilities")
    ap.add_argument("--in", dest="inp"); ap.add_argument("--model", default="gemma4:e4b")
    ap.add_argument("--host", default=HOST)
    a = ap.parse_args()
    spec = json.load(open(a.inp)) if a.inp else json.load(sys.stdin)
    print(json.dumps(decide(spec, a.model, a.host), indent=2))


if __name__ == "__main__":
    main()
