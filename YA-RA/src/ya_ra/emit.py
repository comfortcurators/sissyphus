from __future__ import annotations

from .ast import Door
from .llm import frames_for, Hop


def _c_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _kind_c(kind: str) -> str:
    return {
        "words": "YARA_CHECK_WORDS",
        "exists": "YARA_CHECK_EXISTS",
        "run": "YARA_CHECK_RUN",
        "contains": "YARA_CHECK_CONTAINS",
        "eq": "YARA_CHECK_EQ",
        "use": "YARA_CHECK_EXISTS",
    }.get(kind, "YARA_CHECK_EXISTS")


def _c_checks(door: Door) -> str:
    if not door.checks:
        return "  { YARA_CHECK_WORDS, \"intent\", \"17\", 1.0, 0.0 }\n"
    lines = []
    for c in door.checks:
        a = _c_str(c.args[0] if c.args else "")
        b = _c_str(c.args[1] if len(c.args) > 1 else "")
        lines.append(
            f"  {{ {_kind_c(c.kind)}, \"{a}\", \"{b}\", {float(c.amp.real)}, {float(c.amp.imag)} }}"
        )
    return ",\n".join(lines) + "\n"


def _c_door_body(door: Door, header: str) -> str:
    n = max(len(door.checks), 1)
    return f'''#include "{header}"
static const struct yara_check yara_emitted_checks[] = {{
{_c_checks(door)}}};
int yara_door_entry(void) {{
  struct yara_door d = {{
    .intent = "{_c_str(door.intent)}",
    .pattern = "{_c_str(door.pattern)}",
    .signer = "{_c_str(door.signer)}",
    .timestamp = "{_c_str(door.timestamp)}",
    .rv = "{_c_str(door.rv)}",
    .measure_any = {1 if door.measure == "any" else 0},
    .zero = {1 if door.zero else 0},
    .glimpse = {1 if door.glimpse else 0},
    .checks = yara_emitted_checks,
    .nchecks = {n if door.checks else 1},
  }};
  return yara_measure(&d);
}}
#ifndef YARA_NO_MAIN
int main(void) {{ return yara_door_entry(); }}
#endif
'''


def emit_c(door: Door) -> str:
    return f"/* YA|RA {door.rv} — C. Compile with ya_ra.c. -DYARA_NO_MAIN for a library. */\n" + _c_door_body(
        door, "ya_ra.h"
    )


def emit_cxx(door: Door) -> str:
    checks = []
    for c in door.checks:
        a = _c_str(c.args[0] if c.args else "")
        b = _c_str(c.args[1] if len(c.args) > 1 else "")
        kind = {
            "words": "yara::Kind::Words",
            "exists": "yara::Kind::Exists",
            "run": "yara::Kind::Run",
            "contains": "yara::Kind::Contains",
            "eq": "yara::Kind::Eq",
            "use": "yara::Kind::Exists",
        }.get(c.kind, "yara::Kind::Exists")
        checks.append(
            f'    {{{kind}, "{a}", "{b}", {{{float(c.amp.real)}, {float(c.amp.imag)}}}}}'
        )
    check_src = ",\n".join(checks)
    how = "Any" if door.measure == "any" else "All"
    return f'''// YA|RA {door.rv} — C++
#include "ya_ra.hpp"
int yara_door_entry() {{
  yara::Door d{{
    "{_c_str(door.intent)}",
    "{_c_str(door.pattern)}",
    "{_c_str(door.signer)}",
    "{_c_str(door.timestamp)}",
    "{_c_str(door.rv)}",
    yara::How::{how},
    {"true" if door.zero else "false"},
    {"true" if door.glimpse else "false"},
    {{
{check_src}
    }}
  }};
  return d.ok() ? 0 : 1;
}}
#ifndef YARA_NO_MAIN
int main() {{ return yara_door_entry(); }}
#endif
'''


def emit_python(door: Door) -> str:
    signed = door.signer + " / " + door.timestamp
    lines = [
        f"# YA|RA {door.rv} — Python",
        "from pathlib import Path",
        "import subprocess",
        "ROOT = Path.cwd()",
        f"INTENT = {door.intent!r}",
        f"PATTERN = {door.pattern!r}",
        f"SIGNED = {signed!r}",
        f"RV = {door.rv!r}",
        f"MEASURE = {door.measure!r}",
        f"ZERO = {door.zero}",
        f"GLIMPSE = {door.glimpse}",
        "def measure() -> bool:",
        "    shots = []",
        "    shots.append(len(INTENT.split()) <= 17)",
        "    shots.append(len(PATTERN.split()) <= 17)",
        "    if not SIGNED.strip():",
        "        return False",
    ]
    for c in door.checks:
        if c.kind == "words":
            src = "INTENT" if c.args[0] == "intent" else "PATTERN"
            lines.append(f"    shots.append(len({src}.split()) <= {int(c.args[1])})")
        elif c.kind in {"exists", "use"}:
            lines.append(f"    shots.append((ROOT / {c.args[0]!r}).exists())")
        elif c.kind == "run":
            lines.append(
                f"    shots.append(subprocess.run({c.args[0]!r}, shell=True, cwd=ROOT).returncode == 0)"
            )
        elif c.kind == "contains":
            lines.append(
                f"    shots.append((ROOT / {c.args[0]!r}).is_file() and {c.args[1]!r} in (ROOT / {c.args[0]!r}).read_text(encoding='utf-8', errors='replace'))"
            )
        elif c.kind == "eq":
            lines.append(
                f"    shots.append((ROOT / {c.args[0]!r}).is_file() and (ROOT / {c.args[0]!r}).read_text(encoding='utf-8', errors='replace') == {c.args[1]!r})"
            )
    lines += [
        "    if MEASURE == 'any':",
        "        return (not shots) or any(shots)",
        "    return all(shots)",
        'if __name__ == "__main__":',
        "    raise SystemExit(0 if measure() else 1)",
        "",
    ]
    return "\n".join(lines)


def emit_kernel(door: Door) -> str:
    return f'''/* YA|RA {door.rv} — language kernel. Polarity 0 = ok. */
#include "ya_ra_k.h"
int yara_k_entry(void) {{
  static const struct yara_k_door d = {{
    "{_c_str(door.intent)}",
    "{_c_str(door.pattern)}",
    "{_c_str(door.signer)}",
    "{_c_str(door.timestamp)}",
    "{_c_str(door.rv)}",
    {1 if door.measure == "any" else 0},
  }};
  return yara_k_syscall(YARA_SYS_MEASURE, (void *)&d);
}}
#ifndef YARA_NO_MAIN
int main(void) {{ return yara_k_entry(); }}
#endif
'''


def emit_quantum(door: Door) -> str:
    amps = [c.amp for c in door.checks] or [1 + 0j]
    n = len(amps)
    lines = [
        f"# YA|RA {door.rv} — Hilbert ℂ^{{2^{n}}}. Born rule after measure.",
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{n}];",
        f"creg c[{n}];",
    ]
    for i, a in enumerate(amps):
        theta = 2.0 * __import__("math").atan2(abs(a), 1.0)
        phi = __import__("cmath").phase(a)
        kind = door.checks[i].kind if door.checks else "signed"
        lines.append(f"// qubit {i}: {kind} amp {a}")
        lines.append(f"ry({theta:.10f}) q[{i}];")
        if abs(phi) > 1e-12:
            lines.append(f"rz({phi:.10f}) q[{i}];")
        lines.append(f"measure q[{i}] -> c[{i}];")
    lines.append(f"// Intent : {_c_str(door.intent)}")
    lines.append(f"// Pattern: {_c_str(door.pattern)}")
    lines.append(f"// Signed. {_c_str(door.signer)}")
    return "\n".join(lines) + "\n"


def emit_llm(door: Door) -> str:
    g, d = frames_for(door)
    return Hop(glimpse=g, depth=d, hopped=False, reply=None).wire()


def emit_toe(door: Door) -> str:
    n = max(len(door.checks), 1)
    return f'''/* YA|RA {door.rv} — signed sum Z, not the unsigned slide */
#include "ya_ra.h"
#include "toe.h"
static const struct yara_check yara_emitted_checks[] = {{
{_c_checks(door)}}};
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
    .checks = yara_emitted_checks,
    .nchecks = {n if door.checks else 1},
  }};
  int m = yara_measure(&d);
  struct yara_toe_term terms[{n}];
  int nt = yara_nshots < {n} ? yara_nshots : {n};
  for (int i = 0; i < nt; i++) {{
    terms[i].re = yara_shots[i].re;
    terms[i].im = yara_shots[i].im;
    terms[i].passed = yara_shots[i].passed;
  }}
  struct yara_toe_cut cut = {{
    .intent = d.intent,
    .pattern = d.pattern,
    .signer = d.signer,
    .action_is_door = 0
  }};
  struct yara_toe_z z;
  int r = yara_toe_project(&cut, terms, nt, &z);
  return (m == YARA_OK && r == YARA_OK) ? YARA_OK : YARA_FAIL;
}}
'''


def emit_rust(door: Door) -> str:
    stmts = [
        "    assert!(intent.split_whitespace().count() <= 17);",
        "    assert!(pattern.split_whitespace().count() <= 17);",
        "    assert!(!signer.is_empty());",
    ]
    for c in door.checks:
        if c.kind == "exists" or c.kind == "use":
            stmts.append(f'    assert!(std::path::Path::new("{_c_str(c.args[0])}").exists());')
        elif c.kind == "words":
            var = "intent" if c.args[0] == "intent" else "pattern"
            stmts.append(f"    assert!({var}.split_whitespace().count() <= {c.args[1]});")
        elif c.kind == "run":
            stmts.append(
                f'    assert!(std::process::Command::new("sh").arg("-c").arg("{_c_str(c.args[0])}")'
                ".status().unwrap().success());"
            )
        elif c.kind == "contains":
            stmts.append(
                f'    assert!(std::fs::read_to_string("{_c_str(c.args[0])}").unwrap().contains("{_c_str(c.args[1])}"));'
            )
        elif c.kind == "eq":
            stmts.append(
                f'    assert_eq!(std::fs::read_to_string("{_c_str(c.args[0])}").unwrap(), "{_c_str(c.args[1])}");'
            )
    return (
        f"// YA|RA {door.rv} — Rust\nfn main() {{\n"
        f'    let intent = "{_c_str(door.intent)}";\n'
        f'    let pattern = "{_c_str(door.pattern)}";\n'
        f'    let signer = "{_c_str(door.signer)}";\n'
        + "\n".join(stmts)
        + '\n    println!("ok");\n}\n'
    )


TARGETS = {
    "c": emit_c,
    "cxx": emit_cxx,
    "c++": emit_cxx,
    "python": emit_python,
    "kernel": emit_kernel,
    "quantum": emit_quantum,
    "llm": emit_llm,
    "toe": emit_toe,
    "rust": emit_rust,
}


def emit(door: Door, target: str) -> str:
    fn = TARGETS.get(target)
    if not fn:
        raise ValueError("unknown target " + target)
    return fn(door)
