from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .ast import Check, Door
from .parse import ParseError, parse
from .paths import PathEscape, confined
from .quantum import psi_and_born
from .toe import Cut, project as toe_project


class RunRefused(Exception):
    """run requires an explicit execution capability."""


@dataclass
class Shot:
    ok: bool
    detail: str
    amp: complex
    kind: str = ""
    status: str = "fail"


@dataclass
class Outcome:
    ok: bool
    shots: list[Shot]
    psi: list[complex]
    born: float
    z: complex
    errors: list[str] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    missing_provenance: bool = False
    cut: Cut | None = None
    what_is: str = ""
    what_became: str = ""
    aforementioned: str = ""


def _words(s: str) -> int:
    return len(s.split())


def measure(
    door: Door,
    root: Path | None = None,
    _stack: tuple[str, ...] = (),
    *,
    allow_run: bool = False,
    require_provenance: bool = False,
    action_is_door: bool = False,
) -> Outcome:
    root = Path(root or ".").resolve()
    shots: list[Shot] = []
    errors: list[str] = []
    refusals: list[str] = []

    iw, pw = _words(door.intent), _words(door.pattern)
    if iw > 17:
        errors.append(f"intent {iw}>17")
    if pw > 17:
        errors.append(f"pattern {pw}>17")

    missing_prov = not door.envelope.present
    if require_provenance and missing_prov:
        refusals.append("missing provenance")

    for c in door.checks:
        shots.append(_run_one(door, c, root, _stack, allow_run=allow_run, require_provenance=require_provenance))

    for s in shots:
        if s.status == "refuse":
            refusals.append(s.detail)

    if door.measure == "any":
        checks_ok = (not shots) or any(s.status == "pass" for s in shots)
        if not checks_ok:
            errors.extend(s.detail for s in shots if s.status == "fail")
    else:
        checks_ok = all(s.status == "pass" for s in shots) if shots else True
        errors.extend(s.detail for s in shots if s.status == "fail")

    psi, born_p = psi_and_born([s.amp for s in shots], [s.status == "pass" for s in shots])
    cut = toe_project(door, [s.amp for s in shots], [s.status == "pass" for s in shots], action_is_door=action_is_door)
    z = cut.z
    if cut.refused:
        refusals.append(cut.reason)
    ok = checks_ok and not errors and not refusals
    what_is, what_became, aforementioned = _plane(door, root)
    if ok and (door.cura or door.universe) and aforementioned:
        (root / "aforementioned.YA-RA").write_text(
            "Intent : What is was seen. Change already moved.\n"
            "Pattern: weaved within aforementioned.\n",
            encoding="utf-8",
        )
    return Outcome(
        ok=ok,
        shots=shots,
        psi=psi,
        born=born_p,
        z=z,
        errors=errors,
        refusals=refusals,
        missing_provenance=missing_prov,
        cut=cut,
        what_is=what_is,
        what_became=what_became,
        aforementioned=aforementioned,
    )


def _run_one(
    door: Door,
    c: Check,
    root: Path,
    stack: tuple[str, ...],
    *,
    allow_run: bool,
    require_provenance: bool,
) -> Shot:
    if c.kind == "words":
        text = door.intent if c.args[0] == "intent" else door.pattern
        got = _words(text)
        n = int(c.args[1])
        ok = got <= n
        return Shot(ok, "ok" if ok else f"{c.args[0]} {got}>{n}", c.amp, c.kind, "pass" if ok else "fail")
    if c.kind == "exists":
        try:
            p = confined(root, c.args[0])
        except PathEscape:
            return Shot(False, f"path refused {c.args[0]}", c.amp, c.kind, "refuse")
        ok = p.exists()
        return Shot(ok, "ok" if ok else f"missing {c.args[0]}", c.amp, c.kind, "pass" if ok else "fail")
    if c.kind == "run":
        if not allow_run:
            return Shot(False, "run refused: need --allow-run", c.amp, c.kind, "refuse")
        r = subprocess.run(c.args[0], shell=True, cwd=root, capture_output=True)
        ok = r.returncode == 0
        return Shot(ok, "ok" if ok else "run failed", c.amp, c.kind, "pass" if ok else "fail")
    if c.kind == "contains":
        try:
            p = confined(root, c.args[0])
        except PathEscape:
            return Shot(False, f"path refused {c.args[0]}", c.amp, c.kind, "refuse")
        if not p.is_file():
            return Shot(False, f"missing {c.args[0]}", c.amp, c.kind, "fail")
        ok = c.args[1] in p.read_text(encoding="utf-8", errors="replace")
        return Shot(ok, "ok" if ok else f"{c.args[0]} does not contain {c.args[1]!r}", c.amp, c.kind, "pass" if ok else "fail")
    if c.kind == "eq":
        try:
            p = confined(root, c.args[0])
        except PathEscape:
            return Shot(False, f"path refused {c.args[0]}", c.amp, c.kind, "refuse")
        if not p.is_file():
            return Shot(False, f"missing {c.args[0]}", c.amp, c.kind, "fail")
        ok = p.read_text(encoding="utf-8", errors="replace") == c.args[1]
        return Shot(ok, "ok" if ok else f"{c.args[0]} != {c.args[1]!r}", c.amp, c.kind, "pass" if ok else "fail")
    if c.kind == "use":
        try:
            path = confined(root, c.args[0])
        except PathEscape:
            return Shot(False, f"path refused {c.args[0]}", c.amp, c.kind, "refuse")
        key = str(path)
        if key in stack:
            return Shot(False, f"circular use {c.args[0]}", c.amp, c.kind, "fail")
        if not path.is_file():
            return Shot(False, f"missing module {c.args[0]}", c.amp, c.kind, "fail")
        try:
            child = parse(path.read_text(encoding="utf-8"), source=str(path))
        except (ParseError, OSError) as e:
            return Shot(False, f"use {c.args[0]}: {e}", c.amp, c.kind, "fail")
        out = measure(
            child,
            root=path.parent,
            _stack=stack + (key,),
            allow_run=allow_run,
            require_provenance=require_provenance,
        )
        if out.refusals:
            return Shot(False, f"use {c.args[0]} refused", c.amp, c.kind, "refuse")
        return Shot(out.ok, "ok" if out.ok else f"use {c.args[0]} contradicted", c.amp, c.kind, "pass" if out.ok else "fail")
    return Shot(False, f"unknown {c.kind}", c.amp, c.kind, "fail")


def _plane(door: Door, root: Path) -> tuple[str, str, str]:
    used: list[Door] = []
    for c in door.checks:
        if c.kind != "use":
            continue
        try:
            path = confined(root, c.args[0])
        except PathEscape:
            continue
        if not path.is_file():
            continue
        try:
            used.append(parse(path.read_text(encoding="utf-8"), source=str(path)))
        except (ParseError, OSError):
            continue
    door.used = used
    if not used:
        return door.intent, "", ""

    def name(d: Door) -> str:
        return Path(d.source).name.lower()

    what_is = next((d for d in used if "what-is" in name(d)), used[0])
    what_became = next((d for d in used if "became" in name(d)), used[-1])
    return what_is.intent, what_became.intent, f"{what_is.intent} | {what_became.intent}"
