"""YA|RA LLM transporter. Glimpse first. Depth second."""

from __future__ import annotations

from pathlib import Path
import sys

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ya_ra.llm import Frame, Hop, frames_for, hop

__all__ = ["Frame", "Hop", "frames_for", "hop"]
