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
from ya_ra.semantics import CANONICAL, CONFORMANCE
from ya_ra.toe import project as toe_project


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
        self.assertEqual(RV, "rv0.3")


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# rv0.3 fixes: the write capability, the TOE cross-backend split, and the
# conformance table that called a weakened cell preserved.
# ---------------------------------------------------------------------------


class TestWriteCapability(unittest.TestCase):
    """`run` needed --allow-run; the cura/universe write needed nothing at all.

    One property, and every way it breaks: the write must not happen without
    its own capability, must happen with it, and must NOT be unlocked by
    --allow-run — executing and writing are separately grantable.
    """

    def _cura_root(self) -> Path:
        d = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "YA-RA" / "programs" / "cura", d / "cura")
        root = d / "cura"
        (root / "aforementioned.YA-RA").unlink(missing_ok=True)
        return root

    def test_the_write_needs_its_own_capability(self):
        refused = self._cura_root()
        door = parse((refused / "main.YA-RA").read_text(encoding="utf-8"), source=str(refused))
        out = measure(door, root=refused)
        self.assertFalse((refused / "aforementioned.YA-RA").exists())
        self.assertTrue(any("allow-write" in r for r in out.refusals))

        # --allow-run is not a writer
        ran = self._cura_root()
        measure(parse((ran / "main.YA-RA").read_text(encoding="utf-8"), source=str(ran)), root=ran, allow_run=True)
        self.assertFalse((ran / "aforementioned.YA-RA").exists())

        # granted, it writes
        granted = self._cura_root()
        out = measure(parse((granted / "main.YA-RA").read_text(encoding="utf-8"), source=str(granted)), root=granted, allow_write=True)
        if out.aforementioned:
            self.assertTrue((granted / "aforementioned.YA-RA").exists())


class TestToeAgreesAcrossBackends(unittest.TestCase):
    """An unsigned door is missing-provenance in Python and must be so in C.

    The divergence was real: C refused on an empty signer where Python does
    not, so the same door was refused under `--to toe` and not under `measure`.
    Python is canonical; the C runtime must agree, and must still refuse the
    one thing that IS refused — the unsigned action.
    """

    def test_unsigned_is_not_refused_on_either_backend(self):
        door = parse("Intent : unsigned\nPattern: still language\n")
        cut = toe_project(door, [1 + 0j], [True])
        self.assertFalse(cut.refused)
        self.assertTrue(cut.missing_provenance)

        src = (ROOT / "YA-RA" / "runtime" / "toe" / "toe.h").read_text(encoding="utf-8")
        self.assertNotIn("|| !c->signer || !c->signer[0]", src)
        self.assertIn("missing_provenance", src)
        self.assertIn("c->action_is_door", src)


class TestConformanceIsHonest(unittest.TestCase):
    """A backend that drops a canonical guarantee is not `preserved`.

    Both directions: the hosted backends must not claim confinement or the run
    gate they do not have, and python-measure must still claim everything it
    does have — or the relabel has simply become pessimism.
    """

    def test_no_backend_claims_a_guarantee_it_lacks(self):
        for target in ("c", "cxx", "rust"):
            for kind in ("exists", "contains", "eq", "run"):
                self.assertNotEqual(
                    CONFORMANCE[target][kind], "preserved",
                    f"{target}/{kind} claims preserved without confinement or the run gate",
                )
            self.assertEqual(CONFORMANCE[target]["bind"], "unsupported")

        for kind in CANONICAL:
            self.assertEqual(CONFORMANCE["python-measure"][kind], "preserved")


class TestBinding(unittest.TestCase):
    """A check may name what it read, and a later check may use the name.

    This is the line between assertion and computation: before it, every check
    answered pass/fail and whatever it had read died with the answer.
    """

    def _root(self, manifest: str = "target.txt\n") -> Path:
        d = Path(tempfile.mkdtemp())
        (d / "manifest.txt").write_text(manifest, encoding="utf-8")
        (d / "target.txt").write_text("hello plane\n", encoding="utf-8")
        (d / "b.YA-RA").write_text(
            "Intent : bind what one check read and use it in the next\n"
            "Pattern: break the manifest and the second check cannot find its file\n"
            "\u22a6 contains manifest.txt \"target\" as listed\n"
            "\u22a6 exists $listed\n",
            encoding="utf-8",
        )
        return d

    def test_a_value_flows_from_one_check_to_the_next_and_can_fail(self):
        root = self._root()
        out = measure(parse((root / "b.YA-RA").read_text(encoding="utf-8")), root=root)
        self.assertTrue(out.ok)
        # contains yields the READ TEXT, not a bool, or nothing could flow
        self.assertEqual(out.shots[0].value, "target.txt\n")

        # and it is Pattern: point the manifest elsewhere and it contradicts
        broken = self._root(manifest="nothing.txt\n")
        self.assertFalse(measure(parse((broken / "b.YA-RA").read_text(encoding="utf-8")), root=broken).ok)

    def test_an_unbound_name_is_refused_not_silently_emptied(self):
        # Substituting "" would turn `exists $nope` into a check on the root
        # and answer a question nobody asked.
        door = parse("Intent : a\nPattern: b\n\u22a6 exists $nope\n")
        out = measure(door, root=Path(tempfile.mkdtemp()))
        self.assertFalse(out.ok)
        self.assertTrue(any("unbound $nope" in s.detail for s in out.shots))

    def test_a_name_is_visible_only_after_it_is_bound(self):
        # Order is the semantic change. Used before bound, it is unbound.
        root = self._root()
        (root / "o.YA-RA").write_text(
            "Intent : order is the semantic change\n"
            "Pattern: swap the two lines and the name is unbound\n"
            "\u22a6 exists $listed\n"
            "\u22a6 contains manifest.txt \"target\" as listed\n",
            encoding="utf-8",
        )
        out = measure(parse((root / "o.YA-RA").read_text(encoding="utf-8")), root=root)
        self.assertEqual(out.shots[0].status, "refuse")

    def test_as_composes_with_amp_in_either_order(self):
        for line in ('\u22a6 words intent <= 17 amp 2 as w', '\u22a6 words intent <= 17 as w amp 2'):
            d = parse(f"Intent : a\nPattern: b\n{line}\n")
            self.assertEqual(d.checks[0].bind, "w")
            self.assertEqual(d.checks[0].amp, 2 + 0j)

    def test_the_founders_triple_binds_across_the_plane(self):
        prog = ROOT / "YA-RA" / "programs" / "qiskit-rust"
        door = parse((prog / "main.YA-RA").read_text(encoding="utf-8"), source=str(prog))
        self.assertTrue(measure(door, root=prog).ok)
        # the symbol is read off the firmware's own declaration, not retyped
        bound = [c.bind for c in door.checks if c.bind]
        self.assertEqual(bound, ["symbol"])

