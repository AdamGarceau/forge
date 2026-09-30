"""Run: cd ~/forge/jev && uv run python test_shim.py   (needs Ollama up; JEV_SHIM_MODEL to override)"""
import json, os, threading, urllib.request
from typing import Literal

PORT = 8766
os.environ["TYPESAFE_BASE_URL"] = f"http://127.0.0.1:{PORT}"
os.environ["TYPESAFE_API_KEY"] = "dummy-key"

def resident_model():
    try:
        d = json.load(urllib.request.urlopen("http://localhost:11434/api/ps", timeout=5))
        for m in d.get("models", []):
            if m["name"].startswith("gemma4"):
                return m["name"]
    except Exception:
        pass
    return "gemma4:e4b"

model = os.environ.get("JEV_SHIM_MODEL") or resident_model()
os.environ["JEV_SHIM_MODEL"] = model
import shim
srv = shim.serve(PORT, model)
threading.Thread(target=srv.serve_forever, daemon=True).start()
print("model:", model)

import jev
from pydantic import BaseModel, Field
from typesafe_sdk import TypeSafeClient, Noul, Choice, Score
from typesafe_sdk import TypeSafeError

class Triage(BaseModel):
    department: Literal["billing", "technical", "sales"]
    is_urgent: bool
    frustration: int = Field(ge=0, le=2)

@jev.fn
def triage(ticket: str) -> Triage:
    """A customer support ticket:

    {{ ticket }}
    """
    return triage.state()

r = triage("I was charged twice on my card. Fix this NOW, I am furious.")
print("(a) triage:", r)
assert isinstance(r, Triage) and r.department == "billing", r

c = TypeSafeClient()
print("models:", [m.name for m in c.models.list().models] if hasattr(c, "models") else "n/a")
resp = c.system_one(
    state="I was charged twice. Please help.",
    questions={
        "billing": Noul(instructions="Is this message about billing?"),
        "dept": Choice(instructions="Which department?", criteria={"billing": "money", "technical": "bugs", "sales": None}),
        "urgency": Score(instructions="How urgent?", criteria=["Can wait", "This week", "Today"]),
    },
) if hasattr(c, "system_one") else None
print("(b) noul:", resp.answers["billing"].noul, "choice:", resp.answers["dept"].probabilities,
      "score:", resp.answers["urgency"].score, resp.answers["urgency"].probabilities)
assert 0.0 <= resp.answers["billing"].noul <= 1.0
assert abs(sum(resp.answers["dept"].probabilities.values()) - 1) < 0.01
assert abs(sum(resp.answers["urgency"].probabilities.values()) - 1) < 0.01

try:
    c.system_one(state="x", questions={"s": Score(criteria=[str(i) for i in range(10)])})
    raise SystemExit("expected 422 for 10 levels")
except TypeSafeError as e:
    print("10-level score rejected:", str(e)[:100])
print("PASS")
