"""Certify that a permutation is a BASIS ELEMENT of the k-stack-sortable class.

A basis element is what the open problem asks about: a permutation that is
unsortable, every one-point deletion of which is sortable.  The claim splits
into n+1 independently checkable pieces:

  * the permutation itself is UNSORTABLE
        -> DIMACS + DRAT certificate, checked by drat-trim (third party)
  * each of its n one-point deletions is SORTABLE
        -> an explicit operation word, replayed by verify.py (no solver
           trust needed at all -- you just run the machine)

The second half is n positive claims a sceptic can check with a twenty-line
simulator, no SAT solver involved.

    python scripts/verify_basis.py --perm 6-15-2-17-... --k 3
"""

from __future__ import annotations

import argparse
import hashlib
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
                    help="decide unsortability in memory instead of writing "
                         "and checking a DRAT certificate (no solver binaries "
                         "needed; the verdict is then a solver verdict only)")
    a = ap.parse_args(argv)

    perm = from_string(a.perm)
    n = len(perm)
    print(f"permutation : {to_string(perm)}")
    print(f"length      : {n}   stacks: {a.k}\n")

    report = {"perm": to_string(perm), "n": n, "k": a.k}

    # Step 1 is not optional.  --skip-certificate used to skip it altogether,
    # which made this script report the identity permutation as a basis
    # element: every deletion of it is sortable, and nothing ever checked that
    # the permutation itself was not.
    if a.skip_certificate:
        print("[1] deciding whether the permutation is UNSORTABLE "
              "(in memory, no certificate) ...", flush=True)
        r = solve(perm, k=a.k, mode="reduced")
        report["unsortable_claim"] = {"sortable": bool(r.sortable),
                                      "certified": False}
        if r.sortable:
            print(f"    SORTABLE -- {to_string(perm)} is not a witness at all.")
            if r.ops is not None and verify.sorts(list(perm), r.ops, k=a.k):
                print(f"    operation word, replayable with verify.py: "
                      f"{''.join(map(str, r.ops))}")
            print("\nVERDICT: not a witness.")
            return 1
        print("    UNSORTABLE (solver verdict; rerun without "
              "--skip-certificate for a DRAT certificate)\n")
    else:
        print("[1] certifying the permutation itself is UNSORTABLE ...", flush=True)
        e = certify(perm, k=a.k, brute_force=False)
        e["certified"] = True
        report["unsortable_claim"] = e
        if e["sortable"]:
            print("    !! SOLVER SAYS SORTABLE -- this is not a witness at all")
            print("\nVERDICT: not a witness.")
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

    # Both halves are required.  Reaching here means step 1 found the
    # permutation unsortable, since the sortable branches return early.
    unsortable = not report["unsortable_claim"]["sortable"]
    is_basis = unsortable and bad == 0
    report["is_basis_element"] = is_basis

    # A report for somebody else's permutation must not overwrite ours, and
    # must not land under a name the doc-consistency tests expect to find in
    # claims.json.  Only permutations this repo actually claims get the plain
    # filename.
    claims_path = RESULTS / "claims.json"
    ours = set()
    if claims_path.exists():
        ours = {c["perm"] for c in json.loads(claims_path.read_text())}
    if to_string(perm) in ours:
        out = RESULTS / f"basis_k{a.k}_n{n}.json"
    else:
        tag = hashlib.sha1(to_string(perm).encode()).hexdigest()[:8]
        out = RESULTS / f"basis_k{a.k}_n{n}_{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")

    if is_basis:
        print(f"VERDICT: {to_string(perm)} is a BASIS ELEMENT of the "
              f"{a.k}-stack-sortable class.")
        print(f"         The shortest such basis element has length <= {n}.")
        if a.skip_certificate:
            print("         (solver verdict only -- no DRAT certificate was "
                  "produced)")
    else:
        print(f"VERDICT: NOT minimal -- {bad} deletion(s) are still unsortable. "
              f"Run the minimiser.")
    try:
        shown = out.relative_to(ROOT)
    except ValueError:
        shown = out          # an output directory outside the repo is fine
    print(f"wrote {shown}")
    return 0 if is_basis else 1


if __name__ == "__main__":
    raise SystemExit(main())
