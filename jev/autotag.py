#!/usr/bin/env python3
"""Auto-tag a task: area + priority with confidence, via Jev (local shim by default).

CLI: uv run python autotag.py "title" [notes]  -> JSON {area, area_conf, priority, priority_conf}
`tag_task` is the @jev.fn form (labels only; jev return models drop confidence).
`autotag` is the calibrated path: same questions through the SDK so confidence survives.
Defaults TYPESAFE_BASE_URL to the local shim (nothing goes to the cloud unless you unset it AND
export JEV_ALLOW_CLOUD=1).
"""
import json, os, sys
from typing import Literal

if not os.environ.get("JEV_ALLOW_CLOUD"):
    os.environ.setdefault("TYPESAFE_BASE_URL", "http://127.0.0.1:8766")
    os.environ.setdefault("TYPESAFE_API_KEY", "local")

import jev
from pydantic import BaseModel
from typesafe_sdk import TypeSafeClient, Choice

AREAS = {"YouTube": "video ideas, scripts, filming, editing, publishing, channel, thumbnails, Etsy/homeschool content business",
         "Job Hunt": "job applications, resumes, interviews, unemployment/work-search filings, recruiters",
         "GYA": "Grab Your Assets: client video/marketing work, gigs, invoices, proposals, gear for client shoots",
         "Maax HQ": "the AI assistant system itself: Claude, agents, automations, the console, tooling and infrastructure",
         "Home": "house, family, kids, errands, vehicles, health, personal life",
         "Army": "Army Reserves: board, warrant packet, drill, military paperwork",
         "Inbox": "unsorted catch-all: vague or miscellaneous items that fit nowhere else"}
PRIORITIES = {"1": "urgent: hard deadline today or blocking income", "2": "high: important, this week",
              "3": "normal: routine, no deadline pressure", "4": "low: someday, nice to have"}
Q_AREA = "Which life/work area does this task belong to?"
Q_PRI = "How urgent is this task?"


class Tag(BaseModel):
    area: Literal["YouTube", "Job Hunt", "GYA", "Maax HQ", "Home", "Army", "Inbox"]
    priority: Literal["1", "2", "3", "4"]


@jev.fn
def tag_task(task: str) -> Tag:
    """A to-do item:

    {{ task }}
    """
    return tag_task.state()


def _state(title, notes=""):
    return f"Task title: {title}\nNotes: {(notes or '')[:400]}"


def autotag(title, notes=""):
    r = TypeSafeClient(timeout=float(os.environ.get("JEV_TIMEOUT", "60"))).system_one(model=os.environ.get("JEV_NATIVE_MODEL"), state=_state(title, notes), questions={
        "area": Choice(instructions=Q_AREA, criteria=AREAS),
        "priority": Choice(instructions=Q_PRI, criteria=PRIORITIES)})
    a, p = r.answers["area"], r.answers["priority"]
    return {"area": a.choice, "area_conf": a.confidence, "priority": int(p.choice), "priority_conf": p.confidence}


if __name__ == "__main__":
    print(json.dumps(autotag(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")))
