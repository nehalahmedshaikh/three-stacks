# Results

Every number here says where it came from. "Verified" means the specific
combination of checks listed in [Verification](#verification) at the bottom.

## The headline

**The shortest permutation not sortable by three stacks in series has length
at most 24**, witnessed by

```
6-15-2-17-9-4-19-7-13-3-18-10-24-5-20-12-23-8-16-21-11-14-22-1
```

which is a **basis element** of the 3-stack-sortable class: it is unsortable,
and all 24 of its one-point deletions are sortable.

Artifacts: [`proofs/k3_n24_3a74bbc0.cnf`](proofs/), `.drat`, `.json`, and
[`results/basis_k3_n24.json`](results/) (operation words for all 24
deletions).

### State of the problem

| bound | length | source |
|---|---|---|
| lower bound — all shorter permutations sort | ≥ 14 | Atkinson; every permutation of length 7·2<sup>t−2</sup>−1 = 13 is 3-stack-sortable |
| Elder's guess | 15 | Elder–Waton wager |
| Waton's guess | 22 | Elder–Waton wager |
| **this repo** | **≤ 24** | verified, certificate included |
| Murphy's conjecture | 25 | **refuted** — see below |
| Atkinson 1992, Lemma 5 | ≤ 38 | previous record, "has stood for over thirty years" |
| Murphy | ≤ 39 / 43 | never presented |
| Tarjan | ≤ 41 | never presented |
| counting ceiling (M6) | ≤ 642 | rigorous, search-free, this repo |

Literature figures are as reported in Vincent Vatter, *An Assortment of
Problems in Permutation Patterns: Unimodality, Equivalence, Derangements, and
Sorting*, [arXiv:2602.16355v2](https://arxiv.org/abs/2602.16355) (24 August
2026), §on stacks in series. That survey states that **no explicit unsortable
permutation for three stacks is presented anywhere** — not Tarjan's, not
Murphy's, not Atkinson's 38. As far as we can tell the length-24 permutation
above is the first explicit, independently checkable witness of any length.

So the answer lies in **[14, 24]**.

### Murphy's conjecture, precisely

Vatter states it as: "Murphy [69, Conjecture 265] guesses more generally that
t stacks in series can sort all permutations of length up to (t+1)!, which
would give **25** as the length of the shortest permutation unsortable by
three stacks in series."

So for t = 3 the conjecture is that *every* permutation of length ≤ 4! = 24
is sortable, and hence that the answer is 25. The length-24 permutation above
is unsortable, so the conjecture is false: it is a counterexample sitting
exactly at the boundary the conjecture predicts.

## Exhaustive counts of sortable permutations

Computed by [`unsortable/simulator.py`](unsortable/simulator.py) (brute-force
DFS), via `python scripts/count_sortable.py`.

| n | 1 stack | 2 stacks in series | 3 stacks in series | n! |
|---:|---:|---:|---:|---:|
| 1 | 1 | 1 | 1 | 1 |
| 2 | 2 | 2 | 2 | 2 |
| 3 | 5 | 6 | 6 | 6 |
| 4 | 14 | 24 | 24 | 24 |
| 5 | 42 | 120 | 120 | 120 |
| 6 | 132 | 720 | 720 | 720 |
| 7 | 429 | 5,018 | 5,040 | 5,040 |
| 8 | 1,430 | 39,374 | 40,320 | 40,320 |
| 9 | 4,862 | 337,816 | 362,880 | 362,880 |

Reality checks, all reproduced:

* **1 stack** gives the Catalan numbers exactly, and the sortable
  permutations are precisely those avoiding `231` — checked permutation by
  permutation for n ≤ 7 (`tests/test_simulator.py`).
* **2 stacks in series** first fail at length **7**, with 22 unsortable
  permutations there. Length 7 is the known answer (Tarjan). Since all
  length-6 permutations sort, those 22 are all basis elements.
* **3 stacks in series** sort everything through n = 9, consistent with
  Atkinson's result that everything up to length 13 sorts.

## Where unsortable permutations start appearing

Random permutations, decided by the SAT encoding (`mode="reduced"`,
CaDiCaL). This is what made the hunt tractable — witnesses are *common* at
length 40, not rare.

| n | unsortable | median solve |
|---:|---:|---:|
| 12–35 | 0 / 12 at each length | 0.1 – 2.8 s |
| 40 | 4 / 12 | 5.9 s |
| 50 | 10 / 12 | 16.6 s |
| 60 | 9 / 9 | 28.4 s |
| 80 | 5 / 5 | 57.7 s |

## How the bound came down

Greedy single-point descent stalls on whatever basis element its random
deletion order reaches. Basin hopping breaks the stall: perturb *upward*
(insertion preserves unsortability by upward closure, so every iterate is
still a guaranteed witness — no search wasted), then descend again along a
fresh random path.

```
random n=40 witness
  -> 33   greedy descent (basis element)
  -> 29   greedy descent, different seed (basis element)
  -> 28 -> 26 -> 25 -> 24     basin hopping
```

Certified basis elements found so far: **24**, 25, 29, 33.

## The counting ceiling (M6)

A run of the machine is a ballot word of length (k+1)n; a ballot word
determines the whole run without reference to values, so the sortable
permutations are exactly the image of the ballot words and

    #sortable(n)  <=  B_k(n) = ((k+1)n)! * prod_{j<=k} j! / prod_{j<=k} (n+j)!

Once n! > B_k(n) an unsortable permutation must exist. Exact crossovers:

| k | crossover | true answer |
|---:|---:|---|
| 1 | **3** | **3** (`231`) — the bound is exactly tight |
| 2 | 50 | 7 |
| 3 | **642** | in [14, 24] |
| 4 | 8,383 | unknown |

Rigorous and search-free, but weak for k ≥ 2 — it is 27× the truth at k = 2.
Worth stating because it holds even if every search fails. (The original plan
guessed the k = 3 crossover would land near 100; the real value is 642,
because B₃(n) ~ 256ⁿ and n! only overtakes that around n ≈ e·256.)

## Negative results worth recording

* **No symmetry is available.** None of reverse, complement, inverse, or
  reverse-complement preserves sortability, for one stack or for two —
  measured exhaustively to n = 7. For k = 1: `231` is unsortable while its
  reverse `132`, complement `213`, inverse `312` and reverse-complement `312`
  all sort. So no symmetry reduction is sound and none is used.
* **Downward closure holds**, as it must — verified exhaustively for
  k = 1, 2, 3 at n ≤ 7, and proved in [docs/notes.md](docs/notes.md) §4. The
  entire minimiser rests on it.
* **PySAT's in-memory proof capture truncates.** For the length-33 witness it
  returned 15 MB of a proof lingeling reported writing as 6.1 MB, and
  drat-trim rejected it ("conflict claimed, but not detected") on an instance
  that is genuinely unsatisfiable. Different solvers failed on different
  instances, which is the signature of lossy capture rather than a wrong
  answer. All certificates are now produced by a solver **binary writing DRAT
  straight to a file**. A truncated proof that still verifies is sound —
  drat-trim checks every step — but one that fails is indistinguishable from a
  wrong answer, which defeats the point of a certificate.

## Verification

Every claim in this file passes the checks that apply to it.

| claim type | checks |
|---|---|
| "π is sortable" | an explicit operation word, **replayed** by [`verify.py`](verify.py), which shares no code with the solver or encoder |
| "π is unsortable" | CaDiCaL UNSAT + **DRAT certificate verified by drat-trim** (third-party) + an independent second solver (glucose4) + the brute-force simulator wherever it can still run |
| "π is a basis element" | the above, plus n replayed operation words, one per one-point deletion |
| the encoding itself | proved in [docs/notes.md](docs/notes.md) §3, and exhaustively equal to brute force for k = 1,2,3 at n ≤ 7 in both encoding modes, sampled to n = 11 |

Reproduce:

```
python -m pytest                                   # 130 tests
python scripts/verify_basis.py --perm 6-15-2-17-9-4-19-7-13-3-18-10-24-5-20-12-23-8-16-21-11-14-22-1
python proofcheck.py                               # drat-trim over every UNSAT claim
python verify.py claims results/claims.json        # replay every SAT claim
```

### What the certificate does not say

drat-trim proves *the CNF is unsatisfiable*. That the CNF asks the
sortability question is a separate matter, established by the proof in
docs/notes.md §3 and by exhaustive agreement with brute force. A reader who
distrusts the encoding should check that proof; a reader who distrusts the
solver should run drat-trim. The two are independent, deliberately.

The brute-force simulator cannot reach n = 24, so at that size the
simulator leg is absent and the encoding's correctness is carried by its
agreement at small n. This is the weakest link in the chain and is stated
plainly rather than buried.
