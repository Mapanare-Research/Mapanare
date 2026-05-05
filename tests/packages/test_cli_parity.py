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
        # v5.44.1 Ps.11.B — extend parity contract beyond mapanare/
        repo_root / "scripts" / "build_stage1.py",
        repo_root / "scripts" / "ir_doctor.py",
        repo_root / "scripts" / "measure_divergence.py",
        repo_root / "benchmarks" / "bench_stdlib.py",
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


# v5.44.1 Ps.11.B — scripts and benchmarks compile-helper invariant.
#
# The bare ``ModuleResolver()`` regex above doesn't fire for these
# files because the v5.44.0 → v5.44.1 audit found they fall through
# to the helper's internal fallback rather than constructing a bare
# resolver themselves. This complementary gate locks the actual
# parity invariant for the script-shape: every call to
# ``compile_multi_module_mir`` or ``_compile_to_llvm_ir`` from these
# files MUST pass an explicit ``resolver=`` kwarg. Falsifiability:
# delete the kwarg and this test fails with the file:line.
SCRIPT_FILES_TO_AUDIT = (
    "scripts/build_stage1.py",
    "scripts/ir_doctor.py",
    "scripts/measure_divergence.py",
    "benchmarks/bench_stdlib.py",
)
COMPILE_HELPER_CALL_RE = re.compile(
    r"\b(compile_multi_module_mir|_compile_to_llvm_ir)\s*\("
)


@pytest.mark.parametrize("rel_path", SCRIPT_FILES_TO_AUDIT)
def test_scripts_pass_resolver_to_compile_helper(rel_path: str) -> None:
    """Scripts/benchmarks must pass an explicit resolver= kwarg to
    every ``compile_multi_module_mir`` / ``_compile_to_llvm_ir`` call.

    Without this gate, falling through to the helper's bare-resolver
    fallback silently bypasses package-aware import resolution — a
    project's ``mn_modules/`` would be invisible to ``ir_doctor.py``
    diff while ``mnc emit-llvm`` resolves it correctly. v5.44.0 Ps.3
    closed parity inside ``mapanare/``; v5.44.1 Ps.11.B closes it
    here.
    """
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / rel_path
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    # Strip comment-only lines and inline ``# ...`` tails so a docstring
    # / commentary mention of the helper name doesn't trigger the gate.
    # Also blank out lines that look like prose (start with whitespace
    # then ``# ``). We preserve line offsets so reported linenos are
    # accurate against the source.
    cleaned_lines: list[str] = []
    for line in raw_lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            cleaned_lines.append("")
            continue
        # Drop inline ``# tail`` comments (best-effort; doesn't handle
        # `#` inside string literals — fine for these scripts where
        # helper calls aren't followed by string-with-# tails).
        if "#" in line:
            line = line.split("#", 1)[0]
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)
    # Find every helper call. Each call's argument list may span
    # multiple lines, so collect the call site's (lineno, slice of
    # text from `(` to its matching `)`).
    for match in COMPILE_HELPER_CALL_RE.finditer(text):
        helper = match.group(1)
        start = match.end()  # position right after the `(`
        # Walk forward, tracking paren depth, to find the matching `)`.
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        call_args = text[start:i - 1]
        if "resolver=" not in call_args:
            # Compute lineno of the call open-paren.
            lineno = text.count("\n", 0, match.start()) + 1
            raise AssertionError(
                f"{path}:{lineno}: {helper}(...) missing required "
                f"`resolver=` kwarg. Construct via "
                f"`build_resolver_for_source(...)` with a tolerant "
                f"PackageDiscoveryError fallback so the script honors "
                f"`mn_modules/` for package-aware projects."
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
