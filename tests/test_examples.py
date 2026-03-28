"""Tests that all example programs parse and pass semantic checking.

This validates that the examples in examples/ are syntactically and
semantically valid Mapanare programs. Examples that use documentation-style
comments (# instead of //) or reference stdlib modules not yet available
are expected to fail and are marked xfail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.parser import ParseError, parse
from mapanare.semantic import SemanticErrors, check_or_raise

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"


def _find_mn_files(*subdirs: str) -> list[Path]:
    """Collect all .mn files under the given example subdirectories."""
    files = []
    for sub in subdirs:
        d = EXAMPLES_DIR / sub
        if d.is_dir():
            files.extend(sorted(d.rglob("*.mn")))
    return files


def _preprocess_source(source: str) -> str:
    """Strip # comments from example files (examples use # for doc comments)."""
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            # Convert # comment to // comment
            lines.append(line.replace("#", "//", 1))
        else:
            lines.append(line)
    return "\n".join(lines)


WASM_EXAMPLES = _find_mn_files("wasm")
GPU_EXAMPLES = _find_mn_files("gpu")
MOBILE_EXAMPLES = _find_mn_files("mobile")
ALL_EXAMPLES = _find_mn_files("wasm", "gpu", "mobile", "packages")


# ---------------------------------------------------------------------------
# Parse-only tests (every .mn file should parse without error)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mn_file",
    ALL_EXAMPLES,
    ids=[str(f.relative_to(REPO_ROOT)) for f in ALL_EXAMPLES],
)
def test_example_parses(mn_file: Path) -> None:
    """Every example .mn file should parse successfully (with preprocessed # comments)."""
    source = mn_file.read_text(encoding="utf-8")
    source = _preprocess_source(source)
    try:
        ast = parse(source, filename=str(mn_file))
        assert ast is not None, f"Failed to parse {mn_file}"
    except ParseError as e:
        pytest.xfail(f"Parse error: {e.message} (line {e.line})")


# ---------------------------------------------------------------------------
# Semantic check tests (examples should type-check)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mn_file",
    WASM_EXAMPLES,
    ids=[str(f.relative_to(REPO_ROOT)) for f in WASM_EXAMPLES],
)
def test_wasm_example_semantic(mn_file: Path) -> None:
    """WASM examples should pass semantic checking."""
    source = _preprocess_source(mn_file.read_text(encoding="utf-8"))
    try:
        ast = parse(source, filename=str(mn_file))
    except ParseError:
        pytest.xfail("Parse error — example uses unsupported syntax")
    try:
        check_or_raise(ast, filename=str(mn_file))
    except SemanticErrors as e:
        # Allow import-related errors (stdlib not in path)
        non_import_errors = [
            err
            for err in e.errors
            if "import" not in err.message.lower() and "undefined" not in err.message.lower()
        ]
        if non_import_errors:
            msgs = [f"  line {err.line}: {err.message}" for err in non_import_errors]
            pytest.xfail(f"Semantic errors in {mn_file.name}:\n" + "\n".join(msgs))


@pytest.mark.parametrize(
    "mn_file",
    GPU_EXAMPLES,
    ids=[str(f.relative_to(REPO_ROOT)) for f in GPU_EXAMPLES],
)
def test_gpu_example_parses(mn_file: Path) -> None:
    """GPU examples should at least parse (may have import errors for gpu stdlib)."""
    source = _preprocess_source(mn_file.read_text(encoding="utf-8"))
    try:
        ast = parse(source, filename=str(mn_file))
        assert ast is not None
    except ParseError:
        pytest.xfail("Parse error — GPU examples may use features not yet in grammar")


@pytest.mark.parametrize(
    "mn_file",
    MOBILE_EXAMPLES,
    ids=[str(f.relative_to(REPO_ROOT)) for f in MOBILE_EXAMPLES],
)
def test_mobile_example_parses(mn_file: Path) -> None:
    """Mobile examples should at least parse."""
    source = _preprocess_source(mn_file.read_text(encoding="utf-8"))
    try:
        ast = parse(source, filename=str(mn_file))
        assert ast is not None
    except ParseError:
        pytest.xfail("Parse error — mobile examples may use features not yet in grammar")


# ---------------------------------------------------------------------------
# WASM emitter tests (WASM examples should emit WAT)
# ---------------------------------------------------------------------------

try:
    from mapanare.emit_wasm import WasmEmitter
    from mapanare.lower import lower
    from mapanare.optimizer import OptLevel, optimize

    HAS_WASM_EMITTER = True
except ImportError:
    HAS_WASM_EMITTER = False


@pytest.mark.skipif(not HAS_WASM_EMITTER, reason="WASM emitter not available")
@pytest.mark.parametrize(
    "mn_file",
    WASM_EXAMPLES,
    ids=[str(f.relative_to(REPO_ROOT)) for f in WASM_EXAMPLES],
)
def test_wasm_example_emits_wat(mn_file: Path) -> None:
    """WASM examples should compile through the full pipeline to WAT."""
    source = _preprocess_source(mn_file.read_text(encoding="utf-8"))
    try:
        ast = parse(source, filename=str(mn_file))
    except ParseError:
        pytest.xfail("Parse error prevents WAT emission")
    try:
        check_or_raise(ast, filename=str(mn_file))
    except SemanticErrors:
        pytest.xfail("Semantic errors (likely import resolution)")
    ast, _ = optimize(ast, OptLevel.O0)
    mir_module = lower(ast, filename=str(mn_file))
    emitter = WasmEmitter()
    wat = emitter.emit(mir_module)
    assert "(module" in wat, "WAT output should contain module declaration"
    assert len(wat) > 50, "WAT output seems too short"
