"""Generate a static HTML benchmark report for mapanare.dev/benchmarks.

Phase 4.5: Reads JSON benchmark results and produces a self-contained HTML page
that can be deployed to mapanare.dev/benchmarks.
"""

from __future__ import annotations

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "benchmarks"


def _load_json(name: str) -> list[dict] | None:  # type: ignore[type-arg]
    """Load a benchmark results JSON file if it exists."""
    path = RESULTS_DIR / name
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def generate_html() -> str:
    """Generate the benchmark report HTML."""
    agents = _load_json("results_agents.json")
    streams = _load_json("results_streams.json")
    comparison = _load_json("results_comparison.json")

    def _table_rows(data: list[dict] | None, columns: list[tuple[str, str]]) -> str:  # type: ignore[type-arg]
        if data is None:
            return "<tr><td colspan='99'>No data — run benchmarks first</td></tr>"
        rows = []
        for row in data:
            cells = "".join(f"<td>{_fmt(row.get(key, 'N/A'))}</td>" for key, _ in columns)
            rows.append(f"<tr>{cells}</tr>")
        return "\n".join(rows)

    def _fmt(val: object) -> str:
        if isinstance(val, float):
            return f"{val:,.4f}"
        if isinstance(val, int):
            return f"{val:,}"
        if val is None:
            return "N/A"
        return str(val)

    agent_cols = [
        ("name", "Scenario"),
        ("messages", "Messages"),
        ("agents", "Agents"),
        ("elapsed_s", "Elapsed (s)"),
        ("messages_per_sec", "Msg/sec"),
        ("avg_latency_us", "Avg Latency (us)"),
    ]

    stream_cols = [
        ("name", "Pipeline"),
        ("items", "Items"),
        ("elapsed_s", "Elapsed (s)"),
        ("items_per_sec", "Items/sec"),
        ("avg_latency_us", "Avg Latency (us)"),
    ]

    compare_cols = [
        ("workload", "Workload"),
        ("mapanare_elapsed_s", "Mapanare (s)"),
        ("asyncio_elapsed_s", "asyncio (s)"),
        ("rust_elapsed_s", "Rust (s)"),
        ("mapanare_vs_asyncio", "vs asyncio"),
        ("mapanare_vs_rust", "vs Rust"),
    ]

    def _header(cols: list[tuple[str, str]]) -> str:
        return "<tr>" + "".join(f"<th>{label}</th>" for _, label in cols) + "</tr>"

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Mapanare Benchmarks</title>
<style>
  body {{ font-family: system-ui, sans-serif;
    max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ color: #1a1a2e; }}
  h2 {{ color: #16213e; margin-top: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: right; }}
  th {{ background: #f0f0f0; text-align: center; }}
  td:first-child {{ text-align: left; font-family: monospace; }}
  .note {{ color: #666; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>Mapanare Language Benchmarks</h1>
<p class="note">Generated from benchmark suite.
Run <code>python benchmarks/run_all.py</code> to regenerate.</p>

<h2>Multi-Agent Message Passing</h2>
<table>
{_header(agent_cols)}
{_table_rows(agents, agent_cols)}
</table>

<h2>Stream Pipeline (1M Items)</h2>
<table>
{_header(stream_cols)}
{_table_rows(streams, stream_cols)}
</table>

<h2>Mapanare vs Python asyncio vs Rust</h2>
<table>
{_header(compare_cols)}
{_table_rows(comparison, compare_cols)}
</table>

<p class="note">Rust baselines from
<code>benchmarks/rust_baseline.json</code> when available.</p>
<p class="note">Platform: Mapanare {_mapanare_version()} | Python runtime benchmarks</p>
</body>
</html>"""
    return html


def _mapanare_version() -> str:
    try:
        from mapanare.cli import __version__

        return __version__
    except ImportError:
        return "0.1.0"


def main() -> None:
    """Generate and write the benchmark report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = generate_html()
    out_path = OUTPUT_DIR / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Benchmark report written to {out_path}")


if __name__ == "__main__":
    main()
