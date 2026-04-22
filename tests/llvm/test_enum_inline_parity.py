"""v5.0.6 Cb.6-test — regression gate for typed-pointer inline-slot rejection.

Cb.6 (closed ~v4.134) tightened the self-hosted `type_fits_inline_slot`
to reject typed-pointer-legacy forms like `"i64*"`. The Python emitter
accepts `i64*` as a legacy form (see `test_enum_inline.TestTypeFitsInlineSlot`),
but the self-hosted emitter uses opaque `ptr` exclusively and must reject
any trailing `*`.

Rattler flagged at v4.144.0 and v4.154.0 that no test asserts this
invariant. A future refactor could silently re-enable typed-pointer
acceptance and propagate through self-compilation before anyone noticed.

This module is the structural regression gate: reads the self-hosted
source, asserts the rejection clause exists in the expected function.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SELF_EMIT = ROOT / "mapanare" / "self" / "emit_llvm.mn"


def test_self_hosted_rejects_typed_pointer_slot() -> None:
    """Assert the self-hosted `type_fits_inline_slot` rejects `*`-suffixed types.

    Structural gate: scans `mapanare/self/emit_llvm.mn` for the
    `type_fits_inline_slot` function body and verifies it contains
    a `resolved.ends_with("*")` → `return false` clause.

    The alternative (end-to-end compile of an enum that would try to
    inline a typed pointer) is brittle — no public .mn surface produces
    `i64*` in the first place because the lowerer emits only opaque
    pointers. Structural coverage is the right granularity here.
    """
    assert SELF_EMIT.exists(), f"self-hosted emitter missing: {SELF_EMIT}"
    src = SELF_EMIT.read_text(encoding="utf-8")

    # Locate the function body.
    marker = "fn type_fits_inline_slot("
    idx = src.find(marker)
    assert idx >= 0, f"type_fits_inline_slot function not found in {SELF_EMIT}"

    # Pull a reasonable window (function bodies in this file are < 30 lines).
    body = src[idx : idx + 1200]

    # The rejection clause must be present and reachable (not commented out).
    lines = [ln.strip() for ln in body.splitlines()]
    has_endswith_star = any('ends_with("*")' in ln and not ln.startswith("//") for ln in lines)
    has_return_false = any(ln == "return false" and not ln.startswith("//") for ln in lines)
    assert has_endswith_star, (
        "type_fits_inline_slot no longer guards against typed-pointer "
        '(Cb.6 regression). Expected a `resolved.ends_with("*")` check.'
    )
    assert has_return_false, (
        "type_fits_inline_slot has the ends_with check but no "
        "`return false` — the guard no longer rejects typed pointers."
    )


def test_self_hosted_and_python_emitters_agree_on_opaque_ptr() -> None:
    """`ptr` (opaque) is accepted by both emitters as a valid inline slot.

    Sanity test: the rejection is specifically for typed-pointer legacy
    forms (`i64*`), not for opaque `ptr`. This test guards against an
    over-broad fix that would break the common case.
    """
    from mapanare.emit_llvm_text import LLVMTextEmitter

    assert LLVMTextEmitter._type_fits_inline_slot("ptr") is True
    assert LLVMTextEmitter._type_fits_inline_slot("i64*") is True  # Python: legacy

    # Self-hosted: scan source for the opaque-ptr acceptance clause.
    src = SELF_EMIT.read_text(encoding="utf-8")
    marker = "fn type_fits_inline_slot("
    idx = src.find(marker)
    body = src[idx : idx + 1200]
    assert 'resolved == "ptr"' in body, (
        "self-hosted no longer explicitly accepts opaque `ptr` — over-broad "
        "rejection would break every boxed-enum payload"
    )
