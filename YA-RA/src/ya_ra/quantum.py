"""Hilbert space ℂ^{2^n}. Each check is a qubit. Born rule is |⟨x|ψ⟩|²."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


def _norm2(amps: list[complex]) -> float:
    return sum((a.conjugate() * a).real for a in amps)


def product_state(amps: list[complex]) -> list[complex]:
    """Each qubit k is (|0⟩ + a_k|1⟩) / √(1+|a_k|²). Tensor them. Empty → |0⟩."""
    n = len(amps)
    if n == 0:
        return [1 + 0j]
    dim = 1 << n
    psi = [0j] * dim
    local = []
    for a in amps:
        nrm = math.sqrt(1.0 + (a.conjugate() * a).real)
        local.append((1 / nrm, a / nrm))
    for idx in range(dim):
        amp = 1 + 0j
        for k in range(n):
            a0, a1 = local[k]
            amp *= a1 if (idx >> k) & 1 else a0
        psi[idx] = amp
    return psi


def born_prob(psi: list[complex], idx: int) -> float:
    if idx < 0 or idx >= len(psi):
        return 0.0
    a = psi[idx]
    return (a.conjugate() * a).real


def bits_to_index(bits: list[bool]) -> int:
    idx = 0
    for k, b in enumerate(bits):
        if b:
            idx |= 1 << k
    return idx


def psi_and_born(amps: list[complex], bits: list[bool]) -> tuple[list[complex], float]:
    """Prepare the product state, return it and Born probability of the observed bits."""
    psi = product_state(amps)
    if not bits:
        return psi, 1.0
    return psi, born_prob(psi, bits_to_index(bits))


def collapse(psi: list[complex], bits: list[bool]) -> list[complex]:
    idx = bits_to_index(bits)
    out = [0j] * len(psi)
    if 0 <= idx < len(psi):
        out[idx] = psi[idx]
    n2 = _norm2(out)
    if n2 <= 0:
        return out
    s = math.sqrt(n2)
    return [a / s for a in out]


def sample(psi: list[complex], rng: random.Random | None = None) -> list[bool]:
    rng = rng or random.Random()
    n = 0
    dim = len(psi)
    while (1 << n) < dim:
        n += 1
    r = rng.random()
    acc = 0.0
    chosen = dim - 1
    for i, a in enumerate(psi):
        acc += (a.conjugate() * a).real
        if r <= acc:
            chosen = i
            break
    return [bool((chosen >> k) & 1) for k in range(n)]


@dataclass
class Hilbert:
    amps: list[complex]

    @classmethod
    def from_checks(cls, check_amps: list[complex]) -> "Hilbert":
        return cls(product_state(check_amps))

    def norm2(self) -> float:
        return _norm2(self.amps)

    def born(self, bits: list[bool]) -> float:
        return born_prob(self.amps, bits_to_index(bits))

    def collapse(self, bits: list[bool]) -> "Hilbert":
        return Hilbert(collapse(self.amps, bits))
