"""Where the search currently stands, and how to pick it back up.

The tracked consolidated record preserves promoted basis elements; a local
scratch log and canonical reports add detail when present. This prints the
state and a command to resume from the best witness so far.

    python scripts/status.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.collect_witnesses import collect

RESULTS = ROOT / "results"
PROOFS = ROOT / "proofs"


def best_witnesses(k: int) -> list[tuple[int, str, str]]:
    """(length, perm, provenance), shortest first."""
    found: dict[str, tuple[int, str]] = {}

    for entry in collect(k):
        why = entry["status"]
        if entry.get("certificate_id"):
            why += f" ({entry['certificate_id']})"
        found[entry["perm"]] = (entry["n"], why)

    return sorted(((n, p, why) for p, (n, why) in found.items()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    a = ap.parse_args(argv)

    rows = best_witnesses(a.k)
    if not rows:
        print(f"no k={a.k} witnesses recorded yet.  Start with:\n"
              f"  python scripts/hunt.py random --n 40 --workers 8")
        return 0

    print(f"unsortable permutations on record for k={a.k}, shortest first:\n")
    for n, p, why in rows[:12]:
        print(f"  {n:>3}  {p}")
        print(f"       {why}")
    if len(rows) > 12:
        print(f"  ... and {len(rows) - 12} more")

    n, best, _ = rows[0]
    certified = list(PROOFS.glob(f"k{a.k}_n{n}_*.drat"))
    print(f"\nbest: length {n}")
    print(f"certificate on disk: {'yes' if certified else 'NO -- run scripts/certify.py'}")

    counts = RESULTS / "counts.json"
    if counts.exists():
        d = json.loads(counts.read_text())
        have = {k: max(map(int, v)) for k, v in d.items() if v}
        print(f"exhaustive counts complete up to: "
              + ", ".join(f"k={k} n={v}" for k, v in sorted(have.items())))

    print(f"\nresume the search:\n"
          f"  python scripts/hunt.py hop --k {a.k} --workers 7 --assume-minimal \\\n"
          f"      --plateau 0.9 --iterations 3000 --perm {best}")
    print(f"\nre-verify everything:\n"
          f"  python scripts/verify_basis.py --k {a.k} --perm {best} --skip-certificate\n"
          f"  python proofcheck.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
