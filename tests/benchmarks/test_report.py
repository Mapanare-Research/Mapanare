"""Tests for benchmark report generation (Phase 4.5 — publish at mapanare.dev/benchmarks)."""

from __future__ import annotations

from benchmarks.generate_report import generate_html


class TestReportGeneration:
    def test_generates_html(self) -> None:
        html = generate_html()
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_contains_benchmark_sections(self) -> None:
        html = generate_html()
        assert "Multi-Agent Message Passing" in html
        assert "Stream Pipeline" in html
        assert "Mapanare vs Python asyncio vs Rust" in html

    def test_contains_table_structure(self) -> None:
        html = generate_html()
        assert "<table>" in html
        assert "<th>" in html

    def test_shows_no_data_message_without_results(self) -> None:
        html = generate_html()
        assert "No data" in html or "<td>" in html

    def test_contains_mapanare_version(self) -> None:
        from pathlib import Path

        version = (Path(__file__).resolve().parents[2] / "VERSION").read_text().strip()
        html = generate_html()
        assert version in html

    def test_contains_run_instructions(self) -> None:
        html = generate_html()
        assert "run_all.py" in html
