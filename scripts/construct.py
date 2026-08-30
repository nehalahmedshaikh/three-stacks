"""Build candidates that overload the middle stack, instead of sampling.

The core analysis (`scripts/core.py`) showed S1 and S3 carrying equal load
while S2 carries about 1.65x either, in both witnesses.  There is a clean
reason.  A stack can sort its input iff that input avoids 231, so:

    S3 can finish  <=>  the sequence arriving at S3 avoids 231

and therefore

    pi is 3-stack-sortable  <=>  some stack-rearrangement of pi
                                 is 2-stack-sortable

S1 is pinned by the input order and S3 by the output order plus its
monotonicity invariant; S2 is the buffer that has to turn what S1 emits into
something 231-avoiding.  An obstruction is a permutation where it cannot.

Two consequences:

* **Necessary condition.** S1 can always pass elements straight through
  (push then immediately pop), so pi itself is one of the sequences S2 might
  see.  Hence every 3-stack-unsortable permutation is 2-stack-unsortable, and
  2-stack-sortable candidates can be rejected with a much cheaper call.
* **What to build.** Permutations that are *robustly* 2-stack-unsortable --
  whose stack-rearrangements are unsortable too.

The families below stress that buffer.  Each is swept over a range of lengths
and the shortest unsortable member reported; a family producing one below 22
beats the current bound.

    python scripts/construct.py --min-n 14 --max-n 24 --workers 12
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.encoding import worker_is_sortable
from unsortable.perms import Perm, check, standardise, to_string

WITNESSES = ROOT / "results" / "witnesses.jsonl"

# the 22 length-7 basis elements of the 2-stack class, used as seeds
TWO_STACK_SEEDS = [(2, 4, 3, 5, 7, 6, 1)]


def one_last(p: Perm) -> Perm:
    """Move value 1 to the final position -- the motif 11 of 13 witnesses share."""
    rest = [v for v in p if v != 1]
    return tuple(rest) + (1,)


def interleaved_runs(n: int, r: int) -> Perm:
    """r decreasing runs, interleaved round-robin.

    Each run alone is trivial for one stack (it comes out reversed); the
    interleaving is what forces the buffer to hold several partly-processed
    runs at once.
    """
    groups = [[v for v in range(1, n + 1) if (v - 1) % r == g][::-1]
              for g in range(r)]
    out: list[int] = []
    idx = [0] * r
    while len(out) < n:
        for g in range(r):
            if idx[g] < len(groups[g]):
                out.append(groups[g][idx[g]])
                idx[g] += 1
    return tuple(out)


def riffle(n: int, b: int) -> Perm:
    """Split into b contiguous value-blocks and interleave them."""
    blocks = [list(range(1 + j * n // b, 1 + (j + 1) * n // b)) for j in range(b)]
    out: list[int] = []
    while any(blocks):
        for blk in blocks:
            if blk:
                out.append(blk.pop(0))
    return tuple(out)


def affine(n: int, a: int) -> Perm | None:
    if gcd(a, n) != 1:
        return None
    return tuple(((a * i) % n) + 1 for i in range(n))


def zigzag(n: int, swing: int) -> Perm:
    """Alternate between the low and high value pools, `swing` at a time."""
    lo = list(range(1, n // 2 + 1))
    hi = list(range(n // 2 + 1, n + 1))[::-1]
    out: list[int] = []
    turn = 0
    while lo or hi:
        src = lo if (turn % 2 == 0 and lo) or not hi else hi
        for _ in range(swing):
            if src:
                out.append(src.pop(0))
        turn += 1
    return tuple(out)


def inflate(seed: Perm, sizes: list[int]) -> Perm:
    """Replace each point of `seed` by a decreasing block of the given size."""
    n = sum(sizes)
    starts, acc = {}, 1
    for v in sorted(range(len(seed)), key=lambda i: seed[i]):
        starts[v] = acc
        acc += sizes[v]
    out: list[int] = []
    for i in range(len(seed)):
        s = starts[i]
        out.extend(range(s + sizes[i] - 1, s - 1, -1))
    return standardise(out)


def families(n: int, rng: random.Random) -> list[tuple[str, Perm]]:
    out: list[tuple[str, Perm]] = []

    def add(name: str, p) -> None:
        if p is None or len(p) != n:
            return
        p = check(p)
        out.append((name, p))
        out.append((name + "+1last", one_last(p)))

    for r in range(2, min(7, n)):
        add(f"interleave(r={r})", interleaved_runs(n, r))
    for b in range(2, min(7, n)):
        add(f"riffle(b={b})", riffle(n, b))
    for a in range(2, n):
        add(f"affine(a={a})", affine(n, a))
    for s in (1, 2, 3):
        add(f"zigzag(swing={s})", zigzag(n, s))
    # inflations of the smallest 2-stack obstruction
    for seed in TWO_STACK_SEEDS:
        m = len(seed)
        for _ in range(12):
            sizes = [1] * m
            for _ in range(n - m):
                sizes[rng.randrange(m)] += 1
            add(f"inflate({to_string(seed)})", inflate(seed, sizes))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--min-n", type=int, default=14)
    ap.add_argument("--max-n", type=int, default=24)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)

    rng = random.Random(a.seed)
    best: dict[str, int] = {}
    print(f"{'n':>3}  {'candidates':>10}  {'2-stack-unsortable':>19}  "
          f"{'3-stack-unsortable':>19}", flush=True)

    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for n in range(a.min_n, a.max_n + 1):
            cands = families(n, rng)
            seen: dict[Perm, str] = {}
            for name, p in cands:
                seen.setdefault(p, name)
            ps = list(seen)
            # cheap necessary condition first: 3-stack-unsortable implies
            # 2-stack-unsortable, and k=2 calls are far cheaper
            two = list(ex.map(worker_is_sortable, ps, [2] * len(ps)))
            survivors = [p for p, s in zip(ps, two) if not s]
            three = list(ex.map(worker_is_sortable, survivors,
                                [a.k] * len(survivors)))
            hits = [p for p, s in zip(survivors, three) if not s]
            print(f"{n:>3}  {len(ps):>10}  {len(survivors):>19}  "
                  f"{len(hits):>19}", flush=True)
            for p in hits:
                fam = seen[p]
                best.setdefault(fam, n)
                print(f"     UNSORTABLE  {fam:<26} {to_string(p)}", flush=True)
                with WITNESSES.open("a", newline="\n") as fh:
                    fh.write(json.dumps({"perm": to_string(p), "n": n,
                                         "k": a.k, "minimal": False,
                                         "kind": "construct",
                                         "family": fam}) + "\n")

    print()
    if best:
        print("shortest unsortable member per family:")
        for fam, n in sorted(best.items(), key=lambda kv: kv[1]):
            print(f"  {n:>3}  {fam}")
    else:
        print("no family produced an unsortable permutation in this range")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
