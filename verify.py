#!/usr/bin/env python3
"""Independent checker for three-stacks claims.

Standalone: imports nothing from the ``unsortable`` package, written directly
from the operational definition of the machine, so a bug shared with the
solver or the search code cannot hide here.

    input -> S1 -> S2 -> ... -> Sk -> output

    op 1        push the next input element onto S1
    op j (2..k) pop S_{j-1}, push onto S_j
    op k+1      pop S_k, append to the output

Two things can be checked:

  * a POSITIVE claim -- "this permutation is sortable, here is how" --
    is checked by replaying the operation sequence.  This is complete
    and needs no trust in anything else.

  * a NEGATIVE claim -- "this permutation is unsortable" -- is checked
    either by exhaustive replay-search (feasible for small n) or, for
    a SAT-based claim, by handing the DRAT certificate to drat-trim.
    See ``proofcheck.py`` for the certificate side.

Usage::

    python verify.py replay 231 --k 1 --ops 1121...
    python verify.py claims results/claims.json
    python verify.py exhaust 3412 --k 2
"""

from __future__ import annotations

import argparse
import json
import sys


class IllegalOperation(Exception):
    pass


def parse_perm(text):
    text = str(text).strip()
    if any(c in text for c in " ,-"):
        parts = [t for t in text.replace(",", " ").replace("-", " ").split() if t]
        vals = [int(t) for t in parts]
    else:
        vals = [int(c) for c in text]
    if sorted(vals) != list(range(1, len(vals) + 1)):
        raise ValueError("not a permutation of 1..n: %r" % text)
    return vals


def replay(perm, ops, k=3):
    """Run the operation sequence and return the output list.

    Raises IllegalOperation if any step is not legal.
    """
    perm = list(perm)
    n = len(perm)
    ops = [int(o) for o in ops]
    if len(ops) != (k + 1) * n:
        raise IllegalOperation(
            "expected %d operations for n=%d, k=%d; got %d"
            % ((k + 1) * n, n, k, len(ops))
        )
    stacks = [[] for _ in range(k)]
    read = 0
    out = []
    for step, op in enumerate(ops):
        if op == 1:
            if read >= n:
                raise IllegalOperation("step %d: input exhausted" % step)
            stacks[0].append(perm[read])
            read += 1
        elif 2 <= op <= k:
            if not stacks[op - 2]:
                raise IllegalOperation("step %d: S%d is empty" % (step, op - 1))
            stacks[op - 1].append(stacks[op - 2].pop())
        elif op == k + 1:
            if not stacks[k - 1]:
                raise IllegalOperation("step %d: S%d is empty" % (step, k))
            out.append(stacks[k - 1].pop())
        else:
            raise IllegalOperation("step %d: bad operation %r" % (step, op))
    if read != n or any(stacks) :
        raise IllegalOperation("machine did not drain")
    return out


def sorts(perm, ops, k=3):
    """True iff ops is a legal run on perm that outputs the identity."""
    try:
        out = replay(perm, ops, k)
    except IllegalOperation:
        return False
    return out == sorted(out)


def exhaust(perm, k=3):
    """Exhaustive independent search.  Returns an op sequence or None.

    No pruning beyond legality and 'never output a wrong value'.  Slow on
    purpose -- this is the thing the fast searcher is checked against.
    """
    perm = list(perm)
    n = len(perm)
    seen = set()

    def go(read, stacks, out_count, ops):
        if out_count == n:
            return list(ops)
        key = (read, tuple(tuple(s) for s in stacks))
        if key in seen:
            return None
        seen.add(key)
        if read < n:
            stacks[0].append(perm[read])
            ops.append(1)
            r = go(read + 1, stacks, out_count, ops)
            if r is not None:
                return r
            ops.pop()
            stacks[0].pop()
        for j in range(2, k + 1):
            if stacks[j - 2]:
                v = stacks[j - 2].pop()
                stacks[j - 1].append(v)
                ops.append(j)
                r = go(read, stacks, out_count, ops)
                if r is not None:
                    return r
                ops.pop()
                stacks[j - 1].pop()
                stacks[j - 2].append(v)
        if stacks[k - 1] and stacks[k - 1][-1] == out_count + 1:
            v = stacks[k - 1].pop()
            ops.append(k + 1)
            r = go(read, stacks, out_count + 1, ops)
            if r is not None:
                return r
            ops.pop()
            stacks[k - 1].append(v)
        return None

    return go(0, [[] for _ in range(k)], 0, [])


def check_claims(path):
    """Check a claims file.  Returns (n_ok, n_bad) and prints a report.

    Each claim is a dict:
        {"perm": "3412", "k": 2, "sortable": true, "ops": "112..."}
        {"perm": "...",  "k": 3, "sortable": false,
         "evidence": "exhaustive" | {"drat": "proofs/x.drat", ...}}
    """
    with open(path) as fh:
        claims = json.load(fh)
    if isinstance(claims, dict):
        claims = claims.get("claims", [])
    ok = bad = 0
    for c in claims:
        perm = parse_perm(c["perm"])
        k = int(c.get("k", 3))
        label = "%s (k=%d)" % ("".join(map(str, perm)) if max(perm) < 10
                               else "-".join(map(str, perm)), k)
        if c.get("sortable"):
            good = sorts(perm, parse_ops(c["ops"]), k)
            print("%-28s sortable   : %s" % (label, "OK" if good else "FAILED"))
        else:
            ev = c.get("evidence")
            if ev == "exhaustive":
                good = exhaust(perm, k) is None
                print("%-28s unsortable : %s (independent exhaustive search)"
                      % (label, "OK" if good else "FAILED"))
            else:
                print("%-28s unsortable : SKIPPED (certificate claim; "
                      "run proofcheck.py)" % label)
                continue
        ok += bool(good)
        bad += (not good)
    print("\n%d verified, %d failed" % (ok, bad))
    return ok, bad


def parse_ops(s):
    if isinstance(s, (list, tuple)):
        return [int(x) for x in s]
    return [int(c) for c in str(s).strip() if not c.isspace()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("replay", help="replay an operation sequence")
    p.add_argument("perm")
    p.add_argument("--ops", required=True)
    p.add_argument("--k", type=int, default=3)

    p = sub.add_parser("exhaust", help="independent exhaustive search")
    p.add_argument("perm")
    p.add_argument("--k", type=int, default=3)

    p = sub.add_parser("claims", help="check a claims json file")
    p.add_argument("path")

    a = ap.parse_args(argv)
    if a.cmd == "replay":
        perm = parse_perm(a.perm)
        out = replay(perm, parse_ops(a.ops), a.k)
        good = out == sorted(out)
        print("output:", "".join(map(str, out)) if max(out) < 10 else out)
        print("SORTS" if good else "DOES NOT SORT")
        return 0 if good else 1
    if a.cmd == "exhaust":
        perm = parse_perm(a.perm)
        r = exhaust(perm, a.k)
        if r is None:
            print("UNSORTABLE by %d stacks in series (exhaustive)" % a.k)
        else:
            print("SORTABLE:", "".join(map(str, r)))
        return 0
    if a.cmd == "claims":
        ok, bad = check_claims(a.path)
        return 0 if bad == 0 else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
