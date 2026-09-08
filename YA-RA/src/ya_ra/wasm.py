"""WASM surface. Words only. use/exists/run refused at emit."""

from __future__ import annotations

from .ast import Door


def emit_wasm(door: Door) -> str:
    from .emit import _c_str, _require

    _require("wasm", door)

    def wc(s: str) -> int:
        return len(s.split())

    iw, pw = wc(door.intent), wc(door.pattern)
    limits = {"intent": 17, "pattern": 17}
    for c in door.checks:
        if c.kind == "words" and len(c.args) >= 2:
            limits[c.args[0]] = int(c.args[1])
    ok = iw <= limits.get("intent", 17) and pw <= limits.get("pattern", 17)
    result = 0 if ok else 1
    return (
        f";; YA|RA {door.rv} — wasm. Words only.\n"
        f";; Intent : {_c_str(door.intent)}\n"
        f";; Pattern: {_c_str(door.pattern)}\n"
        "(module\n"
        "  (memory (export \"memory\") 1)\n"
        "  (func $measure (export \"measure\") (result i32)\n"
        f"    i32.const {result})\n"
        "  (func $intent_words (export \"intent_words\") (result i32)\n"
        f"    i32.const {iw})\n"
        "  (func $pattern_words (export \"pattern_words\") (result i32)\n"
        f"    i32.const {pw})\n"
        ")\n"
    )
