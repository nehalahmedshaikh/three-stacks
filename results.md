# Results

Every number here says where it came from. "Verified" means the specific
combination of checks listed in [Verification](#verification) at the bottom.

## Superseded

Pantone and Vatter (2026) have the bound at **[17, 21]** --
[MathFest talk](https://vincevatter.com/talks/2026-mathfest-stacks/). Their
length-21 witness `6-3-12-8-17-5-2-11-7-19-14-10-4-18-13-21-16-9-20-15-1` is
independently verified in this repo (unsortable, all 21 one-point deletions
sortable with replayed operation words, DRAT checked by drat-trim); its
certificate is `proofs/k3_n21_39ee15ca.*` and it is tagged `external` in
`results/claims.json`. They also proved that every permutation of length 16
or less is sortable, so the answer is at least 17 (up from Atkinson's 14),
and report 7,354 minimal permutations at length 22 where this repo's search
found one. That leaves lengths **17, 18, 19 and 20** open, which is what
[The sorting dual](#the-sorting-dual) sweeps.

Two things below are corrected by their work rather than wrong on their own
terms. Atkinson (1992) had already proved that **every shortest permutation
unsortable by t stacks in series ends in 1** -- the pattern measured in
[What the basis elements look like](#what-the-basis-elements-look-like) is
that theorem, not a new observation, and the two exceptions there are length
29 and 33, which are minimal but not shortest. And the isolation results are
local facts about the particular witnesses probed: 7,354 minimal permutations
exist at length 22, so that set is large and scattered rather than small.

Everything else stands as measured. This repo's own bound is 22.

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
| Atkinson 1992, Lemma 5 | <= 38 | the record when this was built |
| **Pantone and Vatter 2026** | **<= 21**, lower bound 16 | supersedes all of the above |
| Murphy | <= 39 / 43 | never presented |
| Tarjan | <= 41 | never presented |
| counting ceiling (M6) | <= 642 | rigorous, search-free, this repo |

Literature figures are as reported in Vincent Vatter, *An Assortment of
Problems in Permutation Patterns: Unimodality, Equivalence, Derangements, and
Sorting*, [arXiv:2602.16355v2](https://arxiv.org/abs/2602.16355) (24 August
2026). That survey states that **no explicit unsortable permutation for three
stacks is presented anywhere** -- not Tarjan's, not Murphy's, not Atkinson's
38. So this repo's bound is **[14, 22]** -- Waton's guess of 22, and 7 above
Elder's 15. Superseded by [17, 21]; see [Superseded](#superseded).

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

Rigorous and search-free, but weak for k >= 2 -- 7x the truth at k = 2. It
holds even if every search fails. B_3(n) ~ 256^n, so n! only overtakes it
around n ~ e*256.

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
  on the machine.
* **Inversion density runs below random**, 0.41-0.48 against ~0.50, and the
  shorter witnesses have the lower densities. Shorter basis elements look
  less random, which suggests the short ones live in a structured corner of
  the space.
* **No two are related by any symmetry** -- consistent with the finding that
  none of the four symmetries preserves sortability.
* Every length-4 pattern occurs in every basis element, so whatever
  avoidance structure exists lives at larger patterns.

### The shape is causal

Over 25 basis elements of lengths 22-29 (`scripts/shape.py`):

| property | basis elements | uniform permutation |
|---|---|---|
| position of value 1 | median 1.00 of the way through (range 0.93-1.00) | 0.50 |
| position of value 2 | median 0.18 | 0.50 |
| first entry, as a fraction of n | median 0.27 (range 0.25-0.48) | 0.50 |
| alternation (zigzag rate) | 0.81-0.90 | 0.67 |

They are strongly **zigzag** permutations that open about a quarter of the
way up the value range and end on 1. Sampling from that profile and counting,
at length 36, 150 samples each (`scripts/structured_search.py`):

| distribution | unsortable |
|---|---:|
| uniform | 4 / 150 (2.7%) |
| value 1 forced last | 37 / 150 (24.7%) |
| zigzag + value 1 last | **100 / 150 (66.7%)** |

A 25x improvement in hit rate. A witness certifies itself, so a biased search
costs nothing in rigour; `hunt.py random --structured` draws its starting
points from this profile. Extrapolation across lengths fails: resampling all
25 basis elements to length 21 preserving the normalised shape gives 25
candidates, and every one sorts. The shape is a prior, not a formula.

### Structured families are all sortable

Iterated direct and skew sums of `231`, `312`, `2413`, `3142`, and layered
permutations with uniform layers, at every length up to 60: **all sortable**
(`python scripts/hunt.py families`). At length 60 a *random* permutation is
unsortable essentially always (9/9 in the sweep above), yet every structured
family member sorts.

Unsortability here requires genuine disorder, which is why descending from
long random witnesses worked. With the inversion-density observation above,
the short basis elements appear to sit in a narrow band: too ordered and
three stacks cope easily, too disordered and the witness is long.

## Why the search stops at 22

The bound fell 24 -> 23 in 78 hopping iterations and 23 -> 22 in 149, then sat
at 22 for several thousand. Take a witness and decide **every** same-length neighbour -- all
transpositions, all single-point relocations, all adjacent-value swaps. For
n = 22 that is 651 permutations, about two minutes across cores:

| case | neighbours still unsortable | |
|---|---:|---|
| k=2, n=7 -- the **known minimum** | 1 / 51 (1.96%) | exhaustive |
| k=3, n=29 | ~13% | sampled (300) |
| k=3, n=24 | ~1.3% | sampled (300) |
| k=3, n=23 | 4 / 715 (0.56%) | exhaustive |
| k=3, n=22 | **0 / 651 (0%)** | exhaustive |

The length-22 witness is an isolated point: not one of its 651 neighbours is
unsortable, so basin hopping stalls and a same-length walk has nowhere to
step. Hopping worked at all only because it never moves sideways at the
target length -- it descends from lengths where the unsortable set is fat.

**This is not evidence that 22 is the answer.** The k=2 row is the control:
at the known minimum for two stacks the neighbourhood is non-empty, and a
walk started one above it drops to length 7 immediately. Isolation measures
how hard a witness is to move away from. The answer remains anywhere in
[14, 22].

The enumeration is useful for **population**: the exhaustive neighbourhood of
the length-23 witness turned up four new length-23 basis elements in under
three minutes. `scripts/harvest.py` runs it as a breadth-first search over the
basis-element graph, where every minimal unsortable neighbour becomes a new
node and every non-minimal one yields a witness one shorter.

## The landscape has no gradient

Sortability is a yes/no answer, so at length 21 everything we try is sortable
and looks identical to a search. Scoring permutations by *how nearly*
unsortable they are is the obvious fix. For a permutation `p` of length L
define

    f(p) = how many one-point extensions of p (length L+1) are unsortable

which is positive exactly when `p` sits inside a length-(L+1) obstruction. f
costs (L+1)^2 decisions, 484 at L = 21, so it is affordable only via
`FixedLengthDecider`; every unsortable extension it finds is also a new
length-22 basis element, and we have only one.

Measured (`scripts/gradient.py`, 484 decisions per evaluation):

| sample | f |
|---|---|
| the 22 one-point deletions of our length-22 witness | **1, every one of them** |
| 12 same-length neighbours of one of those deletions | 0 |
| 12 uniform random length-21 permutations | 0 |

f is a delta function. Each deletion has exactly one unsortable extension --
the witness we already had -- and everything around them scores zero. The
witness is isolated under same-length moves (0 of 651 neighbours) and in the
containment order: nothing else of length 22 contains any of its deletions.
Gradient-guided search is dead at this length. The obstruction is a needle and
the space around it carries no signal pointing at it, so progress below 22
needs a *construction* -- a reason certain permutations must be unsortable.

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

Three things fall out, agreeing across both:

* **Every input and output constraint is needed.** Being a basis element,
  visible in the proof.
* **S1 and S3 carry near-identical load, and the middle stack carries about
  1.65x either** (317 vs 189, 380 vs 234). S1 is pinned by the input order
  and S3 by the output order plus its monotonicity invariant, so S2 is the
  free buffer that has to absorb the mismatch, and the obstruction is that
  it cannot.
* **The core is dense.** 2.8% of the clauses, spread over every value and
  every ordering constraint, with no small gadget driving the contradiction.

The last point explains the wall. Unsortability here is a global property of
all the interleavings at once, which is why local search finds no gradient
(f = 0 off the witness), why no pruning is available (there is no short
obstruction to prune with), and why the witnesses are isolated points. The
S2-loading invariant is the one lead that points anywhere: build candidates
that maximally overload the middle stack.

## Trying to construct instead of search

A stack can sort its input iff that input avoids 231, so S3 can finish iff
the sequence *arriving* at it avoids 231.  Therefore

    pi is 3-stack-sortable  <=>  some stack-rearrangement of pi
                                 is 2-stack-sortable

and since S1 can always pass elements straight through (push, pop
immediately), pi itself is one of the sequences S2 might see:

    every 3-stack-unsortable permutation is 2-stack-unsortable

k=2 calls are far faster, so that is a cheap filter, used in
`scripts/construct.py`.

**Structured construction fails.**  Interleaved decreasing runs, riffles,
affine maps, zigzags of several amplitudes, and inflations of the length-7
two-stack obstruction, each with and without value 1 moved last, swept over
lengths 14-24:

| | per length |
|---|---:|
| candidates | 45-78 |
| 2-stack-unsortable | 27-55 |
| **3-stack-unsortable** | **0, at every length** |

These families comfortably defeat two stacks and never defeat three. The
third stack absorbs regularity: a periodic permutation gives the machine a
repeating pattern it can answer with a repeating strategy. Obstruction seems
to require irreducibly aperiodic structure, which is what the dense core also
says.

**And a second gradient fails.**  Define `g(pi)` as the fraction of pi's
stack-rearrangements that are 2-stack-sortable; pi is unsortable exactly when
g = 0, so small g ought to mean close.  Sampling 300 rearrangements each:

| | g |
|---|---|
| the length-22 witness | 0.000 |
| 8 of its length-21 deletions | 0.000 all |
| 8 random length-21 permutations | 0.000 (5 of 8), else 0.003-0.053 |

The witness scores zero -- and so does most of the space.  There are ~10^10
rearrangements at this length and the 2-stack-sortable ones are a vanishing
fraction, so a 300-sample estimate saturates at zero almost everywhere.  Same
failure as `f`.

**The pattern across all of it.** Every locally computable measure tried --
neighbourhood density, extension count `f`, rearrangement fraction `g` --
reads zero at the witness and almost everywhere else. That is the dense-core
result seen three ways: when unsortability is a global property with no short
certificate, nothing local can point at it and continuous relaxation has
nothing to relax. Going below 22 needs an idea about the structure of the
class.

## Is the model even right?

The bounds here are worthless if we are simulating the wrong machine. A model
*more restrictive* than "three stacks in series" would call permutations
unsortable that really are sortable, and no amount of solver verification
catches it -- the solver would be faithfully answering the wrong question.
The literature supplies sharp, falsifiable predictions at three points, and
the model hits all of them:

| prediction | source | what we get |
|---|---|---|
| 1 stack sorts exactly `Av(231)`, counted by the Catalan numbers | Knuth | exact, permutation by permutation to n = 7; counts match to n = 11 (58,786 = C(11)) |
| 2 stacks in series first fail at length **7** | Tarjan | exactly 7 -- not 6 (too restrictive), not 8 (too permissive) |
| every permutation of length <= 13 is 3-stack-sortable | Atkinson | **exhaustive** at n = 10 (all 3,628,800 sortable); 800 random permutations at n = 12 and n = 13: **zero** unsortable |

The last row is the direct test. The exhaustive half
(`scripts/count_sortable.py`) leaves no room at n = 10; the sampled half
(`scripts/validate_model.py`) reaches the top of the known-sortable range,
which is where a too-restrictive machine would show. Each of those 800
sortable verdicts also carried an operation word that was *replayed* on the
independent simulator in `verify.py` and did sort, so the solver is producing
runs that work.

A model error would have to reproduce Catalan numbers at k = 1, land exactly
on 7 at k = 2, and leave everything below 14 sortable at k = 3
simultaneously. The remaining gap: all three checks live at n <= 13 and the
witnesses are at n = 22. Clause generation is uniform in n, so there is no
mechanism for the encoding to become wrong only above 13, though the checks
do not rule it out.

## The sorting dual

Sortability by k stacks in series is invariant under

    D(pi) = inverse(reverse_complement(pi))

the reflection of the plot of `pi` about the anti-diagonal. This is
Proposition 5.2 of Vatter,
[arXiv:2602.16355](https://arxiv.org/abs/2602.16355) -- the same paper this
repo already cited for its literature figures. It was re-derived here first
and found in the literature afterwards, which is the second time that has
happened in this project; [docs/notes.md](docs/notes.md) §6 gives the
derivation as time reversal of the interval encoding, and the attribution.

Measured, not assumed:

| check | result |
|---|---|
| `D` preserves sortability over all of `S_n`, k = 1, 2, 3, n <= 7 | agrees on every permutation |
| `D` is an involution, n <= 6 | yes |
| self-dual count, n = 1..10 | 1, 2, 4, 10, 26, 76, 232, 764, 2620, 9496 |
| those are the involution numbers | `pi` is self-dual iff `complement(pi)` is an involution |
| the complete k = 2 basis is `D`-closed, n = 7..10 | yes, at every length |
| Pantone-Vatter's length-21 witness | self-dual |

The last row is forced rather than surprising: the basis is `D`-closed and
they report exactly one minimal permutation at length 21, so `D` has nowhere
else to send it. It does make a usable cross-check of their uniqueness claim
against a symmetry derived independently here, and the two agree.

This also explains two coincidences that looked like separate clues. Their
length-21 witness starts with 6 and has its maximum at position 16; our
length-22 witness starts with 6 and also has its maximum at position 16.
Self-duality forces `pos(max) = n+1 - pi_1` exactly, so for the length-21
witness those are one fact, not two. Our length-22 witness is *not*
self-dual, and `D` maps it to a different unsortable permutation of length 22,
`7-3-13-9-17-5-2-12-21-8-15-4-19-11-6-16-22-10-18-14-20-1` -- a second
witness at that length obtained without any search.

### What it buys

There are `I(n)` self-dual permutations rather than `n!`, and Atkinson's
theorem pins the anti-diagonal point `(n, 1)` for a shortest witness, leaving
`I(n-1)`:

| length | self-dual candidates ending in 1 | vs. `n!` |
|---|---|---|
| 17 | `I(16)` = 46,206,736 | 3.6e14 |
| 18 | `I(17)` = 211,799,312 | 6.4e15 |
| 19 | `I(18)` = 997,313,824 | 1.2e17 |
| 20 | `I(19)` = 4,809,701,440 | 2.4e18 |

That is the difference between hopeless and affordable, and it is the first
**exhaustive** statement this project can make at the frontier length --
everything else here is local search with no coverage guarantee.

### Sweep results

| length | candidates | decided | rate | unsortable found |
|---|---|---|---|---|
| 17 | `I(16)` = 46,206,736 | all | 4,217/s | **0** |

**Length 17 is clear of self-dual witnesses.** No permutation of length 17
that is self-dual and ends in 1 is unsortable by three stacks in series --
46,206,736 candidates, every one decided, 182.6 minutes on 12 cores.

Two things follow, and only these two. Since the basis is `D`-closed, a
length whose basis contains no self-dual element has its basis paired up by
`D`, so **if the answer is 17 then the number of minimal permutations at
length 17 is even**. And that sits oddly beside length 21, where Pantone and
Vatter report exactly *one* -- an odd count, which forces that one to be
self-dual. Whatever is true at 17 has a different character from what is true
at 21.

What does *not* follow: that the answer exceeds 17. A length-17 witness need
not be self-dual, and this sweep says nothing about those.

The restriction to self-dual permutations is a conjecture, not a theorem. A
miss rules out only self-dual witnesses, though `D`-closure means a length
with no self-dual basis element has an *even* number of basis elements. The
restriction finds the correct answer in both cases where the answer is known:
`231` at k = 1 is self-dual, and 4 of the 22 shortest witnesses at k = 2 are
(`3254761`, `3624751`, `4257361`, `4627351` -- all of which also end in 1, so
both restrictions hold together).

Run it with `python scripts/dual.py verify` and
`python scripts/dual.py sweep --n 17`.

## Exhaustive census at k = 2

At k = 3 the first basis element is at length 17 or more, so everything about
the shape of these permutations came from a handful of witnesses. At k = 2 the
first is at length 7 and the whole picture is computable, which turns "does
this clue mean anything?" into a question with an answer.

| length | unsortable | basis elements | solver calls |
|---|---|---|---|
| 7 | 22 | **22** | 5,040 |
| 8 | 946 | 51 | 39,425 |
| 9 | 25,064 | 146 | 337,962 |
| 10 | 536,109 | 604 | 3,093,295 |

The length-7 row is a check against the literature, not a discovery:
Atkinson (1992) found exactly 22 basis elements of length 7 for two stacks in
series, and the census reproduces that count and the standard example
`2435761`. The shortest level is also re-decided by the brute-force
simulator, with no disagreements. `scripts/census.py`, data in
`results/census_k2.json`.

Two things the complete data settles that two k = 3 witnesses cannot:

* **"Ends in 1" is about the shortest, not about basis elements generally.**
  The rate falls 100% (length 7) -> 74.5% -> 17.1% -> 3.6% (length 10). So it
  is exactly Atkinson's theorem, and the reason our length-22 witness ends in
  1 despite not being shortest is that the rate one above the minimum is
  still high.
* **Basis elements proliferate fast**: 22, 51, 146, 604. Pantone and Vatter's
  1 at length 21 against 7,354 at length 22 is the same shape one level up,
  and it is why local search at length 22 finds witnesses easily and length
  21 not at all.

## Negative results

* **None of the four single symmetries is available**, but their composition
  is. Reverse, complement, inverse and reverse-complement each fail to
  preserve sortability, for one stack or for two, measured exhaustively to
  n = 7. For k = 1: `231` is unsortable while its reverse `132`, complement
  `213`, inverse `312` and reverse-complement `312` all sort. This repo
  originally concluded from those four measurements that no symmetry existed.
  That was wrong -- `inverse o reverse o complement` does preserve
  sortability. See [The sorting dual](#the-sorting-dual). Testing the
  generators of a group and concluding nothing in the group works is a bad
  inference, and it cost the project its one available search reduction.
* **Downward closure holds**, as it must -- verified exhaustively for
  k = 1, 2, 3 at n <= 7, and proved in [docs/notes.md](docs/notes.md) §4. The
  entire minimiser rests on it.
* **Deleting more than one point from a basis element is provably useless.**
  Any multi-point deletion is a one-point deletion of an already-sortable
  one-point deletion, so downward closure makes it sortable. The only route
  to a shorter witness is a *different* basis element, which is why the
  minimiser has no "deep" mode and basin hopping is the search.
* **PySAT's in-memory proof capture truncates.** For the length-33 witness it
  returned 15 MB of a proof lingeling reported writing as 6.1 MB, and
  drat-trim rejected it ("conflict claimed, but not detected") on an instance
  that is genuinely unsatisfiable. Different solvers failed on different
  instances, which is the signature of lossy capture. All certificates are
  now produced by a solver **binary writing DRAT straight to a file**. A
  truncated proof that still verifies is sound -- drat-trim checks every step
  -- but one that fails is indistinguishable from a wrong answer.

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
sortability question is established separately, by the proof in
docs/notes.md §3 and by exhaustive agreement with brute force. A reader who
distrusts the encoding should check that proof; a reader who distrusts the
solver should run drat-trim. The two checks are independent.

The brute-force simulator cannot reach n = 22, so at that size the simulator
leg is absent and the encoding's correctness is carried by its agreement at
small n. This is the weakest link in the chain and is stated plainly rather
than buried.
