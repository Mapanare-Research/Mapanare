"""Tests for Phase 1.3 — CI/CD Pipeline configuration."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parent.parent
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict[Any, Any]:
    """Load and return the parsed CI workflow."""
    raw: dict[Any, Any] = yaml.safe_load(CI_WORKFLOW.read_text())
    # YAML parses `on:` as boolean True — normalize to string key "on"
    return {("on" if k is True else k): v for k, v in raw.items()}


# ── Task 1-4: GitHub Actions runs pytest, mypy, ruff, black on every PR ──


class TestCIWorkflowExists:
    def test_workflow_file_exists(self) -> None:
        assert CI_WORKFLOW.exists(), ".github/workflows/ci.yml must exist"

    def test_workflow_is_valid_yaml(self) -> None:
        data = _load_ci()
        assert isinstance(data, dict)


class TestCITriggers:
    def test_triggers_on_push_to_main(self) -> None:
        data = _load_ci()
        assert "main" in data["on"]["push"]["branches"]

    def test_triggers_on_pr_to_main(self) -> None:
        data = _load_ci()
        assert "main" in data["on"]["pull_request"]["branches"]


class TestCISteps:
    """Verify all four required checks are present as steps."""

    def _step_names(self) -> list[str]:
        data = _load_ci()
        job = data["jobs"]["ci"]
        return [step.get("name", "") for step in job["steps"]]

    def _step_runs(self) -> list[str]:
        data = _load_ci()
        job = data["jobs"]["ci"]
        return [step.get("run", "") for step in job["steps"]]

    def test_has_pytest_step(self) -> None:
        runs = self._step_runs()
        assert any("pytest" in r for r in runs), "CI must run pytest"

    def test_has_mypy_step(self) -> None:
        runs = self._step_runs()
        assert any("mypy" in r for r in runs), "CI must run mypy"

    def test_has_ruff_step(self) -> None:
        runs = self._step_runs()
        assert any("ruff" in r for r in runs), "CI must run ruff"

    def test_has_black_step(self) -> None:
        runs = self._step_runs()
        assert any("black" in r for r in runs), "CI must run black"

    def test_has_checkout(self) -> None:
        names = self._step_names()
        assert any("checkout" in n.lower() for n in names), "CI must checkout code"

    def test_has_python_setup(self) -> None:
        names = self._step_names()
        assert any("python" in n.lower() for n in names), "CI must set up Python"


class TestCIConfig:
    def test_uses_python_311(self) -> None:
        data = _load_ci()
        job = data["jobs"]["ci"]
        # Accept either hardcoded 3.11 in a step or a matrix that includes 3.11
        matrix_versions = []
        strategy = job.get("strategy", {})
        if "matrix" in strategy:
            matrix_versions = strategy["matrix"].get("python-version", [])
        if matrix_versions:
            assert "3.11" in matrix_versions, "CI matrix must include Python 3.11"
            return
        steps = job["steps"]
        for step in steps:
            if "with" in step and "python-version" in step.get("with", {}):
                assert step["with"]["python-version"] == "3.11"
                return
        raise AssertionError("CI must specify python-version 3.11")

    def test_installs_dev_deps(self) -> None:
        data = _load_ci()
        runs = [step.get("run", "") for step in data["jobs"]["ci"]["steps"]]
        assert any("[dev]" in r for r in runs), "CI must install dev dependencies"


# ── Task 5: Status badges in README ──


class TestREADMEBadges:
    def test_ci_badge_in_readme(self) -> None:
        readme = (ROOT / "README.md").read_text()
        assert "actions/workflows/ci.yml/badge.svg" in readme, "README must have CI badge"


# ── Verify tools actually run locally ──


class TestToolsRunLocally:
    def test_black_check_passes(self) -> None:
        result = subprocess.run(
            ["black", "--check", "."],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 0, f"black --check failed:\n{result.stderr}"

    def test_ruff_check_passes(self) -> None:
        result = subprocess.run(
            ["ruff", "check", "."],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 0, f"ruff check failed:\n{result.stderr}"

    def test_mypy_passes(self) -> None:
        result = subprocess.run(
            ["mypy", "mapa/", "runtime/"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 0, f"mypy failed:\n{result.stdout}"
