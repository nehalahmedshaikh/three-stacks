"""Exhaustive counts of k-stack-in-series sortable permutations."""

from __future__ import annotations

import argparse
import json
import sys
import time
from math import factorial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unsortable.perms import all_perms
from unsortable.simulator import is_sortable


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    table: dict[str, dict[int, int]] = {}
    for k in a.k:
        row: dict[int, int] = {}
        for n in range(1, a.max_n + 1):
            t0 = time.time()
            c = sum(1 for p in all_perms(n) if is_sortable(p, k=k))
            row[n] = c
            print(
                f"k={k} n={n:2d}  sortable={c:>10,}  of {factorial(n):>10,}"
                f"  ({c / factorial(n):6.2%})  [{time.time() - t0:.1f}s]",
                flush=True,
            )
        table[str(k)] = row
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(table, indent=2))
        print("wrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
