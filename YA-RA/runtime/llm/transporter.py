"""YA|RA LLM transporter. Glimpse first. Depth second."""

from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass
class Frame:
    rv: str
    phase: str
    intent: str
    pattern: str
    signed: str

    def wire(self) -> str:
        return json.dumps(
            {
                "language": "YA|RA",
                "rv": self.rv,
                "phase": self.phase,
                "transporter": {
                    "intent": self.intent,
                    "pattern": self.pattern,
                    "signed": self.signed,
                },
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_wire(s: str) -> "Frame":
        o = json.loads(s)
        t = o["transporter"]
        return Frame(o["rv"], o["phase"], t["intent"], t["pattern"], t["signed"])
