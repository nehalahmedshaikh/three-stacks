# Notes: the machine, the prunings, and the interval encoding

## 1. The machine

`input -> S1 -> S2 -> ... -> Sk -> output`, operations

| op | effect |
|----|--------|
| `r_1` | move the next input element onto S1 |
| `r_j`, `2 <= j <= k` | pop `S_{j-1}`, push onto `S_j` |
| `r_{k+1}` | pop `S_k`, append to the output |

Every element performs each operation exactly once and in order, so a full
run is a word of length `(k+1)n` over the alphabet `{1,...,k+1}` in which
each letter occurs `n` times and every prefix satisfies
`#1 >= #2 >= ... >= #(k+1)` (a *ballot word*, equivalently a standard Young
tableau of rectangular shape `(k+1) x n`).

**Key observation (used by `verify.py` and by the SAT model extractor).**
A ballot word `w` determines the whole run *without reference to the values*:
`r_1` always takes the next input element, `r_j` always takes the top of
`S_{j-1}`. So `w` induces a bijection `phi_w` from input positions to output
positions. Hence

> `pi` is k-stack-sortable **iff** `pi = phi_w^{-1}` for some ballot word `w`,

and the set of sortable permutations of length `n` is exactly the image of
the (finite) set of ballot words under `w |-> phi_w^{-1}`. This is what makes
positive claims cheap to check: hand over `w`, replay, done. It is also the
source of the counting bound in §5.

## 2. The two prunings in `simulator.py`

**P1 — last-stack monotonicity.** `S_k` pops directly to the output, and the
output must be increasing. The pop order of `S_k` is its top-to-bottom order.
So at every instant `S_k` is strictly increasing from top to bottom, and a
push of `v` onto `S_k` is legal only when `S_k` is empty or `v` is smaller
than the current top. (For `k = 1` this applies to `r_1` as well.)

**P2 — forced output.** Suppose the top of `S_k` equals the next value the
output needs, `m`. By P1 anything later pushed on top of it must be smaller
than `m`; but every value smaller than `m` has already been output. So
nothing can ever be pushed above it, and its pop is available now and forever
until taken. Popping immediately therefore loses nothing, and `r_{k+1}`
becomes deterministic whenever it is enabled.

Both are exercised against the unpruned search in `tests/test_simulator.py`
for all permutations of length `<= 6` and `k = 1, 2, 3`.

**Acyclicity.** A state `(i, S1, ..., Sk)` determines, for every element, how
many operations it has performed, hence the total number of operations so
far. Every operation increments that total. So the state graph is a DAG and
a plain visited-set is a sound memo for "no completion from here".

## 3. The interval / non-crossing encoding

Give each value `v` four event times `t_1[v] < t_2[v] < t_3[v] < t_4[v]`, all
`4n` times distinct: the moments at which `v` performs `r_1, r_2, r_3, r_4`.

**Claim.** `pi` is 3-stack-sortable iff such times exist with

* **(a) input order** — if `v` precedes `w` in `pi` then `t_1[v] < t_1[w]`;
* **(b) output order** — `t_4[v] < t_4[w]` iff `v < w`;
* **(c) non-crossing** — for each stack `s in {1,2,3}` write
  `a_v = t_s[v]`, `b_v = t_{s+1}[v]` (the interval during which `v` occupies
  `S_s`). No pair may *cross*: there is no `v, w` with
  `a_v < a_w < b_v < b_w`.

### Proof

*(=>)* Given a sorting run, read the times off the run. (a) and (b) are
immediate. For (c): if `a_v < a_w < b_v` then `w` was pushed onto `S_s` after
`v` and while `v` was still there, so `w` sits above `v`; LIFO forces `w` to
leave first, i.e. `b_w < b_v`. So `a_v < a_w < b_v < b_w` is impossible.

*(<=)* Given times satisfying (a)–(c), sort all `4n` events by time and
perform the corresponding operations in that order. Each is legal:

* `r_1` for `v`: (a) says the `t_1` order is exactly `pi`'s order, so `v` is
  the next input element.
* `r_{s+1}` for `v` (`s = 1,2,3`): the elements on `S_s` just before `b_v`
  are those `w` with `a_w < b_v < b_w`. If such a `w` had `a_w > a_v` we
  would have `a_v < a_w < b_v < b_w`, a crossing, excluded by (c). So every
  element on `S_s` at that moment entered before `v` did; `v` is on top.
* `r_4` for `v`: by (b) the output comes out in increasing value order, and
  it contains every value, so it is the identity.

Nothing else can go wrong: `t_1[v] < t_2[v] < t_3[v] < t_4[v]` guarantees
each element performs its four operations in order, and distinctness makes
the total order well defined. ∎

**Only the relative order of the `4n` events matters**, so the SAT encoding
uses pairwise `before` variables plus transitivity.

### Hand check on `231`, one stack

One stack, two events per value. (a) gives `t_1[2] < t_1[3] < t_1[1]`;
(b) gives `t_2[1] < t_2[2] < t_2[3]`. Chaining through
`t_1[1] < t_2[1]`: `t_1[2] < t_1[3] < t_1[1] < t_2[1] < t_2[2] < t_2[3]`.
Look at the pair `(2, 3)`: `a_2 = t_1[2] < a_3 = t_1[3] < b_2 = t_2[2] <
b_3 = t_2[3]`. That is exactly a crossing, so no valid assignment exists and
`231` is unsortable by one stack — matching `Av(231)`. ✓

### Hand check on `231`, two stacks

With `k = 2` each value has three events and (b) reads
`t_3[1] < t_3[2] < t_3[3]`. The run `112123233` sorts it —
`S1<-2, S1<-3, S2<-3, S1<-1, S2<-1, out 1, S2<-2, out 2, out 3`
(`python verify.py replay 231 --k 2 --ops 112123233`). Reading the times off
that run:

| v | t1 | t2 | t3 |
|---|----|----|----|
| 1 | 4  | 5  | 6  |
| 2 | 1  | 7  | 8  |
| 3 | 2  | 3  | 9  |

(a) `t_1[2]=1 < t_1[3]=2 < t_1[1]=4`, matching `231`. ✓
(b) `t_3[1]=6 < t_3[2]=8 < t_3[3]=9`. ✓
(c) `S1` intervals `2:[1,7]`, `3:[2,3]`, `1:[4,5]` — the last two are nested
inside the first and disjoint from each other. `S2` intervals `3:[3,9]`,
`1:[5,6]`, `2:[7,8]` — likewise. No crossings. ✓ The extra stack buys the
room to nest what one stack had to cross.

## 4. Downward closure

**Claim.** If `pi` is k-stack-sortable and `pi'` is obtained by deleting one
entry, then `pi'` is k-stack-sortable. (So the sortable permutations form a
permutation class, unsortability is closed upward, and the shortest
unsortable permutation is a basis element.)

**Proof.** Let `w` be a sorting run for `pi` and let `v` be the deleted
value. Delete from `w` the `k+1` operations performed by `v`; call the
result `w'`. Run `w'` on `pi'`.

Each surviving element performs the same operations in the same relative
order. They are all legal:

* `r_1` — deleting `v` from the input preserves the relative order of the
  others, so each still arrives when `w'` asks for it.
* `r_{j+1}` — when element `u` popped `S_j` in the original run, `u` was on
  top, so `v` was *not* above `u` at that moment. Removing `v` from `S_j`
  therefore never puts anything above `u`, and `u` is still on top.
* The output is the original output with `v` deleted, i.e. increasing.
  Standardising gives the identity. ∎

`minimise` is sound because of this: it need only check that the shrunken
permutation is still unsortable. `tests/test_closure.py` checks the claim
exhaustively for `k = 1, 2, 3` at `n <= 7`, where the `k = 1, 2` cases include
unsortable permutations, and against a known long `k = 3` witness.

**Symmetries.** None of reverse, complement, inverse, or reverse-complement
preserves sortability on its own. For `k = 1`: `231` is unsortable while its
reverse `132`, complement `213`, inverse `312`, and reverse-complement `312`
are all sortable. `tests/test_closure.py` measures this for `k = 2, 3` too.

Their *composition* `inverse o reverse o complement` does preserve
sortability — see §6. Testing the four maps one at a time and concluding that
no symmetry exists was a mistake; a group generated by non-symmetries can
still contain one.

## 5. The counting ceiling (M6)

By §1 every sortable permutation is `phi_w^{-1}` for some ballot word, so

    #{sortable of length n, k stacks}  <=  #{ballot words}
                                       =  ((k+1)n)! * prod_{j=0}^{k} j!
                                          / prod_{j=0}^{k} (n+j)!

the `(k+1)`-dimensional Catalan number. For `k = 3` this grows like
`256^n / poly(n)` while `n!` grows faster, so beyond the crossover point
unsortable permutations must exist. See `unsortable/counting.py` for the
exact crossover; it is a rigorous, search-free upper bound on the answer,
though a weak one.

## 6. The sorting dual

**Claim.** `pi` is k-stack-sortable in series iff `D(pi)` is, where

    D(pi) = inverse(reverse_complement(pi))

which reflects the plot of `pi` about the anti-diagonal.

This is Proposition 5.2 of Vatter, [arXiv:2602.16355](https://arxiv.org/abs/2602.16355),
stated there for symbol-oblivious reversible machines: if `M` sorts `pi` then
the reversed machine `M^r` sorts `(pi^rc)^-1`. For k stacks in series the
reversed machine is the same machine, so the map is a symmetry of the class.
It was re-derived here before being found in the literature; the derivation
below is included because it is short inside the interval encoding of §3, and
because an earlier version of §4 wrongly recorded that no symmetry was
available—the four maps were tested individually, but not their composition.

**Proof.** Take a sorting run for `pi` and let `t_1[v] < ... < t_{k+1}[v]` be
the event times of §3. Reverse time: put `u_s[v] = -t_{k+2-s}[v]`.

* Negation reverses every comparison, so `u_1` orders the values by the
  reverse of the old *output* order, and `u_{k+1}` by the reverse of the old
  *input* order.
* Stack `s` becomes stack `k+1-s`. Its occupancy interval
  `[t_s[v], t_{s+1}[v]]` becomes `[-t_{s+1}[v], -t_s[v]]`, still an interval,
  and negation preserves nesting and disjointness. So the laminar condition
  of §3(c) holds for every stack of the reversed run.

The reversed run is therefore legal, and it takes input `n, n-1, ..., 1` to
output `pi_n, ..., pi_1`. Relabelling so the output is the identity — send
value `v` to `n+1-pi^{-1}(v)` — makes the input permutation

    sigma_i = n+1 - pi^{-1}(n+1-i)

and expanding `inverse(reverse_complement(pi))` gives the same formula. So
`sigma = D(pi)`, and a run for `pi` yields a run for `D(pi)`. Time reversal is
an involution, so the converse holds too. ∎

**`D` is an involution, and its fixed set is small.** `pi = D(pi)` says the
point set of `pi` is symmetric about the anti-diagonal; complementing turns
that into symmetry about the main diagonal, so

    pi is self-dual  <=>  complement(pi) is an involution

and there are `I(n)` self-dual permutations of length `n` rather than `n!` —
`1, 2, 4, 10, 26, 76, 232, 764, 2620, 9496, ...`. Combined with Atkinson's
theorem that the shortest unsortable permutation ends in `1`, which pins the
anti-diagonal point `(n, 1)`, the count drops to `I(n-1)`.

That is what makes an exhaustive sweep possible at the frontier: `I(16)` is
46 million where `17!` is 356 trillion. `scripts/dual.py` verifies the
symmetry exhaustively over `S_n` and runs the sweep; `tests/test_closure.py`
pins both the symmetry and the counting characterisation.

**What the sweep can conclude.** Restricting to self-dual permutations is a
conjecture, not a theorem. A miss rules out only self-dual witnesses — though
because the basis is `D`-closed, a length with no self-dual basis element has
an *even* number of basis elements, which is a real constraint. The
restriction finds the right answer in both cases where the answer is known:
`231` at `k = 1` is self-dual, and four of the twenty-two shortest witnesses
at `k = 2` are. The length-21 witness of Pantone and Vatter is self-dual as
well, but that is forced rather than evidence — they report exactly one
minimal permutation at that length, and `D` has nowhere else to send it.
