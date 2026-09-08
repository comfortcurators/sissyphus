"""LLM transporter. Glimpse first. Depth second. A hop is a real request when a key is set."""

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
    intent: str
    pattern: str
    signed: str

    def transporter(self) -> dict:
        return {
            "intent": self.intent,
            "pattern": self.pattern,
            "signed": self.signed,
        }

    def as_dict(self) -> dict:
        return {
            "language": "YA|RA",
            "rv": self.rv,
            "phase": self.phase,
            "transporter": self.transporter(),
        }

    def wire(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False)

    @staticmethod
    def from_wire(s: str) -> "Frame":
        o = json.loads(s)
        t = o["transporter"]
        return Frame(o["rv"], o["phase"], t["intent"], t["pattern"], t["signed"])


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


def frames_for(door: Door) -> tuple[Frame, Frame]:
    signed = f"{door.signer} / {door.timestamp}"
    g = Frame(door.rv, "glimpse", door.intent, door.pattern, signed)
    d = Frame(door.rv, "depth", door.intent, door.pattern, signed)
    return g, d


def hop(door: Door, *, key: str | None = None, url: str | None = None, model: str | None = None) -> Hop:
    g, d = frames_for(door)
    key = key if key is not None else os.environ.get("YARA_LLM_KEY") or os.environ.get("XAI_API_KEY")
    url = url or os.environ.get("YARA_LLM_URL") or "https://api.x.ai/v1/chat/completions"
    model = model or os.environ.get("YARA_LLM_MODEL") or "grok-4"
    if not key:
        return Hop(glimpse=g, depth=d, hopped=False, reply=None)
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Greet with a glimpse, then serve depth.\n" + g.wire()},
                {"role": "user", "content": d.wire()},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        reply = payload["choices"][0]["message"]["content"]
        return Hop(glimpse=g, depth=d, hopped=True, reply=reply)
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError, TimeoutError) as e:
        return Hop(glimpse=g, depth=d, hopped=False, reply=None, error=str(e))
