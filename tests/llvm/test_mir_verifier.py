"""MIR Verifier integration tests.

Runs the MIR verifier on all golden test files (tests/golden/*.mn) to
ensure the lowering pipeline produces structurally valid MIR.
"""

from __future__ import annotations

import glob
import os

import pytest

from mapanare.lower import lower
from mapanare.mir import MIRVerifier, verify
from mapanare.parser import parse
from mapanare.semantic import check

_GOLDEN_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    "golden",
)

_GOLDEN_FILES = sorted(glob.glob(os.path.join(_GOLDEN_DIR, "*.mn")))

# Sanity-check: we expect at least 15 golden tests
assert len(_GOLDEN_FILES) >= 15, f"Expected >=15 golden files, found {len(_GOLDEN_FILES)}"


def _lower_file(filepath: str):
    """Parse, check, and lower a .mn file to MIR."""
    with open(filepath, encoding="utf-8") as f:
        source = f.read()
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    ast = parse(source, filename=filepath)
    check(ast, filename=filepath)
    return lower(ast, module_name=module_name)


@pytest.mark.parametrize(
    "golden_file",
    _GOLDEN_FILES,
    ids=[os.path.basename(f) for f in _GOLDEN_FILES],
)
class TestMIRVerifierGolden:
    """Run the MIR verifier on every golden test file."""

    def test_verifier_passes(self, golden_file: str) -> None:
        """Lowered MIR from golden file passes structural verification."""
        mir_module = _lower_file(golden_file)
        errors = verify(mir_module)
        assert (
            errors == []
        ), f"MIR verification errors in {os.path.basename(golden_file)}:\n" + "\n".join(
            str(e) for e in errors
        )

    def test_verifier_class_passes(self, golden_file: str) -> None:
        """MIRVerifier class (relaxed SSA, default mode) produces no errors."""
        mir_module = _lower_file(golden_file)
        verifier = MIRVerifier(strict_ssa=False)
        errors = verifier.verify_module(mir_module)
        assert (
            errors == []
        ), f"MIRVerifier errors in {os.path.basename(golden_file)}:\n" + "\n".join(
            str(e) for e in errors
        )


class TestStrictSSA:
    """Test that strict_ssa mode detects redefinitions."""

    def test_strict_rejects_mutable_redef(self) -> None:
        """Mutable variable reassignment triggers strict SSA error."""
        source = """\
fn main() {
    let mut x: Int = 0
    x = 1
    print(str(x))
}
"""
        ast = parse(source)
        check(ast)
        mir_module = lower(ast, module_name="test")
        verifier = MIRVerifier(strict_ssa=True)
        errors = verifier.verify_module(mir_module)
        # Mutable reassignment should produce at least one SSA violation
        ssa_errors = [e for e in errors if "SSA violation" in e.message]
        assert len(ssa_errors) >= 1, (
            "Expected strict SSA to flag mutable redefinition, " f"but got errors: {errors}"
        )

    def test_relaxed_allows_mutable_redef(self) -> None:
        """Mutable variable reassignment passes relaxed (default) verification."""
        source = """\
fn main() {
    let mut x: Int = 0
    x = 1
    print(str(x))
}
"""
        ast = parse(source)
        check(ast)
        mir_module = lower(ast, module_name="test")
        verifier = MIRVerifier(strict_ssa=False)
        errors = verifier.verify_module(mir_module)
        # Filter to only SSA-related errors (structural errors are OK to flag)
        ssa_errors = [e for e in errors if "SSA violation" in e.message]
        assert ssa_errors == [], f"Relaxed SSA should not flag redefinitions: {ssa_errors}"
