"""LLM transporter. Glimpse first. Depth second. Glimpse is transport, not language."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .ast import Door


@dataclass
class Frame:
    rv: str
    phase: str
    payload: dict

    def as_dict(self) -> dict:
        return {"language": "YA|RA", "rv": self.rv, "phase": self.phase, "transporter": self.payload}

    def wire(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False)

    @property
    def intent(self) -> str:
        return str(self.payload.get("intent", ""))

    @property
    def pattern(self) -> str:
        return str(self.payload.get("pattern", ""))

    @property
    def signed(self) -> str:
        env = self.payload.get("envelope") or {}
        return f"{env.get('actor', '')} / {env.get('timestamp', '')}".strip(" /")


@dataclass
class Hop:
    glimpse: Frame
    depth: Frame
    hopped: bool
    reply: str | None
    error: str | None = None

    def envelope(self) -> dict:
        return {
            "language": "YA|RA",
            "rv": self.glimpse.rv,
            "hop": [self.glimpse.as_dict(), self.depth.as_dict()],
            "rule": "greet with a glimpse, then serve depth.",
            "hopped": self.hopped,
            "reply": self.reply,
            "error": self.error,
        }

    def wire(self) -> str:
        return json.dumps(self.envelope(), ensure_ascii=False, indent=2) + "\n"


def frames_for(door: Door):
    env = {
        "kind": door.envelope.kind,
        "actor": door.envelope.actor,
        "timestamp": door.envelope.timestamp,
        "note": door.envelope.note,
    }
    glimpse = Frame(door.rv, "glimpse", {"intent": door.intent, "pattern": door.pattern.split(".")[0].strip() or door.pattern})
    depth = Frame(
        door.rv,
        "depth",
        {
            "intent": door.intent,
            "pattern": door.pattern,
            "measure": door.measure,
            "zero": door.zero,
            "checks": [{"kind": c.kind, "args": list(c.args), "amp": repr(c.amp)} for c in door.checks],
            "envelope": env,
            "source": door.source,
        },
    )
    return glimpse, depth


def hop(door: Door, *, key=None, url=None, model=None) -> Hop:
    g, d = frames_for(door)
    key = key if key is not None else os.environ.get("YARA_LLM_KEY") or os.environ.get("XAI_API_KEY")
    url = url or os.environ.get("YARA_LLM_URL") or "https://api.x.ai/v1/chat/completions"
    model = model or os.environ.get("YARA_LLM_MODEL") or "grok-4"
    if not key:
        return Hop(glimpse=g, depth=d, hopped=False, reply=None)
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": "Greet with a glimpse, then serve depth.\n" + g.wire()}, {"role": "user", "content": d.wire()}]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer " + key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return Hop(glimpse=g, depth=d, hopped=True, reply=payload["choices"][0]["message"]["content"])
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError) as e:
        return Hop(glimpse=g, depth=d, hopped=False, reply=None, error=str(e))
