from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "YA-RA" / "src"
sys.path.insert(0, str(SRC))

from ya_ra.measure import measure
from ya_ra.parse import parse


def _run(args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "ya_ra", *args], cwd=ROOT, capture_output=True, text=True, env=env)


class TestCut(unittest.TestCase):
    def test_unsigned_sentence_still_has_z(self):
        out = measure(parse("Intent : bare\nPattern: still a language\n"), root=ROOT)
        self.assertTrue(out.ok)
        self.assertIsNotNone(out.cut)
        self.assertFalse(out.cut.refused)
        self.assertTrue(out.cut.missing_provenance)
        self.assertEqual(out.z, 0j)

    def test_attributed_sum(self):
        src = "Intent : a\nPattern: b\nSigned. x / 1\n\u22a6 words intent <= 17 amp 1\n\u22a6 words pattern <= 17 amp 1\n"
        out = measure(parse(src), root=ROOT)
        self.assertTrue(out.ok)
        self.assertEqual(out.z, 2 + 0j)
        self.assertFalse(out.cut.refused)

    def test_slide_is_not_a_door(self):
        out = measure(parse("Intent : fields\nPattern: the integral\n"), root=ROOT, action_is_door=True)
        self.assertFalse(out.ok)
        self.assertTrue(out.cut.refused)
        self.assertIn("unsigned action", out.cut.reason)
        self.assertEqual(out.z, 0j)

    def test_cli_action_refuses(self):
        r = _run(["measure", "--root", str(ROOT), "--action"])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unsigned action", r.stderr)

    def test_cut_statement_parses(self):
        d = parse("Intent : a\nPattern: b\ncut\n")
        self.assertTrue(d.cut)


if __name__ == "__main__":
    unittest.main()
