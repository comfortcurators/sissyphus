"""A program is a folder of doors with main.YA-RA at the root."""

from __future__ import annotations

from pathlib import Path

from .ast import Door
from .parse import parse
from .root import RootError


def from_program(root: Path) -> Door:
    root = Path(root).resolve()
    main = root / "main.YA-RA"
    if not main.is_file():
        raise RootError(f"YA|RA program needs main.YA-RA at {root}")
    door = parse(main.read_text(encoding="utf-8"), source=str(main))
    door.source = str(root)
    return door
