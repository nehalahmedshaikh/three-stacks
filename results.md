# Results

Every number here says where it came from. "Verified" means the specific
combination of checks listed in [Verification](#verification) at the bottom.

## The headline

**The shortest permutation not sortable by three stacks in series has length
at most 22**, witnessed by

```
6-14-2-10-4-18-7-12-3-20-15-9-5-19-13-22-8-17-11-21-16-1
```

which is a **basis element** of the 3-stack-sortable class: it is unsortable,
and all 22 of its one-point deletions are sortable.

Artifacts: [`proofs/k3_n22_332bfe43.cnf`](proofs/), `.drat`, `.json`, and
[`results/basis_k3_n22.json`](results/) (operation words for all 22
deletions). Basis elements of length 23 and 24 are separately certified, as
are witnesses of length 25, 29 and 33. Every distinct basis element found is
recorded in [`results/basis_elements.json`](results/basis_elements.json).

### State of the problem

| bound | length | source |
|---|---|---|
| lower bound -- all shorter permutations sort | >= 14 | Atkinson; every permutation of length 7*2^(t-2)-1 = 13 is 3-stack-sortable |
| Elder's guess | 15 | Elder-Waton wager |
| Waton's guess | 22 | Elder-Waton wager |
| **this repo** | **<= 22** | verified, certificate included |
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

So the answer lies in **[14, 22]** -- exactly Waton's guess of 22, and 7 above
Elder's 15.

### Murphy's conjecture, precisely

Vatter states it as: "Murphy [69, Conjecture 265] guesses more generally that
t stacks in series can sort all permutations of length up to (t+1)!, which
would give **25** as the length of the shortest permutation unsortable by
three stacks in series."

So for t = 3 the conjecture is that *every* permutation of length <= 4! = 24
is sortable, and hence that the answer is 25. The length-24 witness alone
already refutes it -- a counterexample sitting exactly on the boundary the
conjecture predicts -- and the length-22 one puts it well out of reach.

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
| 10 | 16,796 | 3,092,691 | **3,628,800** | 3,628,800 |

Reality checks, all reproduced:

* **1 stack** gives the Catalan numbers exactly -- 16,796 = C(10) and
  58,786 = C(11) -- and the sortable permutations are precisely those
  avoiding `231`, checked permutation by permutation for n <= 7
  (`tests/test_simulator.py`).
* **2 stacks in series** first fail at length **7**, with 22 unsortable
  permutations there. Length 7 is the known answer (Tarjan). Since all
  length-6 permutations sort, those 22 are all basis elements.
* **3 stacks in series** sort **everything** through n = 10 -- all 3,628,800
  permutations, checked one by one, none unsortable. This is the strongest
  available test of the machine model: Atkinson's result says every
  permutation of length <= 13 sorts, and a single unsortable one at n = 10
  would mean we are simulating the wrong machine and every bound here is
  void. (n = 11 would take ~50 hours by brute force and was not attempted;
  the sampled test at n = 12-13 covers that range instead.)

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
  -> 23 -> 22                    basin hopping + plateau drift
```

Certified basis elements: **22**, 23, 24; certified witnesses at 25, 29, 33.
Thirteen distinct basis elements in total, listed in
[`results/basis_elements.json`](results/basis_elements.json).

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
| 3 | **642** | in [14, 22] |
| 4 | 8,383 | unknown |

Rigorous and search-free, but weak for k >= 2 -- it is 7x the truth at k = 2.
Worth stating because it holds even if every search fails. (The original plan
guessed the k = 3 crossover would land near 100; the real value is 642,
because B_3(n) ~ 256^n and n! only overtakes that around n ~ e*256.)

## What the basis elements look like

`scripts/analyse_basis.py` over the distinct basis elements found so far
(lengths 22, 23, 24, 25, 26x2, 27, 28x2, 29x2, 31, 33):

* **Eleven of the thirteen end in `1`**, and both exceptions are among the
  longest (29 and 33). Under a uniform model a permutation ends in 1 with
  probability 1/n ~ 4%, so eleven of thirteen is astronomically unlikely by
  chance. There is a clean mechanical reason: if `1` is the *last* input element, then at the
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

### The witnesses have a measurable shape, and it is causal

Over 25 basis elements of lengths 22-29 (`scripts/shape.py`):

| property | basis elements | uniform permutation |
|---|---|---|
| position of value 1 | median 1.00 of the way through (range 0.93-1.00) | 0.50 |
| position of value 2 | median 0.18 | 0.50 |
| first entry, as a fraction of n | median 0.27 (range 0.25-0.48) | 0.50 |
| alternation (zigzag rate) | 0.81-0.90 | 0.67 |

They are strongly **zigzag** permutations that open about a quarter of the
way up the value range and end on 1.

This is not just a description of what the search happened to find -- it is
*causal*, and the cheapest way to show that is to sample from the profile and
count. At length 36, 150 samples each (`scripts/structured_search.py`):

| distribution | unsortable |
|---|---:|
| uniform | 4 / 150 (2.7%) |
| value 1 forced last | 37 / 150 (24.7%) |
| zigzag + value 1 last | **100 / 150 (66.7%)** |

A 25x improvement in hit rate. Since a witness certifies itself, a biased
search costs nothing in rigour -- which is why `hunt.py random --structured`
now draws its starting points from this profile instead of uniformly.

What does *not* work is naive extrapolation across lengths: resampling all 25
basis elements down to length 21 (preserving the normalised shape) gives 25
candidates, and every one of them sorts. The shape is a strong prior, not a
formula.

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

## Why the search stops at 22

The bound fell 24 -> 23 in 78 hopping iterations and 23 -> 22 in 149, then sat
at 22 for several thousand. That is a different regime, and it is measurable.

Take a witness and decide **every** same-length neighbour -- all
transpositions, all single-point relocations, all adjacent-value swaps. For
n = 22 that is 651 permutations, about two minutes across cores:

| case | neighbours still unsortable | |
|---|---:|---|
| k=2, n=7 -- the **known minimum** | 1 / 51 (1.96%) | exhaustive |
| k=3, n=29 | ~13% | sampled (300) |
| k=3, n=24 | ~1.3% | sampled (300) |
| k=3, n=23 | 4 / 715 (0.56%) | exhaustive |
| k=3, n=22 | **0 / 651 (0%)** | exhaustive |

So the length-22 witness is an isolated point: not one of its 651 neighbours
is unsortable. That is why basin hopping stalled and why a same-length walk
is useless there -- there is nowhere to step. It also explains why hopping
worked at all: it never moves sideways at the target length, it descends from
lengths where the unsortable set is still fat.

**This is not evidence that 22 is the answer.** The k=2 row is the control
that rules that inference out: at the *known* minimum for two stacks the
neighbourhood is not empty either, and a walk started one above it drops to
length 7 immediately. Isolation measures how hard the witness is to move
away from, not how close the bound is to the truth. The answer remains
anywhere in [14, 22].

What the enumeration is good for is **population**. The exhaustive
neighbourhood of the length-23 witness turned up four new length-23 basis
elements in under three minutes -- and structure cannot be inferred from a
single example. `scripts/harvest.py` runs this as a breadth-first search over
the basis-element graph: every unsortable neighbour that is minimal becomes a
new node, and any that is *non-minimal* immediately yields a witness one
shorter. That is the current route, and it serves both goals at once.

## The landscape has no gradient (a negative result)

Every search here is blind, because sortability is a yes/no answer: at length
21 everything we try is sortable and they all look identical. The obvious fix
is to score permutations by *how nearly* unsortable they are. For a
permutation `p` of length L define

    f(p) = how many one-point extensions of p (length L+1) are unsortable

which is positive exactly when `p` sits inside a length-(L+1) obstruction.
It is affordable only because of `FixedLengthDecider` -- f costs (L+1)^2
decisions, 484 at L = 21 -- and it has a second payoff: every unsortable
extension it finds is a new length-22 basis element, and we have only one.

Measured (`scripts/gradient.py`, 484 decisions per evaluation):

| sample | f |
|---|---|
| the 22 one-point deletions of our length-22 witness | **1, every one of them** |
| 12 same-length neighbours of one of those deletions | 0 |
| 12 uniform random length-21 permutations | 0 |

So f is not a gradient, it is a delta function. Each deletion has *exactly
one* unsortable extension -- the witness we already had -- and everything
around them scores zero. The witness is isolated not just under same-length
moves (0 of 651 neighbours unsortable) but in the containment order too:
nothing else of length 22 contains any of its deletions.

That kills gradient-guided search at this length, and it is worth stating
plainly rather than quietly dropping. It also sharpens the picture from the
neighbourhood table above: the obstruction is a needle, and the space around
it carries no signal pointing at it. Progress below 22 needs a *construction*
-- a reason certain permutations must be unsortable -- rather than any search
that has to be led there by local information.

## What the refutation actually says

A DRAT proof certifies a contradiction but does not explain it.  drat-trim's
`-c` flag extracts the **unsatisfiable core** -- the subset of the original
constraints that participate -- and mapping those clauses back to what they
encode says *why* a permutation is unsortable.  Two independent witnesses
(`scripts/core.py`):

| | length 22 | length 24 |
|---|---:|---:|
| core size | 6,121 / 220,966 (2.8%) | 7,823 / 287,534 (2.7%) |
| input-order constraints used | **21 of 21** | **23 of 23** |
| output-order constraints used | **21 of 21** | **23 of 23** |
| non-crossing on S1 | 188 | 234 |
| non-crossing on **S2** | **317** | **380** |
| non-crossing on S3 | 190 | 234 |

Three things fall out, and they agree across both:

* **Every input and output constraint is needed.** Not a single one is
  dispensable, which is what being a basis element looks like at the level
  of the proof rather than by definition.
* **S1 and S3 carry near-identical load, and the middle stack carries about
  1.65x either** (317 vs 189, 380 vs 234).  That is a sharp invariant.  It
  has a natural reading: S1 is pinned by the input order and S3 by the output
  order plus its monotonicity invariant, so S2 is the free buffer that has to
  absorb the mismatch -- and the obstruction is precisely that it cannot.
* **The core is dense, not local.** 2.8% of the clauses, but spread over
  every value and every ordering constraint.  There is no small gadget
  driving the contradiction.

That last point is the explanation for the wall.  Unsortability here is a
global property of all the interleavings at once, not something a short
sub-pattern certifies -- which is exactly why local search finds no gradient
(f = 0 off the witness), why no pruning is available (there is no short
obstruction to prune with), and why the witnesses are isolated points.  The
blocker is a property of the problem, not of the search.

The S2-loading invariant is the one lead that points somewhere: it suggests
building candidates that maximally overload the middle stack, rather than
sampling and hoping.

## Is the model even right?

The bounds here are worthless if we are simulating the wrong machine. A model
*more restrictive* than "three stacks in series" would call permutations
unsortable that really are sortable, and every number above would be too
small. This is the one failure mode that no amount of solver verification
catches, because the solver would be faithfully answering the wrong question.

The literature supplies sharp, falsifiable predictions at three different
points, and the model hits all of them:

| prediction | source | what we get |
|---|---|---|
| 1 stack sorts exactly `Av(231)`, counted by the Catalan numbers | Knuth | exact, permutation by permutation to n = 7; counts match to n = 11 (58,786 = C(11)) |
| 2 stacks in series first fail at length **7** | Tarjan | exactly 7 -- not 6 (too restrictive), not 8 (too permissive) |
| every permutation of length <= 13 is 3-stack-sortable | Atkinson | **exhaustive** at n = 10 (all 3,628,800 sortable); 800 random permutations at n = 12 and n = 13: **zero** unsortable |

That last row is the direct test. The exhaustive half (`scripts/count_sortable.py`)
leaves no room at n = 10 at all; the sampled half (`scripts/validate_model.py`)
reaches to the very top of the known-sortable range. If our machine were even
slightly too restrictive, this is exactly where it would show, and it does not. Every one of
those 800 sortable verdicts also came with an operation word that was
*replayed* on the independent simulator in `verify.py` and really did sort --
so the SAT solver is not merely saying "satisfiable", it is producing runs
that work.

A model error would have to be wrong in a way that simultaneously reproduces
Catalan numbers at k = 1, lands exactly on 7 at k = 2, and leaves everything
below 14 sortable at k = 3. The remaining honest gap is that all three checks
live at n <= 13, and the witnesses are at n = 22. The encoding has no
size-dependent logic -- clause generation is uniform in n -- so there is no
natural mechanism for it to become wrong only above 13, but it is not
something the checks above rule out.

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

All six certificates currently in `proofs/` verify:

```
k3_n22_332bfe43  VERIFIED   k3_n23_4a24b696  VERIFIED   k3_n24_3a74bbc0  VERIFIED
k3_n25_b6356c09  VERIFIED   k3_n29_9d1e218c  VERIFIED   k3_n33_10985bce  VERIFIED
```

Reproduce:

```
python -m pytest                                   # 253 tests
python scripts/verify_basis.py --perm 6-14-2-10-4-18-7-12-3-20-15-9-5-19-13-22-8-17-11-21-16-1
python proofcheck.py                               # drat-trim over every UNSAT claim
python verify.py claims results/claims.json        # replay every SAT claim
```

### What the certificate does not say

drat-trim proves *the CNF is unsatisfiable*. That the CNF asks the
sortability question is a separate matter, established by the proof in
docs/notes.md §3 and by exhaustive agreement with brute force. A reader who
distrusts the encoding should check that proof; a reader who distrusts the
solver should run drat-trim. The two are independent, deliberately.

The brute-force simulator cannot reach n = 22, so at that size the simulator
leg is absent and the encoding's correctness is carried by its agreement at
small n. This is the weakest link in the chain and is stated plainly rather
than buried.
