# three-stacks

> ### Current status
>
> **Pantone and Vatter (2026) narrowed the answer to [17, 21]**, presented in
> [this MathFest talk](https://vincevatter.com/talks/2026-mathfest-stacks/).
> They proved that every permutation of length at most 16 is sortable and
> gave this unsortable permutation of length 21:
>
> ```
> 6-3-12-8-17-5-2-11-7-19-14-10-4-18-13-21-16-9-20-15-1
> ```
>
> This repository's independently obtained upper bound 22 is superseded. It
> now verifies their length-21 witness—including every one-point deletion and
> a checked DRAT certificate. Lengths **17–20 remain open**. See
> [results.md](results.md) for provenance, measurements, and limitations.

**A permutation of length 22 that three stacks in series cannot sort — with a
machine-checkable proof.**

```
6-14-2-10-4-18-7-12-3-20-15-9-5-19-13-22-8-17-11-21-16-1
```

It is a **basis element**: unsortable, but every one of its 22 one-point
deletions *is* sortable, each with an operation word you can replay by hand.
At the time this was built the record was 38 (Atkinson, 1992), so the bound
[14, 22] refuted Murphy's conjecture of 25 and matched Waton's guess of 22.

Full numbers, provenance, and caveats: **[results.md](results.md)**.

---

## The problem

Three stacks in series:

```
input ──▶ S1 ──▶ S2 ──▶ S3 ──▶ output
```

Four operations. Every element performs each exactly once, in order:

| op | effect |
|----|--------|
| `r1` | move the next input element onto S1 |
| `r2` | pop S1, push S2 |
| `r3` | pop S2, push S3 |
| `r4` | pop S3, append to output |

A permutation is *3-stack-sortable in series* if some legal sequence of
operations leaves `1,2,3,…` in the output. Every run is exactly `4n`
operations.

One stack sorts exactly the permutations avoiding `231` (Knuth). Two stacks
in series first fail at length 7. For three stacks, **the length of the
shortest permutation that cannot be sorted is open** — attributed to Waton,
and the subject of a beer wager between Elder (who guessed 15) and Waton (who
guessed 22).

![a sorting run](docs/img/51742638-k3.svg)

*Each bar is one value occupying one stack, over time. Sortability is exactly
the claim that all three lanes can be drawn with no two bars crossing.*
Interactive version: [`docs/visualiser.html`](docs/visualiser.html).

## Approach

Three facts make the search tractable:

**1. Sortability is a non-crossing condition.** Give each value `v` four event
times `t₁[v] < t₂[v] < t₃[v] < t₄[v]`. Then `π` is sortable **iff** those
times can be chosen so that

* `t₁` respects `π` (input order), and
* `t₄` respects value order (output is the identity), and
* for each stack, the occupancy intervals `[tₛ[v], tₛ₊₁[v]]` are pairwise
  **nested or disjoint, never crossing**.

Crossing is forbidden because it is exactly a LIFO violation: `w` pushed on
top of `v` but popped after it. That is the whole encoding — no simulation of
stack contents, just a total order on `4n` events with transitivity clauses.
Proved in [docs/notes.md](docs/notes.md) §3, and validated against brute force
exhaustively for k = 1, 2, 3 at n ≤ 7 before anything was built on it.

**2. Long witnesses are everywhere.** Random permutations of length 40 are
unsortable about a third of the time and decide in seconds. Finding *a*
witness is easy; the work is shrinking it.

**3. Basin hopping does the shrinking.** Greedy deletion stalls on whatever
basis element it happens to reach (33, then 29). Unsortability is closed
*upward*, so inserting points into a witness keeps it a witness, for free.
Perturb up, descend again on a fresh random path, keep the best. Accepting
*equal-length* results as the new starting point matters as much as the
perturbation — without it the walk re-perturbs one permutation and never
drifts.

```
random n=40  →  33  →  29  →  28 → 26 → 25 → 24  →  23 → 22
                greedy        basin hopping         + plateau drift
```

## Verify it yourself

```bash
# Ubuntu/Debian: install python3-venv first if ensurepip is unavailable
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -n 4                   # full exhaustive suite; expect it to take a while
python -m pytest -n 4 -m "not slow"     # quicker routine confidence check

# replay a sorting run by hand — no solver involved
python verify.py replay 231 --k 2 --ops 112123233

# re-decide a small case from scratch, independently
python verify.py exhaust 2435761 --k 2

# the headline claim, end to end
python scripts/verify_basis.py --perm 6-14-2-10-4-18-7-12-3-20-15-9-5-19-13-22-8-17-11-21-16-1
python proofcheck.py                    # drat-trim over every UNSAT claim
```

[`verify.py`](verify.py) and [`proofcheck.py`](proofcheck.py) import nothing
from the solver package, so a bug shared between checker and solver cannot
hide.

`proofcheck.py` needs [drat-trim](https://github.com/marijnheule/drat-trim)
and `scripts/certify.py` needs a CaDiCaL binary. Neither is bundled; the
Python tests do not require them. Build instructions, including the Ubuntu
build and the MinGW traps that cost hours, are in
[docs/building.md](docs/building.md).

## Check a candidate of your own

Lengths **17, 18, 19 and 20** are the open ones. If you have a permutation you
think three stacks cannot sort, this answers both questions about it — is it
unsortable, and is it minimal:

```bash
# solver verdict only; needs nothing but python-sat
python scripts/verify_basis.py --perm 6-3-12-8-17-5-2-11-7-19-14-10-4-18-13-21-16-9-20-15-1 --k 3 --skip-certificate

# the same, plus a DRAT certificate checked by drat-trim
python scripts/verify_basis.py --perm <your permutation> --k 3
```

Exit status is 0 for a basis element and 1 otherwise, and the output says
which way it failed:

* **sortable** — it prints an operation word you can replay with
  `verify.py replay`, so the refutation needs no trust in the solver;
* **not minimal** — it prints the shorter witness hiding inside it, which you
  can then feed back in;
* **basis element** — every one-point deletion comes with a replayable
  operation word, so the positive half of the claim is checkable with a
  twenty-line simulator.

Permutations are `6-3-12-...` or `2435761` for single digits. Reports land in
`results/` under a name tagged with the permutation's hash, so they never
overwrite the ones committed here.

## Hunt for something shorter

```bash
python scripts/hunt.py random --n 40 --rounds 10 --workers 8   # find and shrink
python scripts/hunt.py hop --perm <witness> --workers 8        # basin hop
python scripts/certify.py --perm <witness>                     # make artifacts
```

Local search is exhausted — every route reaches 22 and stops. The one
reduction that makes an *exhaustive* sweep possible at the frontier is the
**sorting dual** `D(pi) = inverse(reverse_complement(pi))`, which preserves
sortability (Vatter, [arXiv:2602.16355](https://arxiv.org/abs/2602.16355)
Prop. 5.2; derived in [docs/notes.md](docs/notes.md) §6). A permutation is
self-dual iff its complement is an involution, so there are `I(n)` of them
rather than `n!` — 46 million at length 17 against 356 trillion.

```bash
python scripts/dual.py verify                 # check the symmetry exhaustively
python scripts/dual.py sweep --n 17           # every self-dual candidate
python scripts/census.py --k 2 --maxlen 10    # complete basis census at k=2
```

Restricting to self-dual permutations is a conjecture, not a theorem — see
[results.md](results.md#the-sorting-dual) for what a miss does and does not
rule out.

## Layout

| path | what |
|---|---|
| [`unsortable/simulator.py`](unsortable/simulator.py) | brute-force ground truth, k stacks in series |
| [`unsortable/encoding.py`](unsortable/encoding.py) | the SAT encoding, `full` (auditable) and `reduced` (fast) modes |
| [`unsortable/minimizer.py`](unsortable/minimizer.py) | descent to a basis element, parallel across cores |
| [`unsortable/search.py`](unsortable/search.py) | witness hunting, structured families, basin hopping |
| [`unsortable/counting.py`](unsortable/counting.py) | the search-free counting ceiling |
| [`scripts/dual.py`](scripts/dual.py) | the sorting dual: verify it, sweep the permutations it fixes |
| [`scripts/census.py`](scripts/census.py) | exhaustive basis census (reproduces Atkinson's 22 at k=2) |
| [`verify.py`](verify.py) | **independent** replayer and exhaustive checker |
| [`proofcheck.py`](proofcheck.py) | **independent** drat-trim runner |
| [`docs/notes.md`](docs/notes.md) | proofs: the encoding, the prunings, downward closure |
| [`docs/visualiser.html`](docs/visualiser.html) | watch a permutation flow through the stacks |
| [`results.md`](results.md) | every number, with provenance |

## Caveats

* **An upper bound, not the answer.** This repository's length-22 permutation
  is a basis element, but Pantone and Vatter's later work gives the current
  interval **[17, 21]**.
* **Not peer reviewed.** Verified is not refereed.
* **The certificate proves the CNF is unsatisfiable**, not that the CNF asks
  the right question. See [results.md § Verification](results.md#verification).
* **Brute force cannot reach n = 22**, so at that size the simulator cannot
  independently re-decide the instance.
* Literature figures are taken from Vatter,
  [arXiv:2602.16355v2](https://arxiv.org/abs/2602.16355) (24 Aug 2026).
