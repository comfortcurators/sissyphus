# YA|RA rv0.2.0 — past the single action

The slide titled *The theory of everything (so far)* writes one number:

$$
Z=\int\mathcal{D}(\mathrm{Fields})\,\exp\!\left(i\int d^{4}x\sqrt{-g}\,\mathcal{L}\right)
$$

That is a total. It has no observer. It cannot fail as a door.

YA|RA does not replace $R$, $F_{\mu\nu}$, or $\psi$. It refuses to treat that integral as a door, and it computes a different number:

$$
Z_{\mathrm{YA|RA}}=\sum_k a_k\,[c_k\text{ passed}]
$$

attributed, signed, finite. `runtime/toe/toe.h` returns that sum, or refuses if the cut is unsigned.

## Type

A door's type is Signed. Checks have kinds `words | exists | run | contains | eq | use`. Unknown kinds do not parse. `use PATH` is a module: that path is a door, measured in the parent's collapse.

## Measure

- `measure all` — product of projectors. One fail contradicts the Intent.
- `measure any` — sum of projectors. One pass keeps the Intent.

## Hilbert / Born

Each check is a qubit. The unmeasured state is the product

$$
|\psi\rangle=\bigotimes_k \frac{|0\rangle+a_k|1\rangle}{\sqrt{1+|a_k|^2}}
$$

in $\mathbb{C}^{2^n}$. $|1\rangle$ is pass. Born's rule is $P(x)=|\langle x|\psi\rangle|^2$. Collapse projects onto the observed bitstring and renormalises. QASM emit prepares that product with `ry`/`rz` and measures. `amp` is not a costume; it is $a_k$.

## Kernel

The kernel is a syscall table, not a Linux driver.

| nr | name | arg |
| --- | --- | --- |
| 1 | WORDS | `const char *` |
| 2 | MEASURE | `const struct yara_k_door *` |
| 3 | EXISTS | hosted hook, else fail |

Polarity is `0 = ok` in C, C++, kernel, and TOE.

## LLM

Glimpse first. Depth second. `ya-ra hop` builds both frames. If `YARA_LLM_KEY` or `XAI_API_KEY` is set, it POSTs them to the model and records the reply. If not, the hop is dry and the JSON is still a valid two-phase envelope.

## C / C++

Emitted C is `yara_door_entry` plus optional `main`. Compile with `-DYARA_NO_MAIN` and link `ya_ra.c` to call a door from an existing program. C++ field is `how`; `measure()` is the verb.

Input → Logic → Output stays the founder diagram.
what is → change → what becomes
