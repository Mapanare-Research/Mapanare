"""Tests for benchmark integrity (Phase 1.3).

Verifies that benchmark .mn files use the language features they claim to test,
compile correctly, and produce valid output.
"""

from __future__ import annotations

from mapanare.cli import _compile_source

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _compile_and_run(mn_path: str) -> str:
    """Compile a .mn file and execute, returning stdout."""
    import io
    import sys
    from pathlib import Path

    source = Path(mn_path).read_text(encoding="utf-8")
    code = _compile_source(source, mn_path)

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    try:
        # Execute the compiled code
        exec(compile(code, mn_path, "exec"), {"__name__": "__main__"})
        # If there's an asyncio.run in the code, it already ran
    finally:
        sys.stdout = old_stdout

    return captured.getvalue().strip()


# ---------------------------------------------------------------------------
# Task 1: Stream pipeline uses actual stream primitives
# ---------------------------------------------------------------------------


class TestStreamPipelineIntegrity:
    """Verify 03_stream_pipeline.mn uses stream primitives."""

    def test_compiles(self) -> None:
        from pathlib import Path

        source = Path("test_vs/03_stream_pipeline.mn").read_text(encoding="utf-8")
        code = _compile_source(source, "03_stream_pipeline.mn")
        assert "Stream.from_iter" in code or "stream" in code

    def test_uses_stream_primitives(self) -> None:
        from pathlib import Path

        source = Path("test_vs/03_stream_pipeline.mn").read_text(encoding="utf-8")
        # Must use stream() constructor
        assert "stream(" in source
        # Must use at least one stream operator
        assert ".map(" in source or ".filter(" in source or ".fold(" in source

    def test_does_not_use_plain_loop_only(self) -> None:
        from pathlib import Path

        source = Path("test_vs/03_stream_pipeline.mn").read_text(encoding="utf-8")
        code = _compile_source(source, "03_stream_pipeline.mn")
        # The compiled code should use Stream, not just a for loop
        assert "Stream" in code or "stream" in code

    def test_produces_correct_output(self) -> None:
        output = _compile_and_run("test_vs/03_stream_pipeline.mn")
        # stream(0..1000000).map(x => x*3).filter(x => x%2==0).fold(0, +)
        # Sum of x*3 for even x*3 in 0..999999
        # x*3 is even when x is even, so sum of 6*x for x in 0,1,...,499999
        # = 6 * (499999 * 500000 / 2) = 6 * 124999750000 = 749998500000
        assert output == "749998500000"


# ---------------------------------------------------------------------------
# Task 2: Concurrency benchmark uses multiple agents
# ---------------------------------------------------------------------------


class TestConcurrencyIntegrity:
    """Verify 02_concurrency.mn uses actual concurrent agents."""

    def test_uses_agent_primitives(self) -> None:
        from pathlib import Path

        source = Path("test_vs/02_concurrency.mn").read_text(encoding="utf-8")
        assert "agent " in source
        assert "spawn " in source
        assert "<-" in source
        assert "sync " in source

    def test_uses_multiple_agents(self) -> None:
        from pathlib import Path

        source = Path("test_vs/02_concurrency.mn").read_text(encoding="utf-8")
        # Should spawn more than one worker
        spawn_count = source.count("spawn ")
        assert spawn_count >= 2, f"Expected multiple spawns, got {spawn_count}"

    def test_produces_correct_output(self) -> None:
        output = _compile_and_run("test_vs/02_concurrency.mn")
        # 4 workers, each processes 2500 messages: val*2+1 for val in their range
        # Total = sum(i*2+1 for i in range(10000)) = 100000000
        assert output == "100000000"


# ---------------------------------------------------------------------------
# Task 3: Benchmark table has "Features Tested" column
# ---------------------------------------------------------------------------


class TestBenchmarkTable:
    """Verify README benchmark tables have Features Tested column."""

    def test_performance_table_has_features_column(self) -> None:
        from pathlib import Path

        readme = Path("README.md").read_text(encoding="utf-8")
        # Find the performance table header
        assert "| Benchmark | Features Tested |" in readme

    def test_expressiveness_table_has_features_column(self) -> None:
        from pathlib import Path

        readme = Path("README.md").read_text(encoding="utf-8")
        lines = readme.splitlines()
        # Find expressiveness table
        for line in lines:
            if "Expressiveness" in line:
                break
        # The table after "Expressiveness" should have Features Tested
        in_section = False
        for line in lines:
            if "Expressiveness" in line:
                in_section = True
            if in_section and line.startswith("| Benchmark"):
                assert "Features Tested" in line
                break


# ---------------------------------------------------------------------------
# Task 4: Benchmark notes exist
# ---------------------------------------------------------------------------


class TestBenchmarkNotes:
    """Verify README has honest benchmark notes."""

    def test_notes_section_exists(self) -> None:
        from pathlib import Path

        readme = Path("README.md").read_text(encoding="utf-8")
        assert "**Benchmark notes:**" in readme

    def test_notes_cover_all_benchmarks(self) -> None:
        from pathlib import Path

        readme = Path("README.md").read_text(encoding="utf-8")
        assert "**Fibonacci:**" in readme
        assert "**Message Passing:**" in readme
        assert "**Stream Pipeline:**" in readme
        assert "**Matrix Multiply:**" in readme

    def test_matrix_note_is_honest(self) -> None:
        from pathlib import Path

        readme = Path("README.md").read_text(encoding="utf-8")
        # Should mention constant data limitation
        assert "constant" in readme.lower() or "1.0 * 2.0" in readme


# ---------------------------------------------------------------------------
# Task 5: Agent pipeline benchmark exists and works
# ---------------------------------------------------------------------------


class TestAgentPipelineBenchmark:
    """Verify 05_agent_pipeline.mn exists and works."""

    def test_mn_file_exists(self) -> None:
        from pathlib import Path

        assert Path("test_vs/05_agent_pipeline.mn").exists()

    def test_py_file_exists(self) -> None:
        from pathlib import Path

        assert Path("test_vs/05_agent_pipeline.py").exists()

    def test_go_file_exists(self) -> None:
        from pathlib import Path

        assert Path("test_vs/05_agent_pipeline.go").exists()

    def test_rs_file_exists(self) -> None:
        from pathlib import Path

        assert Path("test_vs/05_agent_pipeline.rs").exists()

    def test_uses_multiple_agents(self) -> None:
        from pathlib import Path

        source = Path("test_vs/05_agent_pipeline.mn").read_text(encoding="utf-8")
        agent_count = source.count("agent ")
        assert agent_count >= 3, "Pipeline should have at least 3 stages"

    def test_uses_string_operations(self) -> None:
        from pathlib import Path

        source = Path("test_vs/05_agent_pipeline.mn").read_text(encoding="utf-8")
        assert "String" in source

    def test_compiles_and_runs(self) -> None:
        output = _compile_and_run("test_vs/05_agent_pipeline.mn")
        # Should produce a numeric result
        assert output.strip().isdigit() or output.strip().lstrip("-").isdigit()

    def test_produces_correct_output(self) -> None:
        output = _compile_and_run("test_vs/05_agent_pipeline.mn")
        assert output == "78670"

    def test_in_benchmark_runner(self) -> None:
        from test_vs.run_benchmarks import BENCHMARKS

        bench_ids = [b[0] for b in BENCHMARKS]
        assert "05_agent_pipeline" in bench_ids
