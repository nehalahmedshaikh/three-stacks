"""Promote the minimal witnesses out of the scratch log into a tracked file.

`results/witnesses.jsonl` is git-ignored: it is an append-only log of
everything the search touched, most of it non-minimal and superseded. But it
is also the only place the *basis elements* live once the four certified pairs
are set aside, and those are primary data -- each is a permutation that was
decided unsortable while all of its one-point deletions were decided
sortable. Deleting a working copy would lose them.

This rewrites them into `results/basis_found.json`, deduplicated, with the
provenance stated: they are solver verdicts, not DRAT-certified claims. Only
the four in `claims.json` carry certificates.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.perms import from_string

SRC = ROOT / "results" / "witnesses.jsonl"
OUT = ROOT / "results" / "basis_found.json"


def main() -> int:
    if not SRC.exists():
        print(f"{SRC} is absent; nothing to promote")
        return 0
    rows = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
    certified = {c["perm"]: c
                 for c in json.loads((ROOT / "results" / "claims.json")
                                     .read_text())}

    seen: dict[tuple[int, str], dict] = {}
    for r in rows:
        if not r.get("minimal") or not r.get("perm"):
            continue
        key = (r["k"], r["perm"])
        if key not in seen:
            seen[key] = r

    by_k: dict[int, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
    for (k, perm), r in sorted(seen.items()):
        n = len(from_string(perm))
        by_k[k][n].append(perm)

    payload = {
        "what": "basis elements found by this repo's search: unsortable, "
                "every one-point deletion sortable",
        "provenance": "solver verdicts from unsortable/encoding.py, "
                      "reproducible with scripts/verify_basis.py. NOT "
                      "DRAT-certified -- only the entries in claims.json "
                      "carry certificates.",
        "certified_elsewhere": sorted(
            p for (k, p) in seen if p in certified),
        "basis": {str(k): {str(n): sorted(ps) for n, ps in sorted(lv.items())}
                  for k, lv in sorted(by_k.items())},
    }
    OUT.write_text(json.dumps(payload, indent=1) + "\n")

    total = sum(len(ps) for lv in by_k.values() for ps in lv.values())
    print(f"wrote {OUT} with {total} distinct basis elements")
    for k, lv in sorted(by_k.items()):
        counts = ", ".join(f"n={n}: {len(ps)}" for n, ps in sorted(lv.items()))
        print(f"  k={k}  {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
