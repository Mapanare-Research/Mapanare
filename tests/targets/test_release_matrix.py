"""Tests for GitHub Actions publish/release build matrix."""

from __future__ import annotations

from pathlib import Path

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PUBLISH_YML = _PROJECT_ROOT / ".github" / "workflows" / "publish.yml"


def _load_workflow() -> dict:  # type: ignore[type-arg]
    """Load and parse the publish workflow YAML."""
    content = _PUBLISH_YML.read_text(encoding="utf-8")
    return yaml.safe_load(content)


class TestPublishWorkflowExists:
    def test_publish_yml_exists(self) -> None:
        assert _PUBLISH_YML.is_file()


class TestPublishWorkflowStructure:
    def test_triggers_on_push_main(self) -> None:
        wf = _load_workflow()
        on_key = True if True in wf else "on"
        triggers = wf[on_key]
        assert "push" in triggers
        assert "branches" in triggers["push"]
        assert "main" in triggers["push"]["branches"]

    def test_has_build_cli_job(self) -> None:
        wf = _load_workflow()
        assert "build-cli" in wf["jobs"]

    def test_build_matrix_has_three_targets(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build-cli"]["strategy"]["matrix"]["include"]
        assert len(matrix) == 3

    def test_linux_target_in_matrix(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build-cli"]["strategy"]["matrix"]["include"]
        artifacts = [m["artifact"] for m in matrix]
        assert "mapanare-linux-x64" in artifacts

    def test_macos_target_in_matrix(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build-cli"]["strategy"]["matrix"]["include"]
        artifacts = [m["artifact"] for m in matrix]
        assert "mapanare-mac-arm64" in artifacts

    def test_windows_target_in_matrix(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build-cli"]["strategy"]["matrix"]["include"]
        artifacts = [m["artifact"] for m in matrix]
        assert "mapanare-win-x64" in artifacts

    def test_each_target_has_os(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build-cli"]["strategy"]["matrix"]["include"]
        for entry in matrix:
            assert "os" in entry
            assert entry["os"].endswith("-latest")

    def test_each_target_has_artifact_name(self) -> None:
        wf = _load_workflow()
        matrix = wf["jobs"]["build-cli"]["strategy"]["matrix"]["include"]
        for entry in matrix:
            assert "artifact" in entry
            assert entry["artifact"].startswith("mapanare-")

    def test_has_release_job(self) -> None:
        wf = _load_workflow()
        assert "release" in wf["jobs"]

    def test_has_pypi_job(self) -> None:
        wf = _load_workflow()
        assert "publish-pypi" in wf["jobs"]
