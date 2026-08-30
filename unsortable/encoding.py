"""M1: SAT encoding of k-stack-in-series sortability.

The encoding is the interval / non-crossing one proved in ``docs/notes.md``.
Each value ``v`` gets ``k+1`` event times ``t_1[v] < ... < t_{k+1}[v]``; only
their *relative* order matters, so the variables are pairwise "before"
literals over the ``(k+1)n`` events, with transitivity clauses making the
relation a total order.

Constraints:

  (a) input order      t_1 order agrees with pi
  (b) output order     t_{k+1} order agrees with value order
  (c) non-crossing     for each stack s, the occupancy intervals
                       [t_s[v], t_{s+1}[v]] are pairwise nested or disjoint

Two modes:

``mode="full"`` (default)
    A faithful, auditable CNF.  Unit clauses come only from the constraints
    themselves; all transitivity triples are emitted; the solver derives
    everything else.  Use this for any claim shipping a DRAT certificate: the
    certificate proves *this CNF* unsatisfiable and nothing more.

``mode="reduced"``
    The encoder first computes the transitive closure of the forced
    precedences and drops variables and clauses that are thereby determined.
    Much smaller and faster; used during the search.  Anything it flags is
    re-run in ``full`` mode before being claimed.

A DRAT proof certifies that the CNF is unsatisfiable.  That the CNF *is* the
sortability question is established by the proof in ``docs/notes.md`` and by
exhaustive agreement with the brute-force simulator
(``tests/test_encoding.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable, Sequence

from .perms import Perm, check

TRUE = 1
FALSE = -1
FREE = 0


@dataclass
class Instance:
    """A CNF for 'is this permutation k-stack-sortable?'."""

    perm: Perm
    k: int
    mode: str
    n_events: int
    n_vars: int
    clauses: list[list[int]]
    var_of: dict[tuple[int, int], int]  # (e, f) with e < f  ->  variable
    trivially_unsat: bool = False
    reason: str = ""

    # --- event bookkeeping ---------------------------------------------
    def event(self, value: int, phase: int) -> int:
        """Event id for value performing operation r_{phase+1} (phase 0..k)."""
        return (value - 1) * (self.k + 1) + phase

    def event_name(self, e: int) -> tuple[int, int]:
        return (e // (self.k + 1) + 1, e % (self.k + 1))

    @property
    def n_clauses(self) -> int:
        return len(self.clauses)

    def to_dimacs(self) -> str:
        head = f"p cnf {self.n_vars} {len(self.clauses)}\n"
        body = "".join(" ".join(map(str, c)) + " 0\n" for c in self.clauses)
        return head + body

    def write_dimacs(self, path) -> None:
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", newline="\n") as fh:
            fh.write(f"c 3-stacks: is {''.join(map(str, self.perm)) if max(self.perm) < 10 else '-'.join(map(str, self.perm))} sortable by {self.k} stacks in series?\n")
            fh.write(f"c encoding mode: {self.mode}\n")
            fh.write(f"p cnf {self.n_vars} {len(self.clauses)}\n")
            for c in self.clauses:
                fh.write(" ".join(map(str, c)))
                fh.write(" 0\n")


class _Builder:
    def __init__(self, perm: Sequence[int], k: int, mode: str):
        self.perm = check(perm)
        self.n = len(self.perm)
        self.k = k
        self.mode = mode
        self.N = (k + 1) * self.n
        self.clauses: list[list[int]] = []
        self.var_of: dict[tuple[int, int], int] = {}
        self.n_vars = 0
        # known[e][f] in {TRUE, FALSE, FREE}: is 'e before f' determined?
        self.known: list[list[int]] | None = None
        self.unsat = False
        self.reason = ""

    # -- events --
    def ev(self, v: int, phase: int) -> int:
        return (v - 1) * (self.k + 1) + phase

    # -- variables --
    def var(self, e: int, f: int) -> int:
        key = (e, f) if e < f else (f, e)
        vid = self.var_of.get(key)
        if vid is None:
            self.n_vars += 1
            vid = self.n_vars
            self.var_of[key] = vid
        return vid

    def lit(self, e: int, f: int) -> int:
        """Literal meaning 'event e happens before event f'."""
        return self.var(e, f) if e < f else -self.var(f, e)

    # -- the forced precedence graph, straight from the constraints --
    def base_edges(self) -> list[tuple[int, int]]:
        edges = []
        # phases of one element happen in order
        for v in range(1, self.n + 1):
            for p in range(self.k):
                edges.append((self.ev(v, p), self.ev(v, p + 1)))
        # (a) input order: consecutive entries of pi suffice, the rest follows
        for i in range(self.n - 1):
            edges.append((self.ev(self.perm[i], 0), self.ev(self.perm[i + 1], 0)))
        # (b) output order: consecutive values suffice
        for v in range(1, self.n):
            edges.append((self.ev(v, self.k), self.ev(v + 1, self.k)))
        return edges

    def build(self) -> Instance:
        edges = self.base_edges()

        if self.mode == "reduced":
            self.known = _closure(self.N, edges)
            if self.known is None:
                return self._bail("forced precedences contain a cycle")
        else:
            self.known = None
            for e, f in edges:
                self.clauses.append([self.lit(e, f)])

        self._transitivity()
        if self.unsat:
            return self._bail(self.reason)
        self._noncrossing()
        if self.unsat:
            return self._bail(self.reason)

        return Instance(
            perm=self.perm, k=self.k, mode=self.mode, n_events=self.N,
            n_vars=self.n_vars, clauses=self.clauses, var_of=self.var_of,
        )

    def _bail(self, reason: str) -> Instance:
        return Instance(
            perm=self.perm, k=self.k, mode=self.mode, n_events=self.N,
            n_vars=self.n_vars, clauses=[[1], [-1]] if self.n_vars == 0 else self.clauses + [[]],
            var_of=self.var_of, trivially_unsat=True, reason=reason,
        )

    # -- clause helpers that respect 'known' in reduced mode --
    def _state(self, e: int, f: int) -> int:
        if self.known is None:
            return FREE
        return self.known[e][f]

    def _emit(self, triples: Iterable[tuple[int, int, bool]]) -> None:
        """Emit one clause given (e, f, positive) literal specs.

        A literal spec (e, f, True) means 'e before f'; (e, f, False) means
        its negation.  Determined literals are folded away.
        """
        out: list[int] = []
        for e, f, pos in triples:
            st = self._state(e, f)
            if st == TRUE:
                if pos:
                    return  # clause satisfied
                continue  # literal is false, drop it
            if st == FALSE:
                if not pos:
                    return
                continue
            lit = self.lit(e, f)
            out.append(lit if pos else -lit)
        if not out:
            self.unsat = True
            self.reason = self.reason or "constraint reduced to the empty clause"
            return
        self.clauses.append(out)

    def _transitivity(self) -> None:
        for a, b, c in combinations(range(self.N), 3):
            # a<b & b<c -> a<c
            self._emit([(a, b, False), (b, c, False), (a, c, True)])
            if self.unsat:
                return
            # b<a & c<b -> c<a
            self._emit([(a, b, True), (b, c, True), (a, c, False)])
            if self.unsat:
                return

    def _noncrossing(self) -> None:
        n, k = self.n, self.k
        for s in range(k):  # stack S_{s+1}: interval [t_{s+1}, t_{s+2}]
            for v in range(1, n + 1):
                av, bv = self.ev(v, s), self.ev(v, s + 1)
                for w in range(1, n + 1):
                    if w == v:
                        continue
                    aw, bw = self.ev(w, s), self.ev(w, s + 1)
                    # forbid a_v < a_w < b_v < b_w
                    self._emit([(av, aw, False), (aw, bv, False), (bv, bw, False)])
                    if self.unsat:
                        return


def _closure(N: int, edges: Sequence[tuple[int, int]]) -> list[list[int]] | None:
    """Transitive closure as a known-relation matrix, or None if cyclic."""
    reach = [0] * N  # bitmask of nodes reachable from i (excluding i)
    adj: list[list[int]] = [[] for _ in range(N)]
    for a, b in edges:
        adj[a].append(b)

    colour = [0] * N  # 0 white, 1 grey, 2 black
    order: list[int] = []
    for root in range(N):
        if colour[root]:
            continue
        stack = [(root, 0)]
        colour[root] = 1
        while stack:
            node, idx = stack[-1]
            if idx < len(adj[node]):
                stack[-1] = (node, idx + 1)
                nxt = adj[node][idx]
                if colour[nxt] == 1:
                    return None  # cycle
                if colour[nxt] == 0:
                    colour[nxt] = 1
                    stack.append((nxt, 0))
            else:
                stack.pop()
                colour[node] = 2
                order.append(node)
    for node in order:  # reverse topological order
        m = 0
        for nxt in adj[node]:
            m |= (1 << nxt) | reach[nxt]
        reach[node] = m

    known = [[FREE] * N for _ in range(N)]
    for a in range(N):
        ra = reach[a]
        for b in range(N):
            if a != b and (ra >> b) & 1:
                known[a][b] = TRUE
                known[b][a] = FALSE
    return known


def encode(perm: Sequence[int], k: int = 3, mode: str = "full") -> Instance:
    if mode not in ("full", "reduced"):
        raise ValueError("mode must be 'full' or 'reduced'")
    return _Builder(perm, k, mode).build()


# --- solving ----------------------------------------------------------------

@dataclass
class Result:
    perm: Perm
    k: int
    sortable: bool
    ops: tuple[int, ...] | None = None
    proof: list[str] | None = None
    mode: str = "full"
    n_vars: int = 0
    n_clauses: int = 0
    seconds: float = 0.0
    solver: str = ""
    note: str = ""


def solve(
    perm: Sequence[int],
    k: int = 3,
    mode: str = "full",
    with_proof: bool = False,
    solver_name: str = "cadical195",
    time_budget: float | None = None,
) -> Result:
    """Decide sortability with a SAT solver.

    Returns a Result; on SAT, ``ops`` is a replayable operation sequence.
    On UNSAT with ``with_proof``, ``proof`` holds the DRAT lines.
    """
    import time

    from pysat.formula import CNF
    from pysat.solvers import Solver

    inst = encode(perm, k=k, mode=mode)
    if inst.trivially_unsat:
        return Result(perm=inst.perm, k=k, sortable=False, mode=mode,
                      n_vars=inst.n_vars, n_clauses=inst.n_clauses,
                      note=f"unsat during encoding: {inst.reason}")

    cnf = CNF(from_clauses=inst.clauses)
    t0 = time.perf_counter()
    kwargs = {}
    if with_proof:
        kwargs["with_proof"] = True
    with Solver(name=solver_name, bootstrap_with=cnf, **kwargs) as s:
        if time_budget is not None:
            # PySAT has no portable timeout; caller should use a subprocess.
            pass
        sat = s.solve()
        model = s.get_model() if sat else None
        proof = None
        if not sat and with_proof:
            proof = s.get_proof()
    dt = time.perf_counter() - t0

    ops = _model_to_ops(inst, model) if sat else None
    return Result(perm=inst.perm, k=k, sortable=bool(sat), ops=ops, proof=proof,
                  mode=mode, n_vars=inst.n_vars, n_clauses=inst.n_clauses,
                  seconds=dt, solver=solver_name)


def _model_to_ops(inst: Instance, model: Sequence[int]) -> tuple[int, ...]:
    """Turn a satisfying assignment into a replayable operation word."""
    truth = {abs(l): (l > 0) for l in model}
    N = inst.n_events
    k = inst.k

    # rebuild the 'known' relation the same way the builder did, so that
    # reduced-mode instances (which omit determined pairs) still decode.
    b = _Builder(inst.perm, inst.k, inst.mode)
    known = _closure(N, b.base_edges()) if inst.mode == "reduced" else None

    def before(e: int, f: int) -> bool:
        if known is not None and known[e][f] != FREE:
            return known[e][f] == TRUE
        key = (e, f) if e < f else (f, e)
        vid = inst.var_of.get(key)
        if vid is None:
            raise KeyError(f"no variable for pair {key}")
        val = truth.get(vid, True)
        return val if e < f else not val

    rank = [0] * N
    for e in range(N):
        rank[e] = sum(1 for f in range(N) if f != e and before(f, e))
    order = sorted(range(N), key=lambda e: rank[e])
    return tuple(order[i] % (k + 1) + 1 for i in range(N))


def is_sortable(perm: Sequence[int], k: int = 3, mode: str = "reduced") -> bool:
    return solve(perm, k=k, mode=mode).sortable


_WORKER_DECIDERS: dict = {}


def worker_is_sortable(perm: Sequence[int], k: int = 3) -> bool:
    """Process-local cached FixedLengthDecider, keyed by (length, k).

    For use as the map function of a ProcessPoolExecutor: each worker builds
    the shared CNF for a given length once and reuses it, so a fan-out over a
    neighbourhood or a deletion scan pays the build cost once per worker
    rather than once per permutation.
    """
    key = (len(perm), k)
    d = _WORKER_DECIDERS.get(key)
    if d is None:
        d = _WORKER_DECIDERS[key] = FixedLengthDecider(len(perm), k=k)
    return d.is_sortable(perm)


class FixedLengthDecider:
    """Decide many permutations of the *same* length, sharing one CNF.

    Only one part of the encoding depends on the permutation.  Transitivity,
    the non-crossing clauses, the per-element phase order and the output order
    are all identical for every permutation of a given length -- the input
    order (a) is the only thing that changes, and it is n-1 unit facts about
    the ``t_1`` events.

    So: build the formula once, then decide each permutation by solving under
    those n-1 literals as **assumptions**.  Profiling one decision at n = 22
    showed 46% of the time building the CNF in Python and 40% handing it to
    the solver, against 14% actually solving.  This removes both for every
    call after the first, and lets the solver carry learned clauses across
    closely related instances -- a neighbourhood, a plateau walk -- which is
    the larger win.

    Asserting a unit clause and assuming the same literal are
    equisatisfiable, so correctness is unchanged; ``tests/test_encoding.py``
    checks this class against the one-shot path exhaustively.
    """

    def __init__(self, n: int, k: int = 3, solver_name: str = "cadical195"):
        from pysat.formula import CNF
        from pysat.solvers import Solver

        self.n, self.k = n, k
        b = _Builder(tuple(range(1, n + 1)), k, "full")
        # every clause except the input order, which becomes assumptions
        b._transitivity()
        b._noncrossing()
        for v in range(1, n + 1):
            for p in range(k):
                b.clauses.append([b.lit(b.ev(v, p), b.ev(v, p + 1))])
        for v in range(1, n):
            b.clauses.append([b.lit(b.ev(v, k), b.ev(v + 1, k))])
        self._b = b
        self.n_vars, self.n_clauses = b.n_vars, len(b.clauses)
        self._solver = Solver(name=solver_name,
                              bootstrap_with=CNF(from_clauses=b.clauses))
        self.calls = 0

    def _assumptions(self, perm: Sequence[int]) -> list[int]:
        b = self._b
        return [b.lit(b.ev(perm[i], 0), b.ev(perm[i + 1], 0))
                for i in range(len(perm) - 1)]

    def is_sortable(self, perm: Sequence[int]) -> bool:
        p = check(perm)
        if len(p) != self.n:
            raise ValueError(f"expected length {self.n}, got {len(p)}")
        self.calls += 1
        return bool(self._solver.solve(assumptions=self._assumptions(p)))

    def ops(self, perm: Sequence[int]) -> tuple[int, ...] | None:
        """A replayable operation word, or None if unsortable."""
        if not self.is_sortable(perm):
            return None
        inst = Instance(perm=check(perm), k=self.k, mode="full",
                        n_events=self._b.N, n_vars=self._b.n_vars,
                        clauses=self._b.clauses, var_of=self._b.var_of)
        return _model_to_ops(inst, self._solver.get_model())

    def close(self) -> None:
        self._solver.delete()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
