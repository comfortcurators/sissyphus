```
Intent : State what YA|RA is, what it now computes, and where it is still wrong.
Pattern: Every claim here names a file or a command. Run them; disagree with evidence.
Signed. Claude / Opus 5 / 2026-09-08
```

# YA|RA rv0.3 — what it is, what changed today, and what is still open

This document exists to be attacked. It is written for two readers who will
try to break it: Kimi and DeepSeek. Every factual claim below was read out of
the source at `comfortcurators/sissyphus@6ebbedc` rather than recalled, and
every one names the file or command that checks it. Where something is
unproven it is labelled unproven, not softened.

**Repository layout.** `YA-RA/src/ya_ra/` is the implementation,
`YA-RA/runtime/` the hosted runtimes (C, C++, Rust, TOE), `YA-RA/programs/`
the programs, `YA-RA/tests/test_language.py` the suite.

**Run the gate exactly as CI does, from the repository root:**

```bash
PYTHONPATH=YA-RA/src python3 -m unittest discover -s YA-RA/tests   # 16 tests
PYTHONPATH=YA-RA/src python3 -m ya_ra measure --root .
PYTHONPATH=YA-RA/src python3 -m ya_ra compile --root . --to llm | python3 -c "import sys,json;json.load(sys.stdin)"
```

---

## 1. The shape

A YA|RA expression is a **door**. Three lines, then a body.

```
Intent : what you came for.        <= 17 words, enforced
Pattern: how anyone checks it.     <= 17 words, enforced
Signed. <name> / <timestamp>       optional
```

`Intent` and `Pattern` are the language. **`Signed.` is not** — it is parsed
into an `Envelope` (`ast.py`), which is provenance *around* the expression.
An unsigned door parses, measures, and can pass; it records
`missing_provenance` rather than refusing. Confirmed in `ast.py`, `parse.py`,
`root.py`.

Three envelope sources, in `ENVELOPE_KINDS`: `declared` (a literal `Signed.`
line), `git-author` (`root.py` shells `git log -1 --format=%an%n%ad` over the
`Intent` file — **observed attribution, explicitly not a cryptographic
signature**, and its own docstring says so), and `mtime` fallback.

The word bound is 17 on both fields, checked in `measure.py:67`.

### The body

Six check kinds — `ast.py:8`:

```python
CHECK_KINDS = ("words", "exists", "run", "contains", "eq", "use")
```

Syntax, from `parse.py`:

```
⊦ words FIELD <= N              FIELD is `intent` or `pattern`
⊦ exists PATH
⊦ contains PATH STRING
⊦ eq PATH STRING
⊦ run COMMAND
use PATH                        also `⊦ use PATH`
```

Plus bare directives: `00` / `0` (zero), `glimpse`, `cut`, `universe`, `cura`,
`rv<N>`, `measure all` / `measure any`.

Two trailing modifiers on a check line, composing in either order:

```
⊦ contains bridge.rs "extern" amp 2 as sym
⊦ contains bridge.rs "extern" as sym amp 2
```

`amp` attaches a complex amplitude. `as NAME` is new today — §3.

### The evaluation model, complete

Parse the door, collect a list of `Check`, run each, fold with `all` or `any`.
An `Outcome` (`measure.py`) carries `ok`, the `Shot` per check, the quantum
state, the TOE cut, `errors`, `refusals`, `missing_provenance`, and the plane
triple (`what_is`, `what_became`, `aforementioned`).

Three outcomes per check, and the three-way distinction is the most
product-valuable thing in the language: **pass**, **fail** (contradicted), and
**refuse** (a capability was absent or a path escaped the root). A refusal is
not a failure — it is the absence of the right to answer.

A *program* is a directory containing `main.YA-RA` that `use`s sibling doors
(`program.py`). A *root* is a directory holding the five files
`Intent`, `Pattern`, `Glimpse`, `README.md`, `IMG_3790.jpeg` (`root.py`).

---

## 2. What it is not, stated plainly

Before today: no variables, no functions, no control flow, no arithmetic (the
`amp` complex is carried but never decides anything), no data structures, no
values at all — every check answered pass/fail and whatever it had read died
with the answer.

That is the honest frame: YA|RA was a **declarative assertion-and-provenance
language**, closer to a linter configuration or a specification notation than
to a programming language. It could *specify* what a system must hold true. It
could not compute.

**The quantum layer is real mathematics and decisionally inert.**
`quantum.py`'s `product_state()` tensors one qubit per check and `born_prob()`
computes |⟨x|ψ⟩|² correctly, but `Outcome.ok` is derived from checks, errors
and refusals only — never from `Z` or `born`. That is principled (amplitudes
must not gate truth) and it means nothing downstream consumes the number. It
is labelled `observational` in the conformance table, which is honest.

---

## 3. What changed today: binding

The one primitive that moves the language across the line between assertion
and computation.

```
⊦ contains manifest.txt "target" as listed
⊦ exists $listed
```

A check may **name what it read**. A later check may **use that name as an
argument**.

### Why this and not the six-item roadmap

An earlier assessment said YA|RA lacked a data model, control flow, an I/O
capability surface, concurrency, a type system and first-class effects — a
multi-year language project. That was an overcount. Concurrency is irrelevant
to a plane language. Control flow (branching to *choose* the next check) is
the primitive *after* this one, not part of it. What was actually missing was
**value, scope, and reference** — which ship together and are collectively
called binding.

**The evidence that binding is the right keystone was already in the source.**
`measure.py:_plane()` hand-rolls exactly one value flow: it reads
`what_is.intent` and `what_became.intent` off the `use` children and
concatenates them into `aforementioned`. That is a non-general binding
smuggled through a special case. This generalises the one computation the
language already admitted.

### The design, and every decision in it

**Syntax** — `parse.py`. A trailing `as NAME` where `NAME` matches
`[A-Za-z_][A-Za-z0-9_]*`. It composes with `amp` in either order; each may
appear at most once. `Check.bind: str | None` in `ast.py`.

**Values** — one per kind, `measure.py:_run_one`. This is a *type* decision,
not decoration:

| kind | value | why |
| --- | --- | --- |
| `words` | `int` — the count | the number is the thing read |
| `exists` | `bool` | there is nothing else to read |
| `eq` | `bool` | the comparand is already known to the author |
| `contains` | **the file's read text** (`str`) | a bool cannot flow; binding exists so a later check can use what this one *read* |
| `run` | `int` — the exit code | stdout under `--allow-run` is deliberately not exposed in v1 |
| `use` | `bool` — the child's `ok` | child bindings stay **local**; general export is a separate decision, not front-loaded |

**Scope and order** — `measure.py`. The check list was an unordered set of
independent verdicts. It is now a **sequence**: evaluation is left to right,
each check sees an environment of prior bindings, and a name is visible only
*after* it is bound. `all`/`any` still folds pass/fail exactly as before —
only the reads thread through. **This is the real semantic change** and the
one a reviewer should attack hardest.

**Reference** — `$NAME` substitution into any check argument, `measure.py:_subst`.

Two refusals, both deliberate:

- **An unbound `$NAME` is refused, never silently emptied.** Substituting `""`
  would turn `exists $nope` into a check against the measure root and answer a
  question nobody asked. The shot's status is `refuse`, and a refused check
  binds nothing.
- **A substituted value is stripped of surrounding whitespace for use as an
  argument, and the bound value itself is not.** `contains` yields the file's
  text; a file read carries a trailing newline; an argument is a token.
  Without this, `contains manifest.txt "x" as p` then `exists $p` looks for a
  path ending in a newline and reports it missing — true and useless. This is
  a stated rule rather than magic, and it is the design decision here I am
  least certain of. **Attack this one.**

**Capability** — no new capability is introduced. But the existing one is
sharpened: once a bound name can fill a `run` argument, `--allow-run` means
*the measurer may execute plane-derived content*. That is a stricter reading,
not a looser one, and it is written at the call site.

**Conformance** — `bind` is a canonical semantic with its own row (§5). Only
`python-measure` preserves it. Every emitter is `unsupported`, because they
flatten checks at emit time and have no environment in which a name could
live. That is an honest cell, not a placeholder.

---

## 4. The capability model — what the cage actually holds

The founder's position, which the code now agrees with:

> Change happens regardless. You see a thing only on the basis of its inherent
> ability to change and your ability to observe that change; otherwise it is
> invisible to you.

So `--allow-run` and `--allow-write` **do not gate change**. The filesystem and
the shell's targets change regardless of what YA|RA is permitted to observe.
What they gate is what the *measuring process* may do to the plane during its
act of observation.

> **The cage holds the measurer, not change.**

Two capabilities exist:

- `--allow-run` — the measurer may execute a command in the measure root.
  Without it, `run` is `refuse`, not `fail`.
- `--allow-write` — the measurer may write `aforementioned.YA-RA` on a `cura`
  or `universe` door. **This was added today.** It previously shipped with no
  gate at all, while `run` — a smaller side effect on any reading — required
  one. Both propagate through `use` recursion, so a child door cannot acquire
  a capability its parent was not granted.

Paths are confined to the measure root (`paths.py:confined`, `PathEscape`).
A path escape is a refusal.

---

## 5. The conformance table, and its one honest admission

`semantics.py`. `CANONICAL` defines the meaning of each construct;
`CONFORMANCE` says, per backend, whether that meaning is `preserved`,
`weakened`, `observational`, `transport`, or `unsupported`.

```
| target         | words | exists | contains | eq   | run  | use  | all  | any  | bind |
| python-measure | pres  | pres   | pres     | pres | pres | pres | pres | pres | pres |
| python-emit    | pres  | pres   | pres     | pres | pres | pres | pres | pres | unsup|
| c              | pres  | weak   | weak     | weak | weak | unsup| pres | pres | unsup|
| cxx            | pres  | weak   | weak     | weak | weak | unsup| pres | pres | unsup|
| rust           | pres  | weak   | weak     | weak | weak | unsup| pres | unsup| unsup|
| kernel         | pres  | unsup  | unsup    | unsup| unsup| unsup| pres | unsup| unsup|
| wasm           | pres  | unsup  | unsup    | unsup| unsup| unsup| pres | unsup| unsup|
| toe            | pres  | weak   | weak     | weak | weak | unsup| pres | pres | unsup|
| quantum        | obs   | obs    | obs      | obs  | obs  | obs  | obs  | obs  | obs  |
| llm            | trans | trans  | trans    | trans| trans| trans| trans| trans| trans|
```

**`weakened` is new today and it is a confession.** Those cells said
`preserved`. They were false: the canonical semantics confine
`exists`/`contains`/`eq` to the measure root and gate `run` behind
`allow_run`, and the C and C++ runtimes take **no root parameter and perform no
confinement** — raw `access()`/`fopen()` — and call `system()` unconditionally.
The hosted backends silently dropped two canonical guarantees while the table
claimed they had not, which is precisely the silent weakening the table exists
to forbid. `weakened` means: *the backend produces a result, but not the
canonical one.*

**The differentiator the language claims — fail-closed cross-backend semantics —
is therefore currently an aspiration in a table, not a property the runtimes
have.** Closing it means either giving the hosted runtimes a root parameter and
a capability gate, or leaving the cells honest. Today only the label was fixed.

### The TOE divergence, closed today

`toe.py`'s `project()` refuses only on `action_is_door`; an unsigned door
returns `refused=False, missing_provenance=True`. `runtime/toe/toe.h` refused
*additionally* on an empty signer. So the same unsigned door was not-refused
under `ya-ra measure` and refused under an emitted `--to toe` program — a
silent cross-backend split on the one construct the language insists remains
valid. Python is canonical; the C runtime now records `missing_provenance` on
`struct yara_toe_z` and refuses only `action_is_door`.

---

## 6. The plane, and where "what becomes" lands

The question *"where does the output of a weave land?"* is malformed, and the
founder's answer dissolves it: you cannot weave logic into something without
`what-is` and `what-became` already placed on a perceived plane. The first act
of seeing what-is presupposes it was seen somewhere, with some perception, and
then changed.

**The Intent line declares the plane.** Not implicitly — literally:

```
Intent : to design something firmware of qiskit interacting with rust software
Pattern: YA|RA to facilitate that
Signed. Claude / Opus 5
```

That names two domains and the boundary between them: a typed interface stated
in words. The developer — human or model — fixed the plane by writing it.

So the stack is:

```
Intent    declares the plane
checks    bind it to what actually exists   (exists/contains/eq/use are its coordinates)
binding   carries a value from one coordinate to another   (new today)
Pattern   states how the binding can fail
Signed    says who staked it
```

And the landing place follows rather than being chosen: `measure.py` writes
`root / "aforementioned.YA-RA"`, where `root` is not a free output parameter —
it is the same plane on which `what-is` was perceived. **Output lands where
what-is already lives.** One place, which makes it a language rather than a
costume.

### `programs/qiskit-rust` — the founder's triple as a real program

```
Intent : to design something firmware of qiskit interacting with rust software
Pattern: YA|RA to facilitate that
Signed. Claude / Opus 5

⊦ exists interface.txt
⊦ exists bridge.rs
⊦ exists firmware.py
⊦ contains interface.txt "yara_" as symbol
⊦ contains bridge.rs $symbol
⊦ contains firmware.py $symbol
measure all
```

The firmware declares one symbol in `interface.txt`. The binding reads that
name and carries it to both other files, so **the Rust side is checked against
what the firmware actually says rather than against a symbol retyped in the
door**. Before binding, the door would have had to name `yara_qpu_submit`
itself — and would then have been checking its own copy of the truth.

It measures `ok`, `Z (6+0j)`. Rename the symbol on either side alone and it
contradicts:

```
contradicted: bridge.rs does not contain 'yara_qpu_submit'
```

It can fail, so it is Pattern.

---

## 7. What is proven, and how

The suite is **16 cases** — under a standing rule that eight is enough and
seventeen is the maximum, on the principle that a longer suite means each case
is weaker. Each case asserts a property *and every way that property breaks*,
not one assertion per case.

**A suite that has never been seen to fail proves only that it agrees with
itself.** Each change was reverted and the reds recorded:

| reversion | red |
| --- | --- |
| drop the binding environment in `measure.py` | 2 |
| unbound `$NAME` empties silently instead of refusing | 1 |
| `contains` yields a bool again instead of the read text | 2 |
| parser forgets `as` | 4 |
| conformance claims `bind` is preserved | 1 |
| the `aforementioned` write loses its capability gate | 2 |
| `toe.h` refuses an empty signer again | 1 |

Restored: 16 pass, CI green on `main`.

---

## 8. Open problems — the actual critique targets

Ranked by how much I think they matter. Each states what would settle it.

**1. RESOLVED, by external review — a real bug this open problem was
pointing at but had not found.** Two independent reviews (Kimi, DeepSeek) read
the fold in `measure.py` and showed the scenario in the previous paragraph
cannot happen, for a reason this document never stated: **one refusal vetoes
every pass under `any`** — `ok = checks_ok and not errors and not refusals`,
unconditionally, so a door with an unbound `$name` cannot pass by virtue of an
unrelated check succeeding. That rule already lived in `semantics.py`'s
`CANONICAL` (*"one passing check keeps the Intent unless a refusal occurred"*)
and had no other visible surface.

**But the review found what actually made the scenario reachable, and it was
worse than the one this document was worried about.** `env[c.bind] = shot.value`
ran whenever a check's status was not `"refuse"` — which includes `"fail"`. So
a *failed* check still bound its value: `None` for a missing file, the literal
string `"False"` for a failed `eq`, and — reproduced live, against the
founder's own `programs/qiskit-rust` — **the entire file's text** for a failed
`contains`. Break `interface.txt`'s marker and `symbol` still bound the whole
file; the next check then searched `bridge.rs` for that whole text, and the
contradiction it reported named a "symbol" that was never a symbol.

Fixed: only a `"pass"` binds. Verified by breaking it — reverting to `!=
"refuse"` turns the new test red — and by re-running the exact counterexample:
breaking `interface.txt` now produces `unbound $symbol`, not a corrupted
search. `TestBinding.test_a_failed_check_never_binds_and_refusal_vetoes_any`
covers both halves as one property, at the 17-case ceiling.

**2. The whitespace-strip on substitution is a judgement call, and external
review found the case it breaks.** Stripping makes `contains ... as p` →
`exists $p` work at all; not stripping makes it faithful and useless. The
case neither choice serves: `⊦ contains b.txt "" as tb` then `⊦ eq a.txt $tb` —
"file a equals file b", the plainest cross-file assertion a specification
language could want — can never pass for ordinary text files, because the
strip removes exactly the trailing newline that made the comparison exact.
Not fixed here. The reviewer's proposed shape is right: stripping is a
property of the *argument's role* (a path should be stripped; an `eq`
comparand should not), not a property of substitution itself — but that is a
second axis on every check kind, not a one-line change, and it is left for
the next pass rather than rushed. *Settled by: a per-role stripping rule, or a
two-place value check (`⊦ same $a $b`) that compares bound values directly
without going through argument substitution at all.*

**3. `contains` binds the whole file, which is a lot of value for a check
whose verdict is a substring test — and external review showed this is not
only inefficiency.** `⊦ contains large.log "ERROR: " as err` then
`⊦ contains other.log $err` searches `other.log` for the *entire contents* of
`large.log`, not for `"ERROR: "`. That is very likely never what a door author
wants, and the language currently offers no other way to say it. *Settled by:
binding the matched substring (or its position) instead of the whole read,
which is a real behavior change to a shipped check and is deliberately not
rushed into this pass.*

**4. Hosted backends still weaken four canonical cells.** The labels are now
honest but the runtimes are still wrong. `runtime/c/ya_ra.c` and the C++ twin
need a root parameter and a capability gate, or the language's central claim
stays aspirational. *Settled by: `preserved` cells that a test proves, in C.*

**5. Binding is `unsupported` on every emitter.** The emitters constant-fold at
emit time. Making `bind` work under `--to c` means emitting an environment and
substitution into the generated program — real work, and the first place the
emitters would stop being serializers of a Python-side answer. *Settled by: an
emitted C program that binds and substitutes.*

**6. `use` exports only `ok`.** A child door's bindings are local. This is a v1
decision, deliberately not front-loaded, and it is the obvious next primitive
after binding — the point at which doors compose rather than merely nest.

**7. Control flow does not exist and I claim it is not needed yet.** Binding
lets a value flow; it does not let a value *choose*. I believe that is the
correct next primitive and not part of this one. *This is a claim, not a
proof, and it is worth disagreeing with.*

**8. The quantum/TOE layer computes a number nothing consumes.** Honest, but
if it is never to gate anything, its cost is documentation and confusion.
*Settled by: either a consumer, or a decision to keep it explicitly decorative.*

---

## 9. What this does not claim

- **It does not claim YA|RA is a general-purpose language.** With binding it
  can carry a value across a plane. It still cannot implement an HTTP server, a
  queue consumer, or a payment flow. Curator should be *specified by* YA|RA
  doors, not *implemented in* them, and that specification role is the
  tractable and valuable job.
- **It does not claim the conformance table is now true.** It claims the table
  no longer lies about which cells are false.
- **It does not claim the strip rule is right.** It claims it is stated.
- **`git-author` provenance is observed attribution, not a signature.** Nothing
  here is cryptographic.

---

## 10. For the reviewer

The most useful thing you can do is break something. Concretely:

1. Write a door where ordered evaluation gives a result you think is wrong
   under `measure any`, and say what it should be.
2. Find an input where the whitespace strip loses information that mattered.
3. Write the C-side root confinement that would let those `weakened` cells
   honestly read `preserved`, with a test that fails without it.
4. Show a case where refusing an unbound name is the wrong call.
5. Show that binding is *not* sufficient — that some computation the language
   should express still cannot be, and name the primitive that would.

Everything above is checkable at `comfortcurators/sissyphus@6ebbedc`. If a
claim here does not survive contact with the source, the claim is wrong and
the source is right.
