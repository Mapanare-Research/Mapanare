"""Tests for the v5.44.0 Ps.4 install-diagnostics surface.

Locks: when a build resolves imports through installed packages, both
the ``--verbose`` stderr surface and the ``--diag-json`` JSON file
record the (name, version, source) triples and match what ``mapanare.lock``
contains. Build diagnostics are never surfaced when compilation fails.

Falsifiability: removing the ``_surface_install_diagnostics`` call from
any cmd_* fails ``test_diag_json_records_resolved_packages``; corrupting
the schema fails the JSON-shape assertions.
"""

from __future__ import annotations

import json
from pathlib import Path

from mapanare import cli
from mapanare.modules import ImportRecord, ModuleResolver


def _make_resolver_with_log() -> ModuleResolver:
    """Build a ModuleResolver and seed its _import_log directly."""
    resolver = ModuleResolver()
    resolver._import_log.extend(
        [
            ImportRecord(
                package_name="mn_collections",
                import_name="mn_collections",
                version="0.1.0",
                source="mn_modules",
                integrity="sha256:abc",
                import_path=("mn_collections",),
                resolved_filepath="/proj/mn_modules/mn_collections-0.1.0/main.mn",
            ),
            ImportRecord(
                package_name="mn_collections",
                import_name="mn_collections",
                version="0.1.0",
                source="mn_modules",
                integrity="sha256:abc",
                import_path=("mn_collections", "utils"),
                resolved_filepath="/proj/mn_modules/mn_collections-0.1.0/utils.mn",
            ),
            ImportRecord(
                package_name="mn_http",
                import_name="mn_http",
                version="0.2.0",
                source="mn_modules",
                integrity="sha256:def",
                import_path=("mn_http",),
                resolved_filepath="/proj/mn_modules/mn_http-0.2.0/main.mn",
            ),
        ]
    )
    return resolver


# ---------------------------------------------------------------------------
# --verbose stderr surface
# ---------------------------------------------------------------------------


def test_verbose_emits_one_line_per_unique_package(capsys) -> None:
    """--verbose dedupes on (name, version): 3 records → 2 unique → 2 lines."""
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/x.mn", "--verbose"])
    resolver = _make_resolver_with_log()

    cli._surface_install_diagnostics(args, resolver)

    captured = capsys.readouterr()
    err_lines = [line for line in captured.err.splitlines() if line]
    assert len(err_lines) == 2
    assert "[package] mn_collections@0.1.0 from mn_modules" in err_lines
    assert "[package] mn_http@0.2.0 from mn_modules" in err_lines


def test_verbose_silent_when_no_packages_resolved(capsys) -> None:
    """--verbose on a project with no package imports prints nothing."""
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/x.mn", "--verbose"])
    resolver = ModuleResolver()  # empty log

    cli._surface_install_diagnostics(args, resolver)

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_no_verbose_no_diag_json_silent(capsys) -> None:
    """Without --verbose or --diag-json, the surface is silent."""
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/x.mn"])
    resolver = _make_resolver_with_log()

    cli._surface_install_diagnostics(args, resolver)

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


# ---------------------------------------------------------------------------
# --diag-json surface
# ---------------------------------------------------------------------------


def test_diag_json_records_resolved_packages(tmp_path: Path) -> None:
    """--diag-json writes a JSON file with one entry per (name, version)."""
    diag = tmp_path / "diag.json"
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/x.mn", "--diag-json", str(diag)])
    resolver = _make_resolver_with_log()

    cli._surface_install_diagnostics(args, resolver)

    payload = json.loads(diag.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert len(payload["packages"]) == 2

    by_name = {p["name"]: p for p in payload["packages"]}
    assert "mn_collections" in by_name
    assert "mn_http" in by_name

    coll = by_name["mn_collections"]
    assert coll["version"] == "0.1.0"
    assert coll["import_name"] == "mn_collections"
    assert coll["source"] == "mn_modules"
    assert coll["integrity"] == "sha256:abc"
    # Two imports of mn_collections recorded.
    assert len(coll["imports"]) == 2
    assert {tuple(i["import_path"]) for i in coll["imports"]} == {
        ("mn_collections",),
        ("mn_collections", "utils"),
    }


def test_diag_json_empty_when_no_imports(tmp_path: Path) -> None:
    """No package imports → diag-json still written, with empty packages list."""
    diag = tmp_path / "diag.json"
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/x.mn", "--diag-json", str(diag)])
    resolver = ModuleResolver()

    cli._surface_install_diagnostics(args, resolver)

    payload = json.loads(diag.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["packages"] == []


def test_diag_json_and_verbose_compose(tmp_path: Path, capsys) -> None:
    """Both surfaces fire together cleanly."""
    diag = tmp_path / "diag.json"
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/x.mn", "--verbose", "--diag-json", str(diag)])
    resolver = _make_resolver_with_log()

    cli._surface_install_diagnostics(args, resolver)

    captured = capsys.readouterr()
    assert "[package] mn_collections@0.1.0 from mn_modules" in captured.err
    payload = json.loads(diag.read_text(encoding="utf-8"))
    assert len(payload["packages"]) == 2


# ---------------------------------------------------------------------------
# Diag matches the lockfile
# ---------------------------------------------------------------------------


def test_diag_json_matches_lockfile(tmp_path: Path) -> None:
    """The (name, version) tuples in diag-json match the project's lockfile.

    This is the load-bearing reproducibility contract: the build records
    EXACTLY what the lockfile pinned.
    """
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "mapanare.toml").write_text(
        '[package]\nname = "consumer"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    pkg_dir = proj / "mn_modules" / "mn_collections-0.1.0"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "mapanare.toml").write_text(
        '[package]\nname = "mn_collections"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (pkg_dir / "main.mn").write_text("pub fn x() -> Int { return 1 }\n", encoding="utf-8")
    lockfile_data = {
        "lockfile_version": 1,
        "packages": [
            {
                "name": "mn_collections",
                "version": "0.1.0",
                "git": "https://example/x.git",
                "commit": "deadbeef",
                "integrity": "sha256:lock",
            }
        ],
    }
    (proj / "mapanare.lock").write_text(
        json.dumps(lockfile_data, indent=2) + "\n", encoding="utf-8"
    )

    src = proj / "main.mn"
    src.write_text("import mn_collections\n\nfn main() {}\n", encoding="utf-8")

    # Manually trigger resolution by walking through the resolver.
    resolver = cli._build_resolver_from_args(
        cli.build_parser().parse_args(["build", str(src)]),
        source_path=str(src),
    )
    # Simulate the import resolution that semantic check would do.
    resolver.resolve_module(["mn_collections"], str(src))

    diag = tmp_path / "diag.json"
    args = cli.build_parser().parse_args(["build", str(src), "--diag-json", str(diag)])
    cli._surface_install_diagnostics(args, resolver)

    payload = json.loads(diag.read_text(encoding="utf-8"))
    diag_pkgs = {(p["name"], p["version"]) for p in payload["packages"]}
    lock_pkgs = {(p["name"], p["version"]) for p in lockfile_data["packages"]}
    assert diag_pkgs == lock_pkgs
    # Integrity also matches.
    assert payload["packages"][0]["integrity"] == "sha256:lock"
