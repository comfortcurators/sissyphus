from __future__ import annotations

import re

from .ast import Check, Door, RV


class ParseError(Exception):
    pass


_INTENT = re.compile(r"^Intent\s*:\s*(.*)$")
_PATTERN = re.compile(r"^Pattern\s*:\s*(.*)$")
_SIGNED = re.compile(r"^Signed\.\s*(.+?)\s*/\s*(.+)$")
_CHECK = re.compile(r"^(?:⊦|check)\s+(\S+)(?:\s+(.*))?$")
_RV = re.compile(r"^rv\s*(\d+(?:\.\d+){0,2})$", re.I)
_MEASURE = re.compile(r"^measure\s+(all|any)$", re.I)
_AMP = re.compile(r"^(.*?)\s+amp\s+(\S+)\s*$")


def parse(src: str, source: str = "") -> Door:
    lines = src.replace("\r\n", "\n").split("\n")
    i = 0

    def skip():
        nonlocal i
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
            i += 1

    skip()
    rv = RV
    if i < len(lines) and _RV.match(lines[i].strip()):
        rv = "rv" + _RV.match(lines[i].strip()).group(1)
        i += 1
        skip()
    if i + 2 >= len(lines):
        raise ParseError("YA|RA door needs Intent, Pattern, Signed")

    im, pm, sm = _INTENT.match(lines[i].strip()), _PATTERN.match(lines[i + 1].strip()), _SIGNED.match(lines[i + 2].strip())
    if not (im and pm and sm):
        raise ParseError("YA|RA door spelling is Intent / Pattern / Signed.")

    door = Door(
        intent=im.group(1).strip(),
        pattern=pm.group(1).strip(),
        signer=sm.group(1).strip(),
        timestamp=sm.group(2).strip(),
        rv=rv,
        source=source,
    )
    if not door.intent or not door.pattern or not door.signer:
        raise ParseError("empty field")

    for n, raw in enumerate(lines[i + 3 :], start=i + 4):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if s in {"00", "0"}:
            door.zero = True
            continue
        if s.lower() == "glimpse":
            door.glimpse = True
            continue
        if _RV.match(s):
            door.rv = "rv" + _RV.match(s).group(1)
            continue
        mm = _MEASURE.match(s)
        if mm:
            door.measure = mm.group(1).lower()
            continue
        cm = _CHECK.match(s)
        if not cm:
            raise ParseError(f"line {n}: {s!r}")
        kind, rest = cm.group(1), (cm.group(2) or "").strip()
        amp = 1 + 0j
        am = _AMP.match(rest)
        if am:
            rest = am.group(1).strip()
            amp = complex(am.group(2).replace("i", "j"))
        if kind == "words":
            m = re.match(r"^(intent|pattern)\s*<=\s*(\d+)$", rest)
            if not m:
                raise ParseError("words FIELD <= N")
            args = [m.group(1), m.group(2)]
        else:
            args = [rest] if rest else []
        door.checks.append(Check(kind=kind, args=args, amp=amp))
    return door
