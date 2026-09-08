from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "YA-RA" / "src"
sys.path.insert(0, str(SRC))

from ya_ra.ast import RV
from ya_ra.emit import UnsupportedSemantic, emit
from ya_ra.llm import frames_for, hop
from ya_ra.measure import measure
from ya_ra.parse import ParseError, parse
from ya_ra.quantum import Hilbert, product_state, psi_and_born
from ya_ra.root import from_root
from ya_ra.semantics import CONFORMANCE
from ya_ra.weave import weave


def _run(args, cwd=None):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "ya_ra", *args], cwd=cwd or ROOT, capture_output=True, text=True, env=env)


def _has(cmd):
    return shutil.which(cmd) is not None


WORDS = "Intent : host\nPattern: calls the door\n\u22a6 words intent <= 17\n"


class TestParse(unittest.TestCase):
    def test_example(self):
        d = parse((ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text())
        self.assertEqual(d.rv, "rv0.2.0")
        self.assertTrue(d.glimpse)
        self.assertTrue(d.zero)
        self.assertEqual(d.measure, "all")
        self.assertEqual(d.signer, "Yash Rajvansh")
        self.assertEqual(d.envelope.kind, "declared")

    def test_rejects_unknown_kind(self):
        with self.assertRaises(ParseError):
            parse("Intent : a\nPattern: b\nSigned. x / 1\n\u22a6 foobar baz\n")

    def test_contains_eq(self):
        d = parse("Intent : a door\nPattern: a pattern\nSigned. x / 1\n\u22a6 contains Glimpse \"glimpse\"\n\u22a6 eq Intent \"nope\"\n")
        self.assertEqual(d.checks[0].kind, "contains")
        self.assertEqual(d.checks[1].kind, "eq")

    def test_unsigned_core_parses(self):
        d = parse("Intent : bare\nPattern: still a language\n")
        self.assertEqual(d.envelope.kind, "none")
        self.assertEqual(d.signer, "")

    def test_unsigned_is_not_malformed(self):
        out = measure(parse("Intent : bare\nPattern: still a language\n"), root=ROOT)
        self.assertTrue(out.ok)
        self.assertTrue(out.missing_provenance)


class TestRoot(unittest.TestCase):
    def test_from_root(self):
        d = from_root(ROOT)
        self.assertIn("change is certain", d.intent)
        out = measure(d, root=ROOT)
        self.assertTrue(out.ok, out.errors)
        self.assertGreater(out.born, 0.0)

    def test_cli_root(self):
        r = _run(["measure", "--root", str(ROOT)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("measured ok", r.stdout)

    def test_root_files_not_a_raw_door(self):
        self.assertNotEqual(_run(["parse", str(ROOT / "Intent")]).returncode, 0)


class TestMeasure(unittest.TestCase):
    def test_example_from_repo_root(self):
        d = parse((ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text())
        self.assertTrue(measure(d, root=ROOT).ok)

    def test_use_module(self):
        d = parse("Intent : parent\nPattern: uses a child\nuse YA-RA/examples/child.YA-RA\n")
        self.assertTrue(measure(d, root=ROOT).ok)

    def test_words_fail(self):
        d = parse("Intent : " + "word " * 20 + "\nPattern: p\n")
        self.assertFalse(measure(d, root=ROOT).ok)

    def test_default_run_refused(self):
        out = measure(parse("Intent : lab\nPattern: shell\n\u22a6 run true\n"), root=ROOT)
        self.assertFalse(out.ok)
        self.assertEqual(out.shots[0].status, "refuse")

    def test_allow_run(self):
        out = measure(parse("Intent : lab\nPattern: shell\n\u22a6 run true\n"), root=ROOT, allow_run=True)
        self.assertTrue(out.ok, out.errors + out.refusals)

    def test_require_provenance(self):
        out = measure(parse("Intent : bare\nPattern: still a language\n"), root=ROOT, require_provenance=True)
        self.assertFalse(out.ok)

    def test_root_traversal_refused(self):
        out = measure(parse("Intent : x\nPattern: y\n\u22a6 exists ../etc/passwd\n"), root=ROOT)
        self.assertEqual(out.shots[0].status, "refuse")

    def test_absolute_path_refused(self):
        out = measure(parse("Intent : x\nPattern: y\n\u22a6 exists /etc/passwd\n"), root=ROOT)
        self.assertEqual(out.shots[0].status, "refuse")

    def test_symlink_escape_refused(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            outside = td / "outside"
            outside.write_text("secret")
            inside = td / "root"
            inside.mkdir()
            try:
                (inside / "escape").symlink_to(outside)
            except OSError:
                self.skipTest("no symlink")
            out = measure(parse("Intent : x\nPattern: y\n\u22a6 exists escape\n"), root=inside)
            self.assertEqual(out.shots[0].status, "refuse")


class TestQuantum(unittest.TestCase):
    def test_born_sums_to_one(self):
        psi = product_state([1 + 0j, 1 + 0j])
        self.assertAlmostEqual(sum((a.conjugate() * a).real for a in psi), 1.0, places=9)

    def test_born_of_all_pass(self):
        _, p = psi_and_born([1 + 0j], [True])
        self.assertAlmostEqual(p, 0.5, places=9)

    def test_collapse_renorm(self):
        self.assertAlmostEqual(Hilbert.from_checks([1 + 0j]).collapse([True]).norm2(), 1.0, places=9)

    def test_amp_does_not_decide_truth(self):
        out = measure(parse("Intent : a\nPattern: b\n\u22a6 words intent <= 17 amp 0\n"), root=ROOT)
        self.assertTrue(out.ok)
        self.assertEqual(out.z, 0j)


class TestEmit(unittest.TestCase):
    def setUp(self):
        self.door = parse((ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text())
        self.words = parse(WORDS)

    def test_llm_json(self):
        obj = json.loads(emit(self.door, "llm"))
        self.assertEqual(obj["language"], "YA|RA")
        self.assertEqual(obj["hop"][0]["phase"], "glimpse")
        self.assertEqual(obj["hop"][1]["phase"], "depth")

    def test_python_emit_runs(self):
        p = Path(tempfile.mkdtemp()) / "door.py"
        p.write_text(emit(self.door, "python"))
        r = subprocess.run([sys.executable, str(p)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_python_emit_includes_exists(self):
        self.assertIn("Intent", emit(self.door, "python"))

    def test_kernel_refuses_exists(self):
        with self.assertRaises(UnsupportedSemantic):
            emit(self.door, "kernel")

    def test_c_refuses_use(self):
        d = parse("Intent : parent\nPattern: uses a child\nuse YA-RA/examples/child.YA-RA\n")
        with self.assertRaises(UnsupportedSemantic):
            emit(d, "c")

    def test_c_and_cxx_and_kernel_and_toe(self):
        if not _has("gcc") or not _has("g++"):
            self.skipTest("no gcc/g++")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "c.c").write_text(emit(self.door, "c"))
            r = subprocess.run(["gcc", "-Wall", "-Werror", f"-I{ROOT / 'YA-RA' / 'runtime' / 'c'}", str(td / "c.c"), str(ROOT / "YA-RA" / "runtime" / "c" / "ya_ra.c"), "-o", str(td / "c.bin")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(subprocess.run([str(td / "c.bin")], cwd=ROOT).returncode, 0)
            (td / "k.c").write_text(emit(self.words, "kernel"))
            r = subprocess.run(["gcc", "-Wall", "-Werror", "-ffreestanding", f"-I{ROOT / 'YA-RA' / 'runtime' / 'kernel'}", str(td / "k.c"), "-o", str(td / "k.bin")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_quantum_qasm(self):
        q = emit(self.door, "quantum")
        self.assertIn("OPENQASM 2.0", q)
        self.assertIn("observational", q)

    def test_c_interop_no_main(self):
        if not _has("gcc"):
            self.skipTest("no gcc")
        d = parse(WORDS)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "door.c").write_text(emit(d, "c"))
            (td / "host.c").write_text("int yara_door_entry(void);\nint main(void){ return yara_door_entry(); }\n")
            r = subprocess.run(["gcc", "-DYARA_NO_MAIN", "-Wall", "-Werror", f"-I{ROOT / 'YA-RA' / 'runtime' / 'c'}", str(td / "door.c"), str(td / "host.c"), str(ROOT / "YA-RA" / "runtime" / "c" / "ya_ra.c"), "-o", str(td / "h.bin")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(subprocess.run([str(td / "h.bin")]).returncode, 0)

    def test_compiler_absent_is_skippable(self):
        self.assertIsInstance(_has("definitely-not-a-compiler-xyz"), bool)


class TestTOE(unittest.TestCase):
    def test_signed_sum(self):
        out = measure(parse("Intent : a\nPattern: b\nSigned. x / 1\n\u22a6 words intent <= 17 amp 1\n"), root=ROOT)
        self.assertTrue(out.ok)
        self.assertEqual(out.z, 1 + 0j)


class TestLLM(unittest.TestCase):
    def test_dry_hop(self):
        d = from_root(ROOT)
        k1 = os.environ.pop("XAI_API_KEY", None)
        k2 = os.environ.pop("YARA_LLM_KEY", None)
        try:
            h = hop(d, key="")
            self.assertFalse(h.hopped)
            json.loads(h.wire())
        finally:
            if k1 is not None: os.environ["XAI_API_KEY"] = k1
            if k2 is not None: os.environ["YARA_LLM_KEY"] = k2


class TestWeave(unittest.TestCase):
    def test_two_modules(self):
        a, b = weave(from_root(ROOT))
        self.assertTrue(a.source.endswith("#1"))


class TestPackage(unittest.TestCase):
    def test_version(self):
        self.assertEqual(RV, "rv0.2.0")

    def test_no_leftover_tree(self):
        self.assertFalse((ROOT / "ya-ra").exists())

    def test_cli_rv(self):
        r = _run(["--rv"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("rv0.2.0", r.stdout)


class TestConformance(unittest.TestCase):
    def test_no_silent_weaken(self):
        allowed = {"preserved", "unsupported", "observational", "transport", "n/a"}
        for row in CONFORMANCE.values():
            for cell in row.values():
                self.assertIn(cell, allowed)


if __name__ == "__main__":
    unittest.main()
