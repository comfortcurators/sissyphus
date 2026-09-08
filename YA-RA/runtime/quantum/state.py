"""YA|RA Hilbert space. ℂ^{2^n}. Born rule is |⟨x|ψ⟩|²."""

from __future__ import annotations

from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ya_ra.quantum import Hilbert, born_prob, collapse, product_state, psi_and_born, sample

__all__ = ["Hilbert", "born_prob", "collapse", "product_state", "psi_and_born", "sample"]
