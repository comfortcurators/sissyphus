from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "YA-RA" / "src"
sys.path.insert(0, str(SRC))

from ya_ra.ast import RV  # noqa: E402
from ya_ra.emit import emit  # noqa: E402
from ya_ra.llm import hop  # noqa: E402
from ya_ra.measure import measure  # noqa: E402
from ya_ra.parse import ParseError, parse  # noqa: E402
from ya_ra.quantum import Hilbert, product_state, psi_and_born  # noqa: E402
from ya_ra.root import from_root  # noqa: E402
from ya_ra.weave import weave  # noqa: E402


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "ya_ra", *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


class TestParse(unittest.TestCase):
    def test_example(self):
        src = (ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text()
        d = parse(src)
        self.assertEqual(d.rv, "rv0.2.0")
        self.assertTrue(d.glimpse)
        self.assertTrue(d.zero)
        self.assertEqual(d.measure, "all")
        self.assertEqual(d.signer, "Yash Rajvansh")

    def test_rejects_unknown_kind(self):
        src = "Intent : a\nPattern: b\nSigned. x / 1\n⊦ foobar baz\n"
        with self.assertRaises(ParseError):
            parse(src)

    def test_contains_eq(self):
        src = (
            "Intent : a door\nPattern: a pattern\nSigned. x / 1\n"
            '⊦ contains Glimpse "glimpse"\n'
            '⊦ eq Intent "nope"\n'
        )
        d = parse(src)
        self.assertEqual(d.checks[0].kind, "contains")
        self.assertEqual(d.checks[1].kind, "eq")


class TestRoot(unittest.TestCase):
    def test_from_root(self):
        d = from_root(ROOT)
        self.assertIn("change is certain", d.intent)
        self.assertIn("weaved", d.pattern)
        self.assertTrue(d.glimpse)
        self.assertTrue(d.zero)
        out = measure(d, root=ROOT)
        self.assertTrue(out.ok, out.errors)
        self.assertGreater(out.born, 0.0)

    def test_cli_root(self):
        r = _run(["measure", "--root", str(ROOT)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("measured ok", r.stdout)
        self.assertIn("born", r.stdout)
        self.assertIn("Z ", r.stdout)

    def test_root_files_not_a_raw_door(self):
        r = _run(["parse", str(ROOT / "Intent")])
        self.assertNotEqual(r.returncode, 0)


class TestMeasure(unittest.TestCase):
    def test_example_from_repo_root(self):
        d = parse((ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text())
        out = measure(d, root=ROOT)
        self.assertTrue(out.ok, out.errors)

    def test_use_module(self):
        src = (
            "Intent : parent\nPattern: uses a child\nSigned. x / 1\n"
            "use YA-RA/examples/child.YA-RA\n"
        )
        d = parse(src)
        out = measure(d, root=ROOT)
        self.assertTrue(out.ok, out.errors)

    def test_words_fail(self):
        src = "Intent : " + "word " * 20 + "\nPattern: p\nSigned. x / 1\n"
        d = parse(src)
        out = measure(d, root=ROOT)
        self.assertFalse(out.ok)


class TestQuantum(unittest.TestCase):
    def test_born_sums_to_one(self):
        psi = product_state([1 + 0j, 1 + 0j])
        total = sum((a.conjugate() * a).real for a in psi)
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_born_of_all_pass(self):
        _, p = psi_and_born([1 + 0j], [True])
        self.assertAlmostEqual(p, 0.5, places=9)
        h = Hilbert.from_checks([1 + 0j])
        self.assertAlmostEqual(h.norm2(), 1.0, places=9)
        self.assertAlmostEqual(h.born([True]), 0.5, places=9)

    def test_collapse_renorm(self):
        h = Hilbert.from_checks([1 + 0j])
        c = h.collapse([True])
        self.assertAlmostEqual(c.norm2(), 1.0, places=9)


class TestEmit(unittest.TestCase):
    def setUp(self):
        self.door = parse((ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text())

    def test_llm_json(self):
        raw = emit(self.door, "llm")
        obj = json.loads(raw)
        self.assertEqual(obj["language"], "YA|RA")
        self.assertEqual(len(obj["hop"]), 2)
        self.assertEqual(obj["hop"][0]["phase"], "glimpse")
        self.assertEqual(obj["hop"][1]["phase"], "depth")

    def test_python_emit_runs(self):
        code = emit(self.door, "python")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "door.py"
            p.write_text(code)
            r = subprocess.run([sys.executable, str(p)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_python_emit_includes_exists(self):
        code = emit(self.door, "python")
        self.assertIn("Intent", code)

    def test_c_and_cxx_and_kernel_and_toe(self):
        gcc = subprocess.run(["gcc", "--version"], capture_output=True)
        gxx = subprocess.run(["g++", "--version"], capture_output=True)
        if gcc.returncode != 0 or gxx.returncode != 0:
            self.skipTest("no gcc/g++")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "c.c").write_text(emit(self.door, "c"))
            r = subprocess.run(
                [
                    "gcc", "-Wall", "-Wextra", "-Werror",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'c'}",
                    str(td / "c.c"),
                    str(ROOT / "YA-RA" / "runtime" / "c" / "ya_ra.c"),
                    "-o", str(td / "c.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(td / "c.bin")], cwd=ROOT, capture_output=True)
            self.assertEqual(r.returncode, 0)

            (td / "x.cpp").write_text(emit(self.door, "cxx"))
            r = subprocess.run(
                [
                    "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'cxx'}",
                    str(td / "x.cpp"),
                    "-o", str(td / "x.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(td / "x.bin")], cwd=ROOT, capture_output=True)
            self.assertEqual(r.returncode, 0)

            (td / "k.c").write_text(emit(self.door, "kernel"))
            r = subprocess.run(
                [
                    "gcc", "-Wall", "-Wextra", "-Werror", "-ffreestanding",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'kernel'}",
                    str(td / "k.c"),
                    "-o", str(td / "k.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(td / "k.bin")], capture_output=True)
            self.assertEqual(r.returncode, 0)

            (td / "t.c").write_text(emit(self.door, "toe"))
            r = subprocess.run(
                [
                    "gcc", "-Wall", "-Wextra", "-Werror",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'c'}",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'toe'}",
                    str(td / "t.c"),
                    str(ROOT / "YA-RA" / "runtime" / "c" / "ya_ra.c"),
                    "-o", str(td / "t.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(td / "t.bin")], cwd=ROOT, capture_output=True)
            self.assertEqual(r.returncode, 0)

    def test_quantum_qasm(self):
        q = emit(self.door, "quantum")
        self.assertIn("OPENQASM 2.0", q)
        self.assertIn("ry(", q)
        self.assertIn("measure", q)

    def test_c_interop_no_main(self):
        gcc = subprocess.run(["gcc", "--version"], capture_output=True)
        if gcc.returncode != 0:
            self.skipTest("no gcc")
        d = parse("Intent : host\nPattern: calls the door\nSigned. x / 1\n⊦ words intent <= 17\n")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "door.c").write_text(emit(d, "c"))
            (td / "host.c").write_text(
                "int yara_door_entry(void);\nint main(void){ return yara_door_entry(); }\n"
            )
            r = subprocess.run(
                [
                    "gcc", "-DYARA_NO_MAIN", "-Wall", "-Werror",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'c'}",
                    str(td / "door.c"),
                    str(td / "host.c"),
                    str(ROOT / "YA-RA" / "runtime" / "c" / "ya_ra.c"),
                    "-o", str(td / "h.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run([str(td / "h.bin")])
            self.assertEqual(r.returncode, 0)


class TestTOE(unittest.TestCase):
    def test_refuse_unsigned(self):
        src = (
            '#include "toe.h"\n'
            "int main(void) {\n"
            "  struct yara_toe_cut c = {\"i\",\"p\",\"\",0};\n"
            "  struct yara_toe_term t = {1,0,1};\n"
            "  struct yara_toe_z z;\n"
            "  return yara_toe_project(&c, &t, 1, &z) == 1 && z.refused ? 0 : 1;\n"
            "}\n"
        )
        gcc = subprocess.run(["gcc", "--version"], capture_output=True)
        if gcc.returncode != 0:
            self.skipTest("no gcc")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "u.c").write_text(src)
            r = subprocess.run(
                [
                    "gcc", "-Wall", "-Werror",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'toe'}",
                    str(td / "u.c"), "-o", str(td / "u.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(subprocess.run([str(td / "u.bin")]).returncode, 0)

    def test_signed_sum(self):
        d = parse("Intent : a\nPattern: b\nSigned. x / 1\n⊦ words intent <= 17 amp 1\n")
        out = measure(d, root=ROOT)
        self.assertTrue(out.ok)
        self.assertEqual(out.z, 1 + 0j)


class TestLLM(unittest.TestCase):
    def test_dry_hop(self):
        d = from_root(ROOT)
        env_key = os.environ.pop("XAI_API_KEY", None)
        env_key2 = os.environ.pop("YARA_LLM_KEY", None)
        try:
            h = hop(d, key="")
            self.assertFalse(h.hopped)
            json.loads(h.wire())
            self.assertEqual(h.glimpse.phase, "glimpse")
            self.assertEqual(h.depth.phase, "depth")
        finally:
            if env_key is not None:
                os.environ["XAI_API_KEY"] = env_key
            if env_key2 is not None:
                os.environ["YARA_LLM_KEY"] = env_key2


class TestWeave(unittest.TestCase):
    def test_two_modules(self):
        d = from_root(ROOT)
        a, b = weave(d)
        self.assertTrue(a.glimpse)
        self.assertFalse(b.glimpse)
        self.assertTrue(a.source.endswith("#1"))
        self.assertTrue(b.source.endswith("#2"))


class TestPackage(unittest.TestCase):
    def test_version(self):
        self.assertEqual(RV, "rv0.2.0")
        self.assertEqual((ROOT / "YA-RA" / "VERSION").read_text().strip(), "rv0.2.0")

    def test_no_leftover_tree(self):
        self.assertFalse((ROOT / "ya-ra").exists())

    def test_cli_rv(self):
        r = _run(["--rv"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("rv0.2.0", r.stdout)


if __name__ == "__main__":
    unittest.main()
