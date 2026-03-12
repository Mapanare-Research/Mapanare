"""Tests for the Mapanare package manager stub (Phase 3.5)."""

from __future__ import annotations

import os
import tempfile

import pytest

from stdlib.pkg import (
    Dependency,
    LockedDependency,
    LockFile,
    LockFileError,
    ManifestError,
    MapanareManifest,
    init_project,
    load_lockfile,
    load_manifest,
    parse_manifest,
    publish_package,
    save_lockfile,
    save_manifest,
)

# -----------------------------------------------------------------------
# mapanare.toml manifest format tests
# -----------------------------------------------------------------------


class TestDependency:
    def test_from_string(self) -> None:
        dep = Dependency.from_dict("foo", ">=1.0.0")
        assert dep.name == "foo"
        assert dep.version == ">=1.0.0"
        assert dep.git is None
        assert dep.branch is None

    def test_from_dict_with_git(self) -> None:
        dep = Dependency.from_dict(
            "bar",
            {"version": "0.2.0", "git": "https://github.com/x/bar.git", "branch": "dev"},
        )
        assert dep.name == "bar"
        assert dep.version == "0.2.0"
        assert dep.git == "https://github.com/x/bar.git"
        assert dep.branch == "dev"

    def test_from_dict_minimal(self) -> None:
        dep = Dependency.from_dict("baz", {"git": "https://github.com/x/baz.git"})
        assert dep.version == "*"
        assert dep.git == "https://github.com/x/baz.git"

    def test_from_dict_invalid(self) -> None:
        with pytest.raises(ManifestError, match="invalid dependency format"):
            Dependency.from_dict("bad", 42)

    def test_to_dict_simple(self) -> None:
        dep = Dependency(name="foo", version="1.0.0")
        assert dep.to_dict() == {"version": "1.0.0"}

    def test_to_dict_with_git(self) -> None:
        dep = Dependency(name="foo", version="1.0.0", git="https://x.git", branch="main")
        d = dep.to_dict()
        assert d["git"] == "https://x.git"
        assert d["branch"] == "main"


class TestParseManifest:
    def test_minimal_manifest(self) -> None:
        toml = '[package]\nname = "myapp"\nversion = "0.1.0"\n'
        m = parse_manifest(toml)
        assert m.name == "myapp"
        assert m.version == "0.1.0"
        assert m.description == ""
        assert m.dependencies == {}

    def test_full_manifest(self) -> None:
        toml = """\
[package]
name = "myapp"
version = "1.2.3"
description = "An awesome app"
authors = ["Alice", "Bob"]
license = "MIT"
mapanare_version = ">=0.2.0"
entry = "src/main.mn"

[dependencies]
http_client = ">=1.0.0"
utils = { version = "0.5.0", git = "https://github.com/Mapanare-Research/utils.git" }

[dev-dependencies]
test_helper = "0.1.0"
"""
        m = parse_manifest(toml)
        assert m.name == "myapp"
        assert m.version == "1.2.3"
        assert m.description == "An awesome app"
        assert m.authors == ["Alice", "Bob"]
        assert m.license == "MIT"
        assert m.mapanare_version == ">=0.2.0"
        assert m.entry == "src/main.mn"
        assert "http_client" in m.dependencies
        assert m.dependencies["http_client"].version == ">=1.0.0"
        assert "utils" in m.dependencies
        assert m.dependencies["utils"].git == "https://github.com/Mapanare-Research/utils.git"
        assert "test_helper" in m.dev_dependencies

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ManifestError, match="name"):
            parse_manifest('[package]\nversion = "1.0.0"\n')

    def test_missing_version_raises(self) -> None:
        with pytest.raises(ManifestError, match="version"):
            parse_manifest('[package]\nname = "x"\n')

    def test_comments_ignored(self) -> None:
        toml = '# comment\n[package]\nname = "x"\n# another\nversion = "1.0.0"\n'
        m = parse_manifest(toml)
        assert m.name == "x"

    def test_empty_dependencies(self) -> None:
        toml = '[package]\nname = "x"\nversion = "1.0.0"\n\n[dependencies]\n'
        m = parse_manifest(toml)
        assert m.dependencies == {}

    def test_single_author_string(self) -> None:
        toml = '[package]\nname = "x"\nversion = "1.0.0"\nauthors = "Solo"\n'
        m = parse_manifest(toml)
        assert m.authors == ["Solo"]


class TestManifestRoundTrip:
    def test_to_toml_and_back(self) -> None:
        original = MapanareManifest(
            name="roundtrip",
            version="2.0.0",
            description="Test roundtrip",
            authors=["Dev"],
            license="Apache-2.0",
            dependencies={
                "dep1": Dependency(name="dep1", version=">=1.0.0"),
            },
        )
        toml_str = original.to_toml()
        parsed = parse_manifest(toml_str)
        assert parsed.name == original.name
        assert parsed.version == original.version
        assert parsed.description == original.description
        assert "dep1" in parsed.dependencies
        assert parsed.dependencies["dep1"].version == ">=1.0.0"

    def test_to_toml_with_git_dep(self) -> None:
        m = MapanareManifest(
            name="test",
            version="0.1.0",
            dependencies={
                "pkg": Dependency(
                    name="pkg",
                    version="1.0.0",
                    git="https://github.com/Mapanare-Research/pkg.git",
                    branch="dev",
                ),
            },
        )
        toml_str = m.to_toml()
        assert "git" in toml_str
        assert "branch" in toml_str


class TestManifestFileIO:
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            m = MapanareManifest(name="fileio", version="0.1.0")
            save_manifest(m, tmpdir)
            loaded = load_manifest(tmpdir)
            assert loaded.name == "fileio"
            assert loaded.version == "0.1.0"

    def test_load_missing_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ManifestError, match="not found"):
                load_manifest(tmpdir)


# -----------------------------------------------------------------------
# mapanare.lock lock file format tests
# -----------------------------------------------------------------------


class TestLockedDependency:
    def test_to_dict(self) -> None:
        ld = LockedDependency(
            name="foo",
            version="1.0.0",
            git="https://github.com/Mapanare-Research/foo.git",
            commit="abc123",
            integrity="sha256:deadbeef",
        )
        d = ld.to_dict()
        assert d["name"] == "foo"
        assert d["commit"] == "abc123"
        assert d["integrity"] == "sha256:deadbeef"

    def test_from_dict(self) -> None:
        d = {
            "name": "bar",
            "version": "2.0.0",
            "git": "https://github.com/Mapanare-Research/bar.git",
            "commit": "def456",
            "integrity": "sha256:cafe",
        }
        ld = LockedDependency.from_dict(d)
        assert ld.name == "bar"
        assert ld.commit == "def456"


class TestLockFile:
    def test_empty_lockfile(self) -> None:
        lf = LockFile()
        assert lf.lockfile_version == 1
        assert lf.packages == []

    def test_to_json_and_back(self) -> None:
        lf = LockFile(
            packages=[
                LockedDependency(
                    name="dep1",
                    version="1.0.0",
                    git="https://github.com/Mapanare-Research/dep1.git",
                    commit="aaa",
                    integrity="sha256:bbb",
                ),
                LockedDependency(
                    name="dep2",
                    version="2.0.0",
                    git="https://github.com/Mapanare-Research/dep2.git",
                    commit="ccc",
                    integrity="sha256:ddd",
                ),
            ]
        )
        json_str = lf.to_json()
        parsed = LockFile.from_json(json_str)
        assert len(parsed.packages) == 2
        assert parsed.packages[0].name == "dep1"
        assert parsed.packages[1].commit == "ccc"

    def test_find_existing(self) -> None:
        lf = LockFile(
            packages=[
                LockedDependency("a", "1.0", "url", "abc", "sha256:x"),
            ]
        )
        assert lf.find("a") is not None
        assert lf.find("a").commit == "abc"  # type: ignore[union-attr]

    def test_find_missing(self) -> None:
        lf = LockFile()
        assert lf.find("nope") is None

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(LockFileError, match="invalid"):
            LockFile.from_json("not json{{{")

    def test_lockfile_version(self) -> None:
        lf = LockFile.from_json('{"lockfile_version": 2, "packages": []}')
        assert lf.lockfile_version == 2


class TestLockFileIO:
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lf = LockFile(
                packages=[
                    LockedDependency("pkg", "1.0", "url", "abc", "sha256:hash"),
                ]
            )
            save_lockfile(lf, tmpdir)
            loaded = load_lockfile(tmpdir)
            assert len(loaded.packages) == 1
            assert loaded.packages[0].name == "pkg"

    def test_load_missing_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lf = load_lockfile(tmpdir)
            assert lf.packages == []


# -----------------------------------------------------------------------
# mapa publish stub tests
# -----------------------------------------------------------------------


class TestPublishPackage:
    def test_publish_requires_token(self) -> None:
        """Publish raises PackageError when no token is available."""
        from unittest.mock import patch

        from stdlib.pkg import PackageError

        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="testpkg")
            with patch("stdlib.pkg._read_token", return_value=None):
                with pytest.raises(PackageError, match="No API token"):
                    publish_package(tmpdir)

    def test_publish_builds_tarball(self) -> None:
        """Publish builds a valid tarball from the project."""
        import io
        import tarfile

        from stdlib.pkg import _build_tarball

        with tempfile.TemporaryDirectory() as tmpdir:
            init_project(tmpdir, name="tarpkg")
            data = _build_tarball(tmpdir)
            assert len(data) > 0
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
                names = tar.getnames()
                assert "mapanare.toml" in names


# -----------------------------------------------------------------------
# Project init tests
# -----------------------------------------------------------------------


class TestInitProject:
    def test_creates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, "myproject")
            m = init_project(project_dir, name="myproject")
            assert m.name == "myproject"
            assert m.version == "0.1.0"
            assert os.path.isfile(os.path.join(project_dir, "mapanare.toml"))

    def test_creates_main_ax(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, "newproj")
            init_project(project_dir, name="newproj")
            main_path = os.path.join(project_dir, "main.mn")
            assert os.path.isfile(main_path)
            with open(main_path) as f:
                assert "Hello, Mapanare!" in f.read()

    def test_does_not_overwrite_main_ax(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, "existing")
            os.makedirs(project_dir)
            main_path = os.path.join(project_dir, "main.mn")
            with open(main_path, "w") as f:
                f.write("custom content")
            init_project(project_dir, name="existing")
            with open(main_path) as f:
                assert f.read() == "custom content"

    def test_default_name_from_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = os.path.join(tmpdir, "auto_named")
            m = init_project(project_dir)
            assert m.name == "auto_named"
