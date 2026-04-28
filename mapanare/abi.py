"""E5 / ABI.1: per-target return-convention classifier.

Implements System V AMD64 §3.2.3, Win64 x64, and AArch64 AAPCS64
return-value rules.  Used by ``emit_llvm_text.py`` at function-header
and call-site emission to choose register-return vs sret.

The classifier takes an LLVM IR type string and the target triple and
returns whether the aggregate should be returned in registers or via
an ``sret`` pointer parameter.

v4.149.0 — closes ABI.1 panel carry-forward (opened v4.125.0).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ReturnABI:
    """How a function's aggregate return should be emitted in LLVM IR."""

    kind: Literal["register", "sret"]


def classify_return(ir_ty: str, total_size: int, triple: str) -> ReturnABI:
    """Classify whether *ir_ty* should return in registers or via sret.

    Parameters
    ----------
    ir_ty : str
        LLVM IR type string, e.g. ``"{i64, i64, i64}"``.
    total_size : int
        ABI byte size of *ir_ty* (caller computes via ``_tsz``).
    triple : str
        Target triple, e.g. ``"x86_64-pc-linux-gnu"``.

    Returns
    -------
    ReturnABI
        ``kind="register"`` if the aggregate fits in return registers,
        ``kind="sret"`` if the caller must allocate and pass a pointer.
    """
    # Scalars always return in a register.
    if not (ir_ty.startswith("{") and ir_ty.endswith("}")):
        return _REG
    if total_size == 0:
        return _REG

    # v5.8.6 We.1: i686-w64-windows-gnu / i686-pc-windows-gnu — Win32
    # cdecl. Must be checked before the generic "windows" branch
    # because that branch matches any triple containing "windows" and
    # would route i686 to Win64 rules. Empirical probe (see
    # docs/roadmap/v5/v5.8.6/SESSION_REPORT.md §Phase 0): structs > 8 B
    # use sret hidden first arg; ≤ 8 B return in EAX:EDX register pair.
    if triple.startswith("i686") or triple.startswith("i386"):
        return _classify_i686_cdecl(total_size)
    if "windows" in triple:
        return _classify_win64(total_size)
    if triple.startswith("aarch64"):
        return _classify_aapcs64(total_size)
    # Default: System V AMD64
    return _classify_sysv(total_size)


# ── internal constants ────────────────────────────────────────────────
_REG = ReturnABI("register")
_SRET = ReturnABI("sret")


# ── per-target classifiers ────────────────────────────────────────────
def _classify_sysv(total_size: int) -> ReturnABI:
    """System V AMD64 ABI §3.2.3 return classification.

    Aggregates ≤ 16 bytes whose eightbyte chunks are all INTEGER class
    return in ``rax`` + ``rdx``.  Larger aggregates use sret.

    Mapanare aggregates contain only integer-class fields (i64, i32,
    i8, i1, ptr), so every eightbyte classifies as INTEGER and the
    16-byte size threshold is the only check needed.
    """
    if total_size <= 16:
        return _REG
    return _SRET


def _classify_win64(total_size: int) -> ReturnABI:
    """Win64 x64 calling convention return classification.

    Only aggregates of exactly 1, 2, 4, or 8 bytes can be returned in
    ``rax``.  All other sizes use sret (hidden first parameter in rcx).
    """
    if total_size in (1, 2, 4, 8):
        return _REG
    return _SRET


def _classify_aapcs64(total_size: int) -> ReturnABI:
    """AArch64 AAPCS64 return classification.

    Aggregates ≤ 16 bytes return in ``x0`` / ``x1``.  Larger aggregates
    use the indirect result register ``x8`` (equivalent to sret).
    """
    if total_size <= 16:
        return _REG
    return _SRET


def _classify_i686_cdecl(total_size: int) -> ReturnABI:
    """i686-w64-mingw32 / i386 System V cdecl return classification.

    Aggregates ≤ 8 bytes return in EAX (and EDX for the high half of an
    8-byte struct).  Anything larger uses a hidden-first-arg sret
    pointer, caller-allocated and pushed before the rest of the args.
    Empirical probe with i686-w64-mingw32-gcc 13 confirms structs of
    sizes 12 / 16 / 24 / 64 / 80 all take the sret path; struct of
    size 8 returns via eax:edx register pair (see v5.8.6 SESSION_REPORT).
    """
    if total_size <= 8:
        return _REG
    return _SRET
