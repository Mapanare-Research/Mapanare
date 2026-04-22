"""Tests for publish + install round-trip using local stubs."""

import hashlib
import io
import json
import os
import tarfile
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from stdlib.pkg import (
    MapanareManifest,
    PackageError,
    _build_tarball,
    _compute_integrity,
    _resolve_best_local,
    _satisfies_constraint,
    _version_tuple,
    install_all,
    install_package,
    load_lockfile,
    load_manifest,
    save_manifest,
)


class TestVersionTuple:
    """Test semver parsing into comparable tuples."""

    def test_basic(self) -> None:
        assert _version_tuple("1.2.3") == (1, 2, 3)

    def test_two_parts(self) -> None:
        assert _version_tuple("1.2") == (1, 2)

    def test_prerelease_stripped(self) -> None:
        assert _version_tuple("1.2.3-beta.1") == (1, 2, 3)

    def test_build_stripped(self) -> None:
        assert _version_tuple("1.2.3+build42") == (1, 2, 3)

    def test_zero(self) -> None:
        assert _version_tuple("0.0.0") == (0, 0, 0)


class TestSatisfiesConstraint:
    """Test semver constraint satisfaction."""

    def test_wildcard(self) -> None:
        assert _satisfies_constraint("1.0.0", "*") is True
        assert _satisfies_constraint("99.99.99", "*") is True

    def test_exact(self) -> None:
        assert _satisfies_constraint("1.2.3", "1.2.3") is True
        assert _satisfies_constraint("1.2.4", "1.2.3") is False

    def test_caret(self) -> None:
        # ^1.2.3 means >=1.2.3, <2.0.0
        assert _satisfies_constraint("1.2.3", "^1.2.3") is True
        assert _satisfies_constraint("1.9.9", "^1.2.3") is True
        assert _satisfies_constraint("2.0.0", "^1.2.3") is False
        assert _satisfies_constraint("1.2.2", "^1.2.3") is False

    def test_caret_zero_major(self) -> None:
        # ^0.2.3 means >=0.2.3, <0.3.0
        assert _satisfies_constraint("0.2.3", "^0.2.3") is True
        assert _satisfies_constraint("0.2.9", "^0.2.3") is True
        assert _satisfies_constraint("0.3.0", "^0.2.3") is False

    def test_tilde(self) -> None:
        # ~1.2.3 means >=1.2.3, <1.3.0
        assert _satisfies_constraint("1.2.3", "~1.2.3") is True
        assert _satisfies_constraint("1.2.9", "~1.2.3") is True
        assert _satisfies_constraint("1.3.0", "~1.2.3") is False

    def test_gte(self) -> None:
        assert _satisfies_constraint("1.2.3", ">=1.2.3") is True
        assert _satisfies_constraint("2.0.0", ">=1.2.3") is True
        assert _satisfies_constraint("1.2.2", ">=1.2.3") is False

    def test_lt(self) -> None:
        assert _satisfies_constraint("1.2.2", "<1.2.3") is True
        assert _satisfies_constraint("1.2.3", "<1.2.3") is False

    def test_compound(self) -> None:
        assert _satisfies_constraint("1.5.0", ">=1.0.0,<2.0.0") is True
        assert _satisfies_constraint("2.0.0", ">=1.0.0,<2.0.0") is False
        assert _satisfies_constraint("0.9.0", ">=1.0.0,<2.0.0") is False


class TestResolveBestLocal:
    """Test version resolution from available list."""

    def test_wildcard_returns_highest(self) -> None:
        available = ["1.0.0", "1.1.0", "2.0.0", "1.5.0"]
        assert _resolve_best_local(available, "*") == "2.0.0"

    def test_caret_returns_highest_matching(self) -> None:
        available = ["1.0.0", "1.1.0", "1.9.0", "2.0.0"]
        assert _resolve_best_local(available, "^1.0.0") == "1.9.0"

    def test_no_match_returns_none(self) -> None:
        available = ["1.0.0", "1.1.0"]
        assert _resolve_best_local(available, "^2.0.0") is None

    def test_empty_returns_none(self) -> None:
        assert _resolve_best_local([], "*") is None


class TestBuildTarball:
    """Test tarball creation for publishing."""

    def test_creates_valid_tarball(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            save_manifest(MapanareManifest(name="test-pkg", version="0.1.0"), d)
            with open(os.path.join(d, "main.mn"), "w") as f:
                f.write('fn main() {\n    print("hello")\n}\n')

            tarball_data = _build_tarball(d)
            assert len(tarball_data) > 0

            # Verify it's a valid gzipped tarball
            with tarfile.open(fileobj=io.BytesIO(tarball_data), mode="r:gz") as tar:
                names = tar.getnames()
                assert "mapanare.toml" in names
                assert "main.mn" in names

    def test_excludes_mn_modules(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            save_manifest(MapanareManifest(name="test-pkg", version="0.1.0"), d)
            os.makedirs(os.path.join(d, "mn_modules", "dep-1.0.0"), exist_ok=True)
            with open(os.path.join(d, "mn_modules", "dep-1.0.0", "lib.mn"), "w") as f:
                f.write("fn dep() {}\n")
            with open(os.path.join(d, "main.mn"), "w") as f:
                f.write('fn main() {\n    print("hello")\n}\n')

            tarball_data = _build_tarball(d)
            with tarfile.open(fileobj=io.BytesIO(tarball_data), mode="r:gz") as tar:
                names = tar.getnames()
                assert not any("mn_modules" in n for n in names)


class TestComputeIntegrity:
    """Test SHA-256 integrity hash computation."""

    def test_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "main.mn"), "w") as f:
                f.write("fn main() {}\n")
            h1 = _compute_integrity(d)
            h2 = _compute_integrity(d)
            assert h1 == h2
            assert h1.startswith("sha256:")

    def test_changes_with_content(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "main.mn"), "w") as f:
                f.write("fn main() {}\n")
            h1 = _compute_integrity(d)
            with open(os.path.join(d, "main.mn"), "w") as f:
                f.write("fn main() { print(42) }\n")
            h2 = _compute_integrity(d)
            assert h1 != h2


class TestInstallAll:
    """Test install-all-from-manifest mode."""

    def test_no_deps_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            save_manifest(MapanareManifest(name="bare", version="0.1.0"), d)
            results = install_all(d)
            assert results == []

    @patch("stdlib.pkg._install_from_registry")
    @patch("stdlib.pkg._install_from_git")
    def test_installs_each_dep(
        self, mock_git: MagicMock, mock_registry: MagicMock
    ) -> None:
        from stdlib.pkg import Dependency, LockedDependency

        # Registry returns None (not found), falls back to git
        mock_registry.return_value = None
        mock_git.return_value = LockedDependency(
            name="json", version="1.0.0", git="x", commit="c", integrity="i"
        )

        with tempfile.TemporaryDirectory() as d:
            manifest = MapanareManifest(
                name="app",
                version="0.1.0",
                dependencies={"json": Dependency(name="json", version="^1.0.0")},
            )
            save_manifest(manifest, d)
            results = install_all(d)
            assert len(results) == 1
            assert results[0].name == "json"


class TestRegistryURL:
    """Test that API endpoints use the v5.2.0 paths."""

    def test_default_registry_url(self) -> None:
        from stdlib.pkg import REGISTRY_URL
        assert "mapanare.dev" in REGISTRY_URL

    def test_install_dir_is_mn_modules(self) -> None:
        from stdlib.pkg import MAPANARE_PACKAGES_DIR
        assert MAPANARE_PACKAGES_DIR == "mn_modules"
