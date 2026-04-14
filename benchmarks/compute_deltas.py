"""Compute v4.99.0 delta (Phase 2) + v4.82.0 cumulative delta (Phase 3)."""

import json
import math
from pathlib import Path

ROOT = Path("/mnt/c/Users/Juan/Documents/GitHub/Mapanare")


def load(p):
    return json.load(open(ROOT / p))


v4_98 = load("benchmarks/v4.98.0-final.json")
v4_82 = load("benchmarks/optimizer/v4.82.0-baseline.json")
v4_107 = load("benchmarks/cross_language/v4.107.0-results.json")
v4_110 = load("benchmarks/v4.110.0-final.json")
v4_110_extra = load("benchmarks/v4.110.0-extra.json")

# Build v4.110.0 Mapanare lookup
v110_map = {}
for e in v4_110["results"]:
    if e["language"] == "Mapanare O2":
        v110_map[e["benchmark"]] = e["wall_median_ms"]
for e in v4_110_extra["results"]:
    v110_map[e["benchmark"]] = e["wall_median_ms"]

# v4.98.0 Mapanare lookup (full 10-program baseline)
v98_map = {e["benchmark"]: e["median_ms"] for e in v4_98["mapanare"]}

# v4.82.0 O2-only Mapanare lookup (5 optimizer programs)
v82_map = {e["benchmark"]: e["median_ms"] for e in v4_82["mapanare"] if e.get("opt_level") == "O2"}

# v4.107.0 Mapanare lookup (same harness as v4.110.0)
v107_map = {
    e["benchmark"]: e["wall_median_ms"]
    for e in v4_107["results"] if e["language"] == "Mapanare O2"
}


def delta_row(name, before, after):
    if before is None or after is None:
        return None
    delta_ms = after - before
    delta_pct = (after - before) / before * 100.0 if before else 0.0
    speedup = before / after if after else float("inf")
    arrow = "improved" if delta_ms < 0 else ("regressed" if delta_ms > 0 else "flat")
    return {
        "benchmark": name,
        "before_ms": before,
        "after_ms": after,
        "delta_ms": delta_ms,
        "delta_pct": delta_pct,
        "speedup": speedup,
        "arrow": arrow,
    }


print("=" * 78)
print("  Table 3: v4.98.0 -> v4.110.0 delta (pre-panel baseline)")
print("=" * 78)
print(f"{'benchmark':<20s}  {'v4.98.0':>10s}  {'v4.110.0':>10s}  {'delta':>10s}  {'pct':>8s}  {'speedup':>8s}")
all_bench = sorted(set(list(v98_map.keys()) + list(v110_map.keys())))
for name in all_bench:
    r = delta_row(name, v98_map.get(name), v110_map.get(name))
    if r:
        print(
            f"{name:<20s}  {r['before_ms']:>8.2f}ms  {r['after_ms']:>8.2f}ms  "
            f"{r['delta_ms']:>+8.2f}ms  {r['delta_pct']:>+7.1f}%  {r['speedup']:>6.2f}x"
        )

print()
print("=" * 78)
print("  Table 4: v4.82.0 -> v4.110.0 cumulative delta (optimizer era)")
print("=" * 78)
print(f"{'benchmark':<20s}  {'v4.82.0':>10s}  {'v4.110.0':>10s}  {'delta':>10s}  {'pct':>8s}  {'speedup':>8s}")
speedups = []
for name in ["fib_recursive", "quicksort", "matmul_naive", "string_concat", "agent_fanout"]:
    r = delta_row(name, v82_map.get(name), v110_map.get(name))
    if r:
        print(
            f"{name:<20s}  {r['before_ms']:>8.2f}ms  {r['after_ms']:>8.2f}ms  "
            f"{r['delta_ms']:>+8.2f}ms  {r['delta_pct']:>+7.1f}%  {r['speedup']:>6.2f}x"
        )
        speedups.append(r["speedup"])

# Geometric mean of speedups
if speedups:
    geo = math.exp(sum(math.log(s) for s in speedups) / len(speedups))
    print(f"\n  Geometric mean speedup (v4.82.0 -> v4.110.0, 5 programs): {geo:.3f}x")

print()
print("=" * 78)
print("  Control: v4.107.0 -> v4.110.0 delta (same harness, isolates post-v4.107.0)")
print("=" * 78)
print(f"{'benchmark':<20s}  {'v4.107.0':>10s}  {'v4.110.0':>10s}  {'delta':>10s}  {'pct':>8s}")
for name in sorted(set(list(v107_map.keys()) + list(v110_map.keys()))):
    r = delta_row(name, v107_map.get(name), v110_map.get(name))
    if r:
        print(
            f"{name:<20s}  {r['before_ms']:>8.2f}ms  {r['after_ms']:>8.2f}ms  "
            f"{r['delta_ms']:>+8.2f}ms  {r['delta_pct']:>+7.1f}%"
        )

# Also compute geomean Mapanare/C slowdown for current state (for headline)
print()
print("=" * 78)
print("  Cross-language geomeans (v4.110.0, correct programs only)")
print("=" * 78)
by_bench = {}
for e in v4_110["results"]:
    by_bench.setdefault(e["benchmark"], {})[e["language"]] = e

c_correct = ["fib_recursive", "struct_alloc", "enum_match", "prime_sieve", "string_concat"]  # excluding quicksort (wrong checksum)
print(f"Included (5 correct): {c_correct}")
print(f"Excluded: quicksort (List<Int> indexing bug, docket Qs.1)")
print()

for lang in ["C (gcc -O2)", "C (clang -O2)", "Rust -O", "Go", "Mapanare O2", "Python 3.12"]:
    ratios = []
    for b in c_correct:
        mn = by_bench[b]["Mapanare O2"]["wall_median_ms"]
        other = by_bench[b][lang]["wall_median_ms"]
        if other > 0:
            ratios.append(mn / other)
    if ratios:
        geo = math.exp(sum(math.log(r) for r in ratios) / len(ratios))
        if lang == "Mapanare O2":
            print(f"  {lang:<18s}  (1.000x by def)")
        else:
            print(f"  Mapanare vs {lang:<18s}  ratio={geo:>6.2f}x  (>1 means Mapanare slower)")
