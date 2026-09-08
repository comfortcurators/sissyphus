from __future__ import annotations

from .ast import Door


def _c_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def emit_c(door: Door) -> str:
    return f'''/* YA|RA {door.rv} — C */
#include "ya_ra.h"
int main(void) {{
  struct yara_door d = {{
    .intent = "{_c_str(door.intent)}",
    .pattern = "{_c_str(door.pattern)}",
    .signer = "{_c_str(door.signer)}",
    .timestamp = "{_c_str(door.timestamp)}",
    .rv = "{_c_str(door.rv)}",
    .measure_any = {1 if door.measure == "any" else 0},
    .zero = {1 if door.zero else 0},
    .glimpse = {1 if door.glimpse else 0},
  }};
  return yara_measure(&d) ? 0 : 1;
}}
'''


def emit_cxx(door: Door) -> str:
    return f'''// YA|RA {door.rv} — C++
#include "ya_ra.hpp"
int main() {{
  yara::Door d{{
    "{_c_str(door.intent)}",
    "{_c_str(door.pattern)}",
    "{_c_str(door.signer)}",
    "{_c_str(door.timestamp)}",
    "{_c_str(door.rv)}",
    yara::Measure::{"Any" if door.measure == "any" else "All"},
    {"true" if door.zero else "false"},
    {"true" if door.glimpse else "false"}
  }};
  return d.measure() ? 0 : 1;
}}
'''


def emit_python(door: Door) -> str:
    return f'''# YA|RA {door.rv} — Python
INTENT = "{_c_str(door.intent)}"
PATTERN = "{_c_str(door.pattern)}"
SIGNED = "{_c_str(door.signer)} / {_c_str(door.timestamp)}"
RV = "{_c_str(door.rv)}"
MEASURE = "{door.measure}"
ZERO = {door.zero}
GLIMPSE = {door.glimpse}

def measure() -> bool:
    if len(INTENT.split()) > 17 or len(PATTERN.split()) > 17:
        return False
    return True

if __name__ == "__main__":
    raise SystemExit(0 if measure() else 1)
'''


def emit_kernel(door: Door) -> str:
    return f'''/* YA|RA {door.rv} — language kernel, freestanding C */
#include "ya_ra_k.h"
int yara_k_entry(void) {{
  static const struct yara_k_door d = {{
    "{_c_str(door.intent)}",
    "{_c_str(door.pattern)}",
    "{_c_str(door.signer)}",
    "{_c_str(door.rv)}",
  }};
  return yara_k_measure(&d);
}}
'''


def emit_quantum(door: Door) -> str:
    n = max(len(door.checks), 1)
    lines = [f"# YA|RA {door.rv} — quantum measure", "OPENQASM 2.0;", 'include "qelib1.inc";', f"qreg q[{n}];", f"creg c[{n}];"]
    for i, _ch in enumerate(door.checks or [None]):
        lines.append(f"h q[{i}];")
        lines.append(f"measure q[{i}] -> c[{i}];")
    lines.append(f"// Intent : {_c_str(door.intent)}")
    lines.append(f"// Pattern: {_c_str(door.pattern)}")
    lines.append(f"// Signed. {_c_str(door.signer)}")
    return "\n".join(lines) + "\n"


def emit_llm(door: Door) -> str:
    phase = "glimpse" if door.glimpse or door.zero else "depth"
    return (
        "{{\n"
        f'  "language": "YA|RA",\n'
        f'  "rv": "{_c_str(door.rv)}",\n'
        f'  "phase": "{phase}",\n'
        f'  "transporter": {{\n'
        f'    "intent": "{_c_str(door.intent)}",\n'
        f'    "pattern": "{_c_str(door.pattern)}",\n'
        f'    "signed": "{_c_str(door.signer)} / {_c_str(door.timestamp)}"\n'
        f"  }},\n"
        f'  "rule": "greet with a glimpse, then serve depth."\n'
        "}\n"
    )


def emit_toe(door: Door) -> str:
    return f'''/* YA|RA {door.rv} versus the single action */
#include "toe.h"
int main(void) {{
  struct yara_toe_cut cut = {{
    .intent = "{_c_str(door.intent)}",
    .pattern = "{_c_str(door.pattern)}",
    .signer = "{_c_str(door.signer)}",
    .action_is_door = 0
  }};
  return yara_toe_reject_unsigned(&cut);
}}
'''


TARGETS = {
    "c": emit_c,
    "cxx": emit_cxx,
    "c++": emit_cxx,
    "python": emit_python,
    "kernel": emit_kernel,
    "quantum": emit_quantum,
    "llm": emit_llm,
    "toe": emit_toe,
}


def emit(door: Door, target: str) -> str:
    fn = TARGETS.get(target)
    if not fn:
        raise ValueError("unknown target " + target)
    return fn(door)
