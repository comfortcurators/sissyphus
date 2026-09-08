from __future__ import annotations

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
from ya_ra.measure import measure
from ya_ra.parse import parse
from ya_ra.root import from_root


def _run(args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "ya_ra", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


class TestYA_RA(unittest.TestCase):
    def test_unsigned_is_language(self):
        d = parse("Intent : bare\nPattern: still a language\n")
        out = measure(d, root=ROOT)
        self.assertEqual(d.envelope.kind, "none")
        self.assertTrue(out.ok)
        self.assertTrue(out.missing_provenance)

    def test_root_measures(self):
        out = measure(from_root(ROOT), root=ROOT)
        self.assertTrue(out.ok, out.errors)
        r = _run(["measure", "--root", str(ROOT)])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_run_needs_allow(self):
        d = parse("Intent : lab\nPattern: shell\n\u22a6 run true\n")
        self.assertEqual(measure(d, root=ROOT).shots[0].status, "refuse")
        self.assertTrue(measure(d, root=ROOT, allow_run=True).ok)

    def test_paths_stay_inside(self):
        abs_ = measure(parse("Intent : x\nPattern: y\n\u22a6 exists /etc/passwd\n"), root=ROOT)
        up = measure(parse("Intent : x\nPattern: y\n\u22a6 exists ../etc/passwd\n"), root=ROOT)
        self.assertEqual(abs_.shots[0].status, "refuse")
        self.assertEqual(up.shots[0].status, "refuse")

    def test_use_is_recursive(self):
        d = parse("Intent : parent\nPattern: uses a child\nuse YA-RA/examples/child.YA-RA\n")
        self.assertTrue(measure(d, root=ROOT).ok)
        from ya_ra.program import from_program
        curator = from_program(ROOT / "YA-RA" / "programs" / "curator")
        self.assertTrue(measure(curator, root=ROOT / "YA-RA" / "programs" / "curator").ok)

    def test_backends_do_not_weaken(self):
        d = parse("Intent : parent\nPattern: uses a child\nuse YA-RA/examples/child.YA-RA\n")
        with self.assertRaises(UnsupportedSemantic):
            emit(d, "c")
        exists = parse((ROOT / "YA-RA" / "examples" / "sissyphus.YA-RA").read_text())
        with self.assertRaises(UnsupportedSemantic):
            emit(exists, "kernel")

    def test_c_unsigned_door(self):
        if not shutil.which("gcc"):
            self.skipTest("no gcc")
        d = parse("Intent : host\nPattern: calls the door\n\u22a6 words intent <= 17\n")
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "door.c").write_text(emit(d, "c"))
            (td / "host.c").write_text(
                "extern int yara_missing_provenance;\n"
                "int yara_door_entry(void);\n"
                "int main(void){\n"
                "  int r = yara_door_entry();\n"
                "  if (r != 0) return 1;\n"
                "  return yara_missing_provenance ? 0 : 2;\n"
                "}\n"
            )
            r = subprocess.run(
                [
                    "gcc", "-DYARA_NO_MAIN", "-Wall", "-Werror",
                    f"-I{ROOT / 'YA-RA' / 'runtime' / 'c'}",
                    str(td / "door.c"), str(td / "host.c"),
                    str(ROOT / "YA-RA" / "runtime" / "c" / "ya_ra.c"),
                    "-o", str(td / "h.bin"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(subprocess.run([str(td / "h.bin")]).returncode, 0)

    def test_slide_is_not_a_door(self):
        out = measure(parse("Intent : fields\nPattern: the integral\n"), root=ROOT, action_is_door=True)
        self.assertFalse(out.ok)
        self.assertTrue(out.cut.refused)
        r = _run(["measure", "--root", str(ROOT), "--action"])
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(RV, "rv0.3.0")


if __name__ == "__main__":
    unittest.main()
