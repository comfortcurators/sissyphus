"""Filesystem observations stay inside the declared root."""

from __future__ import annotations

from pathlib import Path


class PathEscape(Exception):
    """A path left the measure root. Distinct from a failed exists/contains/eq."""


def confined(root: Path, rel: str) -> Path:
    if rel is None or not str(rel).strip():
        raise PathEscape("empty path")
    raw = str(rel)
    if raw.startswith("~") or raw.startswith("/"):
        raise PathEscape(raw)
    if len(raw) >= 2 and raw[1] == ":":
        raise PathEscape(raw)
    p = Path(raw)
    if p.is_absolute():
        raise PathEscape(raw)
    if ".." in p.parts:
        raise PathEscape(raw)
    root_r = Path(root).resolve()
    cand = (root_r / p).resolve()
    try:
        cand.relative_to(root_r)
    except ValueError as e:
        raise PathEscape(raw) from e
    return cand
