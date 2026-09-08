from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ast import RV
from .emit import TARGETS, UnsupportedSemantic, emit
from .llm import hop
from .measure import measure
from .parse import ParseError, parse
from .program import from_program
from .root import RootError, from_root
from .weave import weave


def _load(file: str | None, root: Path) -> object:
    if file:
        p = Path(file)
        if p.is_dir():
            if (p / "main.YA-RA").is_file():
                return from_program(p)
            return from_root(p)
        return parse(p.read_text(encoding="utf-8"), source=str(p))
    return from_root(root)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="YA|RA", description="YA|RA language rv0.3.0")
    p.add_argument("--rv", action="version", version=RV)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_src(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("file", nargs="?", help="expression file, or omit to assemble from --root")
        sp.add_argument("--root", default=".", help="measure root; also the five-file tree")

    pc = sub.add_parser("compile")
    add_src(pc)
    pc.add_argument("--to", required=True, choices=sorted(set(TARGETS)))
    pc.add_argument("-o", "--out")

    pm = sub.add_parser("measure")
    add_src(pm)
    pm.add_argument("--allow-run", action="store_true", help="permit run checks")
    pm.add_argument("--require-provenance", action="store_true", help="refuse unsigned expressions")
    pm.add_argument("--action", action="store_true", help="treat the input as the unsigned integral; the cut refuses")

    pp = sub.add_parser("parse")
    add_src(pp)

    pw = sub.add_parser("weave")
    add_src(pw)

    ph = sub.add_parser("hop")
    add_src(ph)

    args = p.parse_args(argv)
    root = Path(args.root)
    try:
        door = _load(args.file, root)
    except (ParseError, RootError, OSError) as e:
        print(f"YA|RA: {e}", file=sys.stderr)
        return 2

    if args.cmd == "parse":
        print("YA|RA", door.rv)
        print("Intent :", door.intent)
        print("Pattern:", door.pattern)
        print("envelope", door.envelope.kind, door.envelope.actor or "-", "/", door.envelope.timestamp or "-")
        print("00" if door.zero else "not-zero", "glimpse" if door.glimpse else "depth", "cut" if door.cut else "no-cut", "measure", door.measure)
        for c in door.checks:
            print(f"⊦ {c.kind} {' '.join(c.args)} amp {c.amp}")
        return 0

    if args.cmd == "weave":
        a, b = weave(door)
        print("0")
        print("  1", "glimpse", a.source)
        print("  2", "depth", b.source)
        return 0

    if args.cmd == "measure":
        out = measure(
            door,
            root=root,
            allow_run=args.allow_run,
            require_provenance=args.require_provenance,
            action_is_door=args.action,
        )
        if out.ok:
            print(f"YA|RA {door.rv} measured ok")
            print(f"born {out.born:.6f} (observational)")
            print(f"Z {out.z}")
            if out.aforementioned:
                print("what is :", out.what_is)
                print("what became:", out.what_became)
                print("aforementioned:", out.aforementioned)
            return 0
        for err in out.refusals:
            print("refused:", err, file=sys.stderr)
        for err in out.errors:
            print("contradicted:", err, file=sys.stderr)
        return 1

    if args.cmd == "hop":
        result = hop(door)
        sys.stdout.write(result.wire())
        return 0 if result.error is None else 1

    if args.to == "wasm":
        measure(door, root=root)
    try:
        code = emit(door, args.to)
    except UnsupportedSemantic as e:
        print(f"YA|RA unsupported-semantic: {e}", file=sys.stderr)
        return 3
    if args.out:
        Path(args.out).write_text(code, encoding="utf-8")
    else:
        sys.stdout.write(code)
    if args.to == "llm":
        json.loads(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
