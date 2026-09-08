"""YA|RA type system. A door's type is Signed. Checks have kinds."""

from __future__ import annotations

from .ast import CHECK_KINDS, Check, Door


class TypeError_(Exception):
    pass


def typecheck(door: Door) -> Door:
    if not door.intent:
        raise TypeError_("Intent is empty")
    if not door.pattern:
        raise TypeError_("Pattern is empty")
    if not door.signer:
        raise TypeError_("Unsigned. A door's type is Signed.")
    if door.measure not in {"all", "any"}:
        raise TypeError_("measure is all|any")
    if not door.rv.startswith("rv"):
        raise TypeError_("version token is always rv")
    for i, c in enumerate(door.checks):
        _check_type(c, i)
    return door


def _check_type(c: Check, i: int) -> None:
    if c.kind not in CHECK_KINDS:
        raise TypeError_(f"check {i}: unknown kind {c.kind!r}")
    if not isinstance(c.amp, complex):
        raise TypeError_(f"check {i}: amp is complex")
    if c.kind == "words":
        if len(c.args) != 2 or c.args[0] not in {"intent", "pattern"}:
            raise TypeError_("words FIELD <= N")
        try:
            n = int(c.args[1])
        except ValueError as e:
            raise TypeError_("words N is int") from e
        if n < 0:
            raise TypeError_("words N >= 0")
    elif c.kind in {"exists", "run", "use"}:
        if len(c.args) != 1 or not c.args[0]:
            raise TypeError_(f"{c.kind} needs one argument")
    elif c.kind in {"contains", "eq"}:
        if len(c.args) != 2 or not c.args[0]:
            raise TypeError_(f"{c.kind} PATH STRING")
