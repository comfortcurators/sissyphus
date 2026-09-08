"""00 → two patterns. One becomes itself through two."""

from __future__ import annotations

from .ast import Door


def weave(door: Door) -> tuple[Door, Door]:
    left = Door(
        intent=door.intent,
        pattern="pattern-1 of " + door.pattern,
        signer=door.signer,
        timestamp=door.timestamp,
        rv=door.rv,
        measure=door.measure,
        zero=False,
        glimpse=True,
        checks=list(door.checks),
        source=door.source,
    )
    right = Door(
        intent=door.intent,
        pattern="pattern-2 of " + door.pattern,
        signer=door.signer,
        timestamp=door.timestamp,
        rv=door.rv,
        measure=door.measure,
        zero=False,
        glimpse=False,
        checks=list(door.checks),
        source=door.source,
    )
    return left, right
