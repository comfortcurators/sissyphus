from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ast import Door


@dataclass
class Shot:
    ok: bool
    detail: str
    amp: complex


@dataclass
class Outcome:
    ok: bool
    shots: list[Shot]
    psi: list[complex]


def _words(s: str) -> int:
    return len(s.split())


def measure(door: Door, root: Path | None = None) -> Outcome:
    root = Path(root or ".")
    shots: list[Shot] = []
    for c in door.checks:
        if c.kind == "words":
            text = door.intent if c.args[0] == "intent" else door.pattern
            got = _words(text)
            n = int(c.args[1])
            ok = got <= n
            shots.append(Shot(ok, "ok" if ok else f"{c.args[0]} {got}>{n}", c.amp))
        elif c.kind == "exists":
            ok = (root / c.args[0]).exists()
            shots.append(Shot(ok, "ok" if ok else f"missing {c.args[0]}", c.amp))
        elif c.kind == "run":
            import subprocess

            r = subprocess.run(c.args[0], shell=True, cwd=root, capture_output=True)
            shots.append(Shot(r.returncode == 0, "ok" if r.returncode == 0 else "run failed", c.amp))
        else:
            shots.append(Shot(False, f"unknown {c.kind}", c.amp))

    psi = [s.amp if s.ok else 0j for s in shots]
    if door.measure == "any":
        ok = (not shots) or any(s.ok for s in shots)
    else:
        ok = all(s.ok for s in shots) if shots else True
    if _words(door.intent) > 17 or _words(door.pattern) > 17:
        ok = False
    return Outcome(ok=ok, shots=shots, psi=psi)
