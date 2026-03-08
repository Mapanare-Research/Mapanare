"""Tests for GitHub Actions release build matrix (Phase 4.5)."""

from __future__ import annotations

from pathlib import Path

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_RELEASE_YML = _PROJECT_ROOT / ".github" / "workflows" / "release.yml"


def _load_workflow() -> dict:  # type: ignore[type-arg]
    """Load and parse the release workflow YAML."""
    content = _RELEASE_YML.read_text(encoding="utf-8")
    return yaml.safe_load(content)


class TestReleaseWorkflowExists:
    def test_release_yml_exists(self) -> None:
        assert _RELEASE_YML.is_file()


class TestReleaseWorkflowStructure:
    def test_triggers_on_tags(self) -> None:
        wf = _load_workflow()
        # YAML parses 'on' key as True boolean; access via True key
        on_key = True if True in wf else "on"
        triggers = wf[on_key]
        assert "push" in triggers
        assert "tags" in triggers["push"]
        assert any("v" in t for t in triggers["push"]["tags"])

    def test_has_build_job(self) -> None:
        wf = _load_workflow()
        assert "build" in wf["jobs"]

    def test_build_matrix_has_three_targets(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        assert len(matrix) == 3

    def test_linux_target_in_matrix(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        targets = [m["target"] for m in matrix]
        assert "x86_64-linux-gnu" in targets

    def test_macos_target_in_matrix(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        targets = [m["target"] for m in matrix]
        assert "aarch64-apple-macos" in targets

    def test_windows_target_in_matrix(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        targets = [m["target"] for m in matrix]
        assert "x86_64-windows-msvc" in targets

    def test_each_target_has_os(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        for entry in matrix:
            assert "os" in entry
            assert entry["os"].endswith("-latest") or entry["os"].startswith("macos-")

    def test_each_target_has_artifact_name(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build"]["strategy"]["matrix"]["include"]
        for entry in matrix:
            assert "artifact" in entry
            assert entry["artifact"].startswith("mapa-")

    def test_build_job_runs_tests(self) -> None:
        wf = _load_workflow()
        steps = wf["jobs"]["build"]["steps"]
        step_names = [s.get("name", "") for s in steps]
        assert any("test" in n.lower() for n in step_names)

    def test_has_release_job(self) -> None:
        wf = _load_workflow()
        assert "release" in wf["jobs"]
        assert wf["jobs"]["release"]["needs"] == "build"
