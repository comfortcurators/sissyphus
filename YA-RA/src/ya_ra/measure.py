from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .ast import Door
from .parse import ParseError, parse
from .quantum import psi_and_born


@dataclass
class Shot:
    ok: bool
    detail: str
    amp: complex
    kind: str = ""


@dataclass
class Outcome:
    ok: bool
    shots: list[Shot]
    psi: list[complex]
    born: float
    z: complex
    errors: list[str] = field(default_factory=list)


def _words(s: str) -> int:
    return len(s.split())


def measure(door: Door, root: Path | None = None, _stack: tuple[str, ...] = ()) -> Outcome:
    root = Path(root or ".").resolve()
    shots: list[Shot] = []
    errors: list[str] = []

    iw, pw = _words(door.intent), _words(door.pattern)
    if iw > 17:
        errors.append(f"intent {iw}>17")
    if pw > 17:
        errors.append(f"pattern {pw}>17")
    if not door.signer:
        errors.append("unsigned")

    for c in door.checks:
        shots.append(_run_one(door, c, root, _stack))

    if door.measure == "any":
        checks_ok = (not shots) or any(s.ok for s in shots)
        if not checks_ok:
            errors.extend(s.detail for s in shots if not s.ok)
    else:
        checks_ok = all(s.ok for s in shots) if shots else True
        errors.extend(s.detail for s in shots if not s.ok)

    psi, born_p = psi_and_born([s.amp for s in shots], [s.ok for s in shots])
    z = sum((s.amp if s.ok else 0j) for s in shots)
    ok = checks_ok and not errors
    return Outcome(ok=ok, shots=shots, psi=psi, born=born_p, z=z, errors=errors)


def _run_one(door: Door, c, root: Path, stack: tuple[str, ...]) -> Shot:
    if c.kind == "words":
        text = door.intent if c.args[0] == "intent" else door.pattern
        got = _words(text)
        n = int(c.args[1])
        ok = got <= n
        return Shot(ok, "ok" if ok else f"{c.args[0]} {got}>{n}", c.amp, c.kind)
    if c.kind == "exists":
        ok = (root / c.args[0]).exists()
        return Shot(ok, "ok" if ok else f"missing {c.args[0]}", c.amp, c.kind)
    if c.kind == "run":
        r = subprocess.run(c.args[0], shell=True, cwd=root, capture_output=True)
        return Shot(r.returncode == 0, "ok" if r.returncode == 0 else "run failed", c.amp, c.kind)
    if c.kind == "contains":
        p = root / c.args[0]
        if not p.is_file():
            return Shot(False, f"missing {c.args[0]}", c.amp, c.kind)
        ok = c.args[1] in p.read_text(encoding="utf-8", errors="replace")
        return Shot(ok, "ok" if ok else f"{c.args[0]} does not contain {c.args[1]!r}", c.amp, c.kind)
    if c.kind == "eq":
        p = root / c.args[0]
        if not p.is_file():
            return Shot(False, f"missing {c.args[0]}", c.amp, c.kind)
        ok = p.read_text(encoding="utf-8", errors="replace") == c.args[1]
        return Shot(ok, "ok" if ok else f"{c.args[0]} != {c.args[1]!r}", c.amp, c.kind)
    if c.kind == "use":
        path = (root / c.args[0]).resolve()
        key = str(path)
        if key in stack:
            return Shot(False, f"circular use {c.args[0]}", c.amp, c.kind)
        if not path.is_file():
            return Shot(False, f"missing module {c.args[0]}", c.amp, c.kind)
        try:
            child = parse(path.read_text(encoding="utf-8"), source=str(path))
        except (ParseError, OSError) as e:
            return Shot(False, f"use {c.args[0]}: {e}", c.amp, c.kind)
        out = measure(child, root=path.parent, _stack=stack + (key,))
        return Shot(out.ok, "ok" if out.ok else f"use {c.args[0]} contradicted", c.amp, c.kind)
    return Shot(False, f"unknown {c.kind}", c.amp, c.kind)
