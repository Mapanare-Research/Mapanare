"""Tests for mapanare.lock read/write and determinism."""

import json
import os
import tempfile

import pytest

from stdlib.pkg import (
    LockFile,
    LockFileError,
    LockedDependency,
    load_lockfile,
    save_lockfile,
)


class TestLockFile:
    """Test LockFile serialization and parsing."""

    def test_empty_lockfile(self) -> None:
        lf = LockFile()
        assert lf.lockfile_version == 1
        assert lf.packages == []

    def test_round_trip(self) -> None:
        lf = LockFile(packages=[
            LockedDependency(
                name="dato",
                version="1.0.0",
                git="https://registry.mapanare.dev/v1/packages/dato/1.0.0/tar",
                commit="sha256:abc123",
                integrity="sha256:def456",
            ),
            LockedDependency(
                name="json",
                version="0.2.1",
                git="https://registry.mapanare.dev/v1/packages/json/0.2.1/tar",
                commit="sha256:789abc",
                integrity="sha256:012def",
            ),
        ])
        serialized = lf.to_json()
        parsed = LockFile.from_json(serialized)
        assert len(parsed.packages) == 2
        assert parsed.packages[0].name == "dato"
        assert parsed.packages[0].version == "1.0.0"
        assert parsed.packages[1].name == "json"

    def test_find_existing(self) -> None:
        lf = LockFile(packages=[
            LockedDependency(name="foo", version="1.0.0", git="", commit="", integrity=""),
        ])
        found = lf.find("foo")
        assert found is not None
        assert found.version == "1.0.0"

    def test_find_missing(self) -> None:
        lf = LockFile()
        assert lf.find("nonexistent") is None

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(LockFileError, match="invalid"):
            LockFile.from_json("not valid json{{{")

    def test_deterministic_output(self) -> None:
        """Lockfile JSON output must be deterministic (same input -> same output)."""
        lf = LockFile(packages=[
            LockedDependency(name="a", version="1.0.0", git="x", commit="c", integrity="i"),
            LockedDependency(name="b", version="2.0.0", git="y", commit="d", integrity="j"),
        ])
        out1 = lf.to_json()
        out2 = lf.to_json()
        assert out1 == out2

    def test_json_structure(self) -> None:
        lf = LockFile(packages=[
            LockedDependency(
                name="pkg",
                version="0.1.0",
                git="https://example.com",
                commit="sha256:aaa",
                integrity="sha256:bbb",
            ),
        ])
        data = json.loads(lf.to_json())
        assert data["lockfile_version"] == 1
        assert len(data["packages"]) == 1
        pkg = data["packages"][0]
        assert pkg["name"] == "pkg"
        assert pkg["version"] == "0.1.0"
        assert pkg["commit"] == "sha256:aaa"
        assert pkg["integrity"] == "sha256:bbb"


class TestLockFileDisk:
    """Test lockfile load/save on disk."""

    def test_load_missing_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            lf = load_lockfile(d)
            assert lf.packages == []

    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            lf = LockFile(packages=[
                LockedDependency(
                    name="test-pkg",
                    version="0.5.0",
                    git="https://example.com",
                    commit="sha256:abc",
                    integrity="sha256:def",
                ),
            ])
            save_lockfile(lf, d)

            path = os.path.join(d, "mapanare.lock")
            assert os.path.isfile(path)

            loaded = load_lockfile(d)
            assert len(loaded.packages) == 1
            assert loaded.packages[0].name == "test-pkg"
            assert loaded.packages[0].version == "0.5.0"

    def test_overwrite_existing(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            lf1 = LockFile(packages=[
                LockedDependency(name="a", version="1.0.0", git="", commit="", integrity=""),
            ])
            save_lockfile(lf1, d)

            lf2 = LockFile(packages=[
                LockedDependency(name="b", version="2.0.0", git="", commit="", integrity=""),
            ])
            save_lockfile(lf2, d)

            loaded = load_lockfile(d)
            assert len(loaded.packages) == 1
            assert loaded.packages[0].name == "b"
