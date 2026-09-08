"""00 → two modules. One becomes itself through two."""

from __future__ import annotations

from copy import deepcopy

from .ast import Door


def weave(door: Door) -> tuple[Door, Door]:
    left = deepcopy(door)
    right = deepcopy(door)
    left.zero = False
    right.zero = False
    left.glimpse = True
    right.glimpse = False
    left.source = (door.source or "door") + "#1"
    right.source = (door.source or "door") + "#2"
    # left greets (glimpse). right serves depth.
    return left, right
