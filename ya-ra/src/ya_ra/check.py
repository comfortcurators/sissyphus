from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .parse import Check, Door


@dataclass
class Shot:
    check: Check
    ok: bool
    detail: str


@dataclass
class CheckResult:
    ok: bool
    errors: list[str]
    shots: list[Shot] = field(default_factory=list)
    measure: str = "all"


def _words(s: str) -> int:
    return len(s.split())


def _run_one(door: Door, c: Check, root: Path) -> Shot:
    if c.kind == "exists":
        ok = (root / c.args[0]).exists()
        return Shot(c, ok, "ok" if ok else f"missing {c.args[0]}")
    if c.kind == "words":
        field, n = c.args[0], int(c.args[1])
        text = door.intent if field == "intent" else door.pattern
        got = _words(text)
        ok = got <= n
        return Shot(c, ok, "ok" if ok else f"{field} is {got} words (max {n})")
    if c.kind == "run":
        r = subprocess.run(c.args[0], shell=True, cwd=root, capture_output=True, text=True)
        ok = r.returncode == 0
        tail = (r.stderr or r.stdout or "").strip()[:200]
        return Shot(c, ok, "ok" if ok else f"run failed ({r.returncode}): {c.args[0]}" + (f" — {tail}" if tail else ""))
    if c.kind == "contains":
        p = root / c.args[0]
        if not p.is_file():
            return Shot(c, False, f"missing {c.args[0]}")
        ok = c.args[1] in p.read_text(encoding="utf-8", errors="replace")
        return Shot(c, ok, "ok" if ok else f"{c.args[0]} does not contain {c.args[1]!r}")
    if c.kind == "eq":
        p = root / c.args[0]
        if not p.is_file():
            return Shot(c, False, f"missing {c.args[0]}")
        ok = p.read_text(encoding="utf-8", errors="replace") == c.args[1]
        return Shot(c, ok, "ok" if ok else f"{c.args[0]} != {c.args[1]!r}")
    return Shot(c, False, f"unknown check {c.kind}")


def check(door: Door, root: Path | None = None, max_words: int = 17) -> CheckResult:
    root = Path(root or ".")
    shots: list[Shot] = []
    errors: list[str] = []

    iw, pw = _words(door.intent), _words(door.pattern)
    if iw > max_words:
        errors.append(f"Intent is {iw} words (max {max_words})")
    if pw > max_words:
        errors.append(f"Pattern is {pw} words (max {max_words})")

    for c in door.checks:
        shots.append(_run_one(door, c, root))

    if door.measure == "any":
        if door.checks and not any(s.ok for s in shots):
            errors.extend(s.detail for s in shots if not s.ok)
            errors.append("measure any: every mode failed")
    else:
        errors.extend(s.detail for s in shots if not s.ok)

    return CheckResult(ok=not errors, errors=errors, shots=shots, measure=door.measure)
