"""M4 + M5: find unsortable permutations and minimise them.

    python scripts/hunt.py random   --n 40 --rounds 20 --k 3
    python scripts/hunt.py minimise --perm 27-11-36-... --k 3
    python scripts/hunt.py families --k 3

Every witness found is appended to results/witnesses.jsonl, and the best
one so far is echoed at the end.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable import search
from unsortable.encoding import solve
from unsortable.minimizer import minimise, sat_decider
from unsortable.perms import from_string, to_string

WITNESSES = ROOT / "results" / "witnesses.jsonl"


def record(kind: str, perm, k: int, minimal: bool, extra=None) -> None:
    WITNESSES.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "perm": to_string(perm),
        "n": len(perm),
        "k": k,
        "minimal": minimal,
        "kind": kind,
    }
    if extra:
        row.update(extra)
    with WITNESSES.open("a", newline="\n") as fh:
        fh.write(json.dumps(row) + "\n")


def do_minimise(perm, k: int, cache: dict, seed: int = 0,
                workers: int = 1) -> tuple:
    t0 = time.time()
    print(f"minimising length-{len(perm)} witness {to_string(perm)}", flush=True)

    def on_step(cur, how):
        print(f"    -> {len(cur):3d}  ({how})  {to_string(cur)}", flush=True)
        # checkpoint every step: an interrupted run loses at most one deletion
        record("descent", cur, k, False,
               {"from": to_string(perm), "seconds": round(time.time() - t0, 1)})

    # a shared in-process cache is pointless once workers fan out
    decide = None if workers > 1 else sat_decider(k, cache=cache)
    rep = minimise(perm, k=k, decide=decide, on_step=on_step,
                   rng=random.Random(seed), workers=workers)
    print(f"  minimal at length {rep.length} after {rep.decisions} solver calls "
          f"({time.time() - t0:.1f}s): {to_string(rep.result)}", flush=True)
    record("minimised", rep.result, k, True,
           {"from": to_string(rep.start), "from_n": rep.start_length,
            "solver_calls": rep.decisions, "seconds": round(time.time() - t0, 1)})
    return rep.result


def cmd_random(a) -> int:
    rng = random.Random(a.seed)
    cache: dict = {}
    decide = sat_decider(a.k, cache=cache)
    best = None
    for rnd in range(a.rounds):
        t0 = time.time()
        p = search.find_random_unsortable(a.n, decide, rng, trials=a.trials)
        if p is None:
            print(f"round {rnd}: no unsortable permutation in {a.trials} "
                  f"random tries at n={a.n}", flush=True)
            continue
        print(f"round {rnd}: found unsortable n={a.n} in {time.time()-t0:.1f}s: "
              f"{to_string(p)}", flush=True)
        record("random", p, a.k, False, {"round": rnd})
        m = do_minimise(p, a.k, cache, seed=a.seed + rnd,
                        workers=a.workers)
        if best is None or len(m) < len(best):
            best = m
            print(f"  *** new best: length {len(best)} ***", flush=True)
    if best is not None:
        print(f"\nbest minimal witness: length {len(best)}  {to_string(best)}")
    return 0


def cmd_minimise(a) -> int:
    perm = from_string(a.perm)
    r = solve(perm, k=a.k, mode="reduced")
    if r.sortable:
        print(f"{to_string(perm)} is sortable by {a.k} stacks; nothing to do")
        return 1
    do_minimise(perm, a.k, {}, seed=a.seed, workers=a.workers)
    return 0


def cmd_hop(a) -> int:
    """Basin hopping over basis elements.

    Deleting more points from a basis element provably cannot shorten it
    (see unsortable/minimizer.py), so the only way down is to reach a
    *different* basis element.  Climb a few points -- free, because upward
    closure keeps the result unsortable -- then descend along a fresh random
    path.

    Accepting equal-length results as the new current point matters: without
    it every iteration perturbs the same permutation and the search never
    wanders, it just retries one point.  With it the walk drifts across the
    plateau of length-L basis elements, which is where the openings to L-1
    are found.
    """
    rng = random.Random(a.seed)
    cur = from_string(a.perm)
    r = solve(cur, k=a.k, mode="reduced")
    if r.sortable:
        print(f"{to_string(cur)} is sortable; give me an unsortable start")
        return 1
    if not a.assume_minimal:
        cur = do_minimise(cur, a.k, {}, seed=rng.randrange(10 ** 6),
                          workers=a.workers)
    best = cur
    print(f"\nstarting basin hop from length {len(cur)}\n", flush=True)
    record("hop-best", best, a.k, True, {"iteration": -1})

    stuck = 0
    plateau = 0
    for it in range(a.iterations):
        climb = rng.randint(a.climb_min, a.climb_max)
        start = search.perturb(cur, climb, rng)
        rep = minimise(start, k=a.k, rng=random.Random(rng.randrange(10 ** 6)),
                       workers=a.workers)
        cand = rep.result
        mark = ""
        if len(cand) < len(cur):
            cur, stuck, plateau = cand, 0, 0
        elif len(cand) == len(cur) and rng.random() < a.plateau:
            cur, plateau = cand, plateau + 1  # drift sideways
            mark = "  (plateau move)"
            stuck += 1
        else:
            stuck += 1
        if len(cand) < len(best):
            best = cand
            mark = "  *** NEW BEST ***"
            record("hop-best", best, a.k, True, {"iteration": it})
        print(f"[{it}] {len(start)} -> {len(cand)}  (cur {len(cur)}, best "
              f"{len(best)}){mark}", flush=True)
        if mark:
            print(f"      {to_string(cand)}", flush=True)
        if stuck and stuck % 25 == 0:
            print(f"      ({stuck} without improvement, {plateau} plateau moves)",
                  flush=True)
    print(f"\nbest basis element found: length {len(best)}\n{to_string(best)}")
    return 0


def cmd_walk(a) -> int:
    """Random-walk the set of unsortable permutations at a FIXED length.

    Basin hopping pays for every plateau step twice: a climb to length ~L+5
    and a full descent back, ~100-200 solver calls with the expensive ones at
    the top.  Walking sideways costs one call at length L per proposal.

    The target is not another basis element -- it is a *non-minimal*
    unsortable permutation, because that one has an unsortable deletion, and
    that deletion has length L-1.  So each accepted step is followed by a
    deletion scan, and the first unsortable deletion ends the search.
    """
    from unsortable.minimizer import _Scanner, _single_points, sat_decider
    from concurrent.futures import ProcessPoolExecutor

    rng = random.Random(a.seed)
    cur = from_string(a.perm)
    L = len(cur)
    if solve(cur, k=a.k, mode="reduced").sortable:
        print(f"{to_string(cur)} is sortable; give me an unsortable start")
        return 1

    pool = ProcessPoolExecutor(max_workers=a.workers) if a.workers > 1 else None
    scan = _Scanner(sat_decider(a.k), a.k, "reduced", a.workers, pool)
    accepted = rejected = harvested = 0
    t0 = time.time()
    try:
        for it in range(a.iterations):
            props = [(f"nbr{i}", q) for i, q in
                     enumerate(search.neighbours(cur, rng, a.batch))]
            hit = scan.first_unsortable(props)
            if hit is None:
                rejected += a.batch
                continue
            cur = hit[1]
            accepted += 1

            # the payoff: is this one non-minimal?
            shorter = scan.first_unsortable(_single_points(cur, rng))
            if shorter is not None:
                q = shorter[1]
                print(f"\n*** LENGTH {len(q)} ***\n{to_string(q)}\n", flush=True)
                record("walk-shorter", q, a.k, True, {"from": to_string(cur)})
                if not a.harvest:
                    return 0
                cur = q          # carry on walking at the new, shorter length
                L = len(q)
                continue
            # every deletion sorts, so this is a distinct basis element.
            # Harvesting these is the point: structure cannot be inferred
            # from the single length-22 witness we started with.
            harvested += 1
            record("walk-basis", cur, a.k, True, {"iteration": it})
            if harvested % 5 == 0:
                print(f"[{it}] harvested {harvested} basis elements at "
                      f"length {L}  ({time.time()-t0:.0f}s)", flush=True)
            if accepted % 10 == 0:
                rate = accepted / max(accepted + rejected, 1)
                print(f"[{it}] {accepted} accepted, {rejected} rejected "
                      f"(accept {rate:.1%}), {scan.calls} calls, "
                      f"{time.time()-t0:.0f}s, still {L}", flush=True)
    finally:
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)
    print(f"\nno length-{L-1} witness after {a.iterations} proposals "
          f"({scan.calls} solver calls, {time.time()-t0:.0f}s)")
    return 1


def cmd_families(a) -> int:
    cache: dict = {}
    decide = sat_decider(a.k, cache=cache)
    for name, p in search.families(max_n=a.max_n):
        if not decide(p):
            print(f"UNSORTABLE {name} (n={len(p)}): {to_string(p)}", flush=True)
            record("family", p, a.k, False, {"family": name})
            do_minimise(p, a.k, cache, seed=a.seed, workers=a.workers)
            return 0
        if a.verbose:
            print(f"  sortable {name} (n={len(p)})", flush=True)
    print("no unsortable member found in the structured families")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--k", type=int, default=3)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--k", type=int, default=3, help="number of stacks in series")
    common.add_argument("--seed", type=int, default=0)
    common.add_argument("--workers", type=int, default=1,
                        help="processes used to scan deletion candidates")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("random", parents=[common])
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--trials", type=int, default=60)
    p.set_defaults(fn=cmd_random)

    p = sub.add_parser("minimise", parents=[common])
    p.add_argument("--perm", required=True)
    p.set_defaults(fn=cmd_minimise)

    p = sub.add_parser("hop", parents=[common])
    p.add_argument("--perm", required=True, help="an unsortable starting permutation")
    p.add_argument("--iterations", type=int, default=200)
    p.add_argument("--climb-min", type=int, default=2)
    p.add_argument("--climb-max", type=int, default=6)
    p.add_argument("--plateau", type=float, default=0.5,
                   help="probability of accepting an equal-length basis element "
                        "as the new current point (0 = never wander)")
    p.add_argument("--assume-minimal", action="store_true",
                   help="skip the initial descent (the start is already a basis element)")
    p.set_defaults(fn=cmd_hop)

    p = sub.add_parser("walk", parents=[common])
    p.add_argument("--perm", required=True, help="an unsortable starting permutation")
    p.add_argument("--iterations", type=int, default=100000)
    p.add_argument("--harvest", action="store_true",
                   help="keep walking after a shorter witness, collecting basis elements")
    p.add_argument("--batch", type=int, default=24,
                   help="neighbours proposed per step (evaluated in parallel)")
    p.set_defaults(fn=cmd_walk)

    p = sub.add_parser("families", parents=[common])
    p.add_argument("--max-n", type=int, default=60)
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(fn=cmd_families)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
