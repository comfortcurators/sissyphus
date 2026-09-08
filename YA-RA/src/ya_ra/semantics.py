"""Canonical meanings. A backend preserves a cell or refuses it."""

from __future__ import annotations

CANONICAL = {
    "words": "count whitespace-separated tokens of intent or pattern; pass iff count <= N",
    "exists": "path, confined to measure root, names an existing filesystem object",
    "contains": "confined path is a file whose text contains the given string",
    "eq": "confined path is a file whose exact text equals the given string",
    "run": "execute the command in a shell at the measure root; pass iff exit 0. requires allow_run",
    "use": "confined path is a YA|RA expression; parse and measure it under the same policy; pass iff the child outcome is ok",
    "measure all": "every check must pass; one fail contradicts the Intent; a refusal also contradicts",
    "measure any": "one passing check keeps the Intent unless a refusal occurred",
}

# `weakened` is a real cell, distinct from `preserved` and from `unsupported`:
# the backend produces *a* result for the check, but not the canonical one,
# because it drops a guarantee the canonical semantics require. rv0.3 marked
# these `preserved`, which is exactly the silent weakening the conformance
# table exists to forbid: the C and C++ runtimes take no measure root and do
# raw access()/fopen(), so `exists`/`contains`/`eq` are unconfined, and they
# call system() with no capability gate, so `run` ignores allow_run.
WEAKENED_HOSTED = {
    "exists": "weakened: no root confinement",
    "contains": "weakened: no root confinement",
    "eq": "weakened: no root confinement",
    "run": "weakened: executed unconditionally, allow_run not honoured",
}

CONFORMANCE = {
    "python-measure": {k: "preserved" for k in CANONICAL},
    "python-emit": {k: "preserved" for k in CANONICAL},
    "c": {**{k: "preserved" for k in CANONICAL}, **WEAKENED_HOSTED, "use": "unsupported"},
    "cxx": {**{k: "preserved" for k in CANONICAL}, **WEAKENED_HOSTED, "use": "unsupported"},
    "rust": {
        **{k: "preserved" for k in CANONICAL},
        **WEAKENED_HOSTED,
        "use": "unsupported",
        "measure any": "unsupported",
    },
    "kernel": {
        "words": "preserved",
        "exists": "unsupported",
        "contains": "unsupported",
        "eq": "unsupported",
        "run": "unsupported",
        "use": "unsupported",
        "measure all": "preserved",
        "measure any": "unsupported",
    },
    "wasm": {
        "words": "preserved",
        "exists": "unsupported",
        "contains": "unsupported",
        "eq": "unsupported",
        "run": "unsupported",
        "use": "unsupported",
        "measure all": "preserved",
        "measure any": "unsupported",
    },
    "toe": {**{k: "preserved" for k in CANONICAL}, **WEAKENED_HOSTED, "use": "unsupported"},
    "quantum": {k: "observational" for k in CANONICAL},
    "llm": {k: "transport" for k in CANONICAL},
}
