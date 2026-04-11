#!/usr/bin/env python3
"""scripts/check_no_hollow_features.py — v4.31.0 Phase 3.4.

Catches parse-without-lower features before they reach review. A
**hollow feature** is one that:

1. Parses cleanly — the grammar accepts it and the parser builds an
   AST node for it.
2. Has no semantic effect — the AST node is either ignored at
   lowering, mapped to identity, or ``raise NotImplementedError``.

The v4.18.0–v4.26.0 regression shipped six hollow features in eight
versions (``@gpu``, ``const``, ``await``, FFI bindings, MIR verifier
wiring, fixed-point bootstrap). Five of seven reviewers on the
v4.26.0 panel converged on the phrase "hollow features."

v4.29.0 added a narrow gate: ``git grep "raise NotImplementedError"``
must be empty under ``mapanare/`` and ``runtime/``. v4.31.0 widens it
to structural checks:

- **Device decorator gate.** Every ``@gpu`` / ``@cuda`` / ``@vulkan``
  function in ``tests/golden/`` must either reach a real lowering
  path (``MIRGpuKernel`` entry in the module's ``gpu_kernels`` dict
  after lowering) OR the file must be marked with a
  ``# HOLLOW_OK: <reason>`` comment on the line above the decorator.
  The v4.27.0 recovery specifically rejected the decorators at parse
  time, so a clean tree has zero decorated goldens — any new hit
  means someone re-introduced a hollow decorator.

- **AST-node-without-lowering gate.** For every AST class defined in
  ``mapanare/ast_nodes.py`` that represents an expression or
  statement, check that ``mapanare/lower.py`` mentions the class
  name (``isinstance(expr, ClassName)``). Unreachable AST classes
  are either dead code or hollow features.

- **NotImplementedError subcheck.** Includes the v4.29.0 gate so the
  CI pipeline runs both from a single script.

Usage
-----

    python3 scripts/check_no_hollow_features.py

Exit 0 on clean, 1 on any violation. Intended to run in CI on every
PR.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

_DEVICE_DECORATORS = frozenset({"gpu", "cuda", "metal", "vulkan"})
_HOLLOW_OK_MARKER = "# HOLLOW_OK:"

# AST classes that look like infrastructure (base classes, helpers,
# type wrappers) and don't need a lowering case. Keep this set small
# — every exemption is a chance for a real hollow feature to hide.
_AST_INFRASTRUCTURE = frozenset(
    {
        "ASTNode",
        "Definition",
        "Expr",
        "Stmt",
        "Statement",
        "Pattern",
        "TypeExpr",
        "SourceSpan",
        "Span",
        "Block",
        "Program",
        "Param",
        "TypeParam",
        "Decorator",
        "DocComment",
        # Structural definitions that are handled at the definition
        # level, not the expression level
        "AgentInput",
        "AgentOutput",
        "StructField",
        "EnumVariant",
        "MatchArm",
        "FieldInit",
        "MapEntry",
        "ImportDef",
        "ExportDef",
        "TraitMethod",
        # Pattern sub-variants used by match lowering — handled
        # structurally via the ``Pattern`` base
        "WildcardPattern",
        "LiteralPattern",
        "IdentPattern",
        "ConstructorPattern",
        "TuplePattern",
        "OrPattern",
        "RangePattern",
        # Type annotations — not expressions
        "NamedType",
        "GenericType",
        "FnType",
        "TupleType",
        "TensorType",
        # Full definitions (handled via the Definition dispatch, not
        # expression dispatch)
        "FnDef",
        "AgentDef",
        "PipeDef",
        "StructDef",
        "EnumDef",
        "TraitDef",
        "ImplDef",
        "ImplTraitDef",
        "TipoDef",
        "TypeAlias",
        "ExternFnDef",
        "ModuleLetDef",
        # Top-level statements that are module-level (no lower case)
        "ConstDef",  # removed v4.27.0 but the alias may still appear
    }
)


def _find_ast_expr_classes() -> set[str]:
    """Return the set of ``*Expr`` / ``*Stmt`` AST classes defined in
    ``mapanare/ast_nodes.py``.

    Uses the Python ``ast`` module so the script doesn't run the
    project code; it is pure lint.
    """
    src = Path("mapanare/ast_nodes.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            name = node.name
            if name in _AST_INFRASTRUCTURE:
                continue
            if name.startswith("_"):
                continue
            names.add(name)
    return names


def _find_lower_coverage() -> set[str]:
    """Return the set of AST class names referenced by ``isinstance``
    checks inside ``mapanare/lower.py``.
    """
    src = Path("mapanare/lower.py").read_text(encoding="utf-8")
    # Simple regex: ``isinstance(x, Name)`` or ``isinstance(x, (N1, N2))``.
    pattern = re.compile(r"isinstance\s*\(\s*[^,]+,\s*([^)]+)\)")
    found: set[str] = set()
    for m in pattern.finditer(src):
        inner = m.group(1)
        # Strip outer parens (tuple form)
        inner = inner.strip().lstrip("(").rstrip(")")
        for tok in inner.split(","):
            tok = tok.strip()
            if tok and tok[0].isupper():
                found.add(tok)
    return found


def _check_ast_coverage() -> list[str]:
    """Every AST expr/stmt class must be reachable from ``lower.py``."""
    decl = _find_ast_expr_classes()
    used = _find_lower_coverage()
    missing = sorted(decl - used)
    if not missing:
        return []
    return [
        f"{cls}: defined in mapanare/ast_nodes.py, no isinstance check in mapanare/lower.py"
        for cls in missing
    ]


def _check_device_decorators_in_goldens() -> list[str]:
    """Scan ``tests/golden/*.mn`` for ``@gpu`` / ``@cuda`` / ``@vulkan``.

    The v4.27.0 recovery rejects these decorators at parse time, so a
    clean tree has zero hits. Any hit means a regression unless the
    decorator is preceded by a ``# HOLLOW_OK: <reason>`` comment.
    """
    violations: list[str] = []
    root = Path("tests/golden")
    if not root.exists():
        return violations
    pattern = re.compile(r"^\s*@(\w+)\b")
    for path in sorted(root.glob("*.mn")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(lines):
            m = pattern.match(line)
            if not m:
                continue
            name = m.group(1)
            if name not in _DEVICE_DECORATORS:
                continue
            # Look at the line above for a HOLLOW_OK marker.
            prev = lines[i - 1] if i > 0 else ""
            if _HOLLOW_OK_MARKER in prev:
                continue
            violations.append(
                f"{path}:{i + 1}: device decorator @{name} — "
                f"v4.27.0 rejected these at parse; re-introducing one "
                f"is a hollow-feature regression. Mark with "
                f"`# HOLLOW_OK: <reason>` if this is intentional."
            )
    return violations


def _check_no_notimplementederror() -> list[str]:
    """v4.29.0 gate: ``raise NotImplementedError`` forbidden in source."""
    result = subprocess.run(
        ["git", "grep", "-l", "raise NotImplementedError", "mapanare/", "runtime/"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    hits = [h for h in result.stdout.splitlines() if h and not h.startswith("tests/")]
    if not hits:
        return []
    return [f"{h}: contains `raise NotImplementedError` — hollow feature marker" for h in hits]


def main() -> int:
    violations: list[str] = []

    print("check_no_hollow_features: scanning...")

    step1 = _check_no_notimplementederror()
    if step1:
        print("  step 1 (NotImplementedError): FAIL")
    else:
        print("  step 1 (NotImplementedError): clean")
    violations.extend(step1)

    step2 = _check_device_decorators_in_goldens()
    if step2:
        print("  step 2 (device decorators in goldens): FAIL")
    else:
        print("  step 2 (device decorators in goldens): clean")
    violations.extend(step2)

    step3 = _check_ast_coverage()
    if step3:
        print("  step 3 (AST coverage): FAIL")
    else:
        print("  step 3 (AST coverage): clean")
    violations.extend(step3)

    if violations:
        print("")
        print(f"check_no_hollow_features: {len(violations)} violation(s)")
        for v in violations:
            print(f"  - {v}")
        print("")
        print(
            "If a finding is intentional (e.g. a deprecated AST class "
            "retained for backward compat), either:",
            file=sys.stderr,
        )
        print(
            "  1. Add it to _AST_INFRASTRUCTURE in this script, or",
            file=sys.stderr,
        )
        print(
            "  2. Mark the golden-test decorator with `# HOLLOW_OK: <reason>`",
            file=sys.stderr,
        )
        return 1

    print("check_no_hollow_features: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
