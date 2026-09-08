from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ast import RV
from .emit import TARGETS, emit
from .measure import measure
from .parse import ParseError, parse
from .weave import weave


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="YA|RA", description="YA|RA language rv0.1.0")
    p.add_argument("--rv", action="version", version=RV)
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("compile")
    pc.add_argument("file")
    pc.add_argument("--to", required=True, choices=sorted(set(TARGETS)))
    pc.add_argument("-o", "--out")

    pm = sub.add_parser("measure")
    pm.add_argument("file")
    pm.add_argument("--root", default=".")

    pp = sub.add_parser("parse")
    pp.add_argument("file")

    pw = sub.add_parser("weave")
    pw.add_argument("file")

    args = p.parse_args(argv)
    src = Path(args.file).read_text(encoding="utf-8")
    try:
        door = parse(src, source=args.file)
    except ParseError as e:
        print(f"YA|RA parse: {e}", file=sys.stderr)
        return 2

    if args.cmd == "parse":
        print("YA|RA", door.rv)
        print("Intent :", door.intent)
        print("Pattern:", door.pattern)
        print("Signed.", door.signer, "/", door.timestamp)
        print("00" if door.zero else "not-zero", "glimpse" if door.glimpse else "depth", "measure", door.measure)
        return 0

    if args.cmd == "weave":
        a, b = weave(door)
        print("0")
        print("  1", a.pattern)
        print("  2", b.pattern)
        return 0

    if args.cmd == "measure":
        out = measure(door, root=Path(args.root))
        if out.ok:
            print(f"YA|RA {door.rv} measured ok")
            return 0
        for s in out.shots:
            if not s.ok:
                print("contradicted:", s.detail, file=sys.stderr)
        return 1

    code = emit(door, args.to)
    if args.out:
        Path(args.out).write_text(code, encoding="utf-8")
    else:
        sys.stdout.write(code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
