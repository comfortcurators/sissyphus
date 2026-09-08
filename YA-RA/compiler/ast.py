from __future__ import annotations

from dataclasses import dataclass, field


RV = "rv0.1.0"


@dataclass
class Check:
    kind: str
    args: list[str]
    amp: complex = 1 + 0j


@dataclass
class Door:
    intent: str
    pattern: str
    signer: str
    timestamp: str
    rv: str = RV
    measure: str = "all"
    zero: bool = False
    glimpse: bool = False
    checks: list[Check] = field(default_factory=list)
    source: str = ""

    @property
    def name(self) -> str:
        return "YA|RA"
