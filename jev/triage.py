#!/usr/bin/env python3
"""Fleet report triage (Step 4.2): DONE / BLOCKED / NEEDS-ADAM + outward-facing?, via Jev (local shim).
CLI: uv run python triage.py "<reports.md line>"  -> JSON. Defaults to the local shim; no cloud."""
import json, os, re, sys
if not os.environ.get("JEV_ALLOW_CLOUD"):
    os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8766")
    os.environ.setdefault("TYPESAFE_API_KEY", "local")
from typesafe_sdk import TypeSafeClient, Choice, Noul

VERDICTS = {"DONE": "the worker finished the task and nothing is left waiting on a person",
            "BLOCKED": "the worker could not finish; it hit an obstacle or is missing something it needs",
            "NEEDS-ADAM": "work is finished or partly finished but a decision, check, approval, or input from Adam is still required"}
Q_OUT = "Did the worker send, post, publish, upload, submit, or share anything to a person or service outside this computer?"
LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d{1,2}:\d\d [AP]M) \| ([^|]+?) \| ([^|]*?) \| (.*?)(?: \| (\S+))?$")


def parse(line):
    m = LINE.match(line.strip())
    return dict(zip(("ts", "worker", "status", "text", "path"), m.groups())) if m else None


def triage(text):
    r = TypeSafeClient(timeout=float(os.environ.get("JEV_TIMEOUT", "60"))).system_one(model=os.environ.get("JEV_NATIVE_MODEL"), state="Fleet worker report: " + text[:600], questions={
        "verdict": Choice(instructions="What is the state of this worker's task?", criteria=VERDICTS),
        "outward": Noul(instructions=Q_OUT)})
    v, o = r.answers["verdict"], r.answers["outward"]
    return {"verdict": v.choice, "verdict_conf": v.confidence, "verdict_probs": v.probabilities, "outward_p": o.noul}


if __name__ == "__main__":
    print(json.dumps(triage(sys.argv[1])))
