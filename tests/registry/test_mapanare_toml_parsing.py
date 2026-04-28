"""Tests for mapanare.toml manifest parsing and serialization."""

import pytest

from stdlib.pkg import (
    Dependency,
    ManifestError,
    MapanareManifest,
    parse_manifest,
)


class TestParseManifest:
    """Test manifest parsing from TOML strings."""

    def test_minimal_manifest(self) -> None:
        toml = '[package]\nname = "hello"\nversion = "0.1.0"\n'
        m = parse_manifest(toml)
        assert m.name == "hello"
        assert m.version == "0.1.0"
        assert m.description == ""
        assert m.entry == "main.mn"

    def test_full_manifest(self) -> None:
        toml = """
[package]
name = "dato"
version = "1.2.3"
description = "DataFrame library"
license = "MIT"
repository = "https://github.com/Mapanare-Research/dato"
entry = "src/lib.mn"
authors = ["Juan Denis"]
mapanare_version = ">=5.2.0"

[dependencies]
json = "^1.0.0"
http-server = "~2.1.0"
"""
        m = parse_manifest(toml)
        assert m.name == "dato"
        assert m.version == "1.2.3"
        assert m.description == "DataFrame library"
        assert m.license == "MIT"
        assert m.repository == "https://github.com/Mapanare-Research/dato"
        assert m.entry == "src/lib.mn"
        assert m.authors == ["Juan Denis"]
        assert m.mapanare_version == ">=5.2.0"
        assert "json" in m.dependencies
        assert m.dependencies["json"].version == "^1.0.0"
        assert "http-server" in m.dependencies
        assert m.dependencies["http-server"].version == "~2.1.0"

    def test_inline_table_dependency(self) -> None:
        toml = """
[package]
name = "myapp"
version = "0.1.0"

[dependencies]
custom-lib = { version = ">=1.0.0", git = "https://github.com/user/lib.git", branch = "dev" }
"""
        m = parse_manifest(toml)
        dep = m.dependencies["custom-lib"]
        assert dep.version == ">=1.0.0"
        assert dep.git == "https://github.com/user/lib.git"
        assert dep.branch == "dev"

    def test_missing_name_raises(self) -> None:
        toml = '[package]\nversion = "1.0.0"\n'
        with pytest.raises(ManifestError, match="name"):
            parse_manifest(toml)

    def test_missing_version_raises(self) -> None:
        toml = '[package]\nname = "oops"\n'
        with pytest.raises(ManifestError, match="version"):
            parse_manifest(toml)

    def test_empty_dependencies(self) -> None:
        toml = '[package]\nname = "bare"\nversion = "0.0.1"\n\n[dependencies]\n'
        m = parse_manifest(toml)
        assert m.dependencies == {}

    def test_dev_dependencies(self) -> None:
        toml = """
[package]
name = "myapp"
version = "1.0.0"

[dev-dependencies]
test-utils = "^0.1.0"
"""
        m = parse_manifest(toml)
        assert "test-utils" in m.dev_dependencies
        assert m.dev_dependencies["test-utils"].version == "^0.1.0"

    def test_line_comments_ignored(self) -> None:
        toml = """
# This is a comment
[package]
name = "hello"
version = "1.0.0"
# Another comment
"""
        m = parse_manifest(toml)
        assert m.name == "hello"
        assert m.version == "1.0.0"


class TestManifestSerialization:
    """Test manifest to_toml() round-trip."""

    def test_round_trip_minimal(self) -> None:
        m = MapanareManifest(name="test", version="0.1.0")
        toml = m.to_toml()
        m2 = parse_manifest(toml)
        assert m2.name == "test"
        assert m2.version == "0.1.0"

    def test_round_trip_with_repository(self) -> None:
        m = MapanareManifest(
            name="dato",
            version="1.0.0",
            description="DataFrame library",
            license="MIT",
            repository="https://github.com/Mapanare-Research/dato",
        )
        toml = m.to_toml()
        assert 'repository = "https://github.com/Mapanare-Research/dato"' in toml
        m2 = parse_manifest(toml)
        assert m2.repository == "https://github.com/Mapanare-Research/dato"

    def test_round_trip_with_dependencies(self) -> None:
        m = MapanareManifest(
            name="app",
            version="0.1.0",
            dependencies={
                "json": Dependency(name="json", version="^1.0.0"),
                "http": Dependency(name="http", version="~2.0.0"),
            },
        )
        toml = m.to_toml()
        m2 = parse_manifest(toml)
        assert "json" in m2.dependencies
        assert m2.dependencies["json"].version == "^1.0.0"
        assert "http" in m2.dependencies
        assert m2.dependencies["http"].version == "~2.0.0"

    def test_round_trip_with_git_dependency(self) -> None:
        m = MapanareManifest(
            name="app",
            version="0.1.0",
            dependencies={
                "custom": Dependency(
                    name="custom",
                    version="*",
                    git="https://github.com/user/custom.git",
                    branch="dev",
                ),
            },
        )
        toml = m.to_toml()
        m2 = parse_manifest(toml)
        dep = m2.dependencies["custom"]
        assert dep.git == "https://github.com/user/custom.git"
        assert dep.branch == "dev"


class TestDependencyFromDict:
    """Test Dependency.from_dict()."""

    def test_string_value(self) -> None:
        dep = Dependency.from_dict("foo", "^1.0.0")
        assert dep.name == "foo"
        assert dep.version == "^1.0.0"
        assert dep.git is None

    def test_dict_value(self) -> None:
        dep = Dependency.from_dict("bar", {"version": ">=2.0.0", "git": "https://x.git"})
        assert dep.name == "bar"
        assert dep.version == ">=2.0.0"
        assert dep.git == "https://x.git"

    def test_dict_default_version(self) -> None:
        dep = Dependency.from_dict("baz", {"git": "https://x.git"})
        assert dep.version == "*"

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ManifestError):
            Dependency.from_dict("bad", 42)
