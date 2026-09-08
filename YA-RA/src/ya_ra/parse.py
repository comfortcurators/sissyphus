from __future__ import annotations

import re

from .ast import CHECK_KINDS, Check, Door, Envelope, RV
from .types import TypeError_, typecheck


class ParseError(Exception):
    pass


_INTENT = re.compile(r"^Intent\s*:\s*(.*)$")
_PATTERN = re.compile(r"^Pattern\s*:\s*(.*)$")
_SIGNED = re.compile(r"^Signed\.\s*(.+?)\s*/\s*(.+)$")
_CHECK = re.compile(r"^(?:⊦|check)\s+(\S+)(?:\s+(.*))?$")
_RV = re.compile(r"^rv\s*(\d+(?:\.\d+){0,2})$", re.I)
_MEASURE = re.compile(r"^measure\s+(all|any)$", re.I)
_USE = re.compile(r"^use\s+(\S+)$", re.I)
_AMP = re.compile(r"^(.*?)\s+amp\s+(\S+)\s*$")


def parse(src: str, source: str = "") -> Door:
    lines = src.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0

    def skip() -> None:
        nonlocal i
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
            i += 1

    skip()
    rv = RV
    if i < len(lines) and _RV.match(lines[i].strip()):
        rv = "rv" + _RV.match(lines[i].strip()).group(1)
        i += 1
        skip()
    if i + 1 >= len(lines):
        raise ParseError("YA|RA is Intent | Pattern")

    im = _INTENT.match(lines[i].strip())
    pm = _PATTERN.match(lines[i + 1].strip())
    if not (im and pm):
        raise ParseError("YA|RA spelling is Intent | Pattern")

    env = Envelope()
    body_from = i + 2
    if body_from < len(lines):
        sm = _SIGNED.match(lines[body_from].strip())
        if sm:
            env = Envelope(
                kind="declared",
                actor=sm.group(1).strip(),
                timestamp=sm.group(2).strip(),
                note="declared Signed line is provenance, not a language constituent",
            )
            body_from = body_from + 1

    door = Door(
        intent=im.group(1).strip(),
        pattern=pm.group(1).strip(),
        envelope=env,
        rv=rv,
        source=source,
    )
    if not door.intent or not door.pattern:
        raise ParseError("empty field")

    for n, raw in enumerate(lines[body_from:], start=body_from + 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if _SIGNED.match(s):
            raise ParseError(f"line {n}: Signed belongs in the envelope, once, after Pattern")
        if s in {"00", "0"}:
            door.zero = True
            continue
        if s.lower() == "glimpse":
            door.glimpse = True
            continue
        if s.lower() == "cut":
            door.cut = True
            continue
        if _RV.match(s):
            door.rv = "rv" + _RV.match(s).group(1)
            continue
        mm = _MEASURE.match(s)
        if mm:
            door.measure = mm.group(1).lower()
            continue
        um = _USE.match(s)
        if um:
            door.checks.append(Check(kind="use", args=[um.group(1)]))
            continue
        cm = _CHECK.match(s)
        if not cm:
            raise ParseError(f"line {n}: {s!r}")
        kind, rest = cm.group(1), (cm.group(2) or "").strip()
        amp = 1 + 0j
        am = _AMP.match(rest)
        if am:
            rest = am.group(1).strip()
            try:
                amp = complex(am.group(2).replace("i", "j"))
            except ValueError as e:
                raise ParseError(f"line {n}: bad amp") from e
        if kind not in CHECK_KINDS:
            raise ParseError(f"line {n}: unknown check {kind!r}")
        args = _split_args(kind, rest, n)
        door.checks.append(Check(kind=kind, args=args, amp=amp))

    try:
        typecheck(door)
    except TypeError_ as e:
        raise ParseError(str(e)) from e
    return door


def _split_args(kind: str, rest: str, n: int) -> list[str]:
    if kind == "words":
        m = re.match(r"^(intent|pattern)\s*<=\s*(\d+)$", rest)
        if not m:
            raise ParseError("words FIELD <= N")
        return [m.group(1), m.group(2)]
    if kind in {"exists", "run", "use"}:
        if not rest:
            raise ParseError(f"line {n}: {kind} needs an argument")
        return [rest]
    if kind in {"contains", "eq"}:
        m = re.match(r'^(\S+)\s+("(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|\S+)$', rest)
        if not m:
            raise ParseError(f"line {n}: {kind} PATH STRING")
        return [m.group(1), _unquote(m.group(2))]
    return [rest] if rest else []


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return bytes(s[1:-1], "utf-8").decode("unicode_escape")
    return s
