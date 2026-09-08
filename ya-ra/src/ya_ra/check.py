from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .parse import Door


@dataclass
class CheckResult:
    ok: bool
    errors: list[str]


def _words(s: str) -> int:
    return len(s.split())


def check(door: Door, root: Path | None = None, max_words: int = 17) -> CheckResult:
    root = Path(root or ".")
    errors: list[str] = []

    iw, pw = _words(door.intent), _words(door.pattern)
    if iw > max_words:
        errors.append(f"Intent is {iw} words (max {max_words})")
    if pw > max_words:
        errors.append(f"Pattern is {pw} words (max {max_words})")

    for c in door.checks:
        if c.kind == "exists":
            p = root / c.args[0]
            if not p.exists():
                errors.append(f"missing {c.args[0]}")
        elif c.kind == "words":
            field, n = c.args[0], int(c.args[1])
            text = door.intent if field == "intent" else door.pattern
            got = _words(text)
            if got > n:
                errors.append(f"{field} is {got} words (max {n})")
        elif c.kind == "run":
            r = subprocess.run(c.args[0], shell=True, cwd=root, capture_output=True, text=True)
            if r.returncode != 0:
                tail = (r.stderr or r.stdout or "").strip()[:200]
                errors.append(f"run failed ({r.returncode}): {c.args[0]}" + (f" — {tail}" if tail else ""))
        elif c.kind == "contains":
            p = root / c.args[0]
            if not p.is_file():
                errors.append(f"missing {c.args[0]}")
            elif c.args[1] not in p.read_text(encoding="utf-8", errors="replace"):
                errors.append(f"{c.args[0]} does not contain {c.args[1]!r}")
        elif c.kind == "eq":
            p = root / c.args[0]
            if not p.is_file():
                errors.append(f"missing {c.args[0]}")
            elif p.read_text(encoding="utf-8", errors="replace") != c.args[1]:
                errors.append(f"{c.args[0]} != {c.args[1]!r}")
    return CheckResult(ok=not errors, errors=errors)
