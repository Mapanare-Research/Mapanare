"""Run all Mapanare benchmarks and produce a summary report.

Uses the isolation harness (benchmarks/isolate.py) for reliable measurements:
GC disabled, warmup runs, median of N samples, IQR outlier removal, CV noise detection.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from benchmarks.bench_agents import run_agent_benchmarks
from benchmarks.bench_compare import run_comparison
from benchmarks.bench_streams import run_stream_benchmarks


async def run_all() -> dict:  # type: ignore[type-arg]
    """Run all benchmark suites and return combined results."""
    from dataclasses import asdict

    print("Running agent benchmarks...")
    agents = await run_agent_benchmarks(n_messages=10_000)

    print("Running stream benchmarks...")
    streams = await run_stream_benchmarks(n_items=1_000_000)

    print("Running comparison benchmarks...")
    comparison = await run_comparison(n_messages=10_000, n_items=1_000_000)

    return {
        "agents": [asdict(r) for r in agents],
        "streams": [asdict(r) for r in streams],
        "comparison": [asdict(r) for r in comparison],
    }


def main() -> None:
    """Entry point."""
    results = asyncio.run(run_all())

    out_path = Path("benchmarks/results_all.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nAll benchmark results written to {out_path}")
    print("\nSummary:")
    print(f"  Agent benchmarks:  {len(results['agents'])} scenarios")
    print(f"  Stream benchmarks: {len(results['streams'])} scenarios")
    print(f"  Comparisons:       {len(results['comparison'])} workloads")

    # Check for noisy results
    noisy = []
    for section_name, section in results.items():
        for entry in section:
            cv = entry.get("cv")
            if cv is not None and cv > 0.05:
                name = entry.get("name") or entry.get("workload") or "?"
                noisy.append(f"  {section_name}/{name}: CV={cv:.1%}")
    if noisy:
        print("\nWarning: noisy results (CV > 5%) — consider re-running:")
        for line in noisy:
            print(line)


if __name__ == "__main__":
    main()
