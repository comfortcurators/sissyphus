from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import RV
from .check import check
from .emit import emit
from .parse import ParseError, parse


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ya-ra", description="YA|RA rv0.1.0 — Intent | Pattern | Signed")
    p.add_argument("--rv", action="version", version=RV)
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="measure the door")
    pc.add_argument("file")
    pc.add_argument("--root", default=".")

    pe = sub.add_parser("emit", help="lower Pattern checks to python|rust|c")
    pe.add_argument("file")
    pe.add_argument("--lang", required=True, choices=["python", "rust", "c"])
    pe.add_argument("-o", "--out")

    pp = sub.add_parser("parse", help="print the door")
    pp.add_argument("file")

    args = p.parse_args(argv)
    src = Path(args.file).read_text(encoding="utf-8")
    try:
        door = parse(src, source=args.file)
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 2

    if args.cmd == "parse":
        print(door.rv)
        print(f"measure {door.measure}")
        print(f"Intent : {door.intent}")
        print(f"Pattern: {door.pattern}")
        print(f"Signed. {door.signer} / {door.timestamp}")
        for c in door.checks:
            amp = f" amp {c.amp}" if c.amp is not None else ""
            print(f"⊦ {c.kind} {' '.join(c.args)}{amp}")
        return 0

    if args.cmd == "check":
        result = check(door, root=Path(args.root))
        if result.ok:
            print(f"{door.rv} measure {result.measure} ok")
            return 0
        for err in result.errors:
            print(f"contradicted: {err}", file=sys.stderr)
        return 1

    code = emit(door, args.lang)
    if args.out:
        Path(args.out).write_text(code, encoding="utf-8")
    else:
        sys.stdout.write(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
