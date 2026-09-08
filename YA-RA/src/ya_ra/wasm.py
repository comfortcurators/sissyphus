"""WASM surface. Words execute. use/cura bake the plane at emit. exists/run refuse."""

from __future__ import annotations

from .ast import Door


def emit_wasm(door: Door) -> str:
    from .emit import UnsupportedSemantic, _c_str, _require

    kinds = {c.kind for c in door.checks}
    if kinds & {"exists", "contains", "eq", "run"}:
        _require("wasm", door)

    def wc(s: str) -> int:
        return len(s.split())

    iw, pw = wc(door.intent), wc(door.pattern)
    ok = iw <= 17 and pw <= 17
    used = list(getattr(door, "used", []) or [])
    needs_use = "use" in kinds or door.cura or door.universe
    if needs_use and not used:
        raise UnsupportedSemantic("wasm cannot preserve use")

    what_is = used[0].intent if used else door.intent
    what_became = used[-1].intent if len(used) > 1 else (used[0].intent if used else "")
    for d in used:
        name = (d.source or "").lower()
        if "what-is" in name:
            what_is = d.intent
        if "became" in name:
            what_became = d.intent

    cura = 1 if (door.cura or door.universe or used) else 0
    result = 0 if ok else 1
    return (
        f";; YA|RA {door.rv} — wasm.\n"
        f";; Intent : {_c_str(door.intent)}\n"
        f";; Pattern: {_c_str(door.pattern)}\n"
        f";; what is : {_c_str(what_is)}\n"
        f";; what became: {_c_str(what_became)}\n"
        "(module\n"
        "  (memory (export \"memory\") 1)\n"
        "  (func $measure (export \"measure\") (result i32)\n"
        f"    i32.const {result})\n"
        "  (func $cura (export \"cura\") (result i32)\n"
        f"    i32.const {cura})\n"
        "  (func $intent_words (export \"intent_words\") (result i32)\n"
        f"    i32.const {iw})\n"
        "  (func $pattern_words (export \"pattern_words\") (result i32)\n"
        f"    i32.const {pw})\n"
        ")\n"
    )
