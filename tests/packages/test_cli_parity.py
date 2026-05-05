"""Tests for the v5.44.0 Ps.3 CLI resolver-parity contract.

Locks: every compile / check / emit / test entry point must expose the
``--stdlib-path`` and ``--extra-path`` flags, and must construct a
``ModuleResolver`` via ``_build_resolver_from_args`` so package roots
are discovered identically.

Falsifiability: removing ``_add_resolver_args`` from any subparser
fails ``test_every_compile_subcmd_has_resolver_args``; replacing a
``_build_resolver_from_args`` call with a bare ``ModuleResolver()``
fails the source-grep test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from mapanare import cli

COMPILE_SUBCMDS = (
    "check",
    "run",
    "build",
    "emit-llvm",
    "emit-c",
    "emit-mir",
    "emit-wasm",
    "build-multi",
    "test",
)


@pytest.mark.parametrize("subcmd", COMPILE_SUBCMDS)
def test_every_compile_subcmd_has_resolver_args(subcmd: str) -> None:
    """Every compile/test entry point exposes --stdlib-path and --extra-path."""
    import argparse as _ap
    parser = cli.build_parser()
    # Find the _SubParsersAction explicitly (other actions can also have
    # a `choices` attr but choices is None for them).
    subparsers_action = next(
        action
        for action in parser._actions
        if isinstance(action, _ap._SubParsersAction)
    )
    sp = subparsers_action.choices[subcmd]
    # Extract long-form option strings from the parser's actions.
    options: set[str] = set()
    for action in sp._actions:
        for opt_str in action.option_strings:
            options.add(opt_str)
    assert "--stdlib-path" in options, (
        f"subcommand '{subcmd}' is missing --stdlib-path; wire via "
        f"_add_resolver_args(parser) in build_parser()"
    )
    assert "--extra-path" in options, (
        f"subcommand '{subcmd}' is missing --extra-path; wire via "
        f"_add_resolver_args(parser) in build_parser()"
    )


def test_no_bare_module_resolver_construction_in_compile_paths() -> None:
    """Source-grep gate: every ``ModuleResolver(`` construction outside
    ``_build_resolver_from_args`` / ``build_resolver_for_source`` must be
    a documented fallback.

    The accepted backward-compat fallback shape is
    ``resolver = ModuleResolver()`` immediately preceded by an ``if
    resolver is None`` guard or wrapped in a ``try/except
    PackageDiscoveryError``. Anything else is a regression.
    """
    repo_root = Path(__file__).resolve().parents[2]
    files_to_audit = [
        repo_root / "mapanare" / "cli.py",
        repo_root / "mapanare" / "multi_module.py",
        repo_root / "mapanare" / "test_runner.py",
        repo_root / "mapanare" / "lsp" / "analysis.py",
    ]
    # Match actual assignment/return statements only — not docstring
    # backtick mentions or type-annotation comments.
    code_pattern = re.compile(r"^\s*(?:resolver\s*[:=]|return\s+)?ModuleResolver\s*\(\s*\)\s*$")
    for path in files_to_audit:
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            # Skip comments and clearly docstring lines (line starts with
            # quotes or is inside a backtick fence).
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "``" in line:
                # Documentation reference, not a code statement.
                continue
            if not code_pattern.match(line):
                continue
            # Require the prior 4 lines to contain "if resolver is None"
            # or "except PackageDiscoveryError".
            preceding = lines[max(0, lineno - 5) : lineno - 1]
            preceding_text = "\n".join(preceding)
            assert (
                "resolver is None" in preceding_text
                or "PackageDiscoveryError" in preceding_text
            ), (
                f"{path}:{lineno}: bare ModuleResolver() construction without "
                f"a documented fallback guard. Use _build_resolver_from_args "
                f"(CLI) or build_resolver_for_source (LSP/test runner)."
            )


# ---------------------------------------------------------------------------
# Functional parity test
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "subcmd",
    ["check", "build", "emit-llvm", "emit-mir"],
)
def test_resolver_construction_parity_in_project(
    tmp_path: Path, subcmd: str
) -> None:
    """The same project compiles via each entry point with identical
    package resolution.

    Strategy: build a project with one installed package; for each
    subcommand, run argparse + _build_resolver_from_args; assert the
    resulting resolver sees the same single package root.
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
    (pkg_dir / "main.mn").write_text(
        "pub fn sum_all(xs: List<Int>) -> Int { return 0 }\n", encoding="utf-8"
    )
    src = proj / "main.mn"
    src.write_text(
        'import mn_collections\n\nfn main() {\n    print("hi")\n}\n',
        encoding="utf-8",
    )

    parser = cli.build_parser()
    if subcmd == "build-multi":
        argv = [subcmd, str(src)]
    else:
        argv = [subcmd, str(src)]
    args = parser.parse_args(argv)

    resolver = cli._build_resolver_from_args(args, source_path=str(src))
    roots = resolver.package_roots()
    assert len(roots) == 1
    assert roots[0].package_name == "mn_collections"
    assert roots[0].version == "0.1.0"
    assert roots[0].source == "mn_modules"


def test_collect_explicit_paths_orders_correctly(tmp_path: Path) -> None:
    """`--stdlib-path` first, then `--extra-path`s, then MAPANARE_PATH."""
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "build",
            "/tmp/foo.mn",
            "--stdlib-path",
            "/explicit/stdlib",
            "--extra-path",
            "/extra/a",
            "--extra-path",
            "/extra/b",
        ]
    )
    paths = cli._collect_explicit_paths(args)
    assert paths == ["/explicit/stdlib", "/extra/a", "/extra/b"]


def test_mapanare_path_env_appended(tmp_path: Path, monkeypatch) -> None:
    """MAPANARE_PATH env splits on os.pathsep and appends after CLI flags."""
    import os

    monkeypatch.setenv("MAPANARE_PATH", os.pathsep.join(["/env/a", "/env/b"]))
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/foo.mn"])
    paths = cli._collect_explicit_paths(args)
    assert paths == ["/env/a", "/env/b"]


def test_mapanare_path_dedupes_against_cli(monkeypatch) -> None:
    """Don't double-list a path that's both in --extra-path and MAPANARE_PATH."""
    monkeypatch.setenv("MAPANARE_PATH", "/shared")
    parser = cli.build_parser()
    args = parser.parse_args(["build", "/tmp/foo.mn", "--extra-path", "/shared"])
    paths = cli._collect_explicit_paths(args)
    assert paths == ["/shared"]
