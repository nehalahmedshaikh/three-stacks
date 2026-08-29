"""Certify that a permutation is a BASIS ELEMENT of the k-stack-sortable class.

That is the object the open problem actually asks about: a permutation that
is unsortable, every one-point deletion of which is sortable.  The claim
splits into n+1 independently checkable pieces:

  * the permutation itself is UNSORTABLE
        -> DIMACS + DRAT certificate, checked by drat-trim (third party)
  * each of its n one-point deletions is SORTABLE
        -> an explicit operation word, replayed by verify.py (no solver
           trust needed at all -- you just run the machine)

The second half is the nice part: n positive claims that a sceptic can check
with a twenty-line simulator, no SAT solver involved.

    python scripts/verify_basis.py --perm 6-15-2-17-... --k 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify  # the independent replayer
from scripts.certify import certify
from unsortable.encoding import solve
from unsortable.minimizer import delete_positions
from unsortable.perms import from_string, to_string

RESULTS = ROOT / "results"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perm", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--skip-certificate", action="store_true",
                    help="skip regenerating the DRAT artifacts")
    a = ap.parse_args(argv)

    perm = from_string(a.perm)
    n = len(perm)
    print(f"permutation : {to_string(perm)}")
    print(f"length      : {n}   stacks: {a.k}\n")

    report = {"perm": to_string(perm), "n": n, "k": a.k}

    if not a.skip_certificate:
        print("[1] certifying the permutation itself is UNSORTABLE ...", flush=True)
        e = certify(perm, k=a.k, brute_force=False)
        report["unsortable_claim"] = e
        if e["sortable"]:
            print("    !! SOLVER SAYS SORTABLE -- this is not a witness at all")
            return 1
        print(f"    UNSAT in {e['solve_seconds']}s, "
              f"{e['drat_bytes'] / 1e6:.1f} MB DRAT -> {e['drat']}")
        print(f"    second solver agrees: {e['second_solver'].get('agrees')}\n")

    print(f"[2] checking all {n} one-point deletions are SORTABLE ...", flush=True)
    deletions = []
    bad = 0
    t0 = time.time()
    for i in range(n):
        q = delete_positions(perm, [i])
        r = solve(q, k=a.k, mode="reduced")
        ok = False
        if r.sortable and r.ops is not None:
            ok = verify.sorts(list(q), r.ops, k=a.k)  # replayed, not trusted
        deletions.append({
            "deleted_position": i,
            "deleted_value": perm[i],
            "pattern": to_string(q),
            "sortable": bool(r.sortable),
            "ops": "".join(map(str, r.ops)) if r.ops else None,
            "replay_sorts": ok,
        })
        if not ok:
            bad += 1
            print(f"    position {i:3d} (value {perm[i]:3d}) -> NOT SORTABLE "
                  f"-- {to_string(q)} is a shorter witness!", flush=True)
    report["deletions"] = deletions
    dt = time.time() - t0

    good = sum(1 for d in deletions if d["replay_sorts"])
    print(f"    {good}/{n} deletions sortable, each with a replayed "
          f"operation word ({dt:.1f}s)\n")

    is_basis = bad == 0
    report["is_basis_element"] = is_basis
    out = RESULTS / f"basis_k{a.k}_n{n}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")

    if is_basis:
        print(f"VERDICT: {to_string(perm)} is a BASIS ELEMENT of the "
              f"{a.k}-stack-sortable class.")
        print(f"         The shortest such basis element has length <= {n}.")
    else:
        print(f"VERDICT: NOT minimal -- {bad} deletion(s) are still unsortable. "
              f"Run the minimiser.")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0 if is_basis else 1


if __name__ == "__main__":
    raise SystemExit(main())
