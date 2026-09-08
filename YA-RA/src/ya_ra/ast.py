from __future__ import annotations

from dataclasses import dataclass, field


RV = "rv0.3"

CHECK_KINDS = ("words", "exists", "run", "contains", "eq", "use")
ENVELOPE_KINDS = ("none", "declared", "git-author", "mtime")


@dataclass
class Check:
    kind: str
    args: list[str]
    amp: complex = 1 + 0j


@dataclass
class Envelope:
    """Organisation provenance around an expression. Not part of YA|RA."""

    kind: str = "none"
    actor: str = ""
    timestamp: str = ""
    note: str = ""

    @property
    def present(self) -> bool:
        return self.kind != "none" and bool(self.actor)


@dataclass
class Door:
    intent: str
    pattern: str
    envelope: Envelope = field(default_factory=Envelope)
    rv: str = RV
    measure: str = "all"
    zero: bool = False
    glimpse: bool = False
    cut: bool = False
    universe: bool = False
    cura: bool = False
    checks: list[Check] = field(default_factory=list)
    source: str = ""
    used: list[Door] = field(default_factory=list)

    @property
    def name(self) -> str:
        return "YA|RA"

    @property
    def signer(self) -> str:
        return self.envelope.actor

    @property
    def timestamp(self) -> str:
        return self.envelope.timestamp
