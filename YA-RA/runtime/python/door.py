"""YA|RA Python runtime."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Door:
    intent: str
    pattern: str
    signer: str
    timestamp: str
    rv: str = "rv0.1.0"
    measure: str = "all"
    zero: bool = False
    glimpse: bool = False

    def ok(self) -> bool:
        if not (self.intent and self.pattern and self.signer):
            return False
        if len(self.intent.split()) > 17 or len(self.pattern.split()) > 17:
            return False
        return True
