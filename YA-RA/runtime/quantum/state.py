"""YA|RA quantum measure. Modes of Pattern are basis states."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Psi:
    amps: list[complex]

    def norm2(self) -> float:
        return sum((a.conjugate() * a).real for a in self.amps)

    def collapse(self, bits: list[bool]) -> "Psi":
        return Psi([a if keep else 0j for a, keep in zip(self.amps, bits)])
