from __future__ import annotations

import re
from dataclasses import dataclass, field


class ParseError(Exception):
    pass


@dataclass
class Check:
    kind: str
    args: list[str]
    raw: str
    amp: float | None = None


@dataclass
class Door:
    intent: str
    pattern: str
    signer: str
    timestamp: str
    rv: str = "rv0.1.0"
    measure: str = "all"
    checks: list[Check] = field(default_factory=list)
    source: str = ""


_INTENT = re.compile(r"^Intent\s*:\s*(.*)$")
_PATTERN = re.compile(r"^Pattern\s*:\s*(.*)$")
_SIGNED = re.compile(r"^Signed\.\s*(.+?)\s*/\s*(.+)$")
_CHECK = re.compile(r"^(?:⊦|check)\s+(\S+)(?:\s+(.*))?$")
_RV = re.compile(r"^rv\s*(\d+(?:\.\d+){0,2})$", re.I)
_MEASURE = re.compile(r"^measure\s+(all|any)$", re.I)
_AMP = re.compile(r"^(.*?)\s+amp\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*$")


def parse(src: str, source: str = "") -> Door:
    lines = src.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    i = 0
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
        i += 1
    rv = "rv0.1.0"
    if i < len(lines) and _RV.match(lines[i].strip()):
        rv = "rv" + _RV.match(lines[i].strip()).group(1)
        i += 1
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("#")):
            i += 1
    if i + 2 >= len(lines):
        raise ParseError("door needs Intent, Pattern, Signed")

    im = _INTENT.match(lines[i].strip())
    pm = _PATTERN.match(lines[i + 1].strip())
    sm = _SIGNED.match(lines[i + 2].strip())
    if not im:
        raise ParseError(f"line {i+1}: expected Intent : ...")
    if not pm:
        raise ParseError(f"line {i+2}: expected Pattern: ...")
    if not sm:
        raise ParseError(f"line {i+3}: expected Signed. name / timestamp")

    door = Door(
        intent=im.group(1).strip(),
        pattern=pm.group(1).strip(),
        signer=sm.group(1).strip(),
        timestamp=sm.group(2).strip(),
        rv=rv,
        source=source,
    )
    if not door.intent:
        raise ParseError("empty Intent")
    if not door.pattern:
        raise ParseError("empty Pattern")
    if not door.signer:
        raise ParseError("empty signer")

    for n, raw in enumerate(lines[i + 3 :], start=i + 4):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        rm = _RV.match(s)
        if rm:
            door.rv = "rv" + rm.group(1)
            continue
        mm = _MEASURE.match(s)
        if mm:
            door.measure = mm.group(1).lower()
            continue
        cm = _CHECK.match(s)
        if not cm:
            raise ParseError(f"line {n}: expected ⊦/check/measure, got {s!r}")
        kind = cm.group(1)
        rest = (cm.group(2) or "").strip()
        amp = None
        am = _AMP.match(rest)
        if am:
            rest, amp = am.group(1).strip(), float(am.group(2))
        if kind not in {"exists", "words", "run", "contains", "eq"}:
            raise ParseError(f"line {n}: unknown check {kind!r}")
        args = _split_args(kind, rest, n)
        door.checks.append(Check(kind=kind, args=args, raw=s, amp=amp))
    return door


def _split_args(kind: str, rest: str, n: int) -> list[str]:
    if kind == "exists":
        if not rest:
            raise ParseError(f"line {n}: exists needs a path")
        return [rest]
    if kind == "words":
        m = re.match(r"^(intent|pattern)\s*<=\s*(\d+)$", rest)
        if not m:
            raise ParseError(f"line {n}: words FIELD <= N")
        return [m.group(1), m.group(2)]
    if kind == "run":
        if not rest:
            raise ParseError(f"line {n}: run needs a command")
        return [rest]
    if kind in {"contains", "eq"}:
        m = re.match(r'^(\S+)\s+("(?:\\.|[^"])*"|\'(?:\\.|[^\'])*\'|\S+)$', rest)
        if not m:
            raise ParseError(f"line {n}: {kind} PATH STRING")
        return [m.group(1), _unquote(m.group(2))]
    return [rest]


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return bytes(s[1:-1], "utf-8").decode("unicode_escape")
    return s
