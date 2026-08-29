# Results

Every number here says where it came from. "Verified" means the specific
combination of checks listed in [Verification](#verification) at the bottom.

## The headline

**The shortest permutation not sortable by three stacks in series has length
at most 23**, witnessed by

```
6-11-4-16-2-8-19-5-14-9-17-12-20-3-15-7-23-10-21-18-13-22-1
```

which is a **basis element** of the 3-stack-sortable class: it is unsortable,
and all 23 of its one-point deletions are sortable.

Artifacts: [`proofs/k3_n23_4a24b696.cnf`](proofs/), `.drat`, `.json`, and
[`results/basis_k3_n23.json`](results/) (operation words for all 23
deletions). A second, independently found basis element of length 24 is also
certified, as are ones of length 25, 29 and 33.

### State of the problem

| bound | length | source |
|---|---|---|
| lower bound -- all shorter permutations sort | >= 14 | Atkinson; every permutation of length 7*2^(t-2)-1 = 13 is 3-stack-sortable |
| Elder's guess | 15 | Elder-Waton wager |
| Waton's guess | 22 | Elder-Waton wager |
| **this repo** | **<= 23** | verified, certificate included |
| Murphy's conjecture | 25 | **refuted** -- see below |
| Atkinson 1992, Lemma 5 | <= 38 | previous record, "has stood for over thirty years" |
| Murphy | <= 39 / 43 | never presented |
| Tarjan | <= 41 | never presented |
| counting ceiling (M6) | <= 642 | rigorous, search-free, this repo |

Literature figures are as reported in Vincent Vatter, *An Assortment of
Problems in Permutation Patterns: Unimodality, Equivalence, Derangements, and
Sorting*, [arXiv:2602.16355v2](https://arxiv.org/abs/2602.16355) (24 August
2026). That survey states that **no explicit unsortable permutation for three
stacks is presented anywhere** -- not Tarjan's, not Murphy's, not Atkinson's
38. As far as we can tell the permutations here are the first explicit,
independently checkable witnesses of any length.

So the answer lies in **[14, 23]**, one step from Waton's guess of 22.

### Murphy's conjecture, precisely

Vatter states it as: "Murphy [69, Conjecture 265] guesses more generally that
t stacks in series can sort all permutations of length up to (t+1)!, which
would give **25** as the length of the shortest permutation unsortable by
three stacks in series."

So for t = 3 the conjecture is that *every* permutation of length <= 4! = 24
is sortable, and hence that the answer is 25. The length-24 witness alone
already refutes it -- a counterexample sitting exactly on the boundary the
conjecture predicts -- and the length-23 one puts it further out of reach.

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
| 10 | 16,796 | *running* | *running* | 3,628,800 |

Reality checks, all reproduced:

* **1 stack** gives the Catalan numbers exactly (16,796 = C(10) at n = 10),
  and the sortable permutations are precisely those avoiding `231` -- checked
  permutation by permutation for n <= 7 (`tests/test_simulator.py`).
* **2 stacks in series** first fail at length **7**, with 22 unsortable
  permutations there. Length 7 is the known answer (Tarjan). Since all
  length-6 permutations sort, those 22 are all basis elements.
* **3 stacks in series** sort everything through n = 9, consistent with
  Atkinson's result that everything up to length 13 sorts.

## Where unsortable permutations start appearing

Random permutations, decided by the SAT encoding (`mode="reduced"`,
CaDiCaL). This is what made the hunt tractable -- witnesses are *common* at
length 40, not rare.

| n | unsortable | median solve |
|---:|---:|---:|
| 12-35 | 0 / 12 at each length | 0.1 - 2.8 s |
| 40 | 4 / 12 | 5.9 s |
| 50 | 10 / 12 | 16.6 s |
| 60 | 9 / 9 | 28.4 s |
| 80 | 5 / 5 | 57.7 s |

## How the bound came down

Greedy single-point descent stalls on whatever basis element its random
deletion order reaches. Basin hopping breaks the stall: perturb *upward*
(insertion preserves unsortability by upward closure, so every iterate is
still a guaranteed witness -- no search wasted), then descend again along a
fresh random path.

Accepting **equal-length** results as the new current point turned out to
matter as much as the perturbation itself. Without it, every iteration
perturbs the same permutation and the search merely retries one point; the
run sat at 24 for well over a hundred iterations. With plateau drift it
wanders across the set of length-L basis elements, and that is where the
opening to L-1 was found.

```
random n=40 witness
  -> 33   greedy descent (basis element)
  -> 29   greedy descent, different seed (basis element)
  -> 28 -> 26 -> 25 -> 24        basin hopping
  -> 23                          basin hopping + plateau drift
```

Certified basis elements: **23**, 24, 25, 29, 33.

## The counting ceiling (M6)

A run of the machine is a ballot word of length (k+1)n; a ballot word
determines the whole run without reference to values, so the sortable
permutations are exactly the image of the ballot words and

    #sortable(n)  <=  B_k(n) = ((k+1)n)! * prod_{j<=k} j! / prod_{j<=k} (n+j)!

Once n! > B_k(n) an unsortable permutation must exist. Exact crossovers:

| k | crossover | true answer |
|---:|---:|---|
| 1 | **3** | **3** (`231`) -- the bound is exactly tight |
| 2 | 50 | 7 |
| 3 | **642** | in [14, 23] |
| 4 | 8,383 | unknown |

Rigorous and search-free, but weak for k >= 2 -- it is 7x the truth at k = 2.
Worth stating because it holds even if every search fails. (The original plan
guessed the k = 3 crossover would land near 100; the real value is 642,
because B_3(n) ~ 256^n and n! only overtakes that around n ~ e*256.)

## What the basis elements look like

`scripts/analyse_basis.py` over the distinct basis elements found so far
(lengths 23, 24, 25, 26x2, 27, 28x2, 29x2):

* **Nine of the ten end in `1`.** Under a uniform model a permutation ends in
  1 with probability 1/n ~ 4%, so this is on the order of 1e-12. There is a
  clean mechanical reason: if `1` is the *last* input element, then at the
  moment it arrives every other value is already distributed across the three
  stacks, and every one of them must leave *after* `1` -- in whatever LIFO
  order it happens to be frozen in. Putting `1` last maximises the pressure
  on the machine, and the search discovered this without being told.
* **Inversion density runs below random**, 0.41-0.48 against ~0.50, and the
  shorter witnesses have the lower densities. Shorter basis elements look
  less random, which suggests the short ones live in a structured corner of
  the space.
* **No two are related by any symmetry** -- consistent with the finding that
  none of the four symmetries preserves sortability.
* Every length-4 pattern occurs in every basis element, so whatever
  avoidance structure exists lives at larger patterns.

### Structured families are all sortable

Iterated direct and skew sums of `231`, `312`, `2413`, `3142`, and layered
permutations with uniform layers, at every length up to 60: **all sortable**
(`python scripts/hunt.py families`). At length 60 a *random* permutation is
unsortable essentially always (9/9 in the sweep above), yet every structured
family member sorts.

So unsortability here is not built by stacking local obstructions -- it
requires genuine disorder. That is why the plan's first route (structured
families) yields nothing, and why descending from long random witnesses was
the approach that worked. Combined with the inversion-density observation
above, the short basis elements appear to sit in a narrow band: too ordered
and three stacks cope easily, too disordered and the witness is long.

## Negative results worth recording

* **No symmetry is available.** None of reverse, complement, inverse, or
  reverse-complement preserves sortability, for one stack or for two --
  measured exhaustively to n = 7. For k = 1: `231` is unsortable while its
  reverse `132`, complement `213`, inverse `312` and reverse-complement `312`
  all sort. So no symmetry reduction is sound and none is used.
* **Downward closure holds**, as it must -- verified exhaustively for
  k = 1, 2, 3 at n <= 7, and proved in [docs/notes.md](docs/notes.md) §4. The
  entire minimiser rests on it.
* **Deleting more than one point from a basis element is provably useless.**
  Any multi-point deletion is a one-point deletion of an already-sortable
  one-point deletion, so downward closure makes it sortable. The only route
  to a shorter witness is a *different* basis element. This is why the
  minimiser has no "deep" mode and why basin hopping is the search.
* **PySAT's in-memory proof capture truncates.** For the length-33 witness it
  returned 15 MB of a proof lingeling reported writing as 6.1 MB, and
  drat-trim rejected it ("conflict claimed, but not detected") on an instance
  that is genuinely unsatisfiable. Different solvers failed on different
  instances, which is the signature of lossy capture rather than a wrong
  answer. All certificates are now produced by a solver **binary writing DRAT
  straight to a file**. A truncated proof that still verifies is sound --
  drat-trim checks every step -- but one that fails is indistinguishable from
  a wrong answer, which defeats the point of a certificate.

## Verification

Every claim in this file passes the checks that apply to it.

| claim type | checks |
|---|---|
| "pi is sortable" | an explicit operation word, **replayed** by [`verify.py`](verify.py), which shares no code with the solver or encoder |
| "pi is unsortable" | CaDiCaL UNSAT + **DRAT certificate verified by drat-trim** (third-party) + an independent second solver (glucose4) + the brute-force simulator wherever it can still run |
| "pi is a basis element" | the above, plus n replayed operation words, one per one-point deletion |
| the encoding itself | proved in [docs/notes.md](docs/notes.md) §3, and exhaustively equal to brute force for k = 1,2,3 at n <= 7 in both encoding modes, sampled to n = 11 |

All five certificates currently in `proofs/` verify:

```
k3_n23_4a24b696  VERIFIED   k3_n24_3a74bbc0  VERIFIED   k3_n25_b6356c09  VERIFIED
k3_n29_9d1e218c  VERIFIED   k3_n33_10985bce  VERIFIED
```

Reproduce:

```
python -m pytest                                   # 253 tests
python scripts/verify_basis.py --perm 6-11-4-16-2-8-19-5-14-9-17-12-20-3-15-7-23-10-21-18-13-22-1
python proofcheck.py                               # drat-trim over every UNSAT claim
python verify.py claims results/claims.json        # replay every SAT claim
```

### What the certificate does not say

drat-trim proves *the CNF is unsatisfiable*. That the CNF asks the
sortability question is a separate matter, established by the proof in
docs/notes.md §3 and by exhaustive agreement with brute force. A reader who
distrusts the encoding should check that proof; a reader who distrusts the
solver should run drat-trim. The two are independent, deliberately.

The brute-force simulator cannot reach n = 23, so at that size the simulator
leg is absent and the encoding's correctness is carried by its agreement at
small n. This is the weakest link in the chain and is stated plainly rather
than buried.
