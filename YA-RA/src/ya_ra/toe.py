"""The cut past the unsigned integral.

The slide writes Z = ∫ D(Fields) exp(iS). That number has no observer.
It cannot refuse. It is not a YA|RA expression.

YA|RA computes a different number:

    Z = Σ_k a_k [check_k passed]

Amplitudes do not decide whether a check passed. They weight the sum
after deterministic shots.

Refuse the slide (`action_is_door`). Do not refuse an unsigned sentence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ast import Door


@dataclass
class Cut:
    z: complex
    nterms: int
    refused: bool
    reason: str
    missing_provenance: bool
    action_is_door: bool

    @property
    def ok(self) -> bool:
        return not self.refused


def project(
    door: Door,
    amps: list[complex],
    passed: list[bool],
    *,
    action_is_door: bool = False,
) -> Cut:
    missing = not door.envelope.present
    n = len(amps)
    if action_is_door:
        return Cut(
            z=0j,
            nterms=n,
            refused=True,
            reason="unsigned action is not a door",
            missing_provenance=missing,
            action_is_door=True,
        )
    z = sum((a if ok else 0j) for a, ok in zip(amps, passed))
    return Cut(
        z=z,
        nterms=n,
        refused=False,
        reason="",
        missing_provenance=missing,
        action_is_door=False,
    )
