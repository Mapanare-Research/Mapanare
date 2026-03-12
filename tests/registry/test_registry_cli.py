"""Tests for package registry CLI commands (publish, search, install registry integration)."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from stdlib.pkg import (
    LockedDependency,
    PackageError,
    _build_tarball,
    _resolve_best_local,
    _satisfies_constraint,
    _version_tuple,
    init_project,
    publish_package,
    search_packages,
)

# ---------------------------------------------------------------------------
# Version resolution tests
# ---------------------------------------------------------------------------


class TestVersionTuple:
    def test_simple(self) -> None:
        assert _version_tuple("1.2.3") == (1, 2, 3)

    def test_with_prerelease(self) -> None:
        assert _version_tuple("1.0.0-alpha") == (1, 0, 0)

    def test_with_build(self) -> None:
        assert _version_tuple("1.0.0+build") == (1, 0, 0)


class TestSatisfiesConstraint:
    def test_wildcard(self) -> None:
        assert _satisfies_constraint("1.0.0", "*")
        assert _satisfies_constraint("99.99.99", "*")

    def test_exact(self) -> None:
        assert _satisfies_constraint("1.0.0", "1.0.0")
        assert not _satisfies_constraint("1.0.1", "1.0.0")

    def test_gte(self) -> None:
        assert _satisfies_constraint("1.0.0", ">=1.0.0")
        assert _satisfies_constraint("2.0.0", ">=1.0.0")
        assert not _satisfies_constraint("0.9.0", ">=1.0.0")

    def test_gt(self) -> None:
        assert _satisfies_constraint("1.0.1", ">1.0.0")
        assert not _satisfies_constraint("1.0.0", ">1.0.0")

    def test_lte(self) -> None:
        assert _satisfies_constraint("1.0.0", "<=1.0.0")
        assert not _satisfies_constraint("1.0.1", "<=1.0.0")

    def test_lt(self) -> None:
        assert _satisfies_constraint("0.9.0", "<1.0.0")
        assert not _satisfies_constraint("1.0.0", "<1.0.0")

    def test_caret(self) -> None:
        assert _satisfies_constraint("1.2.3", "^1.2.0")
        assert _satisfies_constraint("1.9.9", "^1.2.0")
        assert not _satisfies_constraint("2.0.0", "^1.2.0")

    def test_caret_zero_major(self) -> None:
        assert _satisfies_constraint("0.2.3", "^0.2.0")
        assert not _satisfies_constraint("0.3.0", "^0.2.0")

    def test_tilde(self) -> None:
        assert _satisfies_constraint("1.2.5", "~1.2.3")
        assert not _satisfies_constraint("1.3.0", "~1.2.3")

    def test_equals(self) -> None:
        assert _satisfies_constraint("1.0.0", "=1.0.0")
        assert not _satisfies_constraint("1.0.1", "=1.0.0")

    def test_combined(self) -> None:
        assert _satisfies_constraint("1.5.0", ">=1.0.0,<2.0.0")
        assert not _satisfies_constraint("2.0.0", ">=1.0.0,<2.0.0")
        assert not _satisfies_constraint("0.9.0", ">=1.0.0,<2.0.0")


class TestResolveBestLocal:
    def test_wildcard_returns_highest(self) -> None:
        versions = ["1.0.0", "2.0.0", "1.5.0"]
        assert _resolve_best_local(versions, "*") == "2.0.0"

    def test_constraint_returns_best_match(self) -> None:
        versions = ["1.0.0", "1.1.0", "2.0.0"]
        assert _resolve_best_local(versions, "^1.0.0") == "1.1.0"

    def test_no_match_returns_none(self) -> None:
        versions = ["1.0.0"]
        assert _resolve_best_local(versions, ">=2.0.0") is None

    def test_empty_returns_none(self) -> None:
        assert _resolve_best_local([], "*") is None


# ---------------------------------------------------------------------------
# Tarball building tests
# ---------------------------------------------------------------------------


class TestBuildTarball:
    def test_builds_tarball_with_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testpkg")
            tarball = _build_tarball(tmpdir)
            assert len(tarball) > 0

            # Verify it's a valid tarball
            import io
            import tarfile

            with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tar:
                names = tar.getnames()
                assert "mapanare.toml" in names
                assert "main.mn" in names

    def test_excludes_hidden_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testpkg")
            # Create a hidden directory with an .mn file
            hidden_dir = os.path.join(tmpdir, ".git")
            os.makedirs(hidden_dir)
            with open(os.path.join(hidden_dir, "test.mn"), "w") as f:
                f.write("fn test() {}")

            tarball = _build_tarball(tmpdir)

            import io
            import tarfile

            with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tar:
                names = tar.getnames()
                assert not any(".git" in n for n in names)


# ---------------------------------------------------------------------------
# Publish tests (mocked HTTP)
# ---------------------------------------------------------------------------


class TestPublishPackage:
    def test_publish_no_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testpkg")
            with patch.dict(os.environ, {}, clear=True):
                with patch("stdlib.pkg._read_token", return_value=None):
                    with pytest.raises(PackageError, match="No API token"):
                        publish_package(tmpdir)

    def test_publish_success_mock(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testpkg")

            # Mock urlopen to return success
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(
                {"name": "testpkg", "version": "0.1.0", "checksum": "sha256:abc123"}
            ).encode()
            mock_response.__enter__ = lambda s: s
            mock_response.__exit__ = MagicMock(return_value=False)

            with patch("urllib.request.urlopen", return_value=mock_response):
                result = publish_package(tmpdir, token="mn_testtoken")
                assert result["name"] == "testpkg"
                assert result["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# Search tests (mocked HTTP)
# ---------------------------------------------------------------------------


class TestSearchPackages:
    def test_search_success_mock(self) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "packages": [
                    {
                        "name": "http_client",
                        "description": "HTTP client for Mapanare",
                        "author": "Test",
                        "latest_version": "1.0.0",
                        "keywords": ["http", "network"],
                        "updated_at": 1234567890.0,
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 20,
            }
        ).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = search_packages(query="http")
            assert result["total"] == 1
            assert result["packages"][0]["name"] == "http_client"

    def test_search_empty_mock(self) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"packages": [], "total": 0, "page": 1, "per_page": 20}
        ).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = search_packages(query="nonexistent")
            assert result["total"] == 0


# ---------------------------------------------------------------------------
# Token management tests
# ---------------------------------------------------------------------------


class TestTokenManagement:
    def test_save_and_read_token(self) -> None:
        from stdlib.pkg import _read_token, _save_token

        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = os.path.join(tmpdir, "token")
            with patch("stdlib.pkg.TOKEN_FILE", token_file):
                _save_token("mn_test123")
                assert _read_token() == "mn_test123"

    def test_read_token_from_env(self) -> None:
        from stdlib.pkg import _read_token

        with patch("stdlib.pkg.TOKEN_FILE", "/nonexistent/token"):
            with patch.dict(os.environ, {"MAPANARE_TOKEN": "mn_envtoken"}):
                assert _read_token() == "mn_envtoken"

    def test_read_token_missing(self) -> None:
        from stdlib.pkg import _read_token

        with patch("stdlib.pkg.TOKEN_FILE", "/nonexistent/token"):
            with patch.dict(os.environ, {}, clear=True):
                # Remove MAPANARE_TOKEN if set
                os.environ.pop("MAPANARE_TOKEN", None)
                assert _read_token() is None


# ---------------------------------------------------------------------------
# Install with registry fallback tests
# ---------------------------------------------------------------------------


class TestInstallRegistryFallback:
    def test_explicit_git_skips_registry(self) -> None:
        """When --git is given, skip registry entirely."""
        from stdlib.pkg import install_package

        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testproject")

            with patch("stdlib.pkg._install_from_git") as mock_git:
                mock_git.return_value = LockedDependency(
                    name="pkg",
                    version="1.0.0",
                    git="https://test.git",
                    commit="abc",
                    integrity="sha256:x",
                )
                with patch("stdlib.pkg._install_from_registry") as mock_reg:
                    install_package("pkg", tmpdir, git_url="https://test.git")
                    mock_reg.assert_not_called()
                    mock_git.assert_called_once()

    def test_registry_first_then_git_fallback(self) -> None:
        """When registry returns None, fall back to git."""
        from stdlib.pkg import install_package

        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testproject")

            with patch("stdlib.pkg._install_from_registry", return_value=None):
                with patch("stdlib.pkg._install_from_git") as mock_git:
                    mock_git.return_value = LockedDependency(
                        name="pkg",
                        version="*",
                        git="https://test.git",
                        commit="abc",
                        integrity="sha256:x",
                    )
                    install_package("pkg", tmpdir)
                    mock_git.assert_called_once()
