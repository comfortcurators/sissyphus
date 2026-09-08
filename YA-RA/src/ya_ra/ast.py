from __future__ import annotations

from dataclasses import dataclass, field


RV = "rv0.2.0"

# kinds the type system admits. unknown kinds are a type error.
CHECK_KINDS = ("words", "exists", "run", "contains", "eq", "use")


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
    used: list[Door] = field(default_factory=list)

    @property
    def name(self) -> str:
        return "YA|RA"
