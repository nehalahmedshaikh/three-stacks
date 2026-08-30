"""M6: the counting ceiling.

A full run of the machine is a ballot word of length ``(k+1)n`` over
``{1,...,k+1}`` -- each letter ``n`` times, every prefix satisfying
``#1 >= #2 >= ... >= #(k+1)``.  Equivalently, a standard Young tableau of
rectangular shape ``(k+1) x n``, counted by the hook length formula:

    B_k(n) = ((k+1)n)! * prod_{j=0..k} j!  /  prod_{j=0..k} (n+j)!

As shown in ``docs/notes.md`` §1, a ballot word determines the whole run
without reference to values, so it induces a bijection ``phi_w`` on
positions and ``pi`` is sortable iff ``pi = phi_w^{-1}`` for some ``w``.
Hence

    #{k-stack-sortable permutations of length n}  <=  B_k(n)

and as soon as ``n! > B_k(n)`` an unsortable permutation must exist.  That
crossover is a rigorous, search-free upper bound on the length of the
shortest unsortable permutation.

It is tight for ``k = 1`` (the map is a bijection there, ``B_1 = Catalan``,
crossover 3, and ``231`` is the answer) and very weak for ``k >= 2``:
``B_k(n) ~ (k+1)^{(k+1)n} / poly``, so the crossover sits near
``e * (k+1)^{k+1}`` -- 50 for two stacks whose true answer is 7, and 642 for
three stacks whose true answer is somewhere in [14, 22].
"""

from __future__ import annotations

from math import factorial, lgamma


def ballot_words(n: int, k: int = 3) -> int:
    """Number of legal operation sequences: SYT of shape (k+1) x n."""
    if n < 0:
        raise ValueError("n >= 0")
    num = factorial((k + 1) * n)
    for j in range(k + 1):
        num *= factorial(j)
    den = 1
    for j in range(k + 1):
        den *= factorial(n + j)
    q, r = divmod(num, den)
    assert r == 0, "hook length formula should divide exactly"
    return q


def _log_ballot_words(n: int, k: int) -> float:
    return (lgamma((k + 1) * n + 1)
            + sum(lgamma(j + 1) for j in range(k + 1))
            - sum(lgamma(n + j + 1) for j in range(k + 1)))


def crossover(k: int = 3, limit: int = 100_000) -> int | None:
    """Smallest n with n! > B_k(n).

    No permutation of that length can be sortable... more precisely, not all
    of them can be, so the shortest unsortable permutation has length at
    most this.

    Scans with log-gamma (cheap) and confirms the answer and its predecessor
    with exact integer arithmetic.
    """
    for n in range(1, limit + 1):
        if lgamma(n + 1) > _log_ballot_words(n, k) + 1e-6:
            # confirm exactly, and walk back in case logs were optimistic
            while n > 1 and factorial(n - 1) > ballot_words(n - 1, k):
                n -= 1
            while factorial(n) <= ballot_words(n, k):
                n += 1
            return n
    return None


def table(k: int = 3, ns=None) -> list[tuple[int, int, int, bool]]:
    """Rows of (n, n!, B_k(n), n! > B_k(n))."""
    if ns is None:
        c = crossover(k) or 40
        ns = sorted({1, 2, 3, 4, 5, 10, 20, 50, 100, 200, 500,
                     c - 2, c - 1, c, c + 1})
        ns = [n for n in ns if n >= 1]
    return [(n, factorial(n), ballot_words(n, k), factorial(n) > ballot_words(n, k))
            for n in ns]


def main() -> None:
    for k in (1, 2, 3, 4):
        c = crossover(k)
        print(f"k={k} stacks in series: n! first exceeds B_k(n) at n = {c}")
        print(f"    => the shortest unsortable permutation has length <= {c}"
              f"  (rigorous, no search)")
        if k == 1:
            print("    (B_1 = Catalan; the bound is exactly attained -- 231)")
        print()

    print("k=3 detail near the crossover:")
    c = crossover(3)
    for n in range(c - 3, c + 2):
        f, b = factorial(n), ballot_words(n, 3)
        print(f"  n={n:4d}  n! ~ 1e{len(str(f))-1:<5d} B_3(n) ~ 1e{len(str(b))-1:<5d}"
              f"  {'n! LARGER' if f > b else ''}")


if __name__ == "__main__":
    main()
