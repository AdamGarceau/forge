"""Run: cd ~/forge/jev && uv run python test_own_model.py   (needs Ollama up for nomic-embed-text; no LLM call)"""
import os, threading
PORT = 8767
os.environ["TYPESAFE_BASE_URL"] = f"http://127.0.0.1:{PORT}"
os.environ["TYPESAFE_API_KEY"] = "dummy-key"
import numpy as np
import own_model, shim, autotag
from typesafe_sdk import TypeSafeClient, Choice, Noul, TypeSafeError

# unit: ECE and text
assert own_model.ece([1.0, 1.0], [1, 1]) == 0.0
assert abs(own_model.ece([0.9, 0.9], [1, 0]) - 0.4) < 1e-9
assert own_model.text_of("a", None).startswith("classification: a")

# embeddings are unit-norm and cached
X = own_model.embed(["film the homeschool vlog", "film the homeschool vlog", "renew the truck registration"])
assert X.shape[0] == 3 and np.allclose(np.linalg.norm(X, axis=1), 1) and np.allclose(X[0], X[1])

# model: trains, saves, predicts a label from the known set with a probability distribution
own_model.train()
assert os.path.exists(os.path.join(own_model.MODELS, "own-area.joblib"))
p = own_model.predict_probs("area", "Write the script for the YouTube video about Claude", "hook and outline")
assert abs(sum(p.values()) - 1) < 1e-6 and set(p) == set(autotag.AREAS), p
assert max(p, key=p.get) == "YouTube", p
out = own_model.predict("Submit weekly work search on Utah DWS", "")
assert out["area"] in autotag.AREAS and 0 < out["area_conf"] <= 1 and out["priority"] in "1234", out

# route: /v1/systemone with model own-area, via the SDK
threading.Thread(target=shim.serve(PORT).serve_forever, daemon=True).start()
c = TypeSafeClient()
r = c.system_one(model="own-area", state="Write the script for the YouTube video about Claude\nhook and outline",
                 questions={"area": Choice(instructions=autotag.Q_AREA, criteria=autotag.AREAS)})
a = r.answers["area"]
assert a.choice == "YouTube" and 0 < a.confidence <= 1 and abs(sum(a.probabilities.values()) - 1) < 1e-6, a
# criteria subset: probabilities restricted + renormalised to the labels offered
r = c.system_one(model="own-area", state="Write the script for the YouTube video about Claude",
                 questions={"area": Choice(criteria={"Home": "house", "Inbox": "misc"})})
b = r.answers["area"]
assert set(b.probabilities) == {"Home", "Inbox"} and abs(sum(b.probabilities.values()) - 1) < 1e-6
# unmatched labels -> 422; non-choice -> 422; models list advertises it
for bad in ({"x": Choice(criteria={"nope": "zzz"})}, {"x": Noul(instructions="yes?")}):
    try:
        c.system_one(model="own-area", state="t", questions=bad)
        raise SystemExit("expected 422")
    except TypeSafeError:
        pass
assert "own-area" in [m.name for m in c.models.list().models]
print("PASS")
