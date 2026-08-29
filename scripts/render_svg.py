"""Draw a sorting run as the nesting diagram the SAT encoding actually sees.

Time runs left to right over the 4n operations.  Each stack gets a lane; a
value's bar in lane s spans the interval during which it occupies S_s, drawn
at a height equal to its depth in that stack.  Sortability is exactly the
statement that all three lanes can be drawn without two bars *crossing* --
which in this layout means no bar ever starts inside another and ends
outside it.

    python scripts/render_svg.py --perm 231 --k 2 --out docs/img/231-k2.svg
    python scripts/render_svg.py --perm 41352 --k 3 --out docs/img/41352.svg
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unsortable.perms import from_string, to_string
from unsortable.simulator import sorting_sequence

PALETTE = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2",
           "#ff9da6", "#9d755d", "#eeca3b", "#bab0ac"]


def trace(perm, ops, k):
    """Replay, returning per-value event times and per-interval stack depths."""
    n = len(perm)
    stacks = [[] for _ in range(k)]
    read = 0
    times = {v: [None] * (k + 1) for v in perm}
    depth = {v: [None] * k for v in perm}
    out = []
    for t, op in enumerate(ops):
        if op == 1:
            v = perm[read]
            read += 1
            times[v][0] = t
            depth[v][0] = len(stacks[0])
            stacks[0].append(v)
        elif op <= k:
            v = stacks[op - 2].pop()
            times[v][op - 1] = t
            depth[v][op - 1] = len(stacks[op - 1])
            stacks[op - 1].append(v)
        else:
            v = stacks[k - 1].pop()
            times[v][k] = t
            out.append(v)
    return times, depth, out


def render(perm, ops, k) -> str:
    n = len(perm)
    times, depth, out = trace(perm, ops, k)
    T = len(ops)

    unit = max(14, min(30, 900 // max(T, 1)))
    bar = 15
    gap = 4
    pad = 56
    maxdepth = [max((depth[v][s] for v in perm), default=0) + 1 for s in range(k)]
    lane_h = [d * (bar + gap) + 20 for d in maxdepth]
    W = pad + T * unit + pad
    H = 96 + sum(lane_h) + 70

    css = """
    text { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }
    .lane { fill: var(--lane); }
    .lbl  { fill: var(--fg); font-size: 13px; font-weight: 600; }
    .tick { fill: var(--muted); font-size: 10px; }
    .val  { fill: #fff; font-size: 11px; font-weight: 700; }
    .cap  { fill: var(--muted); font-size: 11px; }
    """
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img">',
        '<style>'
        ':root{--bg:#ffffff;--fg:#1b1f24;--muted:#6b7280;--lane:#f1f3f5;}'
        '@media (prefers-color-scheme: dark){'
        ':root{--bg:#0d1117;--fg:#e6edf3;--muted:#8b949e;--lane:#161b22;}}'
        + css + '</style>',
        f'<rect width="{W}" height="{H}" fill="var(--bg)"/>',
    ]

    def x(t: float) -> float:
        return pad + t * unit

    # input row
    parts.append(f'<text class="lbl" x="8" y="30">in</text>')
    for i, v in enumerate(perm):
        c = PALETTE[(v - 1) % len(PALETTE)]
        parts.append(
            f'<rect x="{x(i) + 1:.1f}" y="16" width="{unit - 2:.1f}" height="{bar}" '
            f'rx="3" fill="{c}"/>'
            f'<text class="val" x="{x(i) + unit / 2:.1f}" y="27.5" '
            f'text-anchor="middle">{v}</text>')

    y = 52
    for s in range(k):
        parts.append(f'<rect x="{pad}" y="{y}" width="{T * unit}" '
                     f'height="{lane_h[s]}" rx="6" class="lane"/>')
        parts.append(f'<text class="lbl" x="8" y="{y + 16}">S{s + 1}</text>')
        for v in perm:
            a, b = times[v][s], times[v][s + 1]
            d = depth[v][s]
            yy = y + 10 + d * (bar + gap)
            w = (b - a) * unit
            c = PALETTE[(v - 1) % len(PALETTE)]
            parts.append(
                f'<rect x="{x(a):.1f}" y="{yy}" width="{w:.1f}" height="{bar}" '
                f'rx="3" fill="{c}" fill-opacity="0.92"/>')
            if w >= 12:
                parts.append(
                    f'<text class="val" x="{x(a) + w / 2:.1f}" y="{yy + 11.5}" '
                    f'text-anchor="middle">{v}</text>')
        y += lane_h[s] + 8

    # output row
    parts.append(f'<text class="lbl" x="8" y="{y + 24}">out</text>')
    for j, v in enumerate(out):
        c = PALETTE[(v - 1) % len(PALETTE)]
        t = times[v][k]
        parts.append(
            f'<rect x="{x(t) + 1:.1f}" y="{y + 10}" width="{unit - 2:.1f}" '
            f'height="{bar}" rx="3" fill="{c}"/>'
            f'<text class="val" x="{x(t) + unit / 2:.1f}" y="{y + 21.5}" '
            f'text-anchor="middle">{v}</text>')

    ops_str = "".join(map(str, ops))
    parts.append(
        f'<text class="cap" x="{pad}" y="{H - 22}">'
        f'{to_string(perm)}  &#183;  {k} stacks in series  &#183;  '
        f'{len(ops)} operations</text>')
    parts.append(
        f'<text class="cap" x="{pad}" y="{H - 8}">{ops_str}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perm", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--ops", default=None, help="operation word; found automatically if omitted")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)

    perm = from_string(a.perm)
    if a.ops:
        ops = tuple(int(c) for c in a.ops.strip())
    else:
        ops = sorting_sequence(perm, k=a.k)
        if ops is None:
            print(f"{to_string(perm)} is not sortable by {a.k} stacks in series; "
                  "nothing to draw")
            return 1
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(render(perm, ops, a.k), encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
