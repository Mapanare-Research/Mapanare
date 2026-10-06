"""Text-based LLVM IR emitter.

Generates alloca/load/store IR. clang mem2reg optimizes to SSA.
"""

from __future__ import annotations

import os
import struct as pystruct
from typing import Any

from mapanare.abi import classify_return  # v4.149.0 E5
from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
    AwaitSuspend,
    BinOp,
    BinOpKind,
    BlockOn,
    Branch,
    Call,
    Cast,
    ClosureCall,
    ClosureCreate,
    Const,
    Copy,
    EnumInit,
    EnumPayload,
    EnumTag,
    EnvLoad,
    ExternCall,
    FieldGet,
    FieldSet,
    IndexGet,
    IndexSet,
    InterpConcat,
    Jump,
    ListInit,
    ListPush,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRPipeInfo,
    MIRType,
    Move,
    Phi,
    Return,
    SignalComputed,
    SignalGet,
    SignalInit,
    SignalSet,
    SignalSubscribe,
    SourceSpan,
    StreamInit,
    StreamOp,
    StreamOpKind,
    StructInit,
    Switch,
    TensorInit,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
)
from mapanare.types import TypeInfo, TypeKind

# ── LLVM type string constants ──────────────────────────────────────
I1 = "i1"
I8 = "i8"
I32 = "i32"
I64 = "i64"
DBL = "double"
VOID = "void"
PTR = "ptr"
STR = "{ptr, i64}"
LIST = "{ptr, i64, i64, i64, i64}"
CLOS = "{ptr, ptr}"
ENUM = "{i64, ptr}"
MN_VALUE = "{i32, i32, {ptr, i64}}"  # 24-byte boxed any: {type_tag, subtype, payload}


# ── Module-level helpers ────────────────────────────────────────────
def _esc(raw: bytes) -> str:
    """Escape bytes for LLVM c\"...\" syntax."""
    out: list[str] = []
    for b in raw:
        if 32 <= b < 127 and b not in (34, 92):
            out.append(chr(b))
        else:
            out.append(f"\\{b:02X}")
    return "".join(out)


def _split_fields(s: str) -> list[str]:
    """Split comma-separated types respecting nested braces."""
    fields: list[str] = []
    depth = 0
    cur = ""
    for ch in s:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if ch == "," and depth == 0:
            fields.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        fields.append(cur.strip())
    return fields


def _talign(ty: str) -> int:
    """Natural alignment of an LLVM type in bytes."""
    t = ty.strip()
    if t in ("i1", "i8"):
        return 1
    if t == "i16":
        return 2
    if t == "i32":
        return 4
    if t in ("i64", "double"):
        return 8
    if t == "ptr" or t.endswith("*"):
        return 8
    if t.startswith("{") and t.endswith("}"):
        inner = t[1:-1].strip()
        if not inner:
            return 1
        return max(_talign(f) for f in _split_fields(inner))
    if t.startswith("[") and "x" in t:
        inner = t[1:].rstrip("]")
        return _talign(inner.split("x", 1)[1].strip())
    return 8


def _tsz(ty: str) -> int:
    """ABI byte size of an LLVM type, including alignment padding."""
    t = ty.strip()
    if t in ("i1", "i8"):
        return 1
    if t == "i16":
        return 2
    if t == "i32":
        return 4
    if t in ("i64", "double"):
        return 8
    if t == "void":
        return 0
    if t == "ptr" or t.endswith("*"):
        return 8
    if t.startswith("{") and t.endswith("}"):
        inner = t[1:-1].strip()
        if not inner:
            return 0
        fields = _split_fields(inner)
        offset = 0
        max_align = 1
        for f in fields:
            fa = _talign(f)
            if fa > max_align:
                max_align = fa
            rem = offset % fa
            if rem != 0:
                offset += fa - rem
            offset += _tsz(f)
        rem = offset % max_align
        if rem != 0:
            offset += max_align - rem
        return offset
    if t.startswith("[") and "x" in t:
        inner = t[1:].rstrip("]")
        parts = inner.split("x", 1)
        return int(parts[0].strip()) * _tsz(parts[1].strip())
    return 8


def _zero(ty: str) -> str:
    """Zero/null constant for an LLVM type."""
    if ty == VOID:
        return ""
    if ty == "ptr" or ty.endswith("*"):
        return "null"
    if ty in (I1, I8, I32, I64):
        return "0"
    if ty in (DBL, "float"):
        return "0.000000e+00"
    if ty.startswith("{") or ty.startswith("["):
        return "zeroinitializer"
    return "0"


def _struct_field0_type(sty: str) -> str:
    """Extract the type of field 0 from an LLVM struct type string like '{i64, {ptr, i64}}'."""
    inner = sty.strip()
    if not inner.startswith("{"):
        return "ptr"
    inner = inner[1:]  # strip leading {
    depth = 0
    for k, ch in enumerate(inner):
        if ch in "({":
            depth += 1
        elif ch in ")}":
            depth -= 1
        elif ch == "," and depth == 0:
            return inner[:k].strip()
    # Single-field struct
    return inner.rstrip("}").strip() or "ptr"


# ── Emitter ─────────────────────────────────────────────────────────
#
# v4.30.0 Phase 4.5: runtime fn attrs audit.
#
# This table maps every Mapanare runtime C function to the LLVM
# attributes declared on its ``@mn_*`` declaration. The panel flagged
# missing ``noalias`` / ``willreturn`` / ``nounwind`` as a 7-cycle
# carry-forward (Rattler #7): allocators didn't advertise that their
# return pointers don't alias, and pure readonly functions didn't
# advertise that they always return. LLVM uses both to enable folds
# and inlining.
#
# Attribute semantics (LLVM Language Reference):
#   - ``nounwind``   — function does not raise C++ exceptions. All
#                      Mapanare C runtime functions qualify.
#   - ``willreturn`` — function eventually returns control to its
#                      caller (no infinite loop, no ``exit``). Every
#                      pure/read/allocation function qualifies.
#   - ``readonly``   — function does not modify any memory the caller
#                      can observe. Implies pure w.r.t. heap state.
#   - ``noalias``    — when applied to the return value, the returned
#                      pointer does not alias any pointer the caller
#                      already held. True for every fresh-allocation
#                      path (``__mn_alloc``, ``__mn_str_from_int``,
#                      ``__mn_list_new``, etc.).
#
# The audit rule: every allocator gains ``noalias`` + ``willreturn``;
# every ``readonly`` function gains ``willreturn``; every deterministic
# C function keeps ``nounwind`` (exceptions only matter on C++ ABIs
# which Mapanare does not cross).
_RUNTIME_FN_ATTRS: dict[str, set[str]] = {
    # Read-only string/collection queries.
    # v4.30.0: added ``willreturn`` to every pure-read function — LLVM
    # can then hoist and CSE the call freely.
    "__mn_str_len": {"nounwind", "readonly", "willreturn"},
    "__mn_str_eq": {"nounwind", "readonly", "willreturn"},
    "__mn_str_cmp": {"nounwind", "readonly", "willreturn"},
    "__mn_str_hash": {"nounwind", "readonly", "willreturn"},
    "__mn_list_len": {"nounwind", "readonly", "willreturn"},
    # v4.42.0: removed readonly+willreturn — __mn_list_get calls abort on
    # OOB, so it is NOT pure and NOT guaranteed to return. Closes P1.
    "__mn_list_get": {"nounwind"},
    "__mn_map_len": {"nounwind", "readonly", "willreturn"},
    "__mn_map_contains": {"nounwind", "readonly", "willreturn"},
    # Allocators. v4.30.0: ``noalias`` on return + ``willreturn``.
    # libc ``malloc`` is documented ``noalias`` by C11; every Mapanare
    # ``__mn_*_new`` / ``__mn_str_from_*`` / ``__mn_*_concat`` wraps a
    # fresh buffer and qualifies the same way.
    "malloc": {"nounwind", "noalias", "willreturn"},
    "__mn_alloc": {"nounwind", "noalias", "willreturn"},
    # Cleanup — terminates, but frees memory so NOT readonly.
    "free": {"nounwind", "willreturn"},
    "__mn_str_free": {"nounwind", "willreturn"},
    "__mn_list_free": {"nounwind", "willreturn"},
    "__mn_map_free": {"nounwind", "willreturn"},
    "__mn_stream_free": {"nounwind", "willreturn"},
    "__mn_stream_free_chain": {"nounwind", "willreturn"},
    "__mn_range_free": {"nounwind", "willreturn"},
    "__mn_signal_free": {"nounwind", "willreturn"},
    "__mn_map_free_deep": {"nounwind", "willreturn"},
    # String-builder allocators — every one returns a fresh heap string.
    "__mn_str_concat": {"nounwind", "noalias", "willreturn"},
    "__mn_str_from_int": {"nounwind", "noalias", "willreturn"},
    "__mn_str_from_float": {"nounwind", "noalias", "willreturn"},
    "__mn_str_from_bool": {"nounwind", "noalias", "willreturn"},
    # Mutation (no noalias — they write through a caller-owned pointer).
    "__mn_list_push": {"nounwind"},
    "__mn_list_set": {"nounwind"},
    # List/map allocators.
    "__mn_list_new": {"nounwind", "noalias", "willreturn"},
    "__mn_list_concat": {"nounwind", "noalias", "willreturn"},
    "__mn_map_set": {"nounwind"},
    "__mn_map_new": {"nounwind", "noalias", "willreturn"},
    # Print — writes to stdout (observable), so no readonly, but does
    # terminate and never throws.
    "__mn_print": {"nounwind", "willreturn"},
    "__mn_println": {"nounwind", "willreturn"},
    # Arena.
    "mn_arena_create": {"nounwind", "noalias", "willreturn"},
    "mn_arena_alloc": {"nounwind", "noalias", "willreturn"},
    "mn_arena_destroy": {"nounwind", "willreturn"},
    # I/O (v3.41.0). Terminates but observable; no readonly beyond
    # the explicit ones below.
    "__mn_read_line": {"nounwind", "willreturn"},
    "__mn_file_append": {"nounwind", "willreturn"},
    "__mn_dir_list_strings": {"nounwind", "willreturn"},
    "__mn_file_exists": {"nounwind", "readonly", "willreturn"},
    "__mn_file_remove": {"nounwind", "willreturn"},
    "__mn_file_size": {"nounwind", "readonly", "willreturn"},
    "__mn_file_mtime": {"nounwind", "readonly", "willreturn"},
    "__mn_dir_create": {"nounwind", "willreturn"},
    "__mn_dir_remove": {"nounwind", "willreturn"},
    "__mn_file_rename": {"nounwind", "willreturn"},
    "__mn_file_copy": {"nounwind", "willreturn"},
    "__mn_realpath": {"nounwind", "willreturn"},
    "__mn_tmpfile_path": {"nounwind", "noalias", "willreturn"},
    # Network, crypto, regex (v3.42.0). The ``*_str`` wrappers all
    # return freshly-allocated strings → noalias + willreturn.
    "__mn_http_get": {"nounwind", "noalias", "willreturn"},
    "__mn_sha256_str": {"nounwind", "noalias", "willreturn"},
    "__mn_base64_encode_str": {"nounwind", "noalias", "willreturn"},
    "__mn_base64_decode_str": {"nounwind", "noalias", "willreturn"},
    "__mn_hmac_sha256_str": {"nounwind", "noalias", "willreturn"},
    "__mn_hex_encode_str": {"nounwind", "noalias", "willreturn"},
    "__mn_random_bytes_str": {"nounwind", "noalias", "willreturn"},
    "__mn_regex_compile_str": {"nounwind", "noalias", "willreturn"},
    "__mn_regex_exec_str": {"nounwind", "willreturn"},
    "__mn_regex_replace_str": {"nounwind", "noalias", "willreturn"},
    "__mn_regex_free": {"nounwind", "willreturn"},
    # GPU builtins (v3.46.0). v4.30.0: query/metadata paths terminate;
    # tensor kernels return new lists → noalias + willreturn.
    "__mn_gpu_available": {"nounwind", "readonly", "willreturn"},
    "__mn_gpu_device_name": {"nounwind", "willreturn"},
    "__mn_gpu_device_memory": {"nounwind", "readonly", "willreturn"},
    "__mn_gpu_tensor_add": {"nounwind", "noalias", "willreturn"},
    "__mn_gpu_tensor_sub": {"nounwind", "noalias", "willreturn"},
    "__mn_gpu_tensor_mul": {"nounwind", "noalias", "willreturn"},
    "__mn_gpu_tensor_div": {"nounwind", "noalias", "willreturn"},
    "__mn_gpu_tensor_matmul": {"nounwind", "noalias", "willreturn"},
    # Tensor literal runtime (v4.42.0). __mn_tensor_alloc returns a fresh
    # heap tensor (noalias); store/free/get are mutation/query helpers.
    "__mn_tensor_alloc": {"nounwind", "noalias", "willreturn"},
    "__mn_tensor_free": {"nounwind", "willreturn"},
    "__mn_tensor_store_f64": {"nounwind", "willreturn"},
    "__mn_tensor_store_i64": {"nounwind", "willreturn"},
    "__mn_tensor_get_f64": {"nounwind", "readonly", "willreturn"},
    "__mn_tensor_get_i64": {"nounwind", "readonly", "willreturn"},
    "__mn_tensor_rank": {"nounwind", "readonly", "willreturn"},
    "__mn_tensor_size": {"nounwind", "readonly", "willreturn"},
    "__mn_tensor_shape_dim": {"nounwind", "readonly", "willreturn"},
    "__mn_tensor_print_f64": {"nounwind", "willreturn"},
    # Tensor multi-dim indexing (v4.43.0). Bounds-check aborts on OOB,
    # so NOT willreturn. The get variants are variadic (rank + indices).
    "__mn_tensor_get_f64_nd": {"nounwind"},
    "__mn_tensor_get_i64_nd": {"nounwind"},
    "__mn_tensor_set_f64_nd": {"nounwind"},
    "__mn_tensor_set_i64_nd": {"nounwind"},
    # Tensor broadcast ops (v4.44.0). Return fresh tensors (noalias).
    # Not willreturn — abort on incompatible shapes or alloc failure.
    "__mn_tensor_add_broadcast_f64": {"nounwind", "noalias"},
    "__mn_tensor_sub_broadcast_f64": {"nounwind", "noalias"},
    "__mn_tensor_mul_broadcast_f64": {"nounwind", "noalias"},
    "__mn_tensor_div_broadcast_f64": {"nounwind", "noalias"},
    "__mn_tensor_add_broadcast_i64": {"nounwind", "noalias"},
    "__mn_tensor_sub_broadcast_i64": {"nounwind", "noalias"},
    "__mn_tensor_mul_broadcast_i64": {"nounwind", "noalias"},
    "__mn_tensor_div_broadcast_i64": {"nounwind", "noalias"},
    "__mn_tensor_add_scalar_f64": {"nounwind", "noalias"},
    "__mn_tensor_sub_scalar_f64": {"nounwind", "noalias"},
    "__mn_tensor_mul_scalar_f64": {"nounwind", "noalias"},
    "__mn_tensor_div_scalar_f64": {"nounwind", "noalias"},
    "__mn_tensor_add_scalar_i64": {"nounwind", "noalias"},
    "__mn_tensor_sub_scalar_i64": {"nounwind", "noalias"},
    "__mn_tensor_mul_scalar_i64": {"nounwind", "noalias"},
    "__mn_tensor_div_scalar_i64": {"nounwind", "noalias"},
    # Reverse scalar ops (v4.47.0): scalar op tensor[i] for non-commutative ops
    "__mn_tensor_rsub_scalar_f64": {"nounwind", "noalias"},
    "__mn_tensor_rdiv_scalar_f64": {"nounwind", "noalias"},
    "__mn_tensor_rsub_scalar_i64": {"nounwind", "noalias"},
    "__mn_tensor_rdiv_scalar_i64": {"nounwind", "noalias"},
    # Tensor reductions (v4.45.0). Global reductions return scalars (no noalias).
    # mean/max/min/argmax/argmin abort on empty tensor (not willreturn).
    "__mn_tensor_sum_f64": {"nounwind"},
    "__mn_tensor_mean_f64": {"nounwind"},
    "__mn_tensor_max_f64": {"nounwind"},
    "__mn_tensor_min_f64": {"nounwind"},
    "__mn_tensor_argmax_f64": {"nounwind"},
    "__mn_tensor_argmin_f64": {"nounwind"},
    "__mn_tensor_sum_i64": {"nounwind"},
    "__mn_tensor_max_i64": {"nounwind"},
    "__mn_tensor_min_i64": {"nounwind"},
    "__mn_tensor_argmax_i64": {"nounwind"},
    "__mn_tensor_argmin_i64": {"nounwind"},
    # Tensor slicing (v4.45.0). Returns fresh tensor (noalias).
    "__mn_tensor_slice": {"nounwind", "noalias"},
    # Tensor stepped slice (v5.45.0 Ts.3.B). Copy semantics — fresh
    # contiguous tensor; conservative omission of noalias to match the
    # rest of the v5.45.0 tensor-producing surface.
    "__mn_tensor_step_slice": {"nounwind"},
    # Tensor reshape (v5.41.0 Ts.1 → v5.45.0 Ts.2.B). Aliases parent's
    # data buffer under the new view-based implementation; ``noalias``
    # is now a lie and is omitted. Refcount-managed lifetime.
    "__mn_tensor_reshape": {"nounwind"},
    # Tensor view (v5.45.0 Ts.2.B). Aliasing — never noalias.
    "__mn_tensor_view": {"nounwind"},
    # Agent runtime (v3.43.0). v4.30.0: ``agent_new`` returns a fresh
    # heap agent handle (noalias); dispatch/send/recv do not.
    "mapanare_agent_new": {"nounwind", "noalias", "willreturn"},
    "mapanare_agent_spawn": {"nounwind", "willreturn"},
    "mapanare_agent_send": {"nounwind", "willreturn"},
    "mapanare_agent_recv_blocking": {"nounwind"},
    "mapanare_agent_stop": {"nounwind", "willreturn"},
    "mapanare_agent_destroy": {"nounwind", "willreturn"},
    # Database runtime (v1.2.0; linked from v4.29.0)
    # runtime/native/mapanare_db.c provides SQLite3, PostgreSQL, Redis,
    # and extended filesystem ops. All third-party libraries (libsqlite3,
    # libpq, libhiredis) are loaded lazily via dlopen; if a library is
    # not installed, the corresponding function returns a graceful error
    # without crashing.
    "__mn_sqlite3_open": {"nounwind"},
    "__mn_sqlite3_close": {"nounwind", "willreturn"},
    "__mn_sqlite3_exec": {"nounwind"},
    "__mn_sqlite3_prepare": {"nounwind"},
    "__mn_sqlite3_bind_int": {"nounwind"},
    "__mn_sqlite3_bind_float": {"nounwind"},
    "__mn_sqlite3_bind_str": {"nounwind"},
    "__mn_sqlite3_bind_null": {"nounwind"},
    "__mn_sqlite3_step": {"nounwind"},
    "__mn_sqlite3_column_int": {"nounwind", "readonly"},
    "__mn_sqlite3_column_float": {"nounwind", "readonly"},
    "__mn_sqlite3_column_str": {"nounwind"},
    "__mn_sqlite3_column_type": {"nounwind", "readonly"},
    "__mn_sqlite3_column_count": {"nounwind", "readonly"},
    "__mn_sqlite3_column_name": {"nounwind"},
    "__mn_sqlite3_finalize": {"nounwind", "willreturn"},
    "__mn_sqlite3_errmsg": {"nounwind"},
    "__mn_pg_connect": {"nounwind"},
    "__mn_pg_close": {"nounwind", "willreturn"},
    "__mn_pg_exec": {"nounwind"},
    "__mn_pg_exec_params": {"nounwind"},
    "__mn_pg_ntuples": {"nounwind", "readonly"},
    "__mn_pg_nfields": {"nounwind", "readonly"},
    "__mn_pg_getvalue": {"nounwind"},
    "__mn_pg_fname": {"nounwind"},
    "__mn_pg_status": {"nounwind", "readonly"},
    "__mn_pg_errmsg": {"nounwind"},
    "__mn_pg_clear": {"nounwind", "willreturn"},
    "__mn_redis_connect": {"nounwind"},
    "__mn_redis_command": {"nounwind"},
    "__mn_redis_command_status": {"nounwind"},
    "__mn_redis_close": {"nounwind", "willreturn"},
    "__mn_redis_errmsg": {"nounwind"},
    # HTML + time + env + url runtime (v4.29.0).
    # runtime/native/mapanare_html.c provides an HTML parser, element
    # queries, time helpers, env reads, and URL parsing. No third-party
    # dependencies.
    "__mn_html_parse": {"nounwind"},
    "__mn_html_free": {"nounwind", "willreturn"},
    "__mn_html_query": {"nounwind"},
    "__mn_html_collection_len": {"nounwind", "readonly"},
    "__mn_html_collection_get": {"nounwind"},
    "__mn_html_element_tag": {"nounwind"},
    "__mn_html_element_attr": {"nounwind"},
    "__mn_html_element_text": {"nounwind"},
    "__mn_html_element_html": {"nounwind"},
    "__mn_html_collection_free": {"nounwind", "willreturn"},
    "__mn_time_now_ms": {"nounwind"},
    "__mn_time_now_unix": {"nounwind"},
    "__mn_sleep_ms": {"nounwind"},
    "__mn_env_get": {"nounwind"},
    "__mn_url_parse_scheme": {"nounwind"},
    "__mn_url_parse_host": {"nounwind"},
    "__mn_url_parse_port": {"nounwind", "readonly"},
    "__mn_url_parse_path": {"nounwind"},
    # v5.1.0 Perf.1: inline list access emits bounds-check trap via abort().
    "abort": {"nounwind", "noreturn"},
}


# v5.49.0 Wn.1 — canonical signatures for ``__mn_*`` runtime symbols
# that user .mn source calls directly (i.e. without going through a
# Mapanare-level builtin handler). Each entry is ``(ret_ty, [param_tys])``
# matching the C declaration in ``runtime/native/mapanare_core.h``.
#
# Why this exists: when .mn source calls ``__mn_file_exists(s)`` (or
# any ``__mn_*`` runtime fn that takes/returns aggregates) the Call
# instruction reaches ``_do_call``'s catchall auto-declare path with
# ``i.dest.ty`` derived from the comparison context (often ``Ptr``
# instead of ``Int`` for unannotated calls — see ``find_clang`` at
# ``mapanare/self/main.mn:80``). The auto-declare path then emitted
# ``declare ptr @__mn_file_exists(ptr)`` (return type wrong) plus a
# call site of ``call ptr @__mn_file_exists({ptr, i64} %v)`` (caller
# passes 16-byte aggregate by value, callee per Win64 ABI expects a
# hidden pointer in RCX) — which on Win64 reads the path string's
# data bytes as if they were the address of an MnString struct,
# producing the v5.49.0 OOM regression. SysV/AAPCS happen to pass
# the same registers and the bug is invisible there. Registry
# entries supersede the MIR-derived (ret, pts) so direct ``__mn_*``
# calls route through ``_rt``'s ABI-correct Win64 sarg/sret lowering.
#
# Pre-register only what is observed in ``mapanare/self/*.mn`` plus
# the wider stdlib FFI surface — unregistered ``__mn_*`` calls keep
# the old auto-declare behavior so this change is non-breaking.
_RUNTIME_FN_SIGS: dict[str, tuple[str, list[str]]] = {
    # Process / argv / environment.
    "__mn_argc": (I64, []),
    "__mn_argv": (STR, [I64]),
    "__mn_exit": (VOID, [I64]),
    "__mn_system": (I64, [STR]),
    "__mn_version_string": (STR, []),
    "__mn_executable_dir": (STR, []),
    "__mn_clang_err_path": (STR, []),
    "__mn_dev_null_redirect": (STR, []),
    "__mn_host_is_windows": (I64, []),
    "__mn_host_is_win64": (I64, []),
    "__mn_host_arch_bits": (I64, []),
    # File / directory I/O — all MnString-arg, the Win64-bug shape.
    "__mn_file_exists": (I64, [STR]),
    "__mn_file_read_or_empty": (STR, [STR]),
    "__mn_file_write": (I64, [STR, STR]),
    "__mn_file_append": (I64, [STR, STR]),
    "__mn_file_remove": (I64, [STR]),
    "__mn_file_size": (I64, [STR]),
    "__mn_file_mtime": (I64, [STR]),
    "__mn_file_rename": (I64, [STR, STR]),
    "__mn_file_copy": (I64, [STR, STR]),
    "__mn_dir_create": (I64, [STR, I64]),
    "__mn_dir_remove": (I64, [STR]),
    "__mn_dir_remove_recursive": (I64, [STR]),
    "__mn_dir_count_files": (I64, [STR]),
    "__mn_dir_total_size": (I64, [STR]),
    "__mn_dir_list_strings": (LIST, [STR]),
    "__mn_realpath": (STR, [STR]),
    "__mn_tmpfile_path": (STR, [STR]),
    "__mn_temp_path": (STR, [STR]),
    # String I/O.
    "__mn_str_eprint": (VOID, [STR]),
    "__mn_str_eprintln": (VOID, [STR]),
    "__mn_str_print": (VOID, [STR]),
    "__mn_str_println": (VOID, [STR]),
    "__mn_read_line": (STR, []),
    # Preprocessor / formatter helpers (v5.14.x / v5.48.x).
    "__mn_indent_to_braces": (STR, [STR]),
    "__mn_rewrite_arm_stmt_shorthand": (STR, [STR]),
    "__mn_count_user_brace_block_openers": (I64, [STR]),
    "__mn_emit_brace_deprecation_warning": (VOID, [STR, I64]),
    # GPU.
    "__mn_gpu_available": (I64, []),
    # Crypto / regex / encoding wrappers (all MnString-arg/return).
    "__mn_http_get": (STR, [STR]),
    "__mn_sha256_str": (STR, [STR]),
    "__mn_base64_encode_str": (STR, [STR]),
    "__mn_base64_decode_str": (STR, [STR]),
    "__mn_hmac_sha256_str": (STR, [STR, STR]),
    "__mn_hex_encode_str": (STR, [STR]),
    "__mn_random_bytes_str": (STR, [I64]),
    "__mn_regex_compile_str": (I64, [STR]),
    "__mn_regex_replace_str": (STR, [I64, STR, STR, I64]),
    "__mn_regex_free": (I64, [I64]),
}


class LLVMTextEmitter:
    """Emit LLVM IR as text from a MIR module."""

    def __init__(
        self,
        module_name: str = "mapanare_module",
        target_triple: str | None = None,
        data_layout: str | None = None,
        debug: bool = False,
    ) -> None:
        self._name = module_name
        self._triple = target_triple or "x86_64-pc-linux-gnu"
        self._layout = data_layout or (
            "e-m:e-p270:32:32-p271:32:32-p272:64:64-" "i64:64-i128:128-f80:128-n8:16:32:64-S128"
        )
        # type registries
        self._structs: dict[str, list[tuple[str, str]]] = {}
        self._struct_idx: dict[str, dict[str, int]] = {}
        self._struct_ty: dict[str, str] = {}
        self._enums: dict[str, tuple[dict[str, int], dict[str, list[MIRType]], dict[str, int]]] = {}
        self._boxed_enum: dict[str, set[tuple[str, int]]] = {}
        # v4.124.0 Rt.1: inline slot count per registered enum.
        #   0 = boxed (existing {i64, ptr} representation)
        #   N ≥ 1 = inline {i64, i64, ..., i64} with N payload slots
        # An enum qualifies for inline storage if every variant has at most
        # N fields, each field is an 8-byte-or-smaller value packable into
        # i64 (Int / Float / Bool / pointer), and no field is marked boxed
        # for self-reference. Inline enums skip malloc on construction,
        # skip the pointer chase on match, and have no drop-glue free.
        # Cap: 2 slots (max 16 bytes of payload) per PLAN guidance —
        # wider variants (3+ fields or heap-owned fields) stay boxed.
        self._enum_inline: dict[str, int] = {}
        # Maximum inline payload slots. Enums with more fields stay boxed.
        self._MAX_INLINE_SLOTS = 2
        self._boxed_struct: dict[str, set[int]] = {}
        self._boxed_struct_mir: dict[str, dict[int, MIRType]] = {}
        self._struct_mir_types: dict[str, dict[int, MIRType]] = {}
        # function signatures
        self._sigs: dict[str, tuple[str, list[str], bool]] = {}
        self._decls: list[str] = []
        self._declared: set[str] = set()
        # globals
        self._globals: list[str] = []
        self._strc = 0
        self._fmts: dict[str, str] = {}
        # per-function (reset each time)
        self._c = 0
        self._alloc: dict[str, tuple[str, str]] = {}
        self._ent: list[str] = []
        self._blk: dict[str, list[str]] = {}
        self._cb = ""
        self._dphi: list[tuple[str, str, list[tuple[str, Value]]]] = []
        self._lroots: dict[str, str] = {}
        self._fn: MIRFunction | None = None
        # drop glue tracking (reset per function)
        self._local_strings: list[str] = []
        self._str_slots: dict[str, str] = {}  # dest var name → str tracking slot
        self._last_tracked_str_slot: str | None = None
        self._local_closures: list[str] = []
        self._local_boxed: list[str] = []  # boxed enum payload ptrs
        self._boxed_slots: dict[str, str] = {}  # dest var name → boxed tracking slot
        self._last_tracked_boxed_slot: str | None = None
        self._list_vars: list[str] = []  # dest names for list cleanup
        # v5.4.4 Own.1 Phase 2 — parallel SSA-source arrays aligned with
        # _local_strings / _local_boxed / _list_vars. Populated by the
        # trackers with the bare SSA source name so drop glue can
        # consult _moved_locals when the lowerer emits Move(src).
        self._local_strings_source: list[str] = []
        self._local_boxed_source: list[str] = []
        self._list_vars_source: list[str] = []
        self._moved_locals: set[str] = set()
        self._map_vars: list[str] = []  # dest names for map cleanup
        self._signal_vars: list[str] = []  # dest names for signal cleanup
        self._stream_vars: list[str] = []  # dest names for stream cleanup
        self._tensor_vars: list[str] = []  # dest names for tensor cleanup (v4.42.0)
        # v5.4.3 — nested-loop depth for free-before-store in _track_*.
        # Pushed when iterating a block whose label starts with
        # for_body / while_body / mapfor_body; popped after.
        self._loop_depth: int = 0
        # v4.146.0 E2: precomputed set of pure function names (module-level)
        self._pure_fns: set[str] = set()
        # debug info (DWARF) — v4.62.0 infrastructure
        self._debug_enabled: bool = debug
        self._debug_metadata_counter: int = 0
        self._debug_file_table: dict[str, int] = {}
        self._debug_location_cache: dict[tuple[int, int, int], int] = {}
        self._debug_type_cache: dict[str, int] = {}
        self._debug_metadata_lines: list[str] = []
        self._debug_subprogram_ids: dict[str, int] = {}
        self._debug_cu_id: int = -1
        self._current_span: SourceSpan | None = None
        self._current_subprogram_id: int = -1
        # dispatch
        self._disp: dict[type, Any] = {}
        self._init_disp()

    # ── dispatch table ──────────────────────────────────────────────
    def _init_disp(self) -> None:
        d = self._disp
        d[Const] = self._do_const
        d[Copy] = self._do_copy
        d[Cast] = self._do_cast
        d[BinOp] = self._do_binop
        d[UnaryOp] = self._do_unary
        d[Call] = self._do_call
        d[ExternCall] = self._do_extern
        d[Return] = self._do_ret
        d[Jump] = self._do_jump
        d[Branch] = self._do_branch
        d[Switch] = self._do_switch
        d[StructInit] = self._do_struct_init
        d[FieldGet] = self._do_field_get
        d[FieldSet] = self._do_field_set
        d[ListInit] = self._do_list_init
        d[ListPush] = self._do_list_push
        d[TensorInit] = self._do_tensor_init
        d[IndexGet] = self._do_idx_get
        d[IndexSet] = self._do_idx_set
        d[MapInit] = self._do_map_init
        d[EnumInit] = self._do_enum_init
        d[EnumTag] = self._do_enum_tag
        d[EnumPayload] = self._do_enum_payload
        d[WrapSome] = self._do_wrap_some
        d[WrapNone] = self._do_wrap_none
        d[WrapOk] = self._do_wrap_ok
        d[WrapErr] = self._do_wrap_err
        d[Unwrap] = self._do_unwrap
        d[InterpConcat] = self._do_interp
        d[ClosureCreate] = self._do_clos_create
        d[ClosureCall] = self._do_clos_call
        d[EnvLoad] = self._do_env_load
        d[AgentSpawn] = self._do_agent_spawn
        d[AgentSend] = self._do_agent_send
        d[AgentSync] = self._do_agent_sync
        d[SignalInit] = self._do_sig_init
        d[SignalGet] = self._do_sig_get
        d[SignalSet] = self._do_sig_set
        d[SignalComputed] = self._do_sig_comp
        d[SignalSubscribe] = self._do_sig_sub
        d[StreamInit] = self._do_stream_init
        d[StreamOp] = self._do_stream_op
        d[Assert] = self._do_assert
        d[AwaitSuspend] = self._do_await_suspend
        d[BlockOn] = self._do_block_on
        d[Move] = self._do_move

    # ── debug metadata helpers (v4.62.0) ─────────────────────────────

    def _alloc_metadata_id(self) -> int:
        """Return the next free metadata ID."""
        mid = self._debug_metadata_counter
        self._debug_metadata_counter += 1
        return mid

    def _emit_debug_metadata(self, content: str) -> str:
        """Emit a metadata node and return its ``!N`` reference."""
        mid = self._alloc_metadata_id()
        ref = f"!{mid}"
        self._debug_metadata_lines.append(f"{ref} = {content}")
        return ref

    def _get_debug_file(self, path: str) -> int:
        """Return the metadata ID for a source file, creating if needed."""
        if path in self._debug_file_table:
            return self._debug_file_table[path]
        import os

        directory = os.path.dirname(path) or "."
        filename = os.path.basename(path)
        mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(
            f'!{mid} = !DIFile(filename: "{filename}", directory: "{directory}")'
        )
        self._debug_file_table[path] = mid
        return mid

    def _get_debug_location(self, file_id: int, line: int, col: int, scope_id: int) -> int:
        """Return the metadata ID for a source location, creating if needed."""
        key = (file_id, line, col)
        if key in self._debug_location_cache:
            return self._debug_location_cache[key]
        mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(
            f"!{mid} = !DILocation(line: {line}, column: {col}, scope: !{scope_id})"
        )
        self._debug_location_cache[key] = mid
        return mid

    def _get_debug_basic_type(self, name: str, size: int, encoding: str) -> int:
        """Return metadata ID for a DWARF basic type, cached by name."""
        if name in self._debug_type_cache:
            return self._debug_type_cache[name]
        mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(
            f'!{mid} = !DIBasicType(name: "{name}", size: {size}, encoding: {encoding})'
        )
        self._debug_type_cache[name] = mid
        return mid

    def _get_debug_type_for_mir(self, ty: MIRType) -> int:
        """Map a MIR type to a DWARF basic type metadata ID."""
        from mapanare.types import TypeKind

        k = ty.kind
        if k == TypeKind.INT:
            return self._get_debug_basic_type("Int", 64, "DW_ATE_signed")
        elif k == TypeKind.FLOAT:
            return self._get_debug_basic_type("Float", 64, "DW_ATE_float")
        elif k == TypeKind.BOOL:
            return self._get_debug_basic_type("Bool", 8, "DW_ATE_boolean")
        else:
            # Placeholder for String, List, Map, etc. — treated as opaque ptr
            return self._get_debug_basic_type("ptr", 64, "DW_ATE_address")

    def _emit_debug_subroutine_type(self, fn: "MIRFunction") -> int:
        """Emit a DISubroutineType for a function and return its metadata ID."""
        type_refs = []
        # Return type (first element; None for void)
        rt = fn.return_type
        if rt and rt.kind != TypeKind.VOID:
            type_refs.append(f"!{self._get_debug_type_for_mir(rt)}")
        else:
            type_refs.append("null")
        # Parameter types
        for p in fn.params:
            type_refs.append(f"!{self._get_debug_type_for_mir(p.ty)}")
        types_list = ", ".join(type_refs)
        # Cache by signature tuple
        sig_key = tuple(type_refs)
        cache_key = str(sig_key)
        if cache_key in self._debug_type_cache:
            return self._debug_type_cache[cache_key]
        types_mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(f"!{types_mid} = !{{{types_list}}}")
        mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(f"!{mid} = !DISubroutineType(types: !{types_mid})")
        self._debug_type_cache[cache_key] = mid
        return mid

    def _emit_debug_compile_unit(self, source_file: str) -> int:
        """Emit a DICompileUnit and return its metadata ID."""
        file_id = self._get_debug_file(source_file)
        mid = self._alloc_metadata_id()
        ver = self._version()
        self._debug_metadata_lines.append(
            f"!{mid} = distinct !DICompileUnit("
            f"language: DW_LANG_C99, "
            f"file: !{file_id}, "
            f'producer: "Mapanare {ver}", '
            f"isOptimized: true, "
            f"runtimeVersion: 0, "
            f"emissionKind: FullDebug)"
        )
        self._debug_cu_id = mid
        return mid

    def _emit_debug_subprogram(self, fn: "MIRFunction", source_file: str) -> int:
        """Emit a DISubprogram for a function and return its metadata ID."""
        file_id = self._get_debug_file(source_file)
        line = fn.source_line if fn.source_line else 0
        sr_type_id = self._emit_debug_subroutine_type(fn)
        is_local = "true" if (not fn.is_public and fn.name != "main") else "false"
        mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(
            f"!{mid} = distinct !DISubprogram("
            f'name: "{fn.name}", '
            f'linkageName: "{fn.name}", '
            f"scope: !{self._debug_cu_id}, "
            f"file: !{file_id}, "
            f"line: {line}, "
            f"type: !{sr_type_id}, "
            f"isLocal: {is_local}, "
            f"isDefinition: true, "
            f"scopeLine: {line}, "
            f"spFlags: DISPFlagDefinition, "
            f"unit: !{self._debug_cu_id})"
        )
        return mid

    def _emit_debug_composite_type(self, name: str, fields: list[tuple[str, "MIRType"]]) -> int:
        """Emit a DICompositeType for a struct and return its metadata ID."""
        cache_key = f"struct:{name}"
        if cache_key in self._debug_type_cache:
            return self._debug_type_cache[cache_key]
        members = []
        offset = 0
        for fname, fty in fields:
            fty_id = self._get_debug_type_for_mir(fty)
            size = 64  # all types are 64-bit in Mapanare's IR layout
            mem_id = self._alloc_metadata_id()
            self._debug_metadata_lines.append(
                f"!{mem_id} = !DIDerivedType(tag: DW_TAG_member, "
                f'name: "{fname}", size: {size}, offset: {offset}, '
                f"baseType: !{fty_id})"
            )
            members.append(f"!{mem_id}")
            offset += size
        elems_id = self._alloc_metadata_id()
        self._debug_metadata_lines.append(f"!{elems_id} = !{{{', '.join(members)}}}")
        mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(
            f"!{mid} = !DICompositeType(tag: DW_TAG_structure_type, "
            f'name: "{name}", size: {offset}, elements: !{elems_id})'
        )
        self._debug_type_cache[cache_key] = mid
        return mid

    def _emit_debug_local_variable(
        self, name: str, ty_id: int, scope_id: int, line: int, arg_index: int = 0
    ) -> int:
        """Emit a DILocalVariable and return its metadata ID."""
        mid = self._alloc_metadata_id()
        arg_part = f", arg: {arg_index}" if arg_index > 0 else ""
        file_id = next(iter(self._debug_file_table.values()), 0)
        self._debug_metadata_lines.append(
            f'!{mid} = !DILocalVariable(name: "{name}"{arg_part}, '
            f"scope: !{scope_id}, file: !{file_id}, line: {line}, type: !{ty_id})"
        )
        return mid

    def _emit_dbg_declare(self, alloca_ref: str, var_meta_id: int) -> None:
        """Emit an llvm.dbg.declare call after an alloca."""
        if not self._debug_enabled or self._current_subprogram_id < 0:
            return
        loc_suffix = ""
        if self._current_span and self._current_span.line > 0:
            file_id = next(iter(self._debug_file_table.values()), 0)
            loc_id = self._get_debug_location(
                file_id,
                self._current_span.line,
                self._current_span.column,
                self._current_subprogram_id,
            )
            loc_suffix = f", !dbg !{loc_id}"
        self._blk[self._cb].append(
            f"  call void @llvm.dbg.declare(metadata ptr {alloca_ref}, "
            f"metadata !{var_meta_id}, metadata !DIExpression()){loc_suffix}"
        )

    def _build_debug_metadata_section(self) -> list[str]:
        """Build the module-level DWARF metadata section."""
        if not self._debug_enabled or not hasattr(self, "_debug_cu_id"):
            return []
        lines = [
            "",
            f"!llvm.dbg.cu = !{{!{self._debug_cu_id}}}",
            "!llvm.module.flags = !{!_mf_dwarf, !_mf_di, !_mf_wchar}",
            "",
        ]
        # Module flags use named placeholders — resolve them
        dwarf_mid = self._alloc_metadata_id()
        di_mid = self._alloc_metadata_id()
        wchar_mid = self._alloc_metadata_id()
        self._debug_metadata_lines.append(f'!{dwarf_mid} = !{{i32 7, !"Dwarf Version", i32 5}}')
        self._debug_metadata_lines.append(f'!{di_mid} = !{{i32 2, !"Debug Info Version", i32 3}}')
        self._debug_metadata_lines.append(f'!{wchar_mid} = !{{i32 1, !"wchar_size", i32 4}}')
        # Replace placeholders
        lines[2] = f"!llvm.module.flags = !{{!{dwarf_mid}, !{di_mid}, !{wchar_mid}}}"
        # All metadata nodes
        lines.extend(self._debug_metadata_lines)
        lines.append("")
        return lines

    # ── public entry point ──────────────────────────────────────────
    def emit(self, mir: MIRModule) -> str:
        """Emit LLVM IR text from a MIR module."""
        # 1) register types (iterative for mutual recursion)
        for _ in range(10):
            prev = {n: list(s.values()) for n, (_, _, s) in self._enums.items()}
            for nm, flds in mir.structs.items():
                self._reg_struct(nm, flds)
            for nm, vs in mir.enums.items():
                self._reg_enum(nm, vs)
            cur = {n: list(s.values()) for n, (_, _, s) in self._enums.items()}
            if prev == cur:
                break
        # 2) declare externs
        for abi, mod, fn, pts, rt in mir.extern_fns:
            full = f"{mod}__{fn}" if mod else fn
            self._decl_fn(full, self._rty(rt), [self._rty(p) for p in pts])
        # 2b) emit module-level constants
        for cname, ctype, cval in mir.consts:
            if isinstance(cval, str):
                slen = len(cval)
                self._globals.append(f'@{cname} = private constant [{slen} x i8] c"{cval}"')
            elif isinstance(cval, int):
                self._globals.append(f"@{cname} = private constant i64 {cval}")
            elif isinstance(cval, float):
                self._globals.append(f"@{cname} = private constant double {cval}")
        # 3) forward-declare MIR functions (strip % from names)
        for f in mir.functions:
            if f.name.startswith("%"):
                f.name = f.name[1:]
            # v4.92.0: async functions return ptr (Future handle), not their declared type
            ret_ty = "ptr" if f.is_async else self._rty(f.return_type)
            self._sigs[f.name] = (
                ret_ty,
                [self._rty(p.ty) for p in f.params],
                False,
            )
        # 4) DWARF metadata (v4.63.0) — emit compile unit + subprograms BEFORE bodies
        if self._debug_enabled:
            source_file = getattr(mir, "source_file", self._name + ".mn")
            self._emit_debug_compile_unit(source_file)
            for f in mir.functions:
                if f.blocks:
                    sp_id = self._emit_debug_subprogram(f, source_file)
                    self._debug_subprogram_ids[f.name] = sp_id
        # 4b) v4.92.0: determine module-level async flag + async fn names before emitting bodies
        self._module_has_async = any(f.is_async for f in mir.functions if f.blocks)
        self._async_fn_names: set[str] = {f.name for f in mir.functions if f.is_async and f.blocks}
        # 4c) v4.146.0 E2: precompute pure function set (fixed-point)
        self._pure_fns = self._compute_pure_fns(mir.functions)
        # 5) emit bodies
        fns: list[str] = []
        for f in mir.functions:
            if f.blocks:
                fns.append(self._emit_fn(f))
        # 6) agent wrappers
        for aname, ainfo in mir.agents.items():
            fns.append(self._emit_agent_wrap(aname, ainfo))
        # 7) pipe defs
        for pname, pinfo in mir.pipes.items():
            fns.append(self._emit_pipe(pname, pinfo))
        # 8a) coroutine intrinsic declarations (v4.70.0)
        self._module_has_async = any(f.is_async for f in mir.functions if f.blocks)
        if self._module_has_async:
            # Ensure malloc/free are declared for frame + future allocation
            self._decl_fn("malloc", "ptr", ["i64"])
            self._decl_fn("free", "void", ["ptr"])
            self._decls.append("; -- coroutine intrinsics (v4.70.0) --")
            self._decls.append("declare token @llvm.coro.id(i32, ptr, ptr, ptr)")
            self._decls.append("declare i1 @llvm.coro.alloc(token)")
            self._decls.append("declare i64 @llvm.coro.size.i64()")
            self._decls.append("declare ptr @llvm.coro.begin(token, ptr)")
            self._decls.append("declare i8 @llvm.coro.suspend(token, i1)")
            self._decls.append("declare i1 @llvm.coro.end(ptr, i1, token)")
            self._decls.append("declare ptr @llvm.coro.free(token, ptr)")
            self._decls.append("declare void @llvm.coro.resume(ptr)")
            self._decls.append("declare void @llvm.coro.destroy(ptr)")
            self._decls.append("declare i1 @llvm.coro.done(ptr)")
            self._decls.append("declare token @llvm.coro.save(ptr)")
            # v4.93.0: multi-threaded work-stealing scheduler runtime declarations
            self._decls.append("; -- coroutine scheduler (v4.93.0) --")
            self._decls.append("declare void @__mn_coro_scheduler_init(i32)")
            self._decls.append("declare void @__mn_coro_scheduler_register(ptr)")
            self._decls.append("declare void @__mn_coro_register_wait(ptr, ptr)")
            self._decls.append("declare void @__mn_coro_scheduler_run()")
            self._decls.append("declare void @__mn_coro_scheduler_destroy()")
            self._decls.append("declare void @__mn_coro_spawn(ptr)")
            self._decls.append("declare ptr @__mn_file_read_async({ptr, i64})")
        # 8b) debug intrinsic declarations (v4.65.0)
        if self._debug_enabled:
            self._decls.append(
                "declare void @llvm.dbg.declare(metadata, metadata, metadata) nounwind readnone"
            )
            self._decls.append(
                "declare void @llvm.dbg.value(metadata, metadata, metadata) nounwind readnone"
            )
        # 9) assemble
        hdr = [
            f"; ModuleID = '{self._name}'",
            f'source_filename = "{self._name}"',
            f'target datalayout = "{self._layout}"',
            f'target triple = "{self._triple}"',
            "",
        ]
        ver = self._version()
        if self._debug_enabled:
            # Version metadata uses allocated IDs to avoid collision with debug IDs
            ver_list_id = self._alloc_metadata_id()
            ver_str_id = self._alloc_metadata_id()
            self._debug_metadata_lines.append(f'!{ver_str_id} = !{{!"{ver}"}}')
            tail = ["", f"!mapanare.version = !{{!{ver_list_id}}}"]
            self._debug_metadata_lines.append(f"!{ver_list_id} = !{{!{ver_str_id}}}")
            tail += self._build_debug_metadata_section()
        else:
            # Module version metadata. v4.123.0 removed the TBAA tree
            # (nodes !1–!9) that used to live here: it was declared but
            # never attached to any load/store, confirmed 100% dead by
            # v4.109.0 forensics, and wiring it would not help at -O2.
            tail = [
                "",
                "!mapanare.version = !{!0}",
                f'!0 = !{{!"{ver}"}}',
                "",
            ]
        parts = hdr
        if self._globals:
            parts += self._globals + [""]
        if self._decls:
            parts += self._decls + [""]
        parts += fns + tail
        return "\n".join(parts)

    def _version(self) -> str:
        try:
            p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION")
            with open(p) as f:
                return f.read().strip()
        except OSError:
            return "unknown"

    # ── type resolution ─────────────────────────────────────────────
    def _rty(self, mt: MIRType) -> str:
        """Resolve MIR type to LLVM type string."""
        k = mt.kind
        if k == TypeKind.INT:
            return I64
        if k == TypeKind.FLOAT:
            return DBL
        if k == TypeKind.BOOL:
            return I1
        if k == TypeKind.CHAR:
            return I8
        if k == TypeKind.STRING:
            return STR
        if k == TypeKind.VOID:
            return VOID
        if k == TypeKind.LIST:
            return LIST
        if k == TypeKind.MAP:
            return PTR
        if k == TypeKind.STRUCT:
            return self._lookup_struct_or_enum(mt.type_info.name)
        if k == TypeKind.ENUM:
            nm = mt.type_info.name
            if nm:
                return self._enum_ty(nm)
            return ENUM
        if k == TypeKind.OPTION:
            a = mt.type_info.args
            inner = self._rti(a[0]) if a else PTR
            return "{" + f"i1, {inner}" + "}"
        if k == TypeKind.RESULT:
            a = mt.type_info.args
            if len(a) >= 2:
                return "{" + f"i1, {{{self._rti(a[0])}, {self._rti(a[1])}}}" + "}"
            return "{i1, {ptr, ptr}}"
        if k == TypeKind.ANY:
            return MN_VALUE
        if k == TypeKind.TENSOR:
            return PTR  # opaque pointer to mapanare_tensor_t
        if k in (TypeKind.AGENT, TypeKind.SIGNAL, TypeKind.STREAM, TypeKind.CHANNEL, TypeKind.FN):
            return PTR
        nm = mt.type_info.name
        if nm:
            return self._lookup_struct_or_enum(nm)
        return PTR

    def _rti(self, ti: TypeInfo) -> str:
        return self._rty(MIRType(type_info=ti))

    def _lookup_struct_or_enum(self, nm: str) -> str:
        if nm in self._struct_ty:
            return self._struct_ty[nm]
        for s in self._struct_ty:
            if s.endswith("__" + nm):
                return self._struct_ty[s]
        if nm in self._enums:
            return self._enum_ty(nm)
        for e in self._enums:
            if e.endswith("__" + nm):
                return self._enum_ty(e)
        return PTR

    def _enum_ty(self, nm: str) -> str:
        """LLVM struct type for a registered enum, inline or boxed.

        Inline enums use `{i64, i64, ..., i64}` with one i64 tag slot
        followed by N i64 payload slots, where N = _enum_inline[nm].
        N == 0 variants (pure unit enums) get `{i64, i64}` to keep the
        in-memory size consistent with single-payload enums — wider
        allocation but it simplifies codegen / drop glue.
        """
        slots = self._enum_inline.get(nm, 0)
        if slots == 0:
            return ENUM
        # Always emit at least one payload slot even for pure unit enums
        # to keep the layout uniform and avoid a separate {i64} case.
        n_slots = max(slots, 1)
        return "{" + ", ".join(["i64"] * (1 + n_slots)) + "}"

    # ── registration ────────────────────────────────────────────────
    def _is_self_ref(self, parent: str, mt: MIRType) -> bool:
        base = parent.rsplit("__", 1)[-1]

        def m(n: str) -> bool:
            return bool(n) and (n == parent or n == base or parent.endswith("__" + n))

        ti = mt.type_info
        if not ti:
            return False
        if mt.kind in (TypeKind.STRUCT, TypeKind.ENUM, TypeKind.UNKNOWN) and m(ti.name):
            return True
        if mt.kind == TypeKind.OPTION and ti.args:
            if hasattr(ti.args[0], "name") and m(ti.args[0].name):
                return True
        if mt.kind == TypeKind.RESULT and ti.args:
            for a in ti.args:
                if hasattr(a, "name") and m(a.name):
                    return True
        return False

    def _reg_struct(self, nm: str, fields: list[tuple[str, MIRType]]) -> None:
        ftypes: list[str] = []
        boxed: set[int] = set()
        for i, (_, ft) in enumerate(fields):
            if self._is_self_ref(nm, ft):
                ftypes.append(PTR)
                boxed.add(i)
            else:
                ftypes.append(self._rty(ft))
        fnames = [n for n, _ in fields]
        self._structs[nm] = list(zip(fnames, ftypes))
        self._struct_idx[nm] = {n: i for i, n in enumerate(fnames)}
        self._struct_ty[nm] = "{" + ", ".join(ftypes) + "}"
        # Preserve MIR types for nested list detection in deep clone
        self._struct_mir_types[nm] = {i: ft for i, (_, ft) in enumerate(fields)}
        if boxed:
            self._boxed_struct[nm] = boxed
            self._boxed_struct_mir[nm] = {i: ft for i, (_, ft) in enumerate(fields) if i in boxed}

    def _reg_enum(self, nm: str, variants: list[tuple[str, list[MIRType]]]) -> None:
        tags: dict[str, int] = {}
        pays: dict[str, list[MIRType]] = {}
        sizes: dict[str, int] = {}
        boxed: set[tuple[str, int]] = set()
        pre = self._boxed_enum.get(nm, set())
        for i, (vn, pts) in enumerate(variants):
            tags[vn] = i
            pays[vn] = pts
            if pts:
                fld_types: list[str] = []
                for j, pt in enumerate(pts):
                    if (vn, j) in pre or self._is_self_ref(nm, pt):
                        fld_types.append(PTR)
                        boxed.add((vn, j))
                    else:
                        fld_types.append(self._rty(pt))
                # Compute aligned struct size
                sizes[vn] = _tsz("{" + ", ".join(fld_types) + "}")
            else:
                sizes[vn] = 0
        self._enums[nm] = (tags, pays, sizes)
        if boxed:
            self._boxed_enum[nm] = boxed
        # v4.124.0 Rt.1: decide inline slot count for this enum (0 =
        # boxed). Qualification: every variant field is i64-packable
        # (Int / Float / Bool / pointer); no field is marked boxed for
        # self-reference; max variant field count ≤ _MAX_INLINE_SLOTS.
        self._enum_inline[nm] = self._compute_enum_inline_slots(pays, boxed)

    def _compute_enum_inline_slots(
        self,
        pays: dict[str, list[MIRType]],
        boxed: set[tuple[str, int]],
    ) -> int:
        """Return inline slot count (0 = boxed, N ≥ 1 = inline with N payload slots)."""
        if boxed:
            return 0
        max_fields = 0
        for _vn, pts in pays.items():
            if len(pts) > max_fields:
                max_fields = len(pts)
            for pt in pts:
                ft = self._rty(pt)
                if not self._type_fits_inline_slot(ft):
                    return 0
        if max_fields > self._MAX_INLINE_SLOTS:
            return 0
        return max_fields

    @staticmethod
    def _type_fits_inline_slot(ft: str) -> bool:
        """True if *ft* is an 8-byte-or-smaller value storable in an i64 slot
        via bitcast / zext / ptrtoint without information loss.

        Int / Float (double) / Bool (i1) / opaque pointers qualify. String
        ({ptr, i64}), List ({ptr, i64, i64}), Result/Option wrapper structs,
        and user structs do not."""
        if ft in ("i64", "double", "i1", "i8", "i16", "i32", "ptr"):
            return True
        if ft.endswith("*"):
            return True
        return False

    def _pack_to_i64(self, val: str, ft: str) -> str:
        """Convert *val* of LLVM type *ft* into an i64 suitable for an inline
        enum payload slot. Reverse of _unpack_from_i64."""
        if ft == "i64":
            return val
        if ft == "double":
            r = self._f("pk")
            self._L(f"{r} = bitcast double {val} to i64")
            return r
        if ft in ("i1", "i8", "i16", "i32"):
            r = self._f("pk")
            self._L(f"{r} = zext {ft} {val} to i64")
            return r
        if ft == "ptr" or ft.endswith("*"):
            r = self._f("pk")
            self._L(f"{r} = ptrtoint ptr {val} to i64")
            return r
        # Unsupported type — should have been filtered by
        # _type_fits_inline_slot during registration.
        return val

    def _unpack_from_i64(self, val: str, ft: str) -> str:
        """Reverse of _pack_to_i64: extract a value of LLVM type *ft* from an
        i64 payload slot."""
        if ft == "i64":
            return val
        if ft == "double":
            r = self._f("upk")
            self._L(f"{r} = bitcast i64 {val} to double")
            return r
        if ft in ("i1", "i8", "i16", "i32"):
            r = self._f("upk")
            self._L(f"{r} = trunc i64 {val} to {ft}")
            return r
        if ft == "ptr" or ft.endswith("*"):
            r = self._f("upk")
            self._L(f"{r} = inttoptr i64 {val} to ptr")
            return r
        return val

    def _res_enum(self, raw: str) -> str:
        if raw in self._enums:
            return raw
        for e in self._enums:
            if e.endswith("__" + raw):
                return e
        return raw

    def _res_struct(self, raw: str) -> str:
        if raw in self._structs:
            return raw
        for s in self._structs:
            if s.endswith("__" + raw):
                return s
        return raw

    def _vtag(self, variant: str, hint: str = "") -> int:
        if variant in ("Some", "Ok"):
            return 1
        if variant in ("None", "Err"):
            return 0
        if hint:
            for en, (tags, _, _) in self._enums.items():
                if (en == hint or en.endswith("__" + hint)) and variant in tags:
                    return tags[variant]
        for _, (tags, _, _) in self._enums.items():
            if variant in tags:
                return tags[variant]
        return 0

    # ── declaration helpers ─────────────────────────────────────────
    @property
    def _is_windows(self) -> bool:
        """v5.8.6 We.1: any Windows target (i686 or x86_64).

        Replaces the v5.8.4 single-flag ``_win64`` semantic, which
        conflated "Windows host" with "use Win64 ABI rules" because
        ``_win64`` returned True for any triple containing ``windows``
        — including ``i686-w64-windows-gnu``. Win32 (cdecl) and Win64
        have different return-size thresholds and different aggregate-
        arg conventions, so the dispatch needs to know both pieces.
        """
        return "windows" in self._triple

    @property
    def _win_arch_bits(self) -> int:
        """v5.8.6 We.1: pointer-width of the target triple in bits.

        32 for ``i686-*`` / ``i386-*``, 64 otherwise. The two-bit pair
        ``(_is_windows, _win_arch_bits)`` selects the ABI dispatch
        path: (True, 64) → Win64 sret/sarg, (True, 32) → i686 cdecl
        sret/byval, (False, *) → SysV / AAPCS64 by-value.
        """
        if self._triple.startswith("i686") or self._triple.startswith("i386"):
            return 32
        return 64

    @property
    def _use_win64_abi(self) -> bool:
        """v5.8.6 We.1: True iff Win64 sret/sarg ABI rules apply."""
        return self._is_windows and self._win_arch_bits == 64

    @property
    def _use_i686_abi(self) -> bool:
        """v5.8.6 We.1: True iff i686 cdecl sret/byval ABI rules apply."""
        return self._is_windows and self._win_arch_bits == 32

    @property
    def _use_apple_aarch64_abi(self) -> bool:
        """v5.8.8 Da.1: True iff Apple AArch64 (AAPCS64-Apple) sret rules apply.

        LLVM's arm64 backend lowers ``define {ptr, i64, ...} @fn()`` (a
        first-class aggregate return) as register-tuple return (x0..xN),
        but the C runtime returns > 16 B aggregates via x8 indirect per
        AAPCS64. The mismatch produces silent miscompilation: caller
        reads x0..xN and gets uninitialised register state. SysV-x86_64
        is forgiving (LLVM's x86_64 backend silently rewrites first-class
        aggregate return → sret-style memory return per AMD64 §3.2.3
        memory class); arm64 is not. See
        ``docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md``.
        """
        return self._triple.startswith("aarch64-apple")

    @property
    def _win64(self) -> bool:
        """v5.8.4 deprecated alias — kept for in-file source compat.

        Now means "use Win64 ABI rules" (was previously "Windows
        host"); for code paths that actually want the latter, use
        ``_is_windows``. Reads as a property so existing call sites
        don't need source rewrites within emit_llvm_text.py.
        """
        return self._use_win64_abi

    @staticmethod
    def _is_ptr(ty: str) -> bool:
        """True if *ty* is a pointer type (opaque or legacy typed)."""
        return ty == "ptr" or ty.endswith("*")

    @staticmethod
    def _is_large_struct(ty: str) -> bool:
        """True if *ty* is a struct that exceeds 8 bytes (Win64 indirect ABI)."""
        return ty.startswith("{") and ty.endswith("}") and _tsz(ty) > 8

    # Threshold for pass-by-reference optimization.  Structs above this size
    # are passed/returned via pointer instead of by value in user-defined
    # functions.  This eliminates the massive insertvalue/extractvalue chains,
    # the sret buffer garbage, and the _clone_list_fields crashes for large
    # state structs (LowerState 240B, LowerResult 248B, EmitState 240B).
    _BYREF_BYTES = 64

    @staticmethod
    def _use_byref(ty: str) -> bool:
        """True if *ty* should use pointer passing (byref) for user function arguments."""
        return ty.startswith("{") and ty.endswith("}") and _tsz(ty) > LLVMTextEmitter._BYREF_BYTES

    def _use_sret(self, ty: str) -> bool:
        """True if *ty* should use sret for return values on the current target.

        v4.149.0 E5 / ABI.1: per-target classification replaces the
        blanket ``_BYREF_BYTES`` threshold for return types.  Implements
        System V AMD64 §3.2.3 (≤ 16 B → register), Win64 (1/2/4/8 B →
        register), and AArch64 AAPCS64 (≤ 16 B → register).

        Argument passing still uses ``_use_byref`` (64 B threshold).
        """
        if not (ty.startswith("{") and ty.endswith("}")):
            return False
        return classify_return(ty, _tsz(ty), self._triple).kind == "sret"

    def _decl_fn(self, nm: str, ret: str, pts: list[str], va: bool = False) -> None:
        if nm in self._declared:
            return
        self._declared.add(nm)
        self._sigs[nm] = (ret, pts, va)

        if self._use_win64_abi:
            # Win64 ABI: large structs passed by pointer, returned via sret
            abi_pts = ["ptr" if self._is_large_struct(t) else t for t in pts]
            if self._is_large_struct(ret):
                sret = f"ptr sret({ret})"
                abi_pts = [sret] + abi_pts
                abi_ret = "void"
            else:
                abi_ret = ret
        elif self._use_i686_abi:
            # v5.8.6 We.1: i686 cdecl — large structs (> 8 B) need
            # the `byval(<orig>) align 4` attribute so LLVM's i686
            # backend lowers them as caller-pushes-by-value, matching
            # gcc/clang's C ABI for ``MnString``-shaped runtime fns.
            # Returns > 8 B use the same sret-with-`align 8` shape.
            abi_pts = [f"ptr byval({t}) align 4" if self._is_large_struct(t) else t for t in pts]
            if self._is_large_struct(ret):
                sret = f"ptr sret({ret}) align 8"
                abi_pts = [sret] + abi_pts
                abi_ret = "void"
            else:
                abi_ret = ret
        elif self._use_sret(ret):
            # v5.8.8 Da.1: SysV / AAPCS64 default — > 16 B aggregate
            # returns must use sret. SysV's "memory class" rule
            # (AMD64 §3.2.3) and AAPCS64's x8 indirect-result rule
            # both lower a > 16 B struct return via a hidden first-arg
            # pointer. LLVM's x86_64 backend silently rewrites
            # first-class aggregate returns to sret-style memory
            # return, so the old shape worked on Linux by accident;
            # LLVM's arm64 backend does not, so the same IR
            # miscompiles on Apple Silicon. Emit the canonical sret
            # form unconditionally — matches clang's lowering on both
            # targets and produces equivalent machine code. See
            # docs/roadmap/v5/v5.8.7/PHASE_0_FINDINGS.md.
            abi_pts = [f"ptr sret({ret}) align 8"] + list(pts)
            abi_ret = "void"
        else:
            abi_pts = list(pts)
            abi_ret = ret

        ps = ", ".join(abi_pts)
        if va:
            ps += ", ..." if ps else "..."
        attrs = _RUNTIME_FN_ATTRS.get(nm, set())
        # v4.30.0 Phase 4.5: ``noalias`` is a return-value attribute and
        # LLVM rejects it on any non-pointer return type. Several
        # Mapanare runtime allocators return MnString (``{ptr, i64}``)
        # or a list struct (``{ptr, i64, i64, i64, i64}``) rather than
        # a raw ``ptr``; the attr table still lists ``noalias`` on
        # those entries to document intent, but we strip it at the
        # declaration site unless the function really returns ``ptr``.
        # The large-struct sret rewrite above also drops the true
        # return to ``void``; those paths never carry ``noalias``
        # because the pointer comes in as a parameter, not out.
        ret_attrs = sorted(a for a in attrs if a == "noalias" and abi_ret == "ptr")
        fn_attrs = sorted(a for a in attrs if a != "noalias")
        ret_prefix = " ".join(ret_attrs) + " " if ret_attrs else ""
        fn_suffix = " " + " ".join(fn_attrs) if fn_attrs else ""
        decl = f"declare {ret_prefix}{abi_ret} @{nm}({ps}){fn_suffix}"
        self._decls.append(decl)

    def _ensure(self, nm: str, ret: str, pts: list[str], va: bool = False) -> None:
        if nm not in self._sigs:
            self._decl_fn(nm, ret, pts, va)

    # ── per-function primitives ─────────────────────────────────────
    def _f(self, pfx: str = "t") -> str:
        n = self._c
        self._c += 1
        return f"%{pfx}.{n}"

    def _alloca(self, ty: str, name: str = "") -> str:
        """Create an alloca in the entry block (avoids stack growth in loops)."""
        a = self._f(name or "a")
        self._ent.append(f"  {a} = alloca {ty}, align 8")
        return a

    def _L(self, txt: str) -> None:  # noqa: N802
        if self._debug_enabled and self._current_span and self._current_subprogram_id >= 0:
            span = self._current_span
            if span.line > 0:
                file_id = next(iter(self._debug_file_table.values()), 0)
                loc_id = self._get_debug_location(
                    file_id, span.line, span.column, self._current_subprogram_id
                )
                txt = f"{txt}, !dbg !{loc_id}"
        self._blk[self._cb].append(f"  {txt}")

    @staticmethod
    def _san(nm: str) -> str:
        # v5.36.0 Js.0: strip all '%' (not just leading) so compound names
        # like f"_map_iter_{value.name}" don't preserve embedded sigils
        # when value.name itself starts with '%' (e.g., "%entries37").
        return nm.replace("%", "").replace(".", "_").replace("-", "_")

    def _get(self, v: Value) -> tuple[str, str]:
        """Load MIR value from alloca → (tmp, type)."""
        for k in (v.name, v.name.lstrip("%"), "%" + v.name.lstrip("%")):
            if k in self._alloc:
                a, ty = self._alloc[k]
                t = self._f("l")
                self._L(f"{t} = load {ty}, ptr {a}")
                return t, ty
        ty = self._rty(v.ty)
        if ty == VOID:
            ty = I64
        return _zero(ty), ty

    def _get_ptr(self, v: Value) -> tuple[str, str] | None:
        for k in (v.name, v.name.lstrip("%"), "%" + v.name.lstrip("%")):
            if k in self._alloc:
                return self._alloc[k]
        return None

    def _put(self, dest: Value, val: str, ty: str) -> None:
        """Store val to dest's alloca."""
        if ty == VOID:
            return
        nm = dest.name
        # Normalize name: check both %name and name variants
        if nm not in self._alloc:
            alt = nm.lstrip("%")
            alt2 = "%" + alt
            if alt in self._alloc:
                nm = alt
            elif alt2 in self._alloc:
                nm = alt2
        if nm not in self._alloc:
            a = self._f(f"{self._san(nm)}.a")
            self._alloc[nm] = (a, ty)
            self._ent.append(f"  {a} = alloca {ty}, align 8")
            self._ent.append(f"  store {ty} {_zero(ty)}, ptr {a}")
        a, aty = self._alloc[nm]
        # If new value is larger, upgrade the alloca BUT keep the old one
        # accessible. Create a new alloca sized for the larger type, but
        # DON'T discard the old alloca mapping — instead, keep BOTH and
        # store the larger value in the new alloca.
        if ty != aty and _tsz(ty) > _tsz(aty):
            a = self._f(f"{self._san(nm)}.up")
            self._alloc[nm] = (a, ty)
            self._ent.append(f"  {a} = alloca {ty}, align 8")
            self._ent.append(f"  store {ty} {_zero(ty)}, ptr {a}")
            aty = ty
        if ty == aty:
            self._L(f"store {ty} {val}, ptr {a}")
        else:
            c = self._coerce(val, ty, aty)
            self._L(f"store {aty} {c}, ptr {a}")
        # Associate variable with its tracking slot for move semantics
        if ty == STR and self._last_tracked_str_slot:
            self._str_slots[dest.name] = self._last_tracked_str_slot
            self._last_tracked_str_slot = None

    def _move_resource(self, name: str) -> None:
        """Zero out tracking slots for a consumed variable (move semantics).

        When a variable is passed to a function call or used as an enum
        payload, its value is "moved" into the callee's data structure.
        Zeroing the tracking slot prevents drop glue from freeing the
        now-owned value.
        """
        if name in self._str_slots:
            slot = self._str_slots.pop(name)
            self._L(f"store {{ptr, i64}} zeroinitializer, ptr {slot}")
        if name in self._boxed_slots:
            slot = self._boxed_slots.pop(name)
            self._L(f"store ptr null, ptr {slot}")
        # v5.4.4 — record the move in _moved_locals so drop glue skips
        # any tracked slot whose source aliases this name, even when
        # _str_slots / _boxed_slots didn't wire the slot at track time.
        self._moved_locals.add(name.lstrip("%"))

    def _do_move(self, i: Move) -> None:
        # v5.4.0 Own.1 Phase 2 — Move marker from the lowerer. Route to
        # _move_resource so the Python emitter recognizes explicit
        # ownership transfers emitted by the self-hosted-style lowerer.
        # _do_call's blanket-move remains the primary path for most calls.
        self._move_resource(i.value.name)

    def _coerce(self, val: str, fr: str, to: str) -> str:
        if fr == to:
            return val
        if self._is_ptr(fr) and self._is_ptr(to):
            return val  # ptr-to-ptr is identity with opaque pointers
        if self._is_ptr(fr) and to == I64:
            t = self._f("p2i")
            self._L(f"{t} = ptrtoint ptr {val} to i64")
            return t
        if fr == I64 and self._is_ptr(to):
            t = self._f("i2p")
            self._L(f"{t} = inttoptr i64 {val} to ptr")
            return t
        if fr in (I1, I8, I32) and to == I64:
            t = self._f("zx")
            self._L(f"{t} = zext {fr} {val} to i64")
            return t
        if fr == I64 and to in (I1, I8, I32):
            t = self._f("tr")
            self._L(f"{t} = trunc i64 {val} to {to}")
            return t
        if fr == I1 and to == I8:
            t = self._f("zx")
            self._L(f"{t} = zext i1 {val} to i8")
            return t
        # memory reinterpret — alloca in entry block to avoid stack growth in loops
        fs, ts = _tsz(fr), _tsz(to)
        if fs >= ts:
            a = self._f("rc")
            self._ent.append(f"  {a} = alloca {fr}, align 8")
            self._L(f"store {fr} {val}, ptr {a}")
            v = self._f("rv")
            self._L(f"{v} = load {to}, ptr {a}")
            return v
        else:
            a = self._f("rc")
            self._ent.append(f"  {a} = alloca {to}, align 8")
            self._L(f"store {to} {_zero(to)}, ptr {a}")
            self._L(f"store {fr} {val}, ptr {a}")
            v = self._f("rv")
            self._L(f"{v} = load {to}, ptr {a}")
            return v

    # ── string / printf helpers ─────────────────────────────────────
    def _mkstr(self, text: str) -> tuple[str, str]:
        raw = text.encode("utf-8")
        n = len(raw)
        esc = _esc(raw)
        gn = f"@.str.{self._strc}"
        self._strc += 1
        at = f"[{n} x i8]"
        self._globals.append(f'{gn} = private constant {at} c"{esc}", align 8')
        p = self._f("sp")
        self._L(f"{p} = getelementptr inbounds {at}, ptr {gn}, i64 0, i64 0")
        s0 = self._f("s")
        self._L(f"{s0} = insertvalue {{ptr, i64}} undef, ptr {p}, 0")
        s1 = self._f("s")
        self._L(f"{s1} = insertvalue {{ptr, i64}} {s0}, i64 {n}, 1")
        return s1, STR

    def _fmtptr(self, fmt: str) -> str:
        if fmt not in self._fmts:
            raw = fmt.encode("utf-8") + b"\x00"
            n = len(raw)
            gn = f"@.fmt.{len(self._fmts)}"
            self._fmts[fmt] = gn
            at = f"[{n} x i8]"
            self._globals.append(f'{gn} = private constant {at} c"{_esc(raw)}", align 8')
        gn = self._fmts[fmt]
        raw = fmt.encode("utf-8") + b"\x00"
        at = f"[{len(raw)} x i8]"
        p = self._f("fp")
        self._L(f"{p} = getelementptr inbounds {at}, ptr {gn}, i64 0, i64 0")
        return p

    def _printf(self, fmt: str, args: list[tuple[str, str]]) -> None:
        self._ensure("printf", I32, [PTR], va=True)
        p = self._fmtptr(fmt)
        a = "".join(f", {ty} {v}" for v, ty in args)
        r = self._f("pf")
        self._L(f"{r} = call i32 (ptr, ...) @printf(ptr {p}{a})")

    def _rt(
        self, fn: str, ret: str, pts: list[str], args: list[tuple[str, str]], nm: str = ""
    ) -> str:
        """Call runtime fn, coerce args. Returns result name (empty for void)."""
        self._ensure(fn, ret, pts)
        coerced: list[tuple[str, str]] = []
        for i, (v, t) in enumerate(args):
            et = pts[i] if i < len(pts) else t
            coerced.append((self._coerce(v, t, et) if t != et else v, et))

        if self._use_win64_abi:
            # Win64 ABI: pass large structs by pointer, return via sret
            abi_args: list[tuple[str, str]] = []
            for v, t in coerced:
                if self._is_large_struct(t):
                    a = self._alloca(t, "sarg")
                    self._L(f"store {t} {v}, ptr {a}")
                    abi_args.append((a, "ptr"))
                else:
                    abi_args.append((v, t))

            if self._is_large_struct(ret):
                sret_a = self._alloca(ret, nm or "sret")
                sret_arg = f"ptr sret({ret}) {sret_a}"
                rest = ", ".join(f"{t} {v}" for v, t in abi_args)
                a_str = f"{sret_arg}, {rest}" if rest else sret_arg
                self._L(f"call void @{fn}({a_str})")
                r = self._f(nm or "rt")
                self._L(f"{r} = load {ret}, ptr {sret_a}")
                return r

            a_str = ", ".join(f"{t} {v}" for v, t in abi_args)
            if ret == VOID:
                self._L(f"call void @{fn}({a_str})")
                return ""
            r = self._f(nm or "rt")
            self._L(f"{r} = call {ret} @{fn}({a_str})")
            return r

        if self._use_i686_abi:
            # v5.8.6 We.1: i686 cdecl — same alloca-and-pass mechanic
            # as Win64, but the call-site argument carries the
            # ``byval(<orig>) align 4`` attribute so LLVM's i686
            # backend lowers it as caller-pushes-by-value (matching
            # gcc/clang's C ABI). Return > 8 B uses the same sret
            # ``align 8`` shape Win64 uses.
            abi_args_i: list[tuple[str, str]] = []
            for v, t in coerced:
                if self._is_large_struct(t):
                    a = self._alloca(t, "sarg")
                    self._L(f"store {t} {v}, ptr {a}")
                    abi_args_i.append((a, f"ptr byval({t}) align 4"))
                else:
                    abi_args_i.append((v, t))

            if self._is_large_struct(ret):
                sret_a_i = self._alloca(ret, nm or "sret")
                sret_arg_i = f"ptr sret({ret}) align 8 {sret_a_i}"
                rest_i = ", ".join(f"{t} {v}" for v, t in abi_args_i)
                a_str_i = f"{sret_arg_i}, {rest_i}" if rest_i else sret_arg_i
                self._L(f"call void @{fn}({a_str_i})")
                r = self._f(nm or "rt")
                self._L(f"{r} = load {ret}, ptr {sret_a_i}")
                return r

            a_str_i = ", ".join(f"{t} {v}" for v, t in abi_args_i)
            if ret == VOID:
                self._L(f"call void @{fn}({a_str_i})")
                return ""
            r = self._f(nm or "rt")
            self._L(f"{r} = call {ret} @{fn}({a_str_i})")
            return r

        if self._use_sret(ret):
            # v5.8.8 Da.1: SysV / AAPCS64 default — sret call shape
            # for > 16 B aggregate returns. Mirrors _decl_fn's default
            # sret declaration. Caller alloca + sret call + load.
            sret_a = self._alloca(ret, nm or "sret")
            sret_arg = f"ptr sret({ret}) align 8 {sret_a}"
            rest = ", ".join(f"{t} {v}" for v, t in coerced)
            a_str = f"{sret_arg}, {rest}" if rest else sret_arg
            self._L(f"call void @{fn}({a_str})")
            r = self._f(nm or "rt")
            self._L(f"{r} = load {ret}, ptr {sret_a}")
            return r

        a = ", ".join(f"{t} {v}" for v, t in coerced)
        if ret == VOID:
            self._L(f"call void @{fn}({a})")
            return ""
        r = self._f(nm or "rt")
        self._L(f"{r} = call {ret} @{fn}({a})")
        return r

    # ── drop glue ──────────────────────────────────────────────────
    def _track_string(self, val: str) -> None:
        """Track a heap-allocated string for drop glue cleanup.

        Emits an alloca in the entry block and stores the string value into it.
        _emit_drop_glue iterates these allocas at every return site and frees
        non-returned strings.
        """
        slot = self._f("str_track")
        self._ent.append(f"  {slot} = alloca {{ptr, i64}}, align 8")
        self._ent.append(f"  store {{ptr, i64}} zeroinitializer, ptr {slot}")
        # v5.4.3 — Rt.03: free-before-store inside loop bodies.
        if self._loop_depth > 0:
            prev = self._f("prev_str")
            self._L(f"{prev} = load {{ptr, i64}}, ptr {slot}")
            self._L(f"call void @__mn_str_free({{ptr, i64}} {prev})")
        self._L(f"store {{ptr, i64}} {val}, ptr {slot}")
        self._local_strings.append(slot)
        # v5.4.4 — parallel source array aligned with _local_strings.
        self._local_strings_source.append(val.lstrip("%"))
        self._last_tracked_str_slot = slot

    def _track_closure(self, val: str) -> None:
        """Track a heap-allocated closure env for drop glue cleanup."""
        slot = self._f("clos_track")
        self._ent.append(f"  {slot} = alloca {{ptr, ptr}}, align 8")
        self._ent.append(f"  store {{ptr, ptr}} zeroinitializer, ptr {slot}")
        # v5.4.3 — free the env ptr only; fn ptr is code, no free.
        if self._loop_depth > 0:
            prev = self._f("prev_clos")
            env_prev = self._f("prev_clos_env")
            self._L(f"{prev} = load {{ptr, ptr}}, ptr {slot}")
            self._L(f"{env_prev} = extractvalue {{ptr, ptr}} {prev}, 1")
            self._L(f"call void @free(ptr {env_prev})")
        self._L(f"store {{ptr, ptr}} {val}, ptr {slot}")
        self._local_closures.append(slot)

    def _track_boxed(self, ptr_val: str) -> None:
        """Track a boxed enum payload pointer for drop glue cleanup."""
        slot = self._f("box_track")
        self._ent.append(f"  {slot} = alloca ptr, align 8")
        self._ent.append(f"  store ptr null, ptr {slot}")
        # v5.4.3 — free-before-store inside loop bodies. @free(null) no-ops.
        if self._loop_depth > 0:
            prev = self._f("prev_box")
            self._L(f"{prev} = load ptr, ptr {slot}")
            self._L(f"call void @free(ptr {prev})")
        self._L(f"store ptr {ptr_val}, ptr {slot}")
        self._local_boxed.append(slot)
        # v5.4.4 — parallel source array aligned with _local_boxed.
        self._local_boxed_source.append(ptr_val.lstrip("%"))
        self._last_tracked_boxed_slot = slot

    def _track_container(self, dest_name: str, container_type: str) -> None:
        """Track a container variable for drop glue cleanup.

        Unlike strings (immutable, tracked by value snapshot), containers are
        mutable — push/set operations change them in place. We track by variable
        name and load the final value at return time from the dest alloca.
        """
        if container_type == "list":
            if dest_name not in self._list_vars:
                self._list_vars.append(dest_name)
                # v5.4.4 — parallel source array aligned with _list_vars.
                self._list_vars_source.append(dest_name.lstrip("%"))
        elif container_type == "map":
            if dest_name not in self._map_vars:
                self._map_vars.append(dest_name)
        elif container_type == "signal":
            if dest_name not in self._signal_vars:
                self._signal_vars.append(dest_name)
        elif container_type == "stream":
            if dest_name not in self._stream_vars:
                self._stream_vars.append(dest_name)

    def _emit_drop_glue(self, ret_val: str | None, ret_ty: str) -> None:
        """Dispatch per-resource cleanup before a return instruction.

        v4.32.0 Phase 2.2 (Cobra Issue #12, 10th cycle): extracted from
        ~300 lines of inline loops into per-kind helpers. Byte-identity
        preserving for main.ll — the order of ``self._ensure`` and
        ``self._L`` calls is unchanged.
        """
        has_any = (
            (self._local_strings)
            or (self._local_closures)
            or (self._local_boxed)
            or self._list_vars
            or self._map_vars
            or self._signal_vars
            or self._stream_vars
            or self._tensor_vars
        )
        if not has_any:
            return
        # v4.78.0: removed blanket early return that skipped ALL drop glue
        # for struct returns containing ptr fields (CARRY_FORWARD #49, 8
        # cycles). _emit_drop_glue_collect_ret_ptrs now extracts every
        # escaping pointer from the return value, and the per-kind helpers
        # compare against ret_ptr_fields before freeing — so the blanket
        # bail is no longer needed.

        self._ensure("__mn_str_free", VOID, [STR])
        ret_str_ptrs, ret_list_ptrs, ret_env, ret_ptr_fields = (
            self._emit_drop_glue_collect_ret_ptrs(ret_val, ret_ty)
        )

        self._emit_drop_glue_strings(ret_str_ptrs, ret_ptr_fields)
        self._ensure("free", VOID, [PTR])
        self._emit_drop_glue_closures(ret_env, ret_ptr_fields)
        self._emit_drop_glue_boxed(ret_ptr_fields)
        if self._list_vars:
            self._ensure("__mn_list_free", VOID, ["ptr"])
        self._emit_drop_glue_lists(ret_list_ptrs, ret_ptr_fields)
        if self._map_vars:
            self._ensure("__mn_map_free_deep", VOID, [PTR])
        self._emit_drop_glue_maps()
        if self._signal_vars:
            self._ensure("__mn_signal_free", VOID, [PTR])
        self._emit_drop_glue_signals()
        if self._stream_vars:
            self._ensure("__mn_stream_free_chain", VOID, [PTR])
        self._emit_drop_glue_streams()
        if self._tensor_vars:
            self._ensure("__mn_tensor_free", VOID, [PTR])
        self._emit_drop_glue_tensors(ret_val, ret_ty)

    def _emit_drop_glue_collect_ret_ptrs(
        self, ret_val: str | None, ret_ty: str
    ) -> tuple[list[str], list[str], str | None, list[str]]:
        """Extract every pointer that will escape via the return value.

        Returns ``(ret_str_ptrs, ret_list_ptrs, ret_env, ret_ptr_fields)``.
        The per-resource drop helpers use these lists to skip freeing
        pointers the function is about to return.
        """
        # Extract returned string's data pointer (to avoid freeing it)
        ret_str_ptrs: list[str] = []
        if ret_val and ret_ty == STR:
            ret_ptr = self._f("ret.ptr")
            self._L(f"{ret_ptr} = extractvalue {{ptr, i64}} {ret_val}, 0")
            ret_str_ptrs.append(ret_ptr)

        # Extract string data pointers from returned struct fields
        if ret_val and ret_ty != STR and ret_ty.startswith("{"):
            sn_s = self._struct_name_for_llvm_type(ret_ty)
            if sn_s and sn_s in self._structs:
                for idx, (_, ft) in enumerate(self._structs[sn_s]):
                    if ft == STR:
                        sf = self._f("ret.ssf")
                        self._L(f"{sf} = extractvalue {ret_ty} {ret_val}, {idx}")
                        sp_ret = self._f("ret.ssp")
                        self._L(f"{sp_ret} = extractvalue {{ptr, i64}} {sf}, 0")
                        ret_str_ptrs.append(sp_ret)

        # Extract returned list's data pointer (to avoid freeing it)
        ret_list_ptrs: list[str] = []
        if ret_val and ret_ty == LIST:
            ret_list_ptr = self._f("ret.lp")
            self._L(f"{ret_list_ptr} = extractvalue {LIST} {ret_val}, 0")
            ret_list_ptrs.append(ret_list_ptr)

        # Extract list data pointers from returned struct fields (avoid freeing them)
        if ret_val and ret_ty != LIST and ret_ty.startswith("{"):
            sn = self._struct_name_for_llvm_type(ret_ty)
            if sn and sn in self._structs:
                for idx, (_, ft) in enumerate(self._structs[sn]):
                    if ft == LIST:
                        lf = self._f("ret.slf")
                        self._L(f"{lf} = extractvalue {ret_ty} {ret_val}, {idx}")
                        lp = self._f("ret.slp")
                        self._L(f"{lp} = extractvalue {LIST} {lf}, 0")
                        ret_list_ptrs.append(lp)

        # Extract returned closure's env pointer (to avoid freeing it)
        ret_env: str | None = None
        if ret_val and ret_ty == CLOS:
            ret_env = self._f("ret.env")
            self._L(f"{ret_env} = extractvalue {{ptr, ptr}} {ret_val}, 1")

        # Extract ALL ptr fields from the return value (to avoid freeing boxed
        # enum payloads, strings, or lists that are part of the return value).
        # Walk the return type recursively and extractvalue every ptr-typed leaf.
        # Always extract when we have param list fields or list vars to compare.
        ret_ptr_fields: list[str] = []
        need_ret_ptrs = (
            self._local_boxed or self._local_strings or self._local_closures or self._list_vars
        )
        if ret_val and ret_ty.startswith("{") and need_ret_ptrs:
            self._extract_ret_ptrs(ret_val, ret_ty, ret_ptr_fields)

        return ret_str_ptrs, ret_list_ptrs, ret_env, ret_ptr_fields

    # ------------------------------------------------------------------
    # v4.32.0 Phase 2.2 — per-resource drop-glue helpers
    # ------------------------------------------------------------------
    # Each helper is the verbatim body of the inline for-loop it
    # replaces. Extracted from _emit_drop_glue (formerly ~300 lines) per
    # Cobra Issue #12 (10th cycle). Keeping them as methods on the
    # emitter class preserves access to self._f, self._L, self._blk,
    # self._cb, self._c, and self._local_* / self._*_vars.

    def _emit_drop_glue_strings(self, ret_str_ptrs: list[str], ret_ptr_fields: list[str]) -> None:
        """Drop-loop for tracked local strings.

        For each slot in self._local_strings, loads the {ptr, i64}
        value, checks the data pointer against any string pointers the
        function is returning (ret_str_ptrs + ret_ptr_fields), and
        calls __mn_str_free unless the pointer would alias.
        """
        for slot in self._local_strings:
            sv = self._f("drop.s")
            self._L(f"{sv} = load {{ptr, i64}}, ptr {slot}")
            sp = self._f("drop.p")
            self._L(f"{sp} = extractvalue {{ptr, i64}} {sv}, 0")
            # Check if pointer is null (string was never assigned)
            sn = self._f("drop.null")
            self._L(f"{sn} = icmp eq ptr {sp}, null")
            skip_lbl = f"drop.skip.{self._c}"
            free_lbl = f"drop.check.{self._c}"
            self._c += 1
            self._L(f"br i1 {sn}, label %{skip_lbl}, label %{free_lbl}")

            # check block: compare with return pointer if applicable
            self._blk[free_lbl] = []
            self._cb = free_lbl
            all_str_ptrs = ret_str_ptrs + ret_ptr_fields
            if all_str_ptrs:
                for rsp in all_str_ptrs:
                    same = self._f("drop.same")
                    self._L(f"{same} = icmp eq ptr {sp}, {rsp}")
                    next_check = f"drop.snext.{self._c}"
                    self._c += 1
                    self._L(f"br i1 {same}, label %{skip_lbl}, label %{next_check}")
                    self._blk[next_check] = []
                    self._cb = next_check
            self._L(f"call void @__mn_str_free({{ptr, i64}} {sv})")
            self._L(f"br label %{skip_lbl}")

            # skip block: continue
            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_closures(self, ret_env: str | None, ret_ptr_fields: list[str]) -> None:
        """Drop-loop for tracked local closure environments.

        For each closure slot, loads the {fn_ptr, env_ptr} pair and
        free's the env pointer unless it aliases a returned pointer
        (ret_env for direct closure returns, ret_ptr_fields for
        closures embedded in struct returns).
        """
        for slot in self._local_closures:
            cv = self._f("drop.c")
            self._L(f"{cv} = load {{ptr, ptr}}, ptr {slot}")
            ep = self._f("drop.ep")
            self._L(f"{ep} = extractvalue {{ptr, ptr}} {cv}, 1")
            en = self._f("drop.enull")
            self._L(f"{en} = icmp eq ptr {ep}, null")
            skip_lbl = f"drop.cskip.{self._c}"
            free_lbl = f"drop.ccheck.{self._c}"
            self._c += 1
            self._L(f"br i1 {en}, label %{skip_lbl}, label %{free_lbl}")

            self._blk[free_lbl] = []
            self._cb = free_lbl
            # Compare closure env against returned pointers (ret_env for direct
            # closure return, ret_ptr_fields for closures embedded in structs).
            all_env_ptrs = list(ret_ptr_fields)
            if ret_env:
                all_env_ptrs.append(ret_env)
            for renv in all_env_ptrs:
                same = self._f("drop.csame")
                self._L(f"{same} = icmp eq ptr {ep}, {renv}")
                next_check = f"drop.cnext.{self._c}"
                self._c += 1
                self._L(f"br i1 {same}, label %{skip_lbl}, label %{next_check}")
                self._blk[next_check] = []
                self._cb = next_check
            self._L(f"call void @free(ptr {ep})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_boxed(self, ret_ptr_fields: list[str]) -> None:
        """Drop-loop for tracked local boxed enum payloads.

        For each boxed slot, loads the raw ptr and frees it unless it
        aliases any returned pointer (ret_ptr_fields).

        v4.103.0: conservative skip when the return value exposes any
        pointer at any nesting level. A boxed enum payload can embed
        other boxed pointers inside its heap storage, and
        `_extract_ret_ptrs` only walks LLVM-level struct values — it
        does not dereference pointers. So a box nested inside another
        box does not appear in `ret_ptr_fields`, and drop-glue freed
        it while it was still referenced from the returned enum.
        Observed as self-hosted parser's `parse_if_expr` building an
        inner `ElseBlock` whose box the drop-glue pass freed before
        the outer If was fully constructed — the allocator reused
        that address for the outer `ElseBlock`, and the nested if/
        else check in `semantic.check_else_clause` walked the aliased
        tree forever.

        Any function whose return value contains a pointer is
        potentially carrying a box. We skip all boxed drops for such
        functions. Boxes fall through to process exit — acceptable
        for a short-lived compiler binary. A principled fix requires
        type-aware deep-pointer walking at return sites and is
        scoped to a future release.
        """
        if ret_ptr_fields and self._local_boxed:
            # Potential box escape through returned pointer. Skip.
            return
        for slot in self._local_boxed:
            bp = self._f("drop.bp")
            self._L(f"{bp} = load ptr, ptr {slot}")
            bn = self._f("drop.bnull")
            self._L(f"{bn} = icmp eq ptr {bp}, null")
            skip_lbl = f"drop.bskip.{self._c}"
            free_lbl = f"drop.bcheck.{self._c}"
            self._c += 1
            self._L(f"br i1 {bn}, label %{skip_lbl}, label %{free_lbl}")

            self._blk[free_lbl] = []
            self._cb = free_lbl
            if ret_ptr_fields:
                for rpf in ret_ptr_fields:
                    same = self._f("drop.bsame")
                    self._L(f"{same} = icmp eq ptr {bp}, {rpf}")
                    next_check = f"drop.bnext.{self._c}"
                    self._c += 1
                    self._L(f"br i1 {same}, label %{skip_lbl}, label %{next_check}")
                    self._blk[next_check] = []
                    self._cb = next_check
            self._L(f"call void @free(ptr {bp})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_lists(self, ret_list_ptrs: list[str], ret_ptr_fields: list[str]) -> None:
        """Drop-loop for tracked list variables.

        For each list_var, resolves the alloca, loads the list struct,
        extracts the data pointer, and calls __mn_list_free unless the
        pointer aliases a returned list pointer (ret_list_ptrs +
        ret_ptr_fields). Variables that cannot be resolved via
        self._alloc are silently skipped (matches pre-extraction
        behavior).
        """
        for var_name in self._list_vars:
            alloc_info = None
            for k in (var_name, var_name.lstrip("%"), "%" + var_name.lstrip("%")):
                if k in self._alloc:
                    alloc_info = self._alloc[k]
                    break
            if alloc_info is None:
                continue
            addr, aty = alloc_info
            lv = self._f("drop.lv")
            self._L(f"{lv} = load {LIST}, ptr {addr}")
            lp = self._f("drop.lp")
            self._L(f"{lp} = extractvalue {LIST} {lv}, 0")
            ln = self._f("drop.lnull")
            self._L(f"{ln} = icmp eq ptr {lp}, null")
            skip_lbl = f"drop.lskip.{self._c}"
            check_lbl = f"drop.lcheck.{self._c}"
            self._c += 1
            self._L(f"br i1 {ln}, label %{skip_lbl}, label %{check_lbl}")

            self._blk[check_lbl] = []
            self._cb = check_lbl
            all_list_ptrs = ret_list_ptrs + ret_ptr_fields
            if all_list_ptrs:
                # Check if this list's data pointer matches ANY returned pointer
                for rlp in all_list_ptrs:
                    lsame = self._f("drop.lsame")
                    self._L(f"{lsame} = icmp eq ptr {lp}, {rlp}")
                    next_check = f"drop.lnext.{self._c}"
                    self._c += 1
                    self._L(f"br i1 {lsame}, label %{skip_lbl}, label %{next_check}")
                    self._blk[next_check] = []
                    self._cb = next_check
            # Pass the variable's alloca directly to __mn_list_free
            self._L(f"call void @__mn_list_free(ptr {addr})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_maps(self) -> None:
        """Drop-loop for tracked map variables.

        For each map_var, resolves the alloca, loads the ptr, and
        calls __mn_map_free_deep unconditionally (no aliasing check —
        maps do not participate in the return-pointer escape analysis
        today).
        """
        for var_name in self._map_vars:
            alloc_info = None
            for k in (var_name, var_name.lstrip("%"), "%" + var_name.lstrip("%")):
                if k in self._alloc:
                    alloc_info = self._alloc[k]
                    break
            if alloc_info is None:
                continue
            addr, _ = alloc_info
            mp = self._f("drop.mp")
            self._L(f"{mp} = load ptr, ptr {addr}")
            mn = self._f("drop.mnull")
            self._L(f"{mn} = icmp eq ptr {mp}, null")
            skip_lbl = f"drop.mskip.{self._c}"
            free_lbl = f"drop.mfree.{self._c}"
            self._c += 1
            self._L(f"br i1 {mn}, label %{skip_lbl}, label %{free_lbl}")

            self._blk[free_lbl] = []
            self._cb = free_lbl
            self._L(f"call void @__mn_map_free_deep(ptr {mp})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_signals(self) -> None:
        """Drop-loop for tracked signal variables.

        For each signal_var, resolves the alloca, loads the ptr, and
        calls __mn_signal_free.
        """
        for var_name in self._signal_vars:
            alloc_info = None
            for k in (var_name, var_name.lstrip("%"), "%" + var_name.lstrip("%")):
                if k in self._alloc:
                    alloc_info = self._alloc[k]
                    break
            if alloc_info is None:
                continue
            addr, _ = alloc_info
            sp = self._f("drop.sig")
            self._L(f"{sp} = load ptr, ptr {addr}")
            sn = self._f("drop.signull")
            self._L(f"{sn} = icmp eq ptr {sp}, null")
            skip_lbl = f"drop.sigskip.{self._c}"
            free_lbl = f"drop.sigfree.{self._c}"
            self._c += 1
            self._L(f"br i1 {sn}, label %{skip_lbl}, label %{free_lbl}")

            self._blk[free_lbl] = []
            self._cb = free_lbl
            self._L(f"call void @__mn_signal_free(ptr {sp})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_streams(self) -> None:
        """Drop-loop for tracked stream variables.

        For each stream_var, resolves the alloca, loads the ptr, and
        calls __mn_stream_free_chain (which walks the fusion chain and
        frees every link).
        """
        for var_name in self._stream_vars:
            alloc_info = None
            for k in (var_name, var_name.lstrip("%"), "%" + var_name.lstrip("%")):
                if k in self._alloc:
                    alloc_info = self._alloc[k]
                    break
            if alloc_info is None:
                continue
            addr, _ = alloc_info
            sp = self._f("drop.strm")
            self._L(f"{sp} = load ptr, ptr {addr}")
            sn = self._f("drop.strmnull")
            self._L(f"{sn} = icmp eq ptr {sp}, null")
            skip_lbl = f"drop.strmskip.{self._c}"
            free_lbl = f"drop.strmfree.{self._c}"
            self._c += 1
            self._L(f"br i1 {sn}, label %{skip_lbl}, label %{free_lbl}")

            self._blk[free_lbl] = []
            self._cb = free_lbl
            self._L(f"call void @__mn_stream_free_chain(ptr {sp})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _emit_drop_glue_tensors(self, ret_val: str | None, ret_ty: str) -> None:
        """Drop-loop for tracked tensor variables (v4.42.0).

        For each tensor_var, resolves the alloca, loads the ptr, and
        calls __mn_tensor_free unless the pointer is being returned.
        """
        for var_name in self._tensor_vars:
            alloc_info = None
            for k in (var_name, var_name.lstrip("%"), "%" + var_name.lstrip("%")):
                if k in self._alloc:
                    alloc_info = self._alloc[k]
                    break
            if alloc_info is None:
                continue
            addr, _ = alloc_info
            tp = self._f("drop.tens")
            self._L(f"{tp} = load ptr, ptr {addr}")
            tn = self._f("drop.tensnull")
            self._L(f"{tn} = icmp eq ptr {tp}, null")
            skip_lbl = f"drop.tensskip.{self._c}"
            free_lbl = f"drop.tensfree.{self._c}"
            self._c += 1

            # Check if this tensor is the return value
            if ret_val and ret_ty == PTR:
                eq = self._f("drop.tensret")
                self._L(f"{eq} = icmp eq ptr {tp}, {ret_val}")
                or_skip = self._f("drop.tensor")
                self._L(f"{or_skip} = or i1 {tn}, {eq}")
                self._L(f"br i1 {or_skip}, label %{skip_lbl}, label %{free_lbl}")
            else:
                self._L(f"br i1 {tn}, label %{skip_lbl}, label %{free_lbl}")

            self._blk[free_lbl] = []
            self._cb = free_lbl
            self._L(f"call void @__mn_tensor_free(ptr {tp})")
            self._L(f"br label %{skip_lbl}")

            self._blk[skip_lbl] = []
            self._cb = skip_lbl

    def _extract_ret_ptrs(self, val: str, ty: str, out: list[str], depth: int = 0) -> None:
        """Recursively extract all ptr-typed fields from a return value.

        Used to prevent drop glue from freeing boxed enum payloads that are
        embedded in the return value (at any nesting depth).
        """
        if depth > 4:
            return  # prevent excessive nesting
        t = ty.strip()
        if t == "ptr":
            out.append(val)
            return
        if not t.startswith("{") or not t.endswith("}"):
            return
        inner = t[1:-1].strip()
        if not inner:
            return
        fields = _split_fields(inner)
        for idx, ft in enumerate(fields):
            ft = ft.strip()
            if ft == "ptr":
                p = self._f("ret.rp")
                self._L(f"{p} = extractvalue {ty} {val}, {idx}")
                out.append(p)
            elif ft.startswith("{"):
                sv = self._f("ret.rs")
                self._L(f"{sv} = extractvalue {ty} {val}, {idx}")
                self._extract_ret_ptrs(sv, ft, out, depth + 1)

    def _emit_arena_destroy(self) -> None:
        """Destroy the per-function arena before return."""
        if self._arena_ptr is not None:
            self._ensure("mn_arena_destroy", VOID, [PTR])
            a = self._f("arena.d")
            self._L(f"{a} = load ptr, ptr {self._arena_ptr}")
            self._L(f"call void @mn_arena_destroy(ptr {a})")

    @staticmethod
    def _fn_is_arena_eligible(fn: MIRFunction) -> bool:
        """Conservative escape analysis: enable arena for functions that return
        non-heap types and have no user function calls."""
        if fn.name == "main":
            return False
        rk = fn.return_type.kind
        non_heap = {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL, TypeKind.VOID, TypeKind.CHAR}
        if rk not in non_heap:
            return False
        for bb in fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, Call):
                    fn_name = inst.fn_name.lstrip("%")
                    if not fn_name.startswith("__mn_") and not fn_name.startswith("__new_"):
                        if fn_name not in (
                            "print",
                            "println",
                            "len",
                            "str",
                            "toString",
                            "int",
                            "float",
                            "ord",
                            "chr",
                            "Some",
                            "Ok",
                            "Err",
                            "join",
                        ):
                            return False
        return True

    # v4.146.0 E2: scalar types eligible for `noundef` parameter attribute.
    # Mapanare has no undef-valued scalar paths (it uses Option types),
    # so `noundef` is sound for all Int / Bool / Float parameters.
    _NOUNDEF_TYPES = frozenset({I64, I1, DBL})

    def _compute_pure_fns(self, functions: list["MIRFunction"]) -> set[str]:
        """Fixed-point computation of pure functions in a module.

        A function is pure (``memory(none)``) if:
        1. All parameters and return type are scalars (i64/i1/double) — no
           pointers, structs, or sret.  This guarantees the function cannot
           read or write caller-visible memory.
        2. Every call in its body goes to itself (self-recursion) or to
           another function already proven pure.

        Uses Kildall-style iteration — converges in O(depth) rounds where
        depth is the longest call chain between pure functions.
        """
        scalars = {TypeKind.INT, TypeKind.FLOAT, TypeKind.BOOL}
        # Pre-filter: only functions with all-scalar signatures are candidates
        candidates: set[str] = set()
        for fn in functions:
            if fn.name == "main" or fn.is_async or not fn.blocks:
                continue
            if fn.return_type.kind not in scalars and fn.return_type.kind != TypeKind.VOID:
                continue
            if all(p.ty.kind in scalars for p in fn.params):
                candidates.add(fn.name)

        pure: set[str] = set()
        changed = True
        while changed:
            changed = False
            for fn in functions:
                if fn.name not in candidates or fn.name in pure:
                    continue
                is_pure = True
                for bb in fn.blocks:
                    for inst in bb.instructions:
                        if isinstance(inst, Call):
                            callee = inst.fn_name.lstrip("%")
                            if callee == fn.name:
                                continue  # self-recursion OK
                            if callee in pure:
                                continue  # call to known-pure OK
                            is_pure = False
                            break
                        # v5.13.1 At.1: Assert lowers to printf + @exit(1) in
                        # the fail block — observable side effects. Pre-v5.13.1
                        # this was latent because no `@test` runner ever called
                        # an assert-bearing fn, so the dead-code-elimination
                        # consequence of the bogus memory(none) attribute never
                        # surfaced. Per-test main wrappers (At.1) call test
                        # functions directly, exposing the gap.
                        if isinstance(inst, Assert):
                            is_pure = False
                            break
                    if not is_pure:
                        break
                if is_pure:
                    pure.add(fn.name)
                    changed = True
        return pure

    # ── function emission ───────────────────────────────────────────
    def _emit_fn(self, fn: MIRFunction) -> str:
        self._c = 0
        self._alloc = {}
        self._ent = []
        self._blk = {}
        self._cb = ""
        self._dphi = []
        self._lroots = {}
        self._fn = fn
        self._current_subprogram_id = self._debug_subprogram_ids.get(fn.name, -1)
        self._local_strings = []
        self._str_slots = {}
        self._last_tracked_str_slot = None
        self._local_closures = []
        self._local_boxed = []
        self._boxed_slots = {}
        self._last_tracked_boxed_slot = None
        self._list_vars = []
        self._map_vars = []
        self._signal_vars = []
        self._stream_vars = []
        self._tensor_vars = []
        self._loop_depth = 0
        # v5.4.4 — reset parallel SSA-source arrays + moved_locals set.
        self._local_strings_source = []
        self._local_boxed_source = []
        self._list_vars_source = []
        self._moved_locals = set()

        # Per-function arena — disabled: text emitter never routes allocations
        # through mn_arena_alloc, so create/destroy was pure overhead.
        self._arena_ptr: str | None = None

        # Determine which params use byref and if return uses sret.
        # v4.149.0 E5 / ABI.1: return-type sret decision uses per-target
        # ABI classifier (classify_return) instead of the blanket 64-byte
        # _use_byref threshold.  Argument byref still uses _use_byref.
        rt_orig = self._rty(fn.return_type)
        self._fn_use_sret = self._use_sret(rt_orig) and fn.name != "main"
        self._fn_sret_ty = rt_orig if self._fn_use_sret else ""
        self._fn_is_async: bool = fn.is_async  # v4.92.0: track for real suspend
        # v4.145.0 E1: unified return block for inline-enum returns.
        # Prevents aggregate PHI after inlining → enables LLVM to merge
        # redundant switches (make_shape dispatch + area dispatch → one switch).
        self._fn_unified_ret = False
        self._fn_unified_ret_ty = ""
        if (
            not self._fn_use_sret
            and fn.name != "main"
            and not fn.is_async
            and rt_orig != VOID
            and fn.return_type
            and fn.return_type.type_info
        ):
            ename = fn.return_type.type_info.name
            if ename and self._enum_inline.get(ename, 0) > 0:
                self._fn_unified_ret = True
                self._fn_unified_ret_ty = rt_orig
        self._fn_byref_params: set[str] = set()
        for p in fn.params:
            ty = self._rty(p.ty)
            if self._use_byref(ty):
                self._fn_byref_params.add(p.name)

        # sret alloca (caller provides it, but we name it here for the callee)
        if self._fn_use_sret:
            self._sret_ptr = "%__sret__"

        # v4.145.0 E1: unified-ret alloca
        if self._fn_unified_ret:
            self._ent.append(f"  %__ret_alloca = alloca {self._fn_unified_ret_ty}, align 8")
            self._ent.append(
                f"  store {self._fn_unified_ret_ty} zeroinitializer, ptr %__ret_alloca"
            )

        # param allocas
        for p in fn.params:
            ty = self._rty(p.ty)
            s = self._san(p.name)
            a = f"%{s}.addr"
            self._alloc[p.name] = (a, ty)
            self._alloc[f"%{p.name}"] = (a, ty)
            if p.name in self._fn_byref_params:
                # Byref param: the pointer IS the alloca — no separate alloca needed.
                # We still create a local alloca and memcpy into it so the callee
                # has its own mutable copy (value semantics).
                self._ent.append(f"  {a} = alloca {ty}, align 8")
                self._ent.append(f"  store {ty} zeroinitializer, ptr {a}")
            else:
                self._ent.append(f"  {a} = alloca {ty}, align 8")

        # Track struct parameters' list fields for drop glue cleanup.
        # When a struct param is copied and the copy's list is pushed to,
        # COW detach creates a new buffer.  The old buffer (in the param)
        # must be freed to prevent memory exhaustion on large compilations.
        self._param_list_fields: list[tuple[str, str, int]] = []
        for p in fn.params:
            if p.ty and p.ty.kind == TypeKind.STRUCT and p.ty.type_info:
                sn = self._res_struct(p.ty.type_info.name)
                if sn in self._structs:
                    sty = self._struct_ty.get(sn, "")
                    if sty:
                        a, _ = self._alloc.get(p.name, ("", ""))
                        if a:
                            for idx, (_, ft) in enumerate(self._structs[sn]):
                                if ft == LIST:
                                    self._param_list_fields.append((a, sty, idx))

        # phi allocas
        for bb in fn.blocks:
            for inst in bb.instructions:
                if not isinstance(inst, Phi):
                    break
                ty = self._rty(inst.dest.ty)
                if ty == VOID:
                    ty = PTR
                s = self._san(inst.dest.name)
                a = f"%phi.{s}"
                self._alloc[inst.dest.name] = (a, ty)
                self._ent.append(f"  {a} = alloca {ty}, align 8")
                self._ent.append(f"  store {ty} {_zero(ty)}, ptr {a}")
                self._dphi.append((a, ty, inst.incoming))

        # Pre-allocate values used before definition (cross-block forward refs).
        # Without this, _get for a value defined in a later block returns
        # zeroinitializer instead of emitting a load instruction.
        defined: set[str] = set()
        used_before_def: set[str] = set()
        for bb in fn.blocks:
            for inst in bb.instructions:
                # Collect uses
                for attr in (
                    "src",
                    "val",
                    "signal",
                    "enum_val",
                    "initial_val",
                    "operand",
                    "lhs",
                    "rhs",
                    "cond",
                    "tag",
                    "obj",
                    "list_val",
                    "element",
                    "index",
                    "closure",
                    "env",
                    "agent",
                    "source",
                    "subscriber",
                ):
                    v = getattr(inst, attr, None)
                    if isinstance(v, Value) and v.name and v.name not in defined:
                        used_before_def.add(v.name)
                for attr in ("args", "parts", "elements", "payload", "captures", "deps"):
                    vs = getattr(inst, attr, None)
                    if isinstance(vs, list):
                        for v in vs:
                            if isinstance(v, Value) and v.name and v.name not in defined:
                                used_before_def.add(v.name)
                # Collect defs
                dest = getattr(inst, "dest", None)
                if dest is not None and hasattr(dest, "name") and dest.name:
                    defined.add(dest.name)
        # Create allocas for forward-referenced values
        pre_idx = 0
        for nm in used_before_def:
            if nm not in self._alloc and not nm.startswith("%void"):
                # Find the type from any instruction that defines this value
                ty = PTR  # fallback
                for bb2 in fn.blocks:
                    for inst2 in bb2.instructions:
                        d2 = getattr(inst2, "dest", None)
                        if d2 is not None and hasattr(d2, "name") and d2.name == nm:
                            ty = self._rty(d2.ty) if hasattr(d2, "ty") else PTR
                            if ty == VOID:
                                ty = PTR
                            break
                    else:
                        continue
                    break
                a = f"%pre.{self._san(nm)}.{pre_idx}"
                pre_idx += 1
                self._alloc[nm] = (a, ty)
                self._ent.append(f"  {a} = alloca {ty}, align 8")
                self._ent.append(f"  store {ty} {_zero(ty)}, ptr {a}")

        # emit dbg.declare for parameters (v4.65.0)
        if self._debug_enabled and self._current_subprogram_id >= 0:
            for idx, p in enumerate(fn.params, 1):
                sname = self._san(p.name)
                alloca_ref = None
                for k in (p.name, sname, f"%{sname}"):
                    if k in self._alloc:
                        alloca_ref = self._alloc[k][0]
                        break
                if alloca_ref:
                    ty_id = self._get_debug_type_for_mir(p.ty)
                    var_id = self._emit_debug_local_variable(
                        p.name,
                        ty_id,
                        self._current_subprogram_id,
                        fn.source_line or 1,
                        arg_index=idx,
                    )
                    file_id = next(iter(self._debug_file_table.values()), 0)
                    loc_id = self._get_debug_location(
                        file_id, fn.source_line or 1, 0, self._current_subprogram_id
                    )
                    self._ent.append(
                        f"  call void @llvm.dbg.declare(metadata ptr {alloca_ref}, "
                        f"metadata !{var_id}, metadata !DIExpression()), !dbg !{loc_id}"
                    )

        # emit blocks
        for bb in fn.blocks:
            self._cb = bb.label
            self._blk[bb.label] = []
            # v5.4.3 — track loop-body nesting so _track_string /
            # _track_boxed / _track_closure prepend a free-before-store
            # when their call site is inside a for/while body.
            bumped = bb.label.startswith(("for_body", "while_body", "mapfor_body"))
            if bumped:
                self._loop_depth += 1
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    continue
                self._current_span = getattr(inst, "span", None)
                h = self._disp.get(type(inst))
                if h:
                    h(inst)
            if bumped:
                self._loop_depth -= 1

        # deferred phi stores
        for addr, ty, incoming in self._dphi:
            for plbl, val in incoming:
                if plbl not in self._blk:
                    continue
                lines = self._blk[plbl]
                ins: list[str] = []
                done = False
                for k in (val.name, val.name.lstrip("%"), "%" + val.name.lstrip("%")):
                    if k in self._alloc:
                        sa, st = self._alloc[k]
                        t = self._f("ps")
                        ins.append(f"  {t} = load {st}, ptr {sa}")
                        if st == ty:
                            ins.append(f"  store {ty} {t}, ptr {addr}")
                        else:
                            cv = self._f("pv")
                            ins.append(f"  {cv} = load {ty}, ptr {sa}")
                            ins.append(f"  store {ty} {cv}, ptr {addr}")
                        done = True
                        break
                if not done:
                    ins.append(f"  store {ty} {_zero(ty)}, ptr {addr}")
                # Insert before the terminator (last line)
                pos = max(len(lines) - 1, 0)
                for idx_ins, ln in enumerate(ins):
                    lines.insert(pos + idx_ins, ln)

        # ensure terminated
        for bb in fn.blocks:
            ls = self._blk[bb.label]
            if not ls or not self._is_term(ls[-1]):
                if self._fn_use_sret:
                    ls.append(
                        f"  store {self._fn_sret_ty} zeroinitializer," f" ptr {self._sret_ptr}"
                    )
                    ls.append("  ret void")
                elif self._fn_unified_ret:
                    urt = self._fn_unified_ret_ty
                    ls.append(f"  store {urt} zeroinitializer, ptr %__ret_alloca")
                    ls.append("  br label %__unified_ret")
                else:
                    rt = self._rty(fn.return_type)
                    if rt == VOID:
                        ls.append("  ret void")
                    else:
                        ls.append(f"  ret {rt} {_zero(rt)}")

        # assemble
        rt = self._rty(fn.return_type)
        # main must return i64 for C ABI compatibility
        if fn.name == "main" and rt == VOID:
            rt = I64
            # patch any "ret void" to "ret i64 0" in all blocks
            # and insert program epilogue (intern table cleanup)
            self._ensure("__mn_intern_destroy", VOID, [])
            # v4.92.0: coroutine scheduler init at main entry
            sched_init = ""
            sched_destroy = ""
            if getattr(self, "_module_has_async", False):
                sched_init = (
                    "  call void @__mn_coro_scheduler_init(i32 0)\n"  # 0 = auto-detect cores
                )
                sched_destroy = "  call void @__mn_coro_scheduler_destroy()\n"
            if sched_init:
                # Add scheduler init as first instruction in entry block
                first_lbl = fn.blocks[0].label if fn.blocks else None
                if first_lbl and first_lbl in self._blk:
                    self._blk[first_lbl].insert(0, sched_init.rstrip())
            for lbl in self._blk:
                for idx, ln in enumerate(self._blk[lbl]):
                    stripped = ln.strip()
                    if stripped == "ret void" or stripped.startswith("ret void, !dbg"):
                        # Preserve any !dbg attachment
                        dbg = ""
                        if ", !dbg" in stripped:
                            dbg = ", " + stripped.split(", ", 1)[1]
                        self._blk[lbl][idx] = (
                            f"{sched_destroy}"
                            f"  call void @__mn_intern_destroy(){dbg}\n  ret i64 0{dbg}"
                        )

        # Build param list with byref/sret ABI adjustments
        param_parts: list[str] = []
        if self._fn_use_sret:
            # v4.84.0: noalias on sret — the caller-allocated return slot
            # does not alias any other pointer the function can observe.
            param_parts.append(f"ptr noalias sret({self._fn_sret_ty}) {self._sret_ptr}")
        for p in fn.params:
            ty = self._rty(p.ty)
            s = self._san(p.name)
            if p.name in self._fn_byref_params:
                # v4.147.0 E3: emit `noalias` on byref pointer params that
                # passed escape analysis.  Only pointer-typed params can carry
                # `noalias` in LLVM IR.
                na = " noalias" if "noalias_ok" in p.attrs else ""
                param_parts.append(f"ptr{na} %{s}.byref")
            else:
                # v4.146.0 E2: `noundef` on scalar parameters.  Mapanare has
                # no undef-valued scalar paths (Option types cover nullable),
                # so this is sound for Int / Bool / Float.
                nd = " noundef" if ty in self._NOUNDEF_TYPES else ""
                # v4.147.0 E3: `noalias` on direct ptr params (e.g. closure
                # env pointers) that passed escape analysis.
                na = " noalias" if (ty == PTR and "noalias_ok" in p.attrs) else ""
                param_parts.append(f"{ty}{na}{nd} %{s}")
        ps = ", ".join(param_parts)
        abi_rt = "void" if self._fn_use_sret else rt

        lk = "internal " if (not fn.is_public and fn.name != "main") else ""
        # v4.83.0: nounwind on all user-defined functions — Mapanare has no
        # exception mechanism, so LLVM can assume no unwind paths.
        # v4.84.0: willreturn — all Mapanare functions terminate (infinite
        # recursion/loops are UB). This enables LICM to hoist calls out
        # of loops and DSE to eliminate dead stores before calls.
        # v4.146.0 E2: pure functions additionally get `memory(none) nofree
        # nosync` — tells LLVM no externally-visible memory effects, enabling
        # earlier interprocedural optimizations.  Purity is precomputed via
        # fixed-point iteration in ``_compute_pure_fns``.
        fn_attrs = " nounwind willreturn"
        if fn.name in self._pure_fns:
            fn_attrs = " nofree nosync nounwind willreturn memory(none)"
        # v4.70.0: presplitcoroutine attribute for async functions
        coro_attr = " presplitcoroutine" if fn.is_async else ""
        dbg_ref = ""
        if self._debug_enabled and fn.name in self._debug_subprogram_ids:
            dbg_ref = f" !dbg !{self._debug_subprogram_ids[fn.name]}"

        if fn.is_async:
            # v4.70.0: Async function — emit coroutine prelude wrapper.
            # The function returns ptr (the Future handle) regardless of the
            # declared return type. The actual return value goes into the Future.
            out: list[str] = [
                f"define {lk}ptr @{fn.name}({ps}){fn_attrs}{coro_attr}{dbg_ref} {{",
                "coro.entry:",
                "  %coro.id = call token @llvm.coro.id(i32 0, ptr null, ptr null, ptr null)",
                "  %coro.size = call i64 @llvm.coro.size.i64()",
                "  %coro.mem = call ptr @malloc(i64 %coro.size)",
                "  %coro.hdl = call ptr @llvm.coro.begin(token %coro.id, ptr %coro.mem)",
                "  ; Allocate Future struct: {i8 state, ptr payload}",
                "  %future = call ptr @malloc(i64 16)",
                "  store i8 0, ptr %future",
                "  %future.hdl.slot = getelementptr inbounds {i8, ptr}, ptr %future, i32 0, i32 1",
                "  store ptr %coro.hdl, ptr %future.hdl.slot",
                "  ; Initial suspend",
                "  %coro.init.save = call token @llvm.coro.save(ptr %coro.hdl)",
                "  %coro.init.susp = call i8 @llvm.coro.suspend(token %coro.init.save, i1 false)",
                "  switch i8 %coro.init.susp, label %coro.ret [",
                "    i8 0, label %pre_entry",
                "    i8 1, label %coro.cleanup",
                "  ]",
                "",
                "pre_entry:",
            ]
            out.extend(self._ent)
            for p in fn.params:
                ty = self._rty(p.ty)
                s = self._san(p.name)
                if p.name in self._fn_byref_params:
                    tmp = self._f("bp")
                    out.append(f"  {tmp} = load {ty}, ptr %{s}.byref")
                    out.append(f"  store {ty} {tmp}, ptr %{s}.addr")
                else:
                    out.append(f"  store {ty} %{s}, ptr %{s}.addr")
            if fn.blocks:
                out.append(f"  br label %{fn.blocks[0].label}")
            mir_labels = {bb.label for bb in fn.blocks}
            for bb in fn.blocks:
                out.append(f"{bb.label}:")
                # Rewrite "ret <ty> <val>" to store into Future + final suspend
                rewritten = []
                for line in self._blk[bb.label]:
                    stripped = line.strip()
                    if stripped.startswith("ret ") and not stripped.startswith("ret void"):
                        # Extract the return value and type
                        parts = stripped.split(" ", 2)
                        if len(parts) >= 3:
                            ret_ty = parts[1]
                            ret_val = parts[2].split(",")[0]  # strip !dbg suffix
                            t = self._f("ret.box")
                            rewritten.append(f"  {t} = call ptr @malloc(i64 8)")
                            rewritten.append(f"  store {ret_ty} {ret_val}, ptr {t}")
                            rvs = self._f("ret.val.slot")
                            rewritten.append("  store i8 1, ptr %future")
                            rewritten.append(
                                f"  {rvs} = getelementptr inbounds {{i8, ptr}}, ptr %future, i32 0, i32 1"  # noqa: E501
                            )
                            rewritten.append(f"  store ptr {t}, ptr {rvs}")
                            rewritten.append("  br label %coro.final")
                        else:
                            rewritten.append(line)
                    elif stripped == "ret void":
                        rewritten.append("  store i8 1, ptr %future")
                        rewritten.append("  br label %coro.final")
                    else:
                        rewritten.append(line)
                out.extend(rewritten)
            # Emit drop glue + await blocks (also rewrite ret instructions)
            for lbl, lines in self._blk.items():
                if lbl not in mir_labels:
                    out.append(f"{lbl}:")
                    rewritten = []
                    for line in lines:
                        stripped = line.strip()
                        if stripped.startswith("ret ") and not stripped.startswith("ret void"):
                            parts = stripped.split(" ", 2)
                            if len(parts) >= 3:
                                ret_ty = parts[1]
                                ret_val = parts[2].split(",")[0]
                                t = self._f("ret.box")
                                rewritten.append(f"  {t} = call ptr @malloc(i64 8)")
                                rewritten.append(f"  store {ret_ty} {ret_val}, ptr {t}")
                                rvs = self._f("ret.val.slot")
                                rewritten.append("  store i8 1, ptr %future")
                                rewritten.append(
                                    f"  {rvs} = getelementptr inbounds {{i8, ptr}},"
                                    f" ptr %future, i32 0, i32 1"
                                )
                                rewritten.append(f"  store ptr {t}, ptr {rvs}")
                                rewritten.append("  br label %coro.final")
                            else:
                                rewritten.append(line)
                        elif stripped == "ret void":
                            rewritten.append("  store i8 1, ptr %future")
                            rewritten.append("  br label %coro.final")
                        else:
                            rewritten.append(line)
                    out.extend(rewritten)
            # Coroutine epilogue blocks
            out.append("coro.final:")
            out.append("  %coro.final.save = call token @llvm.coro.save(ptr %coro.hdl)")
            out.append(
                "  %coro.final.susp = call i8 @llvm.coro.suspend(token %coro.final.save, i1 true)"
            )
            out.append("  switch i8 %coro.final.susp, label %coro.ret [")
            out.append("    i8 0, label %coro.ret")
            out.append("    i8 1, label %coro.cleanup")
            out.append("  ]")
            out.append("coro.cleanup:")
            out.append("  %coro.mem.free = call ptr @llvm.coro.free(token %coro.id, ptr %coro.hdl)")
            out.append("  call void @free(ptr %coro.mem.free)")
            out.append("  br label %coro.ret")
            out.append("coro.ret:")
            out.append("  call i1 @llvm.coro.end(ptr %coro.hdl, i1 false, token none)")
            out.append("  ret ptr %future")
            out.append("}")
        else:
            # Regular (non-async) function emission
            # v4.146.0 E2: `noundef` on scalar return types — Mapanare
            # functions always return well-defined values (no undef/poison).
            ret_nd = "noundef " if (abi_rt in self._NOUNDEF_TYPES and fn.name != "main") else ""
            out = [
                f"define {lk}{ret_nd}{abi_rt} @{fn.name}({ps}){fn_attrs}{dbg_ref} {{",
                "pre_entry:",
            ]
            out.extend(self._ent)
            for p in fn.params:
                ty = self._rty(p.ty)
                s = self._san(p.name)
                if p.name in self._fn_byref_params:
                    tmp = self._f("bp")
                    out.append(f"  {tmp} = load {ty}, ptr %{s}.byref")
                    out.append(f"  store {ty} {tmp}, ptr %{s}.addr")
                else:
                    out.append(f"  store {ty} %{s}, ptr %{s}.addr")
            if fn.blocks:
                out.append(f"  br label %{fn.blocks[0].label}")
            mir_labels = {bb.label for bb in fn.blocks}
            for bb in fn.blocks:
                out.append(f"{bb.label}:")
                out.extend(self._blk[bb.label])
            for lbl, lines in self._blk.items():
                if lbl not in mir_labels:
                    out.append(f"{lbl}:")
                    out.extend(lines)
            # v4.145.0 E1: emit unified return block
            if self._fn_unified_ret:
                urt = self._fn_unified_ret_ty
                out.append("__unified_ret:")
                out.append(f"  %__retval = load {urt}, ptr %__ret_alloca")
                out.append(f"  ret {urt} %__retval")
            out.append("}")
        out.append("")
        return "\n".join(out)

    @staticmethod
    def _is_term(line: str) -> bool:
        s = line.split(", !dbg")[0].strip() if ", !dbg" in line else line.strip()
        return (
            s.startswith("ret ")
            or s.startswith("br ")
            or s.startswith("switch ")
            or s == "unreachable"
            or s == "ret void"
        )

    # ── instruction emitters ────────────────────────────────────────

    # --- Const ---
    def _do_const(self, i: Const) -> None:
        k = i.ty.kind
        v = i.value
        if k == TypeKind.INT:
            self._put(i.dest, str(int(v)) if v is not None else "0", I64)
        elif k == TypeKind.FLOAT:
            fv = float(v) if v is not None else 0.0
            bits = pystruct.unpack("<Q", pystruct.pack("<d", fv))[0]
            self._put(i.dest, f"0x{bits:016X}" if fv != 0.0 else "0.000000e+00", DBL)
        elif k == TypeKind.BOOL:
            self._put(i.dest, "1" if v else "0", I1)
        elif k == TypeKind.CHAR:
            self._put(i.dest, str(ord(v)) if isinstance(v, str) and v else "0", I8)
        elif k == TypeKind.STRING:
            sv, st = self._mkstr(str(v) if v is not None else "")
            self._put(i.dest, sv, st)
        elif k == TypeKind.FN and isinstance(v, str):
            if v in self._sigs:
                t = f"@{v}"  # function is already ptr
                self._put(i.dest, t, PTR)
            else:
                self._put(i.dest, "null", PTR)
        elif k == TypeKind.VOID:
            self._put(i.dest, "0", I1)
        elif v is None:
            ty = self._rty(i.ty)
            self._put(i.dest, _zero(ty), ty)
        else:
            ty = self._rty(i.ty)
            self._put(i.dest, str(v), ty)

    # --- Copy ---
    def _do_copy(self, i: Copy) -> None:
        v, t = self._get(i.src)
        self._put(i.dest, v, t)
        # Track list aliases: when a list is copied, the dest should see
        # future push write-backs to the source. Record the alias so
        # _do_list_push can write back to all copies.
        if t == LIST:
            root = self._lroots.get(i.src.name, i.src.name)
            self._lroots[i.dest.name] = root
            # v4.131.0 Sh.2 fix: only track dest as an owner when we are
            # transferring ownership from src. If src is not tracked (it
            # came from a field-get, enum-payload extract, or function
            # parameter — all aliased sources), then dest is also an
            # alias; it must not be tracked for drop glue. If dest was
            # previously tracked (e.g., `let mut x: List = []` followed
            # by `x = fe.param_types`), untrack it to prevent UAF on the
            # aliased buffer. The original `[]` buffer leaks, but UAF is
            # corrupted-memory, not a leak. See docs/roadmap/v4/v4.131.0.
            if i.src.name in self._list_vars:
                # Ownership transfer: src was an owner, dest becomes the owner
                self._list_vars.remove(i.src.name)
                self._track_container(i.dest.name, "list")
            else:
                # src is an alias; dest must not own this buffer either
                if i.dest.name in self._list_vars:
                    self._list_vars.remove(i.dest.name)
        # v4.132.0 Sh.2 String-residual: mirror v4.131.0 LIST fix for STR.
        # Sh.2 on Strings: a String extracted from a struct field or
        # concat'd into a local then stored into an Instruction enum
        # payload gets freed by drop glue on the local, invalidating
        # every other alias the caller's data structure holds. Fix:
        # only propagate tracking when src was a tracked owner. If src
        # is an alias (field-get, enum-payload, param), dest must not
        # be tracked either. See docs/roadmap/v4/v4.132.0.
        if t == STR:
            src_str_tracked = i.src.name in self._str_slots
            if src_str_tracked:
                # Ownership transfer: remap tracking slot src → dest
                slot = self._str_slots.pop(i.src.name)
                self._str_slots[i.dest.name] = slot
            else:
                # src is an alias; untrack dest if it was previously an owner
                if i.dest.name in self._str_slots:
                    self._str_slots.pop(i.dest.name)
        # v4.140.0 SE.1: mirror Sh.2 ownership-transfer for MAP/SIGNAL/STREAM.
        # Same shape as LIST (v4.131.0): only track dest as owner when src was
        # already tracked; if src is an alias, untrack dest to prevent UAF.
        sk = i.src.ty.kind if i.src.ty else TypeKind.UNKNOWN
        if sk == TypeKind.MAP:
            if i.src.name in self._map_vars:
                self._map_vars.remove(i.src.name)
                self._track_container(i.dest.name, "map")
            else:
                if i.dest.name in self._map_vars:
                    self._map_vars.remove(i.dest.name)
        elif sk == TypeKind.SIGNAL:
            if i.src.name in self._signal_vars:
                self._signal_vars.remove(i.src.name)
                self._track_container(i.dest.name, "signal")
            else:
                if i.dest.name in self._signal_vars:
                    self._signal_vars.remove(i.dest.name)
        elif sk == TypeKind.STREAM:
            if i.src.name in self._stream_vars:
                self._stream_vars.remove(i.src.name)
                self._track_container(i.dest.name, "stream")
            else:
                if i.dest.name in self._stream_vars:
                    self._stream_vars.remove(i.dest.name)
        # List fields in struct copies share the same buffer (bitwise copy,
        # no refcount increment).  This is safe because mn_list_grow always
        # allocates a new buffer (never reallocs), so the shared old buffer
        # stays valid for any aliased copies.  Cloning all list fields on
        # every struct copy was causing O(n²) memory blowup (390K clones
        # for 575 lines of source, each triggering COW detach + allocation).

    def _clone_list_fields(self, dest: Value, sn: str) -> None:
        """After a struct copy, deep-clone any List fields in the destination.

        Without this, the bitwise copy shares the same heap pointer for each
        List field.  A realloc in one copy would free the other's data buffer,
        leading to double-free / use-after-free.

        Also handles nested lists: if a list field's elements are structs
        that contain list fields, uses __mn_list_deep_clone to recursively
        clone those inner lists too (prevents nested copy aliasing).
        """
        fields = self._structs[sn]
        # Quick check: does this struct actually have list fields?
        if not any(ft == LIST for _, ft in fields):
            return
        sty = self._struct_ty[sn]
        pi = self._get_ptr(dest)
        if pi is None:
            return
        addr, aty = pi
        # Only clone when the alloca was created with a matching struct layout.
        # If the alloca type is smaller (e.g. PTR / i8*), GEP would overrun.
        if aty != sty:
            if _tsz(aty) < _tsz(sty):
                return
            # opaque ptr: no bitcast needed, addr is already ptr
        self._ensure("__mn_list_clone", LIST, ["ptr"])
        for idx, (fn, ft) in enumerate(fields):
            if ft == LIST:
                fp = self._f("clf")
                self._L(f"{fp} = getelementptr inbounds {sty}, ptr {addr}, i32 0, i32 {idx}")
                cloned = self._rt("__mn_list_clone", LIST, ["ptr"], [(fp, "ptr")])
                self._L(f"store {LIST} {cloned}, ptr {fp}")

    def _struct_name_for_llvm_type(self, llvm_ty: str) -> str | None:
        """Find the struct name whose LLVM type matches."""
        for sn, sty in self._struct_ty.items():
            if sty == llvm_ty:
                return sn
        return None

    def _clone_nested_struct_lists(self, ptr: str, sty: str, sn: str) -> None:
        """Clone list fields inside a struct-typed field (e.g., MIRModule inside LowerState)."""
        fields = self._structs[sn]
        self._ensure("__mn_list_clone", LIST, ["ptr"])
        for idx, (_, ft) in enumerate(fields):
            if ft != LIST:
                continue
            fp = self._f("nclf")
            self._L(f"{fp} = getelementptr inbounds {sty}, ptr {ptr}, i32 0, i32 {idx}")
            cloned = self._rt("__mn_list_clone", LIST, ["ptr"], [(fp, "ptr")])
            self._L(f"store {LIST} {cloned}, ptr {fp}")

    def _find_nested_list_offsets(self, parent_sn: str, list_field_idx: int) -> list[int]:
        """Find byte offsets of List fields within a list's element type.

        Given a struct field that is a List, determine if the list's elements
        are structs with nested list fields. Returns byte offsets of those
        nested list fields within each element, or empty list if none.
        """
        # We need to know the element type of this list field.
        # The element type info comes from the MIR type annotations.
        # Check if this struct field's MIR type has List<StructType> args.
        mir_fields = self._struct_mir_types.get(parent_sn, {})
        mir_ty = mir_fields.get(list_field_idx)
        if not mir_ty or not hasattr(mir_ty, "type_info"):
            return []
        ti = mir_ty.type_info
        if not ti or not ti.args:
            return []
        # Get the element type
        elem_ti = ti.args[0] if ti.args else None
        if not elem_ti:
            return []
        elem_name = elem_ti.name if hasattr(elem_ti, "name") else ""
        if not elem_name or elem_name not in self._structs:
            return []
        # Found the element struct — find its list field offsets
        elem_fields = self._structs[elem_name]
        offsets: list[int] = []
        running_offset = 0
        for _, eft in elem_fields:
            if eft == LIST:
                offsets.append(running_offset)
            running_offset += _tsz(eft)
        return offsets

    def _emit_offset_array(self, offsets: list[int]) -> str:
        """Emit a global constant array of i64 offsets and return its name."""
        name = f"@.list_offsets.{self._c}"
        self._c += 1
        vals = ", ".join(f"i64 {o}" for o in offsets)
        self._globals.append(f"{name} = private constant [{len(offsets)} x i64] [{vals}]")
        gep = self._f("offp")
        self._L(
            f"{gep} = getelementptr inbounds [{len(offsets)} x i64], " f"ptr {name}, i64 0, i64 0"
        )
        return gep

    # --- Cast ---
    def _do_cast(self, i: Cast) -> None:
        sv, st = self._get(i.src)
        sk, tk = i.src.ty.kind, i.target_type.kind
        self._san(i.dest.name)
        if sk == TypeKind.INT and tk == TypeKind.FLOAT:
            r = self._f("cf")
            self._L(f"{r} = sitofp i64 {sv} to double")
            self._put(i.dest, r, DBL)
        elif sk == TypeKind.FLOAT and tk == TypeKind.INT:
            r = self._f("ci")
            self._L(f"{r} = fptosi double {sv} to i64")
            self._put(i.dest, r, I64)
        elif sk == TypeKind.INT and tk == TypeKind.BOOL:
            r = self._f("cb")
            sv = self._coerce(sv, st, I64) if st != I64 else sv
            self._L(f"{r} = icmp ne i64 {sv}, 0")
            self._put(i.dest, r, I1)
        elif sk == TypeKind.BOOL and tk == TypeKind.INT:
            r = self._f("ci")
            sv = self._coerce(sv, st, I1) if st != I1 else sv
            self._L(f"{r} = zext i1 {sv} to i64")
            self._put(i.dest, r, I64)
        elif sk == TypeKind.INT and tk == TypeKind.STRING:
            r = self._rt("__mn_str_from_int", STR, [I64], [(sv, st)])
            self._track_string(r)
            self._put(i.dest, r, STR)
        elif sk == TypeKind.FLOAT and tk == TypeKind.STRING:
            r = self._rt("__mn_str_from_float", STR, [DBL], [(sv, st)])
            self._track_string(r)
            self._put(i.dest, r, STR)
        elif sk == TypeKind.BOOL and tk == TypeKind.STRING:
            bv = self._coerce(sv, st, I64) if st != I64 else sv
            r = self._rt("__mn_str_from_bool", STR, [I64], [(bv, I64)])
            self._track_string(r)
            self._put(i.dest, r, STR)
        elif sk == TypeKind.INT and tk == TypeKind.CHAR:
            r = self._f("cc")
            sv = self._coerce(sv, st, I64) if st != I64 else sv
            self._L(f"{r} = trunc i64 {sv} to i8")
            self._put(i.dest, r, I8)
        elif sk == TypeKind.CHAR and tk == TypeKind.INT:
            r = self._f("ci")
            sv = self._coerce(sv, st, I8) if st != I8 else sv
            self._L(f"{r} = zext i8 {sv} to i64")
            self._put(i.dest, r, I64)
        else:
            tt = self._rty(i.target_type)
            if st == tt:
                self._put(i.dest, sv, tt)
            else:
                self._put(i.dest, self._coerce(sv, st, tt), tt)

    # --- BinOp ---
    def _do_binop(self, i: BinOp) -> None:  # noqa: C901
        lv, lt = self._get(i.lhs)
        rv, rt_ = self._get(i.rhs)
        lk = i.lhs.ty.kind
        op = i.op

        # detect string from LLVM type
        if lk == TypeKind.UNKNOWN and lt == STR:
            lk = TypeKind.STRING
        if lk == TypeKind.UNKNOWN and rt_ == STR:
            lk = TypeKind.STRING

        # String ops
        if lk == TypeKind.STRING:
            lv = self._coerce(lv, lt, STR) if lt != STR else lv
            rv = self._coerce(rv, rt_, STR) if rt_ != STR else rv
            if op == BinOpKind.ADD:
                r = self._rt("__mn_str_concat", STR, [STR, STR], [(lv, STR), (rv, STR)])
                self._track_string(r)
                self._put(i.dest, r, STR)
            elif op in (BinOpKind.EQ, BinOpKind.NE):
                c = self._rt("__mn_str_eq", I64, [STR, STR], [(lv, STR), (rv, STR)])
                r = self._f("sc")
                cmp = "ne" if op == BinOpKind.EQ else "eq"
                self._L(f"{r} = icmp {cmp} i64 {c}, 0")
                self._put(i.dest, r, I1)
            elif op in (BinOpKind.LT, BinOpKind.GT, BinOpKind.LE, BinOpKind.GE):
                c = self._rt("__mn_str_cmp", I64, [STR, STR], [(lv, STR), (rv, STR)])
                m = {
                    BinOpKind.LT: "slt",
                    BinOpKind.GT: "sgt",
                    BinOpKind.LE: "sle",
                    BinOpKind.GE: "sge",
                }
                r = self._f("sc")
                self._L(f"{r} = icmp {m[op]} i64 {c}, 0")
                self._put(i.dest, r, I1)
            else:
                self._put(i.dest, "0", I64)
            return

        # List concat
        if lk == TypeKind.LIST and op == BinOpKind.ADD:
            lv = self._coerce(lv, lt, LIST) if lt != LIST else lv
            rv = self._coerce(rv, rt_, LIST) if rt_ != LIST else rv
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {lv}, ptr {la}")
            ra = self._alloca(LIST, "rp")
            self._L(f"store {LIST} {rv}, ptr {ra}")
            r = self._rt(
                "__mn_list_concat",
                LIST,
                ["ptr", "ptr"],
                [(la, "ptr"), (ra, "ptr")],
            )
            self._track_container(i.dest.name, "list")
            self._put(i.dest, r, LIST)
            return

        # Float ops
        if lk == TypeKind.FLOAT:
            lv = self._coerce(lv, lt, DBL) if lt != DBL else lv
            rv = self._coerce(rv, rt_, DBL) if rt_ != DBL else rv
            r = self._f("f")
            fm = {
                BinOpKind.ADD: "fadd",
                BinOpKind.SUB: "fsub",
                BinOpKind.MUL: "fmul",
                BinOpKind.DIV: "fdiv",
                BinOpKind.MOD: "frem",
            }
            if op in fm:
                self._L(f"{r} = {fm[op]} double {lv}, {rv}")
                self._put(i.dest, r, DBL)
            elif op in (
                BinOpKind.EQ,
                BinOpKind.NE,
                BinOpKind.LT,
                BinOpKind.GT,
                BinOpKind.LE,
                BinOpKind.GE,
            ):
                cm = {
                    BinOpKind.EQ: "oeq",
                    BinOpKind.NE: "one",
                    BinOpKind.LT: "olt",
                    BinOpKind.GT: "ogt",
                    BinOpKind.LE: "ole",
                    BinOpKind.GE: "oge",
                }
                self._L(f"{r} = fcmp {cm[op]} double {lv}, {rv}")
                self._put(i.dest, r, I1)
            else:
                self._put(i.dest, "0.000000e+00", DBL)
            return

        # Bool logical
        if lk == TypeKind.BOOL and op in (BinOpKind.AND, BinOpKind.OR):
            lv = self._coerce(lv, lt, I1) if lt != I1 else lv
            rv = self._coerce(rv, rt_, I1) if rt_ != I1 else rv
            r = self._f("bl")
            o = "and" if op == BinOpKind.AND else "or"
            self._L(f"{r} = {o} i1 {lv}, {rv}")
            self._put(i.dest, r, I1)
            return

        # Integer (default)
        lv = self._coerce(lv, lt, I64) if lt != I64 else lv
        rv = self._coerce(rv, rt_, I64) if rt_ != I64 else rv
        r = self._f("i")
        im = {
            BinOpKind.ADD: "add nsw",
            BinOpKind.SUB: "sub nsw",
            BinOpKind.MUL: "mul nsw",
            BinOpKind.DIV: "sdiv",
            BinOpKind.MOD: "srem",
            BinOpKind.AND: "and",
            BinOpKind.OR: "or",
        }
        if op in im:
            self._L(f"{r} = {im[op]} i64 {lv}, {rv}")
            self._put(i.dest, r, I64)
        elif op in (
            BinOpKind.EQ,
            BinOpKind.NE,
            BinOpKind.LT,
            BinOpKind.GT,
            BinOpKind.LE,
            BinOpKind.GE,
        ):
            cm = {
                BinOpKind.EQ: "eq",
                BinOpKind.NE: "ne",
                BinOpKind.LT: "slt",
                BinOpKind.GT: "sgt",
                BinOpKind.LE: "sle",
                BinOpKind.GE: "sge",
            }
            self._L(f"{r} = icmp {cm[op]} i64 {lv}, {rv}")
            self._put(i.dest, r, I1)
        else:
            self._put(i.dest, "0", I64)

    # --- UnaryOp ---
    def _do_unary(self, i: UnaryOp) -> None:
        ov, ot = self._get(i.operand)
        k = i.operand.ty.kind
        if i.op == UnaryOpKind.NEG:
            if k == TypeKind.FLOAT:
                r = self._f("neg")
                self._L(f"{r} = fsub double 0.000000e+00, {ov}")
                self._put(i.dest, r, DBL)
            else:
                ov = self._coerce(ov, ot, I64) if ot != I64 else ov
                r = self._f("neg")
                self._L(f"{r} = sub nsw i64 0, {ov}")
                self._put(i.dest, r, I64)
        elif i.op == UnaryOpKind.NOT:
            if k == TypeKind.BOOL:
                ov = self._coerce(ov, ot, I1) if ot != I1 else ov
                r = self._f("not")
                self._L(f"{r} = xor i1 {ov}, 1")
                self._put(i.dest, r, I1)
            else:
                ov = self._coerce(ov, ot, I64) if ot != I64 else ov
                r = self._f("not")
                self._L(f"{r} = icmp eq i64 {ov}, 0")
                self._put(i.dest, r, I1)
        else:
            self._put(i.dest, ov, ot)

    # --- Call (builtin dispatch + user) ---
    def _do_call(self, i: Call) -> None:  # noqa: C901
        fn = i.fn_name

        # __mn_list_push: pass list alloca pointer directly (not a copy)
        # to ensure the push modifies the original list struct in-place.
        if fn == "__mn_list_push" and len(i.args) >= 2:
            list_val = i.args[0]
            elem_val = i.args[1]
            pi = self._get_ptr(list_val)
            if pi:
                la, lt = pi
                if lt != LIST:
                    bc = self._f("lbc")
                    bc = la  # opaque ptr, no bitcast
                    la = bc
                ev, et = self._get(elem_val)
                ea = self._alloca(et, "pea")
                self._L(f"store {et} {ev}, ptr {ea}")
                ep = ea  # opaque ptr, no bitcast
                # v4.101.0 + v4.103.0: move semantics — the element is
                # now owned by the list; zero its tracking slot so
                # drop glue does not free it. See _do_list_push.
                if elem_val.name in self._list_vars:
                    self._list_vars.remove(elem_val.name)
                root_e = self._lroots.get(elem_val.name)
                if root_e and root_e in self._list_vars:
                    self._list_vars.remove(root_e)
                self._move_resource(elem_val.name)
                self._ensure("__mn_list_push", VOID, ["ptr", PTR])
                self._L(f"call void @__mn_list_push(ptr {la}, ptr {ep})")
                self._put(i.dest, "0", I1)  # push returns void
                return

        args = [(self._get(a)) for a in i.args]  # [(val, ty)]
        self._san(i.dest.name)

        # v4.108.0: StringBuilder pointer-based API. The MIR auto-loop pass
        # (string_concat_optimization) emits these calls to replace O(n²)
        # concat loops with amortized O(n) builder appends.
        if fn == "__mn_sb_new" and len(args) >= 1:
            cv = args[0][0] if args[0][1] == I64 else self._coerce(args[0][0], args[0][1], I64)
            r = self._rt("__mn_sb_new", PTR, [I64], [(cv, I64)])
            self._put(i.dest, r, PTR)
            return
        if fn == "__mn_sb_append" and len(args) >= 2:
            sbv = args[0][0] if args[0][1] == PTR else self._coerce(args[0][0], args[0][1], PTR)
            sv = args[1][0] if args[1][1] == STR else self._coerce(args[1][0], args[1][1], STR)
            self._rt(
                "__mn_sb_append",
                VOID,
                [PTR, STR],
                [(sbv, PTR), (sv, STR)],
            )
            self._put(i.dest, "0", I1)
            return
        if fn == "__mn_sb_finish" and len(args) >= 1:
            sbv = args[0][0] if args[0][1] == PTR else self._coerce(args[0][0], args[0][1], PTR)
            r = self._rt("__mn_sb_finish", STR, [PTR], [(sbv, PTR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return

        # v5.49.0 Wn.1 — direct ``__mn_*`` runtime call from .mn source.
        # Route through ``_rt`` for ABI-correct Win64 sarg/sret lowering
        # using the canonical signature from ``_RUNTIME_FN_SIGS``. The
        # auto-declare path below derives types from MIR context, which
        # for unannotated calls like ``if __mn_file_exists(p) != 0`` picks
        # ``Ptr`` and emits the wrong shape on Win64. See
        # ``docs/roadmap/v5/v5.49.0/PRE_PHASE_AUDIT.md``.
        if fn in _RUNTIME_FN_SIGS:
            sig_ret, sig_pts = _RUNTIME_FN_SIGS[fn]
            sig_coerced: list[tuple[str, str]] = []
            for j, (v, t) in enumerate(args):
                et = sig_pts[j] if j < len(sig_pts) else t
                sig_coerced.append((self._coerce(v, t, et) if t != et else v, et))
            if sig_ret == VOID:
                self._rt(fn, sig_ret, list(sig_pts), sig_coerced)
                self._put(i.dest, "0", I1)
            else:
                rsig = self._rt(fn, sig_ret, list(sig_pts), sig_coerced, nm="c")
                if sig_ret == STR:
                    self._track_string(rsig)
                self._put(i.dest, rsig, sig_ret)
            return

        # print / println (both add newline; println is a deprecated alias)
        if fn in ("println", "print"):
            nl = True
            if i.args and i.args[0].ty.kind == TypeKind.STRING and args[0][1] == STR:
                rt_fn = "__mn_str_println" if nl else "__mn_str_print"
                self._rt(rt_fn, VOID, [STR], [args[0]])
            elif i.args and i.args[0].ty.kind == TypeKind.INT:
                self._printf(
                    "%lld\n" if nl else "%lld",
                    [
                        (
                            (
                                self._coerce(args[0][0], args[0][1], I64)
                                if args[0][1] != I64
                                else args[0][0]
                            ),
                            I64,
                        )
                    ],
                )
            elif i.args and i.args[0].ty.kind == TypeKind.FLOAT:
                self._printf("%f\n" if nl else "%f", [(args[0][0], DBL)])
            elif i.args and i.args[0].ty.kind == TypeKind.BOOL:
                bv = self._coerce(args[0][0], args[0][1], I64) if args[0][1] != I64 else args[0][0]
                s = self._rt("__mn_str_from_bool", STR, [I64], [(bv, I64)])
                self._track_string(s)
                rt_fn_b = "__mn_str_println" if nl else "__mn_str_print"
                self._rt(rt_fn_b, VOID, [STR], [(s, STR)])
            elif i.args:
                self._printf(
                    "%lld\n" if nl else "%lld",
                    [(self._coerce(args[0][0], args[0][1], I64), I64)],
                )
            self._put(i.dest, "0", I1)
            return

        # len
        if fn == "len":
            if i.args and i.args[0].ty.kind == TypeKind.STRING:
                r = self._rt("__mn_str_len", I64, [STR], [args[0]])
                self._put(i.dest, r, I64)
            elif i.args and (i.args[0].ty.kind == TypeKind.LIST or args[0][1] == LIST):
                lv = (
                    self._coerce(args[0][0], args[0][1], LIST) if args[0][1] != LIST else args[0][0]
                )
                la = self._alloca(LIST, "ll")
                self._L(f"store {LIST} {lv}, ptr {la}")
                r = self._rt("__mn_list_len", I64, ["ptr"], [(la, "ptr")])
                self._put(i.dest, r, I64)
            elif i.args and i.args[0].ty.kind == TypeKind.MAP:
                r = self._rt("__mn_map_len", I64, [PTR], [args[0]])
                self._put(i.dest, r, I64)
            else:
                self._put(i.dest, "0", I64)
            return

        # str / toString
        if fn in ("str", "toString"):
            ak = i.args[0].ty.kind if i.args else TypeKind.UNKNOWN
            at = args[0][1] if args else PTR
            # Infer from LLVM type when MIR type is UNKNOWN
            if ak == TypeKind.UNKNOWN:
                if at == I64:
                    ak = TypeKind.INT
                elif at == DBL:
                    ak = TypeKind.FLOAT
                elif at == I1:
                    ak = TypeKind.BOOL
                elif at == STR:
                    ak = TypeKind.STRING
            if ak == TypeKind.INT:
                r = self._rt("__mn_str_from_int", STR, [I64], [args[0]])
                self._track_string(r)
            elif ak == TypeKind.FLOAT:
                r = self._rt("__mn_str_from_float", STR, [DBL], [args[0]])
                self._track_string(r)
            elif ak == TypeKind.BOOL:
                bv = self._coerce(args[0][0], args[0][1], I64) if args[0][1] != I64 else args[0][0]
                r = self._rt("__mn_str_from_bool", STR, [I64], [(bv, I64)])
                self._track_string(r)
            elif ak == TypeKind.STRING:
                self._put(i.dest, args[0][0], args[0][1])
                return
            else:
                r, _ = self._mkstr("<?>")
            self._put(i.dest, r, STR)
            return

        # int() / float()
        if fn == "int":
            if i.args and i.args[0].ty.kind == TypeKind.FLOAT:
                r = self._f("ci")
                self._L(f"{r} = fptosi double {args[0][0]} to i64")
            elif i.args and i.args[0].ty.kind == TypeKind.BOOL:
                r = self._f("ci")
                a = self._coerce(args[0][0], args[0][1], I1) if args[0][1] != I1 else args[0][0]
                self._L(f"{r} = zext i1 {a} to i64")
            elif i.args and i.args[0].ty.kind == TypeKind.STRING:
                r = self._rt("__mn_str_to_int", I64, [STR], [args[0]])
            else:
                r = args[0][0] if args else "0"
            self._put(i.dest, r, I64)
            return
        if fn == "float":
            if i.args and i.args[0].ty.kind == TypeKind.INT:
                r = self._f("cf")
                a = self._coerce(args[0][0], args[0][1], I64) if args[0][1] != I64 else args[0][0]
                self._L(f"{r} = sitofp i64 {a} to double")
            elif i.args and i.args[0].ty.kind == TypeKind.STRING:
                r = self._rt("__mn_str_to_float", DBL, [STR], [args[0]])
            else:
                r = args[0][0] if args else "0.000000e+00"
            self._put(i.dest, r, DBL)
            return

        # ord / chr
        if fn == "ord" and i.args:
            r = self._rt("__mn_str_ord", I64, [STR], [args[0]])
            self._put(i.dest, r, I64)
            return
        if fn == "chr" and i.args:
            r = self._rt("__mn_str_chr", STR, [I64], [args[0]])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return

        # C runtime: process + file I/O (self-hosted compiler driver)
        if fn == "__mn_argc":
            r = self._rt("__mn_argc", I64, [], [])
            self._put(i.dest, r, I64)
            return
        if fn == "__mn_argv" and args:
            a = self._coerce(args[0][0], args[0][1], I64) if args[0][1] != I64 else args[0][0]
            r = self._rt("__mn_argv", STR, [I64], [(a, I64)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "__mn_file_read_or_empty" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_file_read_or_empty", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "__mn_exit" and args:
            a = self._coerce(args[0][0], args[0][1], I64) if args[0][1] != I64 else args[0][0]
            self._rt("__mn_exit", VOID, [I64], [(a, I64)])
            self._put(i.dest, "0", I1)
            return
        if fn == "__mn_str_eprint" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            self._rt("__mn_str_eprint", VOID, [STR], [(a, STR)])
            self._put(i.dest, "0", I1)
            return
        if fn == "__mn_str_eprintln" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            self._rt("__mn_str_eprintln", VOID, [STR], [(a, STR)])
            self._put(i.dest, "0", I1)
            return
        if fn == "__mn_file_write" and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], STR) if args[1][1] != STR else args[1][0]
            r = self._rt("__mn_file_write", I64, [STR, STR], [(a0, STR), (a1, STR)])
            self._put(i.dest, r, I64)
            return
        if fn == "__mn_system" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_system", I64, [STR], [(a, STR)])
            self._put(i.dest, r, I64)
            return
        # v5.8.4 Wb.2: host detection — returns 1 on Win64, 0 elsewhere.
        # The self-hosted emitter calls this in emit_mir_module to pick
        # SysV vs Win64 ABI. Registering here so the Python bootstrap
        # also emits the correct `call i64 @__mn_host_is_win64()`.
        if fn == "__mn_host_is_win64":
            r = self._rt("__mn_host_is_win64", I64, [], [])
            self._put(i.dest, r, I64)
            return
        # v5.8.6 We.1: refined (is_windows, arch_bits) pair. Both
        # return Int. The self-hosted emitter calls these in
        # emit_mir_module to dispatch a 3-way ABI (SysV / Win64 /
        # i686 cdecl); the Python bootstrap also routes them so the
        # stage1 build of mnc_all.mn references the new exports.
        if fn == "__mn_host_is_windows":
            r = self._rt("__mn_host_is_windows", I64, [], [])
            self._put(i.dest, r, I64)
            return
        if fn == "__mn_host_arch_bits":
            r = self._rt("__mn_host_arch_bits", I64, [], [])
            self._put(i.dest, r, I64)
            return
        # v5.9.0 DX.2: build-time-baked version string. Replaces the
        # __MN_VERSION__ source-tree placeholder; both the version()
        # surface and the IR metadata node call this at runtime.
        if fn == "__mn_version_string":
            r = self._rt("__mn_version_string", STR, [], [])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        # v5.9.0 DX.4: native cache stats / clean / dev-null shim.
        # Replaces the POSIX-only ``__mn_system("if [ -d ... ]")``
        # shell-out at the cache-stats site; pre-v5.9.0 this errored
        # out on Windows with ``-d was unexpected at this time``.
        if fn == "__mn_dev_null_redirect":
            r = self._rt("__mn_dev_null_redirect", STR, [], [])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "__mn_clang_err_path":
            r = self._rt("__mn_clang_err_path", STR, [], [])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        # v5.10.0 Win.1b.D: directory containing the running binary.
        # find_clang() in main.mn uses this to locate a bundled LLVM
        # toolchain at <exe_dir>/llvm/clang(.exe) before falling back
        # to PATH clang.
        if fn == "__mn_executable_dir":
            r = self._rt("__mn_executable_dir", STR, [], [])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "__mn_dir_count_files" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_dir_count_files", I64, [STR], [(a, STR)])
            self._put(i.dest, r, I64)
            return
        if fn == "__mn_dir_total_size" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_dir_total_size", I64, [STR], [(a, STR)])
            self._put(i.dest, r, I64)
            return
        if fn == "__mn_dir_remove_recursive" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_dir_remove_recursive", I64, [STR], [(a, STR)])
            self._put(i.dest, r, I64)
            return
        # v5.23.1 Mb.1: V.9 lifecycle leak — __mn_indent_to_braces returns
        # an owned MnString allocated in C. Without a dedicated handler
        # the call falls through to the auto-declare path which does not
        # call _track_string, so parser__parse leaks the preprocessed
        # buffer on every invocation. Bounded to single-shot in mnc-stage1
        # (OS reaps on exit) but unbounded if the runtime is embedded in
        # a long-lived process (LSP server, watch-mode compiler).
        #
        # Track the result for drop-glue freeing, but DO NOT register the
        # slot in _str_slots (clear _last_tracked_str_slot before _put).
        # Reason: Python's _do_call applies a blanket-move to every user-
        # function arg, which zeros the _str_slots entry for the variable.
        # parse() does `let preprocessed = __mn_indent_to_braces(source);
        # tokenize(preprocessed, filename)`, and tokenize is a borrow, not
        # a consume — but blanket-move would zero the slot anyway, leaking
        # the buffer. The self-host emit_llvm.mn doesn't have this blanket
        # move (it relies on explicit Move from the lowerer), so stage2/3
        # IR is leak-clean by construction; only stage1 needs this guard.
        if fn == "__mn_indent_to_braces" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_indent_to_braces", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._last_tracked_str_slot = None
            self._put(i.dest, r, STR)
            return
        # v5.48.1 Te.3.D.4.4: match-arm statement-shorthand rewriter.
        # Same routing rationale as __mn_indent_to_braces above —
        # returns an owned MnString that needs drop-glue tracking, and
        # routing through `_rt` ensures the Win64 ABI uses the correct
        # 8-byte large-struct threshold (MnString is 16 B).
        if fn == "__mn_rewrite_arm_stmt_shorthand" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_rewrite_arm_stmt_shorthand", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._last_tracked_str_slot = None
            self._put(i.dest, r, STR)
            return
        # v5.26.0 Mb.9: route the v5.23.2 Te.3.B.2 brace-deprecation
        # functions through `_rt` for the same reason the
        # `__mn_indent_to_braces` handler above exists — without it
        # the call falls through to the user-call path, which uses
        # the 64-byte ``_use_byref`` threshold instead of `_rt`'s
        # 8-byte ``_is_large_struct`` threshold. ``MnString`` is
        # 16 bytes, so on Win64 the call site emits the struct
        # by value while ``_decl_fn`` already declares the function
        # with a ``ptr`` parameter — gcc lowers ``MnString source``
        # per Win64 ABI as pass-by-hidden-pointer, dereferences
        # rcx as the struct pointer, and reads the data buffer's
        # bytes 8..16 as the length field. Surfaced in publish run
        # #48 as ``oom in count_user_brace_block_openers`` with the
        # length read containing ``"generate"`` (bytes 8..16 of
        # ``mnc_all.mn``'s ``// Auto-generated:`` prelude).
        if fn == "__mn_count_user_brace_block_openers" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt(fn, I64, [STR], [(a, STR)])
            self._put(i.dest, r, I64)
            return
        if fn == "__mn_emit_brace_deprecation_warning" and len(args) >= 2:
            pa = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            cv = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
            self._rt(fn, VOID, [STR, I64], [(pa, STR), (cv, I64)])
            self._put(i.dest, "0", I1)
            return

        # High-level I/O builtins (v3.41.0)
        if fn == "read_line":
            r = self._rt("__mn_read_line", STR, [], [])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "read_file" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_file_read_or_empty", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "write_file" and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], STR) if args[1][1] != STR else args[1][0]
            self._rt("__mn_file_write", I64, [STR, STR], [(a0, STR), (a1, STR)])
            self._put(i.dest, "0", I1)
            return
        if fn == "append_file" and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], STR) if args[1][1] != STR else args[1][0]
            self._rt("__mn_file_append", I64, [STR, STR], [(a0, STR), (a1, STR)])
            self._put(i.dest, "0", I1)
            return
        if fn == "file_exists" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_file_exists", I64, [STR], [(a, STR)])
            tb = self._f("tb")
            self._L(f"{tb} = icmp ne i64 {r}, 0")
            self._put(i.dest, tb, I1)
            return
        if fn == "list_dir" and args:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_dir_list_strings", LIST, [STR], [(a, STR)])
            self._put(i.dest, r, LIST)
            return

        # Network, crypto, regex builtins (v3.42.0).
        #
        # v5.39.0 Cr.* fix: defer to user-defined wrappers when present.
        # The stdlib/crypto.mn wrappers `sha256` / `hmac_sha256` /
        # `random_bytes` etc. produce hex / List-of-Int returns, while
        # the raw shortcuts here produce raw bytes / String. Without
        # this gate, user code that imports the stdlib gets the wrong
        # return shape any time the MIR inliner fails to inline (e.g.
        # high call-site count). Same gate applies to `regex_match` /
        # `regex_replace` — stdlib/text/regex.mn defines its own
        # wrappers.
        is_user_defined = fn in self._sigs
        if fn == "http_get" and args and not is_user_defined:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_http_get", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "sha256" and args and not is_user_defined:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_sha256_str", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "base64_encode" and args and not is_user_defined:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_base64_encode_str", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "base64_decode" and args and not is_user_defined:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_base64_decode_str", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "hmac_sha256" and len(args) >= 2 and not is_user_defined:
            a0 = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], STR) if args[1][1] != STR else args[1][0]
            r = self._rt("__mn_hmac_sha256_str", STR, [STR, STR], [(a0, STR), (a1, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "hex_encode" and args and not is_user_defined:
            a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            r = self._rt("__mn_hex_encode_str", STR, [STR], [(a, STR)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "random_bytes" and args and not is_user_defined:
            a = self._coerce(args[0][0], args[0][1], I64) if args[0][1] != I64 else args[0][0]
            r = self._rt("__mn_random_bytes_str", STR, [I64], [(a, I64)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "regex_match" and len(args) >= 2 and not is_user_defined:
            a0 = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], STR) if args[1][1] != STR else args[1][0]
            h = self._rt("__mn_regex_compile_str", I64, [STR], [(a0, STR)])
            r = self._rt(
                "__mn_regex_exec_str", I64, [I64, STR, I64], [(h, I64), (a1, STR), ("0", I64)]
            )
            self._rt("__mn_regex_free", I64, [I64], [(h, I64)])
            tb = self._f("rm")
            self._L(f"{tb} = icmp sgt i64 {r}, 0")
            self._put(i.dest, tb, I1)
            return
        if fn == "regex_replace" and len(args) >= 3 and not is_user_defined:
            a0 = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], STR) if args[1][1] != STR else args[1][0]
            a2 = self._coerce(args[2][0], args[2][1], STR) if args[2][1] != STR else args[2][0]
            h = self._rt("__mn_regex_compile_str", I64, [STR], [(a0, STR)])
            r = self._rt(
                "__mn_regex_replace_str",
                STR,
                [I64, STR, STR, I64],
                [(h, I64), (a1, STR), (a2, STR), ("1", I64)],
            )
            self._rt("__mn_regex_free", I64, [I64], [(h, I64)])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return

        # GPU builtins (v3.46.0)
        if fn == "gpu_available":
            r = self._rt("__mn_gpu_available", I64, [], [])
            tb = self._f("ga")
            self._L(f"{tb} = icmp ne i64 {r}, 0")
            self._put(i.dest, tb, I1)
            return
        if fn == "gpu_device_name":
            r = self._rt("__mn_gpu_device_name", STR, [], [])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return
        if fn == "gpu_device_memory":
            r = self._rt("__mn_gpu_device_memory", I64, [], [])
            self._put(i.dest, r, I64)
            return
        if (
            fn in ("gpu_tensor_add", "gpu_tensor_sub", "gpu_tensor_mul", "gpu_tensor_div")
            and len(args) >= 2
        ):
            a0 = self._coerce(args[0][0], args[0][1], LIST) if args[0][1] != LIST else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], LIST) if args[1][1] != LIST else args[1][0]
            # Pass lists by pointer to avoid ABI mismatch (MnList is 40 bytes)
            pa = self._alloca(LIST, "gta")
            pb = self._alloca(LIST, "gtb")
            self._L(f"store {LIST} {a0}, ptr {pa}")
            self._L(f"store {LIST} {a1}, ptr {pb}")
            cfn = {
                "gpu_tensor_add": "__mn_gpu_tensor_add",
                "gpu_tensor_sub": "__mn_gpu_tensor_sub",
                "gpu_tensor_mul": "__mn_gpu_tensor_mul",
                "gpu_tensor_div": "__mn_gpu_tensor_div",
            }[fn]
            r = self._rt(cfn, LIST, [PTR, PTR], [(pa, PTR), (pb, PTR)])
            self._put(i.dest, r, LIST)
            return
        if fn == "gpu_tensor_matmul" and len(args) >= 5:
            a0 = self._coerce(args[0][0], args[0][1], LIST) if args[0][1] != LIST else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], LIST) if args[1][1] != LIST else args[1][0]
            a2 = self._coerce(args[2][0], args[2][1], I64) if args[2][1] != I64 else args[2][0]
            a3 = self._coerce(args[3][0], args[3][1], I64) if args[3][1] != I64 else args[3][0]
            a4 = self._coerce(args[4][0], args[4][1], I64) if args[4][1] != I64 else args[4][0]
            pa = self._alloca(LIST, "gma")
            pb = self._alloca(LIST, "gmb")
            self._L(f"store {LIST} {a0}, ptr {pa}")
            self._L(f"store {LIST} {a1}, ptr {pb}")
            r = self._rt(
                "__mn_gpu_tensor_matmul",
                LIST,
                [PTR, PTR, I64, I64, I64],
                [(pa, PTR), (pb, PTR), (a2, I64), (a3, I64), (a4, I64)],
            )
            self._put(i.dest, r, LIST)
            return

        # Tensor builtins (v4.42.0)
        if fn == "tensor_rank" and len(args) >= 1:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            r = self._rt("__mn_tensor_rank", I64, [PTR], [(a0, PTR)])
            self._put(i.dest, r, I64)
            return
        if fn == "tensor_size" and len(args) >= 1:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            r = self._rt("__mn_tensor_size", I64, [PTR], [(a0, PTR)])
            self._put(i.dest, r, I64)
            return
        if fn == "tensor_get_f64" and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
            r = self._rt("__mn_tensor_get_f64", DBL, [PTR, I64], [(a0, PTR), (a1, I64)])
            self._put(i.dest, r, DBL)
            return
        if fn == "tensor_get_i64" and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
            r = self._rt("__mn_tensor_get_i64", I64, [PTR, I64], [(a0, PTR), (a1, I64)])
            self._put(i.dest, r, I64)
            return
        if fn == "tensor_shape_dim" and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
            r = self._rt("__mn_tensor_shape_dim", I64, [PTR, I64], [(a0, PTR), (a1, I64)])
            self._put(i.dest, r, I64)
            return
        if fn == "tensor_print" and len(args) >= 1:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            self._ensure("__mn_tensor_print_f64", VOID, [PTR])
            self._L(f"call void @__mn_tensor_print_f64(ptr {a0})")
            return

        # Tensor multi-dim get/set (v4.43.0) — variadic runtime calls
        if fn in ("__mn_tensor_get_f64_nd", "__mn_tensor_get_i64_nd") and len(args) >= 2:
            # args = [(tensor_ptr, ty), (rank, ty), (idx0, ty), (idx1, ty), ...]
            t_ptr = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            rank_v = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
            idx_parts = []
            for j in range(2, len(args)):
                iv = self._coerce(args[j][0], args[j][1], I64) if args[j][1] != I64 else args[j][0]
                idx_parts.append(f"i64 {iv}")
            ret_ty = DBL if "f64" in fn else I64
            self._ensure(fn, ret_ty, [PTR, I64], va=True)
            idx_str = (", " + ", ".join(idx_parts)) if idx_parts else ""
            r = self._f("tget")
            self._L(
                f"{r} = call {ret_ty} (ptr, i64, ...) @{fn}(ptr {t_ptr}, i64 {rank_v}{idx_str})"
            )
            self._put(i.dest, r, ret_ty)
            return
        if fn in ("__mn_tensor_set_f64_nd", "__mn_tensor_set_i64_nd") and len(args) >= 3:
            # args = [(tensor_ptr, ty), (rank, ty), (idx0, ty), ..., (val, ty)]
            t_ptr = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            rank_v = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
            val_ty = DBL if "f64" in fn else I64
            # Last arg is the value; middle args are indices
            val_v = (
                self._coerce(args[-1][0], args[-1][1], val_ty)
                if args[-1][1] != val_ty
                else args[-1][0]
            )
            idx_parts = []
            for j in range(2, len(args) - 1):
                iv = self._coerce(args[j][0], args[j][1], I64) if args[j][1] != I64 else args[j][0]
                idx_parts.append(f"i64 {iv}")
            self._ensure(fn, VOID, [PTR, I64], va=True)
            idx_str = (", " + ", ".join(idx_parts)) if idx_parts else ""
            self._L(
                f"call void (ptr, i64, ...) @{fn}(ptr {t_ptr}, i64 {rank_v}{idx_str}, {val_ty} {val_v})"  # noqa: E501
            )
            return

        # Tensor reduction methods (v4.45.0)
        _TENSOR_REDUCE_F64 = {
            "__mn_tensor_sum_f64": DBL,
            "__mn_tensor_mean_f64": DBL,
            "__mn_tensor_max_f64": DBL,
            "__mn_tensor_min_f64": DBL,
            "__mn_tensor_argmax_f64": I64,
            "__mn_tensor_argmin_f64": I64,
        }
        _TENSOR_REDUCE_I64 = {
            "__mn_tensor_sum_i64": I64,
            "__mn_tensor_max_i64": I64,
            "__mn_tensor_min_i64": I64,
            "__mn_tensor_argmax_i64": I64,
            "__mn_tensor_argmin_i64": I64,
        }
        _ALL_TENSOR_REDUCE = {**_TENSOR_REDUCE_F64, **_TENSOR_REDUCE_I64}
        if fn in _ALL_TENSOR_REDUCE and len(args) >= 1:
            ret = _ALL_TENSOR_REDUCE[fn]
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            self._ensure(fn, ret, [PTR])
            r = self._f("tred")
            self._L(f"{r} = call {ret} @{fn}(ptr {a0})")
            self._put(i.dest, r, ret)
            return

        # Tensor slice (v4.45.0)
        # Lowerer passes flat args: [tensor, s0, s1, ..., e0, e1, ..., rank]
        # C runtime expects: (ptr tensor, ptr starts_array, ptr ends_array, i64 rank)
        # We pack the individual i64 values into stack-allocated arrays.
        # Tensor reshape (v5.41.0 Ts.1 → v5.45.0 Ts.2.B alias swap) and
        # tensor view (v5.45.0 Ts.2.B). Both share the same call shape:
        # Call(fn, [tensor, shape_list]). Shape is a List<Int>; pass it
        # by pointer (same pattern as __mn_gpu_tensor_add). The result
        # aliases the source's data buffer — no `noalias` attribute.
        if fn in ("__mn_tensor_reshape", "__mn_tensor_view") and len(args) == 2:
            t_ptr = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            shape_v = (
                self._coerce(args[1][0], args[1][1], LIST) if args[1][1] != LIST else args[1][0]
            )
            prefix = "tview" if fn == "__mn_tensor_view" else "treshape"
            shape_p = self._alloca(LIST, f"{prefix}_shape")
            self._L(f"store {LIST} {shape_v}, ptr {shape_p}")
            self._ensure(fn, PTR, [PTR, PTR])
            r = self._f(prefix)
            self._L(f"{r} = call ptr @{fn}(ptr {t_ptr}, ptr {shape_p})")
            self._tensor_vars.append(i.dest.name)
            self._put(i.dest, r, PTR)
            return

        if fn == "__mn_tensor_slice" and len(args) >= 3:
            t_ptr = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            # Last arg is rank
            rank_idx = len(args) - 1
            rank_v = (
                self._coerce(args[rank_idx][0], args[rank_idx][1], I64)
                if args[rank_idx][1] != I64
                else args[rank_idx][0]
            )
            ndim = (len(args) - 2) // 2  # (total - tensor - rank) / 2
            # Allocate stack arrays for starts and ends
            starts_arr = self._f("starts_arr")
            ends_arr = self._f("ends_arr")
            self._L(f"{starts_arr} = alloca [{ndim} x i64]")
            self._L(f"{ends_arr} = alloca [{ndim} x i64]")
            # Store individual start/end values into the arrays
            for d in range(ndim):
                s_val = (
                    self._coerce(args[1 + d][0], args[1 + d][1], I64)
                    if args[1 + d][1] != I64
                    else args[1 + d][0]
                )
                e_val = (
                    self._coerce(args[1 + ndim + d][0], args[1 + ndim + d][1], I64)
                    if args[1 + ndim + d][1] != I64
                    else args[1 + ndim + d][0]
                )
                s_gep = self._f("sgep")
                e_gep = self._f("egep")
                self._L(
                    f"{s_gep} = getelementptr inbounds [{ndim} x i64], ptr {starts_arr}, i64 0, i64 {d}"  # noqa: E501
                )
                self._L(
                    f"{e_gep} = getelementptr inbounds [{ndim} x i64], ptr {ends_arr}, i64 0, i64 {d}"  # noqa: E501
                )
                self._L(f"store i64 {s_val}, ptr {s_gep}")
                self._L(f"store i64 {e_val}, ptr {e_gep}")
            self._ensure("__mn_tensor_slice", PTR, [PTR, PTR, PTR, I64])
            r = self._f("tslice")
            self._L(
                f"{r} = call noalias ptr @__mn_tensor_slice(ptr {t_ptr}, ptr {starts_arr}, ptr {ends_arr}, i64 {rank_v})"  # noqa: E501
            )
            self._tensor_vars.append(i.dest.name)
            self._put(i.dest, r, PTR)
            return

        # v5.45.0 Ts.3.B — stepped slice: t[start..end:step] (and per-axis
        # combinations). Args layout from the lowerer:
        #   [obj, s0..s_{n-1}, e0..e_{n-1}, k0..k_{n-1}, rank]
        # so total = 3*ndim + 2. Result is a fresh contiguous tensor (copy
        # semantics, not view) — no `noalias` because v5.45.0 conservatively
        # omits noalias on tensor-producing exports; the runtime returns a
        # genuinely fresh tensor here so callers can rely on disjoint data.
        if fn == "__mn_tensor_step_slice" and len(args) >= 5:
            t_ptr = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            rank_idx = len(args) - 1
            rank_v = (
                self._coerce(args[rank_idx][0], args[rank_idx][1], I64)
                if args[rank_idx][1] != I64
                else args[rank_idx][0]
            )
            ndim = (len(args) - 2) // 3  # (total - tensor - rank) / 3
            starts_arr = self._f("starts_arr")
            ends_arr = self._f("ends_arr")
            steps_arr = self._f("steps_arr")
            self._L(f"{starts_arr} = alloca [{ndim} x i64]")
            self._L(f"{ends_arr} = alloca [{ndim} x i64]")
            self._L(f"{steps_arr} = alloca [{ndim} x i64]")
            for d in range(ndim):
                s_val = (
                    self._coerce(args[1 + d][0], args[1 + d][1], I64)
                    if args[1 + d][1] != I64
                    else args[1 + d][0]
                )
                e_val = (
                    self._coerce(args[1 + ndim + d][0], args[1 + ndim + d][1], I64)
                    if args[1 + ndim + d][1] != I64
                    else args[1 + ndim + d][0]
                )
                k_val = (
                    self._coerce(args[1 + 2 * ndim + d][0], args[1 + 2 * ndim + d][1], I64)
                    if args[1 + 2 * ndim + d][1] != I64
                    else args[1 + 2 * ndim + d][0]
                )
                s_gep = self._f("sgep")
                e_gep = self._f("egep")
                k_gep = self._f("kgep")
                self._L(
                    f"{s_gep} = getelementptr inbounds [{ndim} x i64], ptr {starts_arr}, i64 0, i64 {d}"  # noqa: E501
                )
                self._L(
                    f"{e_gep} = getelementptr inbounds [{ndim} x i64], ptr {ends_arr}, i64 0, i64 {d}"  # noqa: E501
                )
                self._L(
                    f"{k_gep} = getelementptr inbounds [{ndim} x i64], ptr {steps_arr}, i64 0, i64 {d}"  # noqa: E501
                )
                self._L(f"store i64 {s_val}, ptr {s_gep}")
                self._L(f"store i64 {e_val}, ptr {e_gep}")
                self._L(f"store i64 {k_val}, ptr {k_gep}")
            self._ensure("__mn_tensor_step_slice", PTR, [PTR, PTR, PTR, PTR, I64])
            r = self._f("tstepslice")
            self._L(
                f"{r} = call ptr @__mn_tensor_step_slice(ptr {t_ptr}, ptr {starts_arr}, ptr {ends_arr}, ptr {steps_arr}, i64 {rank_v})"  # noqa: E501
            )
            self._tensor_vars.append(i.dest.name)
            self._put(i.dest, r, PTR)
            return

        # Tensor broadcast ops (v4.44.0) — tensor+tensor and tensor+scalar
        _TENSOR_BROADCAST_FNS = {
            "__mn_tensor_add_broadcast_f64",
            "__mn_tensor_sub_broadcast_f64",
            "__mn_tensor_mul_broadcast_f64",
            "__mn_tensor_div_broadcast_f64",
            "__mn_tensor_add_broadcast_i64",
            "__mn_tensor_sub_broadcast_i64",
            "__mn_tensor_mul_broadcast_i64",
            "__mn_tensor_div_broadcast_i64",
        }
        _TENSOR_SCALAR_FNS = {
            "__mn_tensor_add_scalar_f64",
            "__mn_tensor_sub_scalar_f64",
            "__mn_tensor_mul_scalar_f64",
            "__mn_tensor_div_scalar_f64",
            "__mn_tensor_add_scalar_i64",
            "__mn_tensor_sub_scalar_i64",
            "__mn_tensor_mul_scalar_i64",
            "__mn_tensor_div_scalar_i64",
        }
        # Reverse scalar: scalar op tensor[i] (v4.47.0)
        _TENSOR_RSCALAR_FNS = {
            "__mn_tensor_rsub_scalar_f64",
            "__mn_tensor_rdiv_scalar_f64",
            "__mn_tensor_rsub_scalar_i64",
            "__mn_tensor_rdiv_scalar_i64",
        }
        if fn in _TENSOR_BROADCAST_FNS and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            a1 = self._coerce(args[1][0], args[1][1], PTR) if args[1][1] != PTR else args[1][0]
            self._ensure(fn, PTR, [PTR, PTR])
            r = self._f("tbcast")
            self._L(f"{r} = call noalias ptr @{fn}(ptr {a0}, ptr {a1})")
            self._tensor_vars.append(i.dest.name)
            self._put(i.dest, r, PTR)
            return
        if fn in _TENSOR_SCALAR_FNS and len(args) >= 2:
            a0 = self._coerce(args[0][0], args[0][1], PTR) if args[0][1] != PTR else args[0][0]
            scalar_ty = DBL if "f64" in fn else I64
            a1 = (
                self._coerce(args[1][0], args[1][1], scalar_ty)
                if args[1][1] != scalar_ty
                else args[1][0]
            )
            self._ensure(fn, PTR, [PTR, scalar_ty])
            r = self._f("tscal")
            self._L(f"{r} = call noalias ptr @{fn}(ptr {a0}, {scalar_ty} {a1})")
            self._tensor_vars.append(i.dest.name)
            self._put(i.dest, r, PTR)
            return
        # Reverse scalar: scalar op tensor (v4.47.0)
        if fn in _TENSOR_RSCALAR_FNS and len(args) >= 2:
            scalar_ty = DBL if "f64" in fn else I64
            a0 = (
                self._coerce(args[0][0], args[0][1], scalar_ty)
                if args[0][1] != scalar_ty
                else args[0][0]
            )
            a1 = self._coerce(args[1][0], args[1][1], PTR) if args[1][1] != PTR else args[1][0]
            self._ensure(fn, PTR, [scalar_ty, PTR])
            r = self._f("trscal")
            self._L(f"{r} = call noalias ptr @{fn}({scalar_ty} {a0}, ptr {a1})")
            self._tensor_vars.append(i.dest.name)
            self._put(i.dest, r, PTR)
            return

        # join
        if fn == "join" and len(i.args) >= 2:
            sep = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            lv = self._coerce(args[1][0], args[1][1], LIST) if args[1][1] != LIST else args[1][0]
            la = self._alloca(LIST, "jl")
            self._L(f"store {LIST} {lv}, ptr {la}")
            r = self._rt("__mn_str_join", STR, [STR, "ptr"], [(sep, STR), (la, "ptr")])
            self._track_string(r)
            self._put(i.dest, r, STR)
            return

        # String methods
        _smeth: dict[str, tuple[str, list[str], str]] = {
            "char_at": ("__mn_str_char_at", [STR, I64], STR),
            "byte_at": ("__mn_str_byte_at", [STR, I64], I64),
            "substr": ("__mn_str_substr", [STR, I64, I64], STR),
            "starts_with": ("__mn_str_starts_with", [STR, STR], I1),
            "ends_with": ("__mn_str_ends_with", [STR, STR], I1),
            "find": ("__mn_str_find", [STR, STR], I64),
            "contains": ("__mn_str_contains", [STR, STR], I1),
            "trim": ("__mn_str_trim", [STR], STR),
            "trim_start": ("__mn_str_trim_start", [STR], STR),
            "trim_end": ("__mn_str_trim_end", [STR], STR),
            "to_upper": ("__mn_str_to_upper", [STR], STR),
            "to_lower": ("__mn_str_to_lower", [STR], STR),
            "split": ("__mn_str_split", [STR, STR], LIST),
            "replace": ("__mn_str_replace", [STR, STR, STR], STR),
        }
        if (
            fn in _smeth
            and fn not in self._sigs
            and i.args
            and i.args[0].ty.kind == TypeKind.STRING
        ):
            rtn, pts, ret = _smeth[fn]
            if len(args) == len(pts):
                r = self._rt(rtn, ret, pts, args)
                if ret == STR:
                    self._track_string(r)
                elif ret == LIST:
                    self._track_container(i.dest.name, "list")
                self._put(i.dest, r, ret)
                return

        # Some / Ok / Err
        if fn == "Some" and args:
            v, t = args[0]
            ot = f"{{i1, {t}}}"
            s0 = self._f("so")
            self._L(f"{s0} = insertvalue {ot} undef, i1 1, 0")
            s1 = self._f("so")
            self._L(f"{s1} = insertvalue {ot} {s0}, {t} {v}, 1")
            self._put(i.dest, s1, ot)
            return
        if fn == "Ok" and args:
            v, t = args[0]
            rt = f"{{i1, {{{t}, ptr}}}}"
            s0 = self._f("ok")
            self._L(f"{s0} = insertvalue {rt} undef, i1 1, 0")
            s1 = self._f("ok")
            self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 0")
            self._put(i.dest, s1, rt)
            return
        if fn == "Err" and args:
            v, t = args[0]
            rt = f"{{i1, {{ptr, {t}}}}}"
            s0 = self._f("er")
            self._L(f"{s0} = insertvalue {rt} undef, i1 0, 0")
            s1 = self._f("er")
            self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 1")
            self._put(i.dest, s1, rt)
            return

        # Map iteration
        if fn == "__iter_has_next" and i.args and i.args[0].ty.kind == TypeKind.MAP:
            mv, mt = args[0]
            itn = f"_map_iter_{i.args[0].name}"
            if itn not in self._alloc:
                mi = self._rt("__mn_map_iter_new", PTR, [PTR], [(mv, mt)])
                self._alloc[itn] = (f"%{self._san(itn)}.addr", PTR)
                self._ent.append(f"  %{self._san(itn)}.addr = alloca ptr, align 8")
                self._L(f"store ptr {mi}, ptr %{self._san(itn)}.addr")
                ko = self._alloca(PTR, "ko")
                self._alloc[f"{itn}.kout"] = (ko, PTR)
                vo = self._alloca(PTR, "vo")
                self._alloc[f"{itn}.vout"] = (vo, PTR)
            ia, _ = self._alloc[itn]
            iv = self._f("mi")
            self._L(f"{iv} = load ptr, ptr {ia}")
            ka, _ = self._alloc[f"{itn}.kout"]
            va_, _ = self._alloc[f"{itn}.vout"]
            ri = self._rt(
                "__mn_map_iter_next",
                I64,
                [PTR, "ptr", "ptr"],
                [(iv, PTR), (ka, "ptr"), (va_, "ptr")],
            )
            r = self._f("mib")
            self._L(f"{r} = trunc i64 {ri} to i1")
            self._put(i.dest, r, I1)
            return
        if fn == "__iter_next" and i.args and i.args[0].ty.kind == TypeKind.MAP:
            itn = f"_map_iter_{i.args[0].name}"
            if f"{itn}.kout" in self._alloc:
                ka, _ = self._alloc[f"{itn}.kout"]
                kp = self._f("kp")
                self._L(f"{kp} = load ptr, ptr {ka}")
                ety = self._rty(i.dest.ty)
                tp = kp  # opaque ptr, no bitcast
                r = self._f("kv")
                self._L(f"{r} = load {ety}, ptr {tp}")
                self._put(i.dest, r, ety)
            else:
                self._put(i.dest, "0", I64)
            return

        # Stream iteration
        if fn == "__iter_has_next" and i.args and i.args[0].ty.kind == TypeKind.STREAM:
            sv, st = args[0]
            itn = f"_stream_iter_{i.args[0].name}"
            if f"{itn}.out" not in self._alloc:
                oa = self._alloca(I64, "so")
                self._alloc[f"{itn}.out"] = (oa, I64)
            oa, _ = self._alloc[f"{itn}.out"]
            op = oa  # opaque ptr, no bitcast
            ri = self._rt("__mn_stream_next", I64, [PTR, PTR], [(sv, st), (op, PTR)])
            r = self._f("sib")
            self._L(f"{r} = trunc i64 {ri} to i1")
            self._put(i.dest, r, I1)
            return
        if fn == "__iter_next" and i.args and i.args[0].ty.kind == TypeKind.STREAM:
            itn = f"_stream_iter_{i.args[0].name}"
            if f"{itn}.out" in self._alloc:
                oa, oat = self._alloc[f"{itn}.out"]
                ety = self._rty(i.dest.ty)
                if ety == VOID:
                    self._put(i.dest, "0", I64)
                else:
                    tp = oa  # opaque ptr, no bitcast
                    r = self._f("sv")
                    self._L(f"{r} = load {ety}, ptr {tp}")
                    self._put(i.dest, r, ety)
            else:
                self._put(i.dest, "0", I64)
            return

        # Move semantics: when a resource (list, string, boxed) is passed as
        # an argument to a user-defined function, transfer ownership so drop
        # glue won't free it.
        # v4.103.0: also walk _lroots so a list passed via a loaded
        # temp (e.g. new_block(span, stmts) where `stmts` was loaded
        # into a fresh SSA before the call) still drops its root
        # alloca from _list_vars. Without this, parse_block-style
        # `return new_block(..., stmts)` left `stmts` tracked and the
        # drop-glue pass freed its buffer out from under the returned
        # Block — the inner else clause in nested if/else then
        # aliased the outer else body, sending the semantic checker
        # into infinite recursion on nested if/else.
        for j, (v, t) in enumerate(args):
            if j < len(i.args):
                src_name = i.args[j].name
                if t == LIST and src_name in self._list_vars:
                    self._list_vars.remove(src_name)
                root_s = self._lroots.get(src_name)
                if root_s and root_s in self._list_vars:
                    self._list_vars.remove(root_s)
                self._move_resource(src_name)
                if root_s and root_s != src_name:
                    self._move_resource(root_s)

        # User function
        if fn in self._sigs:
            ret, pts, va = self._sigs[fn]
            coerced: list[tuple[str, str]] = []
            for j, (v, t) in enumerate(args):
                et = pts[j] if j < len(pts) else t
                coerced.append((self._coerce(v, t, et) if t != et else v, et))

            # Apply byref ABI: large struct args → pointer, large struct ret → sret.
            # v4.149.0 E5: return sret uses per-target classifier.
            use_sret = self._use_sret(ret) and fn != "main"
            abi_args: list[tuple[str, str]] = []
            for v, t in coerced:
                if self._use_byref(t):
                    a = self._alloca(t, "barg")
                    self._L(f"store {t} {v}, ptr {a}")
                    abi_args.append((a, "ptr"))
                else:
                    abi_args.append((v, t))

            if use_sret:
                sret_a = self._alloca(ret, "sret")
                # Zero the sret buffer — prevents garbage in uninitialized fields
                self._L(f"store {ret} zeroinitializer, ptr {sret_a}")
                sret_part = f"ptr sret({ret}) {sret_a}"
                rest = ", ".join(f"{t} {v}" for v, t in abi_args)
                a_str = f"{sret_part}, {rest}" if rest else sret_part
                self._L(f"call void @{fn}({a_str})")
                r = self._f("c")
                self._L(f"{r} = load {ret}, ptr {sret_a}")
                self._put(i.dest, r, ret)
            elif ret == VOID:
                astr = ", ".join(f"{t} {v}" for v, t in abi_args)
                self._L(f"call void @{fn}({astr})")
                self._put(i.dest, "0", I1)
            else:
                astr = ", ".join(f"{t} {v}" for v, t in abi_args)
                r = self._f("c")
                if va:
                    ft = f"{ret} ({', '.join(pts)}, ...)"
                    self._L(f"{r} = call {ft} @{fn}({astr})")
                else:
                    self._L(f"{r} = call {ret} @{fn}({astr})")
                self._put(i.dest, r, ret)
            return

        # Check if this is a struct constructor (__new_StructName)
        if fn.startswith("__new_") and len(fn) > 6:
            sn = self._res_struct(fn[6:])
            if sn in self._struct_ty:
                sty = self._struct_ty[sn]
                cur = "undef"
                fields_info = self._structs.get(sn, [])
                for j, (av, at) in enumerate(args):
                    ft = fields_info[j][1] if j < len(fields_info) else at
                    if at != ft:
                        av = self._coerce(av, at, ft)
                    nm = self._san(i.dest.name)
                    tmp = nm if j == len(args) - 1 else f"{nm}.f{j}"
                    self._L(f"  %{tmp} = insertvalue {sty} {cur}, {ft} {av}, {j}")
                    cur = f"%{tmp}"
                if not args:
                    cur = _zero(sty)
                self._put(i.dest, cur, sty)
                return

        # Check if this is an enum variant constructor call
        for en, (tags, pays, _) in self._enums.items():
            base = en.rsplit("__", 1)[-1]
            for vn in tags:
                if fn == f"{base}_{vn}" or fn == vn:
                    # Convert to enum init
                    fake = EnumInit(
                        dest=i.dest,
                        enum_type=MIRType(type_info=TypeInfo(kind=TypeKind.ENUM, name=en)),
                        variant=vn,
                        payload=i.args,
                    )
                    self._do_enum_init(fake)
                    return

        # Auto-declare unknown function (with byref ABI adjustments)
        pts_auto = [self._rty(a.ty) for a in i.args]
        for j, pt in enumerate(pts_auto):
            if pt == PTR and j < len(args) and args[j][1] != PTR:
                pts_auto[j] = args[j][1]
        ret_auto = self._rty(i.dest.ty)
        self._decl_fn(fn, ret_auto, pts_auto)

        # Apply same byref logic as the known-function path
        coerced2: list[tuple[str, str]] = []
        for j, (v, t) in enumerate(args):
            et = pts_auto[j] if j < len(pts_auto) else t
            coerced2.append((self._coerce(v, t, et) if t != et else v, et))
        # v4.149.0 E5: return sret uses per-target classifier.
        use_sret2 = self._use_sret(ret_auto) and fn != "main"
        abi_args2: list[tuple[str, str]] = []
        for v, t in coerced2:
            if self._use_byref(t):
                a2 = self._alloca(t, "barg")
                self._L(f"store {t} {v}, ptr {a2}")
                abi_args2.append((a2, "ptr"))
            else:
                abi_args2.append((v, t))
        if use_sret2:
            sret_a2 = self._alloca(ret_auto, "sret")
            self._L(f"store {ret_auto} zeroinitializer, ptr {sret_a2}")
            sret_part2 = f"ptr sret({ret_auto}) {sret_a2}"
            rest2 = ", ".join(f"{t} {v}" for v, t in abi_args2)
            a_str2 = f"{sret_part2}, {rest2}" if rest2 else sret_part2
            self._L(f"call void @{fn}({a_str2})")
            r = self._f("c")
            self._L(f"{r} = load {ret_auto}, ptr {sret_a2}")
            self._put(i.dest, r, ret_auto)
        elif ret_auto == VOID:
            astr2 = ", ".join(f"{t} {v}" for v, t in abi_args2)
            self._L(f"call void @{fn}({astr2})")
            self._put(i.dest, "0", I1)
        else:
            astr2 = ", ".join(f"{t} {v}" for v, t in abi_args2)
            r = self._f("c")
            self._L(f"{r} = call {ret_auto} @{fn}({astr2})")
            self._put(i.dest, r, ret_auto)

    # --- ExternCall ---
    def _do_extern(self, i: ExternCall) -> None:
        args = [self._get(a) for a in i.args]
        # Move semantics for arguments (same as _do_call)
        # v4.103.0: walk _lroots too (see _do_call).
        for j, (v, t) in enumerate(args):
            if j < len(i.args):
                src_name = i.args[j].name
                if t == LIST and src_name in self._list_vars:
                    self._list_vars.remove(src_name)
                root_s = self._lroots.get(src_name)
                if root_s and root_s in self._list_vars:
                    self._list_vars.remove(root_s)
                self._move_resource(src_name)
        full = f"{i.module}__{i.fn_name}" if i.module else i.fn_name

        # v5.49.0 Wn.1 — direct ``__mn_*`` extern call. Same registry
        # check as ``_do_call``: if the symbol has a canonical signature
        # registered, route through ``_rt`` for ABI-correct lowering
        # instead of falling through to the auto-declare path.
        if not i.module and full in _RUNTIME_FN_SIGS:
            sig_ret, sig_pts = _RUNTIME_FN_SIGS[full]
            sig_coerced: list[tuple[str, str]] = []
            for j, (v, t) in enumerate(args):
                et = sig_pts[j] if j < len(sig_pts) else t
                sig_coerced.append((self._coerce(v, t, et) if t != et else v, et))
            if sig_ret == VOID:
                self._rt(full, sig_ret, list(sig_pts), sig_coerced)
                self._put(i.dest, "0", I1)
            else:
                rsig = self._rt(full, sig_ret, list(sig_pts), sig_coerced, nm="ec")
                if sig_ret == STR:
                    self._track_string(rsig)
                self._put(i.dest, rsig, sig_ret)
            return

        if full not in self._sigs:
            pts = [self._rty(a.ty) for a in i.args]
            for j, pt in enumerate(pts):
                if pt == PTR and j < len(args) and args[j][1] != PTR:
                    pts[j] = args[j][1]
            self._decl_fn(full, self._rty(i.dest.ty), pts)
        ret, pts, _ = self._sigs[full]
        coerced: list[tuple[str, str]] = []
        for j, (v, t) in enumerate(args):
            et = pts[j] if j < len(pts) else t
            coerced.append((self._coerce(v, t, et) if t != et else v, et))
        astr = ", ".join(f"{t} {v}" for v, t in coerced)
        if ret == VOID:
            self._L(f"call void @{full}({astr})")
            self._put(i.dest, "0", I1)
        else:
            r = self._f("ec")
            self._L(f"{r} = call {ret} @{full}({astr})")
            self._put(i.dest, r, ret)

    # --- Return ---
    def _do_ret(self, i: Return) -> None:
        if i.val is not None:
            v, t = self._get(i.val)
            assert self._fn is not None
            rt = self._rty(self._fn.return_type)
            if rt == VOID:
                self._emit_drop_glue(None, VOID)
                self._emit_arena_destroy()
                self._L("ret void")
            elif self._fn_use_sret:
                # Store return value into sret pointer and return void
                v = self._coerce(v, t, self._fn_sret_ty) if t != self._fn_sret_ty else v
                self._emit_drop_glue(v, self._fn_sret_ty)
                self._emit_arena_destroy()
                self._L(f"store {self._fn_sret_ty} {v}, ptr {self._sret_ptr}")
                self._L("ret void")
            elif self._fn_unified_ret:
                # v4.145.0 E1: store to unified-ret alloca + branch.
                # After inlining, SROA decomposes the alloca into scalar PHIs,
                # enabling SimplifyCFG to merge redundant enum switches.
                urt = self._fn_unified_ret_ty
                v = self._coerce(v, t, urt) if t != urt else v
                self._emit_drop_glue(v, urt)
                self._emit_arena_destroy()
                self._L(f"store {urt} {v}, ptr %__ret_alloca")
                self._L("br label %__unified_ret")
            else:
                v = self._coerce(v, t, rt) if t != rt else v
                self._emit_drop_glue(v, rt)
                self._emit_arena_destroy()
                self._L(f"ret {rt} {v}")
        else:
            self._emit_drop_glue(None, VOID)
            self._emit_arena_destroy()
            if self._fn_use_sret:
                self._L("ret void")
            elif self._fn_unified_ret:
                urt = self._fn_unified_ret_ty
                self._L(f"store {urt} zeroinitializer, ptr %__ret_alloca")
                self._L("br label %__unified_ret")
            else:
                self._L("ret void")

    # --- Jump / Branch / Switch ---
    def _do_jump(self, i: Jump) -> None:
        self._L(f"br label %{i.target}")

    def _do_branch(self, i: Branch) -> None:
        cv, ct = self._get(i.cond)
        if ct != I1:
            if self._is_ptr(ct):
                cv = self._coerce(cv, ct, I64)
                ct = I64
            if ct == I64:
                t = self._f("bc")
                self._L(f"{t} = icmp ne i64 {cv}, 0")
                cv = t
            elif ct == I1:
                pass
            else:
                cv = self._coerce(cv, ct, I1)
        self._L(f"br i1 {cv}, label %{i.true_block}, label %{i.false_block}")

    def _do_switch(self, i: Switch) -> None:
        tv, tt = self._get(i.tag)
        tv = self._coerce(tv, tt, I64) if tt != I64 else tv
        en = i.tag.ty.type_info.name if i.tag.ty else ""
        cases: list[str] = []
        seen: set[int] = set()
        for cv, cl in i.cases:
            if isinstance(cv, str) and not cv.lstrip("-").isdigit():
                iv = self._vtag(cv, en)
            else:
                iv = int(cv)
            if iv in seen:
                continue
            seen.add(iv)
            cases.append(f"    i64 {iv}, label %{cl}")
        cl = "\n".join(cases)
        self._L(f"switch i64 {tv}, label %{i.default_block} [\n{cl}\n  ]")

    # --- StructInit ---
    def _do_struct_init(self, i: StructInit) -> None:
        sn = self._res_struct(i.struct_type.type_info.name)
        if sn in self._struct_ty:
            sty = self._struct_ty[sn]
            fidx = self._struct_idx.get(sn, {})
            boxed = self._boxed_struct.get(sn, set())
            rn = _zero(sty) if not i.fields else "undef"
            cur = rn
            for pos, (fname, fval) in enumerate(i.fields):
                v, t = self._get(fval)
                idx = fidx.get(fname, pos)
                if idx in boxed:
                    sz = _tsz(t)
                    raw = self._rt("malloc", PTR, [I64], [(str(sz), I64)], "box")
                    tp = raw  # opaque ptr, no bitcast
                    self._L(f"store {t} {v}, ptr {tp}")
                    v, t = raw, PTR
                else:
                    et = (
                        self._structs[sn][idx][1]
                        if sn in self._structs and idx < len(self._structs[sn])
                        else t
                    )
                    if t != et:
                        v = self._coerce(v, t, et)
                        t = et
                nxt = self._f("si")
                self._L(f"{nxt} = insertvalue {sty} {cur}, {t} {v}, {idx}")
                cur = nxt
                # v4.101.0: move semantics — the field value is now
                # owned by the struct. Zero its tracking slot so drop
                # glue does not free the buffer the struct now holds a
                # pointer to. Mirrors the fix in _do_list_push (see
                # its comment for the root-cause rationale).
                #
                # v4.103.0: also drop the value from _list_vars so the
                # list drop-glue pass skips it. The original v4.101.0
                # fix covered strings and boxed enums (`_str_slots`,
                # `_boxed_slots`) but left list tracking untouched.
                # Parser code like ``new Block { stmts: stmts }`` lost
                # its List<Stmt> buffer at parse_block's return,
                # aliasing every nested block's stmts into whatever
                # the allocator reused that address for — observed
                # as the self-hosted semantic checker infinite-
                # recursing on nested if/else because the inner else
                # clause aliased the outer else body.
                if fval.name in self._list_vars:
                    self._list_vars.remove(fval.name)
                root_fv = self._lroots.get(fval.name)
                if root_fv and root_fv in self._list_vars:
                    self._list_vars.remove(root_fv)
                self._move_resource(fval.name)
            self._put(i.dest, cur, sty)
        else:
            # unknown struct
            if i.fields:
                fvals = [self._get(fv) for _, fv in i.fields]
                ftypes = [t for _, t in fvals]
                sty = "{" + ", ".join(ftypes) + "}"
                cur = "undef"
                for idx, (v, t) in enumerate(fvals):
                    nxt = self._f("si")
                    self._L(f"{nxt} = insertvalue {sty} {cur}, {t} {v}, {idx}")
                    cur = nxt
                self._put(i.dest, cur, sty)
            else:
                self._put(i.dest, "null", PTR)

    # --- FieldGet ---
    def _do_field_get(self, i: FieldGet) -> None:
        sn = self._res_struct(i.obj.ty.type_info.name)
        pi = self._get_ptr(i.obj)
        if pi and sn in self._struct_idx and i.field_name in self._struct_idx[sn]:
            addr, aty = pi
            sty = self._struct_ty.get(sn, aty)
            # opaque ptr: no bitcast needed even if aty != sty
            idx = self._struct_idx[sn][i.field_name]
            fp = self._f("fg")
            self._L(f"{fp} = getelementptr inbounds {sty}, ptr {addr}, i32 0, i32 {idx}")
            ft = self._structs[sn][idx][1]
            boxed = self._boxed_struct.get(sn, set())
            if idx in boxed:
                raw = self._f("fr")
                self._L(f"{raw} = load ptr, ptr {fp}")
                at = (
                    self._rty(self._boxed_struct_mir[sn][idx])
                    if sn in self._boxed_struct_mir and idx in self._boxed_struct_mir[sn]
                    else PTR
                )
                if at != PTR:
                    r = self._f("fv")
                    self._L(f"{r} = load {at}, ptr {raw}")
                    self._put(i.dest, r, at)
                else:
                    self._put(i.dest, raw, PTR)
            else:
                r = self._f("fv")
                self._L(f"{r} = load {ft}, ptr {fp}")
                self._put(i.dest, r, ft)
            return
        # fallback: extractvalue
        ov, ot = self._get(i.obj)
        # If value is a pointer, dereference through the struct type
        if self._is_ptr(ot) and sn in self._struct_ty:
            sty = self._struct_ty[sn]
            tp = ov  # opaque ptr, no bitcast needed
            sv = self._f("fld")
            self._L(f"{sv} = load {sty}, ptr {tp}")
            ov, ot = sv, sty
        if sn in self._struct_idx and i.field_name in self._struct_idx[sn]:
            idx = self._struct_idx[sn][i.field_name]
            ft = self._structs[sn][idx][1] if sn in self._structs else PTR
            if self._is_ptr(ot):
                # Still a pointer — can't extractvalue, return as-is
                self._put(i.dest, ov, ot)
            else:
                r = self._f("ev")
                self._L(f"{r} = extractvalue {ot} {ov}, {idx}")
                # If struct lookup gave ptr but dest type is a struct, use dest type
                if ft == PTR and i.dest.ty:
                    dt = self._rty(i.dest.ty)
                    if dt != VOID and dt != PTR:
                        ft = dt
                self._put(i.dest, r, ft)
        else:
            if self._is_ptr(ot):
                self._put(i.dest, ov, ot)
            elif ot.startswith("{"):
                r = self._f("ev")
                self._L(f"{r} = extractvalue {ot} {ov}, 0")
                # Infer field 0 type: prefer dest type, fall back to parsing struct
                ft0 = self._rty(i.dest.ty) if i.dest.ty else PTR
                if ft0 == VOID or ft0 == PTR:
                    ft0 = _struct_field0_type(ot)
                self._put(i.dest, r, ft0)
            else:
                self._put(i.dest, ov, ot)

    # --- FieldSet ---
    def _do_field_set(self, i: FieldSet) -> None:
        vv, vt = self._get(i.val)
        sn = self._res_struct(i.obj.ty.type_info.name)
        pi = self._get_ptr(i.obj)
        if pi and sn in self._struct_idx and i.field_name in self._struct_idx[sn]:
            addr, aty = pi
            sty = self._struct_ty.get(sn, aty)
            # opaque ptr: no bitcast needed even if aty != sty
            idx = self._struct_idx[sn][i.field_name]
            fp = self._f("fs")
            self._L(f"{fp} = getelementptr inbounds {sty}, ptr {addr}, i32 0, i32 {idx}")
            ft = self._structs[sn][idx][1]
            boxed = self._boxed_struct.get(sn, set())
            if idx in boxed:
                sz = _tsz(vt)
                raw = self._rt("malloc", PTR, [I64], [(str(sz), I64)], "box")
                tp = raw  # opaque ptr, no bitcast
                self._L(f"store {vt} {vv}, ptr {tp}")
                self._L(f"store ptr {raw}, ptr {fp}")
            else:
                if vt != ft:
                    vv = self._coerce(vv, vt, ft)
                self._L(f"store {ft} {vv}, ptr {fp}")
            # v4.101.0: move semantics for the stored value (see
            # _do_list_push / _do_struct_init for the rationale).
            # v4.103.0: also drop from _list_vars (see _do_struct_init).
            if i.val.name in self._list_vars:
                self._list_vars.remove(i.val.name)
            root_v = self._lroots.get(i.val.name)
            if root_v and root_v in self._list_vars:
                self._list_vars.remove(root_v)
            self._move_resource(i.val.name)
            return
        # fallback: insertvalue
        ov, ot = self._get(i.obj)
        if sn in self._struct_idx and i.field_name in self._struct_idx[sn]:
            idx = self._struct_idx[sn][i.field_name]
            ft = self._structs[sn][idx][1] if sn in self._structs else vt
            if vt != ft:
                vv = self._coerce(vv, vt, ft)
            r = self._f("iv")
            self._L(f"{r} = insertvalue {ot} {ov}, {ft} {vv}, {idx}")
            self._put(i.obj, r, ot)
            # v4.101.0 + v4.103.0: move semantics for the stored value.
            if i.val.name in self._list_vars:
                self._list_vars.remove(i.val.name)
            root_v2 = self._lroots.get(i.val.name)
            if root_v2 and root_v2 in self._list_vars:
                self._list_vars.remove(root_v2)
            self._move_resource(i.val.name)

    # --- ListInit ---
    def _do_list_init(self, i: ListInit) -> None:
        ety = self._rty(i.elem_type)
        if ety == PTR and i.elements:
            ev, et = self._get(i.elements[0])
            if et != PTR:
                ety = et
        esz = _tsz(ety)
        # Ge.1r: when the element type is unknown (empty [] without type context),
        # _rty returns "ptr" and _tsz returns 8.  This is wrong for lists that
        # may hold structs — LLVM's DSE can propagate the too-small elem_size
        # backwards into the original list variable at -O2, causing heap overreads.
        # Use a safe upper bound (256) for empty lists with unknown element type
        # so that any struct element fits, matching the self-hosted emitter's
        # 384 heuristic.
        if not i.elements and esz <= 8 and i.elem_type.kind in (TypeKind.UNKNOWN,):
            esz = 256
        lv = self._rt("__mn_list_new", LIST, [I64], [(str(esz), I64)], "ln")
        self._track_container(i.dest.name, "list")
        if i.elements:
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {lv}, ptr {la}")
            self._ensure("__mn_list_push", VOID, ["ptr", PTR])
            for j, elem in enumerate(i.elements):
                ev, et = self._get(elem)
                ea = self._alloca(et, "ea")
                self._L(f"store {et} {ev}, ptr {ea}")
                ep = self._f("ep")
                ep = ea  # opaque ptr, no bitcast
                # v4.101.0 + v4.103.0: move element ownership into the
                # list so drop glue does not free the backing buffer
                # (see _do_list_push for the full rationale).
                if elem.name in self._list_vars:
                    self._list_vars.remove(elem.name)
                root_e = self._lroots.get(elem.name)
                if root_e and root_e in self._list_vars:
                    self._list_vars.remove(root_e)
                self._move_resource(elem.name)
                self._L(f"call void @__mn_list_push(ptr {la}, ptr {ep})")
            r = self._f("ll")
            self._L(f"{r} = load {LIST}, ptr {la}")
            lv = r
        self._put(i.dest, lv, LIST)

    # --- TensorInit (v4.42.0) ---
    def _do_tensor_init(self, i: TensorInit) -> None:
        """Emit LLVM IR for a tensor literal.

        1. Stack-allocate shape array: [N x i64]
        2. Store each shape dimension
        3. Call __mn_tensor_alloc(rank, shape_ptr, elem_size)
        4. Call __mn_tensor_store_f64/i64 for each element
        """
        rank = len(i.shape)
        elem_kind = i.elem_type.kind

        # Step 1: Allocate shape array on stack
        shape_a = self._alloca(f"[{rank} x i64]", "tshape")
        for dim_idx, dim_val in enumerate(i.shape):
            gep = self._f("tsd")
            self._L(
                f"{gep} = getelementptr inbounds [{rank} x i64], ptr {shape_a}, i64 0, i64 {dim_idx}"  # noqa: E501
            )
            self._L(f"store i64 {dim_val}, ptr {gep}")

        # Step 2: Determine element size
        from mapanare.types import TypeKind as TK

        elem_size = 8  # sizeof(double) or sizeof(int64_t)

        # Step 3: Call __mn_tensor_alloc
        self._ensure("__mn_tensor_alloc", PTR, [I64, PTR, I64])
        tp = self._f("tp")
        self._L(
            f"{tp} = call noalias ptr @__mn_tensor_alloc("
            f"i64 {rank}, ptr {shape_a}, i64 {elem_size})"
        )

        # Step 4: Store each element
        if elem_kind in (TK.INT, TK.BOOL):
            store_fn = "__mn_tensor_store_i64"
            store_ty = I64
        else:
            store_fn = "__mn_tensor_store_f64"
            store_ty = DBL
        self._ensure(store_fn, VOID, [PTR, I64, store_ty])

        for j, elem in enumerate(i.elements):
            ev, et = self._get(elem)
            cv = self._coerce(ev, et, store_ty) if et != store_ty else ev
            self._L(f"call void @{store_fn}(ptr {tp}, i64 {j}, {store_ty} {cv})")

        # Track for drop glue
        self._tensor_vars.append(i.dest.name)
        self._put(i.dest, tp, PTR)

    # --- ListPush ---
    def _do_list_push(self, i: ListPush) -> None:
        # Get the source list's alloca and push directly to it
        src = i.list_val.name
        root = self._lroots.get(src, src)
        pi = self._get_ptr(Value(name=root, ty=i.list_val.ty))
        if pi is None:
            pi = self._get_ptr(i.list_val)
        if pi:
            a, t = pi
            # Push directly to the source alloca (modifies in-place)
            ev, et = self._get(i.element)
            ea = self._alloca(et, "ea")
            self._L(f"store {et} {ev}, ptr {ea}")
            ep = ea  # opaque ptr, no bitcast
            # v4.101.0: move semantics — the element's ownership is
            # transferred to the list. Zero out the element's tracking
            # slot so drop glue does not free a buffer the list now
            # owns a pointer to. Without this, heap-allocated strings
            # pushed into a List<String> get use-after-freed at
            # function return; readers of the list later see garbage
            # where the first bytes of each pushed string should be.
            # (Root cause for the self-hosted emitter's 16-byte
            # garbage prefix on every `declare` line of mnc-stage1's
            # output.)
            # v4.103.0: also drop from _list_vars so list drop-glue
            # doesn't free pushed-list buffers (List<List<T>> case).
            if i.element.name in self._list_vars:
                self._list_vars.remove(i.element.name)
            root_e = self._lroots.get(i.element.name)
            if root_e and root_e in self._list_vars:
                self._list_vars.remove(root_e)
            self._move_resource(i.element.name)
            self._ensure("__mn_list_push", VOID, ["ptr", PTR])
            # Use the SOURCE alloca directly for push (not a copy)
            if t != LIST:
                bc = a  # opaque ptr, no bitcast
                self._L(f"call void @__mn_list_push(ptr {bc}, ptr {ep})")
            else:
                self._L(f"call void @__mn_list_push(ptr {a}, ptr {ep})")
            # Load updated list
            r = self._f("ul")
            self._L(f"{r} = load {LIST}, ptr {a}" if t == LIST else f"{r} = load {t}, ptr {a}")
            self._put(i.dest, r, LIST)
            self._lroots[i.dest.name] = root
            # Write-back to source and root aliases
            for tn in {root, src, i.list_val.name}:
                for k in (tn, tn.lstrip("%"), "%" + tn.lstrip("%")):
                    if k in self._alloc and k != i.dest.name:
                        ta, tt = self._alloc[k]
                        if ta != a:
                            wv = self._coerce(r, LIST, tt) if LIST != tt else r
                            self._L(f"store {tt} {wv}, ptr {ta}")
        else:
            # Fallback: original approach with temp alloca
            lv, lt = self._get(i.list_val)
            lv = self._coerce(lv, lt, LIST) if lt != LIST else lv
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {lv}, ptr {la}")
            ev, et = self._get(i.element)
            ea = self._alloca(et, "ea")
            self._L(f"store {et} {ev}, ptr {ea}")
            ep = ea  # opaque ptr, no bitcast
            # v4.101.0 + v4.103.0 (see _do_list_push main path above):
            # move the element into the list so drop glue does not free it.
            if i.element.name in self._list_vars:
                self._list_vars.remove(i.element.name)
            root_e = self._lroots.get(i.element.name)
            if root_e and root_e in self._list_vars:
                self._list_vars.remove(root_e)
            self._move_resource(i.element.name)
            self._ensure("__mn_list_push", VOID, ["ptr", PTR])
            self._L(f"call void @__mn_list_push(ptr {la}, ptr {ep})")
            r = self._f("ul")
            self._L(f"{r} = load {LIST}, ptr {la}")
            self._put(i.dest, r, LIST)
            self._lroots[i.dest.name] = root

    # --- IndexGet ---
    def _do_idx_get(self, i: IndexGet) -> None:
        ov, ot = self._get(i.obj)
        iv, it = self._get(i.index)
        ok = i.obj.ty.kind
        if ok == TypeKind.UNKNOWN and ot == LIST:
            ok = TypeKind.LIST
        if ok == TypeKind.LIST:
            ov = self._coerce(ov, ot, LIST) if ot != LIST else ov
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {ov}, ptr {la}")
            iv = self._coerce(iv, it, I64) if it != I64 else iv
            ety = self._rty(i.dest.ty)
            # v5.1.0 Perf.1: inline list access for 8-byte value-type elements.
            # Replaces opaque call @__mn_list_get with GEP+load so LLVM can
            # see through to the backing buffer (enables SROA, vectorization,
            # loop hoisting). Gate: elem size == 8 covers List<Int>, List<Float>,
            # List<Ptr>. String (16B), Bool (1B), structs → slow path.
            if _tsz(ety) == 8:
                # Inline bounds check (unsigned covers negative indices)
                lenp = self._f("lg.lenp")
                self._L(f"{lenp} = getelementptr inbounds {LIST}, ptr {la}, i32 0, i32 1")
                ln = self._f("lg.len")
                self._L(f"{ln} = load i64, ptr {lenp}")
                oob = self._f("lg.oob")
                self._L(f"{oob} = icmp uge i64 {iv}, {ln}")
                trap_lbl = f"lg.trap.{self._c}"
                ok_lbl = f"lg.ok.{self._c}"
                self._c += 1
                self._L(f"br i1 {oob}, label %{trap_lbl}, label %{ok_lbl}")
                # Trap block
                self._blk[trap_lbl] = []
                self._cb = trap_lbl
                self._ensure("abort", VOID, [])
                self._L("call void @abort()")
                self._L("unreachable")
                # Fast path: inline GEP + load
                self._blk[ok_lbl] = []
                self._cb = ok_lbl
                dp = self._f("lg.dp")
                self._L(f"{dp} = getelementptr inbounds {LIST}, ptr {la}, i32 0, i32 0")
                data = self._f("lg.data")
                self._L(f"{data} = load ptr, ptr {dp}")
                ep = self._f("lg.ep")
                self._L(f"{ep} = getelementptr inbounds i64, ptr {data}, i64 {iv}")
                r = self._f("lg.v")
                self._L(f"{r} = load {ety}, ptr {ep}")
                self._put(i.dest, r, ety)
            else:
                # Slow path: opaque call for String, Bool, structs, etc.
                raw = self._rt("__mn_list_get", PTR, ["ptr", I64], [(la, "ptr"), (iv, I64)])
                if ety == PTR:
                    self._put(i.dest, raw, PTR)
                else:
                    tp = raw  # opaque ptr, no bitcast
                    r = self._f("el")
                    self._L(f"{r} = load {ety}, ptr {tp}")
                    self._put(i.dest, r, ety)
        elif ok == TypeKind.STRING:
            r = self._rt("__mn_str_byte_at", I64, [STR, I64], [(ov, ot), (iv, it)])
            self._put(i.dest, r, I64)
        elif ok == TypeKind.MAP:
            ka = self._alloca(it, "ka")
            self._L(f"store {it} {iv}, ptr {ka}")
            kp = ka  # opaque ptr, no bitcast
            raw = self._rt("__mn_map_get", PTR, [PTR, PTR], [(ov, ot), (kp, PTR)])
            ety = self._rty(i.dest.ty)
            tp = raw  # opaque ptr, no bitcast
            r = self._f("mv")
            self._L(f"{r} = load {ety}, ptr {tp}")
            self._put(i.dest, r, ety)
        else:
            self._put(i.dest, "null", PTR)

    # --- IndexSet ---
    def _do_idx_set(self, i: IndexSet) -> None:
        ov, ot = self._get(i.obj)
        iv, it = self._get(i.index)
        vv, vt = self._get(i.val)
        if i.obj.ty.kind == TypeKind.LIST:
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {ov}, ptr {la}")
            iv = self._coerce(iv, it, I64) if it != I64 else iv
            # v5.1.0 Perf.1: inline list store for 8-byte value-type elements.
            if _tsz(vt) == 8:
                # Inline bounds check
                lenp = self._f("ls.lenp")
                self._L(f"{lenp} = getelementptr inbounds {LIST}, ptr {la}, i32 0, i32 1")
                ln = self._f("ls.len")
                self._L(f"{ln} = load i64, ptr {lenp}")
                oob = self._f("ls.oob")
                self._L(f"{oob} = icmp uge i64 {iv}, {ln}")
                trap_lbl = f"ls.trap.{self._c}"
                ok_lbl = f"ls.ok.{self._c}"
                self._c += 1
                self._L(f"br i1 {oob}, label %{trap_lbl}, label %{ok_lbl}")
                # Trap block
                self._blk[trap_lbl] = []
                self._cb = trap_lbl
                self._ensure("abort", VOID, [])
                self._L("call void @abort()")
                self._L("unreachable")
                # Fast path: inline GEP + store
                self._blk[ok_lbl] = []
                self._cb = ok_lbl
                dp = self._f("ls.dp")
                self._L(f"{dp} = getelementptr inbounds {LIST}, ptr {la}, i32 0, i32 0")
                data = self._f("ls.data")
                self._L(f"{data} = load ptr, ptr {dp}")
                ep = self._f("ls.ep")
                self._L(f"{ep} = getelementptr inbounds i64, ptr {data}, i64 {iv}")
                self._L(f"store {vt} {vv}, ptr {ep}")
            else:
                # Slow path: opaque call for String, structs, etc.
                raw = self._rt("__mn_list_get", PTR, ["ptr", I64], [(la, "ptr"), (iv, I64)])
                tp = raw  # opaque ptr, no bitcast
                self._L(f"store {vt} {vv}, ptr {tp}")
        elif i.obj.ty.kind == TypeKind.MAP:
            ka = self._alloca(it, "ka")
            self._L(f"store {it} {iv}, ptr {ka}")
            kp = ka  # opaque ptr, no bitcast
            va = self._alloca(vt, "va")
            self._L(f"store {vt} {vv}, ptr {va}")
            vp = va  # opaque ptr, no bitcast
            self._rt("__mn_map_set", VOID, [PTR, PTR, PTR], [(ov, ot), (kp, PTR), (vp, PTR)])

    # --- MapInit ---
    def _do_map_init(self, i: MapInit) -> None:
        # v5.39.2 Js.4.B.2: derive ksz / vsz / ktag from MapInit's declared
        # key/val MIRTypes regardless of whether the literal has initial
        # pairs. Pre-fix the empty-literal branch hardcoded (8, 8, 0)
        # which mis-sized any non-Int-keyed empty map (e.g.
        # `Map<String, JsonValue> = #{}` got 8-byte buckets and key_type
        # tag 0/INT, so subsequent String inserts wrote past the bucket
        # and lookups missed). decode_object's `entries: Map<String,
        # JsonValue> = #{}` was the load-bearing example.
        ksz = _tsz(self._rty(i.key_type))
        ktag = (
            1
            if i.key_type.kind == TypeKind.STRING
            else (2 if i.key_type.kind == TypeKind.FLOAT else 0)
        )
        if i.pairs:
            fk, _ = self._get(i.pairs[0][0])
            fv, fvt = self._get(i.pairs[0][1])
            vsz = _tsz(fvt)
        else:
            vsz = _tsz(self._rty(i.val_type))
        vtag = 1 if i.val_type.kind == TypeKind.STRING else 0
        mp = self._rt(
            "__mn_map_new",
            PTR,
            [I64, I64, I64, I64],
            [(str(ksz), I64), (str(vsz), I64), (str(ktag), I64), (str(vtag), I64)],
        )
        self._track_container(i.dest.name, "map")
        for kv, vv in i.pairs:
            k, kt = self._get(kv)
            v, vt = self._get(vv)
            ka = self._alloca(kt, "mk")
            self._L(f"store {kt} {k}, ptr {ka}")
            kp = ka  # opaque ptr, no bitcast
            va = self._alloca(vt, "mv")
            self._L(f"store {vt} {v}, ptr {va}")
            vp = va  # opaque ptr, no bitcast
            self._rt("__mn_map_set", VOID, [PTR, PTR, PTR], [(mp, PTR), (kp, PTR), (vp, PTR)])
        self._put(i.dest, mp, PTR)

    # --- EnumInit ---
    def _do_enum_init(self, i: EnumInit) -> None:
        en = self._res_enum(i.enum_type.type_info.name)
        if en in self._enums:
            tags, pays, sizes = self._enums[en]
            tag = tags.get(i.variant, 0)
            boxed = self._boxed_enum.get(en, set())
            ptypes = pays.get(i.variant, [])
            # v4.124.0 Rt.1: inline representation — no malloc, no drop
            # glue. Each payload field is packed into its own i64 slot
            # (Int direct; Float bitcast; Bool/small-int zext; pointer
            # ptrtoint). Unused slots store 0.
            inline_slots = self._enum_inline.get(en, 0)
            if inline_slots > 0:
                enum_ty = self._enum_ty(en)
                n_slots = max(inline_slots, 1)
                packed: list[str] = []
                for j in range(n_slots):
                    if j < len(ptypes) and j < len(i.payload):
                        pval = i.payload[j]
                        ft = self._rty(ptypes[j])
                        if pval.name in self._list_vars:
                            self._list_vars.remove(pval.name)
                        if pval.name in self._map_vars:
                            self._map_vars.remove(pval.name)
                        self._move_resource(pval.name)
                        root_name = self._lroots.get(pval.name)
                        if root_name and root_name in self._list_vars:
                            self._list_vars.remove(root_name)
                        if root_name and root_name in self._map_vars:
                            self._map_vars.remove(root_name)
                        v, t = self._get(pval)
                        if t != ft:
                            v = self._coerce(v, t, ft)
                        packed.append(self._pack_to_i64(v, ft))
                    else:
                        packed.append("0")
                cur = self._f("ei")
                self._L(f"{cur} = insertvalue {enum_ty} undef, i64 {tag}, 0")
                for j, iv in enumerate(packed):
                    nxt = self._f("ei")
                    self._L(f"{nxt} = insertvalue {enum_ty} {cur}, i64 {iv}, {j + 1}")
                    cur = nxt
                self._put(i.dest, cur, enum_ty)
                return
            # Build payload struct type
            pflds: list[str] = []
            for j, pt in enumerate(ptypes):
                if (i.variant, j) in boxed:
                    pflds.append(PTR)
                else:
                    pflds.append(self._rty(pt))
            if i.payload and pflds:
                psty = "{" + ", ".join(pflds) + "}"
                psz = max(_tsz(psty), 8)
                self._ensure("malloc", PTR, [I64])
                raw = self._f("ep")
                self._L(f"{raw} = call ptr @malloc(i64 {psz})")
                self._track_boxed(raw)
                tp = raw  # opaque ptr, no bitcast
                for j, pval in enumerate(i.payload):
                    # Move semantics: payloads are consumed by the enum.
                    # v5.39.2 Js.4.B.2: also drain _map_vars so a Map
                    # payload (e.g. JsonValue::Object) isn't deep-freed
                    # by the enclosing function's drop glue while it's
                    # still owned by the enum payload.
                    if pval.name in self._list_vars:
                        self._list_vars.remove(pval.name)
                    if pval.name in self._map_vars:
                        self._map_vars.remove(pval.name)
                    self._move_resource(pval.name)
                    # Also check root alias (push write-backs)
                    root_name = self._lroots.get(pval.name)
                    if root_name and root_name in self._list_vars:
                        self._list_vars.remove(root_name)
                    if root_name and root_name in self._map_vars:
                        self._map_vars.remove(root_name)
                    # For list values, check if there's a root alloca from push
                    # write-backs (the copy alias may be stale)
                    if root_name and root_name in self._alloc:
                        a_root, t_root = self._alloc[root_name]
                        v = self._f("rl")
                        self._L(f"{v} = load {t_root}, ptr {a_root}")
                        t = t_root
                    else:
                        v, t = self._get(pval)
                    fp = self._f("ef")
                    self._L(f"{fp} = getelementptr inbounds {psty}, ptr {tp}, i32 0, i32 {j}")
                    if (i.variant, j) in boxed:
                        bsz = _tsz(t)
                        bp = self._f("eb")
                        self._L(f"{bp} = call ptr @malloc(i64 {bsz})")
                        btp = bp  # opaque ptr, no bitcast
                        self._L(f"store {t} {v}, ptr {btp}")
                        self._L(f"store ptr {bp}, ptr {fp}")
                    else:
                        ft = pflds[j]
                        if t != ft:
                            v = self._coerce(v, t, ft)
                        self._L(f"store {ft} {v}, ptr {fp}")
                pp = raw
            else:
                pp = "null"
            # Build {tag, payload_ptr}
            s0 = self._f("ei")
            self._L(f"{s0} = insertvalue {{i64, ptr}} undef, i64 {tag}, 0")
            s1 = self._f("ei")
            pp_c = self._coerce(pp, PTR, PTR) if pp != "null" else "null"
            self._L(f"{s1} = insertvalue {{i64, ptr}} {s0}, ptr {pp_c}, 1")
            self._put(i.dest, s1, ENUM)
            # Record boxed association for move semantics
            if self._last_tracked_boxed_slot:
                self._boxed_slots[i.dest.name] = self._last_tracked_boxed_slot
                self._last_tracked_boxed_slot = None
        else:
            self._put(i.dest, "0", I64)

    # --- EnumTag ---
    def _do_enum_tag(self, i: EnumTag) -> None:
        ev, et = self._get(i.enum_val)
        if et == I64:
            self._put(i.dest, ev, I64)
            return
        if self._is_ptr(et):
            r = self._f("et")
            self._L(f"{r} = ptrtoint ptr {ev} to i64")
            self._put(i.dest, r, I64)
            return
        # Extract field 0 (tag) from any struct type
        r = self._f("et")
        self._L(f"{r} = extractvalue {et} {ev}, 0")
        # Determine the extracted type
        inner = et.strip()
        if inner.startswith("{") and inner.endswith("}"):
            fields = _split_fields(inner[1:-1].strip())
            tag_ty = fields[0].strip() if fields else I64
        else:
            tag_ty = I64
        if tag_ty == I64:
            self._put(i.dest, r, I64)
        else:
            r2 = self._f("etz")
            self._L(f"{r2} = zext {tag_ty} {r} to i64")
            self._put(i.dest, r2, I64)

    # --- EnumPayload ---
    def _do_enum_payload(self, i: EnumPayload) -> None:
        en = self._res_enum(i.enum_val.ty.type_info.name)
        if en in self._enums:
            _, pays, _ = self._enums[en]
            ptypes = pays.get(i.variant, [])
            boxed = self._boxed_enum.get(en, set())
            if not ptypes:
                self._put(i.dest, "0", I1)
                return
            # v4.124.0 Rt.1: inline extraction — extract i64 from the
            # relevant payload slot and unpack to the field type (no
            # pointer chase, no load).
            if self._enum_inline.get(en, 0) > 0:
                inline_ty = self._enum_ty(en)
                ev, et = self._get(i.enum_val)
                if self._is_ptr(et):
                    ev = self._coerce(ev, et, inline_ty)
                    et = inline_ty
                idx = i.payload_idx if len(ptypes) > 1 else 0
                slot_idx = idx + 1  # tag occupies slot 0
                raw = self._f("pr")
                self._L(f"{raw} = extractvalue {et} {ev}, {slot_idx}")
                ft = self._rty(ptypes[idx])
                val = self._unpack_from_i64(raw, ft)
                self._put(i.dest, val, ft)
                return
            ev, et = self._get(i.enum_val)
            if self._is_ptr(et):
                ev = self._coerce(ev, et, ENUM)
                et = ENUM
            raw = self._f("pr")
            self._L(f"{raw} = extractvalue {et} {ev}, 1")
            pflds: list[str] = []
            for j, pt in enumerate(ptypes):
                if (i.variant, j) in boxed:
                    pflds.append(PTR)
                else:
                    pflds.append(self._rty(pt))
            psty = "{" + ", ".join(pflds) + "}"
            tp = raw  # opaque ptr, no bitcast
            idx = i.payload_idx if len(ptypes) > 1 else 0
            fp = self._f("pf")
            self._L(f"{fp} = getelementptr inbounds {psty}, ptr {tp}, i32 0, i32 {idx}")
            ft = pflds[idx]
            r = self._f("pv")
            self._L(f"{r} = load {ft}, ptr {fp}")
            if (i.variant, idx) in boxed:
                at = self._rty(ptypes[idx])
                utp = r  # opaque ptr, no bitcast
                r2 = self._f("puv")
                self._L(f"{r2} = load {at}, ptr {utp}")
                self._put(i.dest, r2, at)
            else:
                self._put(i.dest, r, ft)
        else:
            # Result/Option
            ev, et = self._get(i.enum_val)
            v = i.variant
            try:
                if v == "Ok":
                    r = self._f("ok")
                    self._L(f"{r} = extractvalue {et} {ev}, 1, 0")
                elif v == "Err":
                    r = self._f("er")
                    self._L(f"{r} = extractvalue {et} {ev}, 1, 1")
                elif v == "Some":
                    r = self._f("sm")
                    self._L(f"{r} = extractvalue {et} {ev}, 1")
                else:
                    r = self._f("pl")
                    self._L(f"{r} = extractvalue {et} {ev}, 1")
                # Determine result type from the extracted value
                dt = self._rty(i.dest.ty)
                if dt == VOID:
                    dt = PTR
                self._put(i.dest, r, dt)
            except Exception:
                self._put(i.dest, "null", PTR)

    # --- Option/Result wrappers ---
    def _do_wrap_some(self, i: WrapSome) -> None:
        v, t = self._get(i.val)
        ot = f"{{i1, {t}}}"
        s0 = self._f("ws")
        self._L(f"{s0} = insertvalue {ot} undef, i1 1, 0")
        s1 = self._f("ws")
        self._L(f"{s1} = insertvalue {ot} {s0}, {t} {v}, 1")
        self._put(i.dest, s1, ot)

    def _do_wrap_none(self, i: WrapNone) -> None:
        ty = self._rty(i.ty)
        self._put(i.dest, _zero(ty), ty)

    def _do_wrap_ok(self, i: WrapOk) -> None:
        # v5.36.0 Js.0.B: when dest carries full Result<Ok, Err> type info,
        # use it so the produced struct shape matches downstream consumers.
        # Pre-fix the Err slot was hardcoded as `ptr`, which mismatched the
        # alloca size when the consumer (e.g. Js.4 from_json) uses the full
        # typed alloca. Falls back to legacy `{i1, {t, ptr}}` shape when the
        # dest is a generic Result with no args (existing behavior).
        v, t = self._get(i.val)
        if i.dest.ty.kind == TypeKind.RESULT:
            a = i.dest.ty.type_info.args
            if len(a) >= 2:
                ok_ty = self._rti(a[0])
                err_ty = self._rti(a[1])
                rt = f"{{i1, {{{ok_ty}, {err_ty}}}}}"
                s0 = self._f("wo")
                self._L(f"{s0} = insertvalue {rt} undef, i1 1, 0")
                s1 = self._f("wo")
                self._L(f"{s1} = insertvalue {rt} {s0}, {ok_ty} {v}, 1, 0")
                self._put(i.dest, s1, rt)
                return
        rt = f"{{i1, {{{t}, ptr}}}}"
        s0 = self._f("wo")
        self._L(f"{s0} = insertvalue {rt} undef, i1 1, 0")
        s1 = self._f("wo")
        self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 0")
        self._put(i.dest, s1, rt)

    def _do_wrap_err(self, i: WrapErr) -> None:
        # v5.36.0 Js.0.B: sister fix to _do_wrap_ok. Same shape rationale.
        v, t = self._get(i.val)
        if i.dest.ty.kind == TypeKind.RESULT:
            a = i.dest.ty.type_info.args
            if len(a) >= 2:
                ok_ty = self._rti(a[0])
                err_ty = self._rti(a[1])
                rt = f"{{i1, {{{ok_ty}, {err_ty}}}}}"
                s0 = self._f("we")
                self._L(f"{s0} = insertvalue {rt} undef, i1 0, 0")
                s1 = self._f("we")
                self._L(f"{s1} = insertvalue {rt} {s0}, {err_ty} {v}, 1, 1")
                self._put(i.dest, s1, rt)
                return
        rt = f"{{i1, {{ptr, {t}}}}}"
        s0 = self._f("we")
        self._L(f"{s0} = insertvalue {rt} undef, i1 0, 0")
        s1 = self._f("we")
        self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 1")
        self._put(i.dest, s1, rt)

    def _do_unwrap(self, i: Unwrap) -> None:
        v, t = self._get(i.val)
        # Eu.1 (v5.26.1): Result is `{i1, {Ok_ty, Err_ty}}`. The single
        # `extractvalue ..., 1` returns the *inner* aggregate, not the Ok
        # payload, so consumers typed as Ok_ty get a width mismatch. Two
        # extractvalues — field 1 of outer (inner aggregate) then field 0
        # of inner (Ok payload) — and the dest's stored type becomes Ok_ty.
        if i.val.ty.kind == TypeKind.RESULT:
            a = i.val.ty.type_info.args
            if len(a) >= 2:
                ok_ty = self._rti(a[0])
                err_ty = self._rti(a[1])
                inner_ty = "{" + ok_ty + ", " + err_ty + "}"
                inner = self._f("uw_inner")
                self._L(f"{inner} = extractvalue {t} {v}, 1")
                r = self._f("uw")
                self._L(f"{r} = extractvalue {inner_ty} {inner}, 0")
                self._put(i.dest, r, ok_ty)
                return
        r = self._f("uw")
        self._L(f"{r} = extractvalue {t} {v}, 1")
        dt = self._rty(i.dest.ty) if i.dest.ty.kind != TypeKind.UNKNOWN else PTR
        self._put(i.dest, r, dt)

    # --- InterpConcat ---
    def _do_interp(self, i: InterpConcat) -> None:
        if not i.parts:
            sv, st = self._mkstr("")
            self._put(i.dest, sv, st)
            return
        parts: list[tuple[str, str]] = []
        for pv in i.parts:
            v, t = self._get(pv)
            pk = pv.ty.kind
            if pk == TypeKind.STRING or t == STR:
                parts.append((self._coerce(v, t, STR) if t != STR else v, STR))
            elif pk == TypeKind.INT:
                s = self._rt("__mn_str_from_int", STR, [I64], [(v, t)])
                self._track_string(s)
                parts.append((s, STR))
            elif pk == TypeKind.FLOAT:
                s = self._rt("__mn_str_from_float", STR, [DBL], [(v, t)])
                self._track_string(s)
                parts.append((s, STR))
            elif pk == TypeKind.BOOL:
                bv = self._coerce(v, t, I64) if t != I64 else v
                s = self._rt("__mn_str_from_bool", STR, [I64], [(bv, I64)])
                self._track_string(s)
                parts.append((s, STR))
            else:
                s = self._rt("__mn_str_from_int", STR, [I64], [(self._coerce(v, t, I64), I64)])
                self._track_string(s)
                parts.append((s, STR))
        cur = parts[0][0]
        self._ensure("__mn_str_concat", STR, [STR, STR])
        for pstr, _ in parts[1:]:
            r = self._f("ic")
            self._L(
                f"{r} = call {{ptr, i64}} @__mn_str_concat({{ptr, i64}} {cur}, {{ptr, i64}} {pstr})"
            )
            self._track_string(r)
            cur = r
        self._put(i.dest, cur, STR)

    # --- Closure ---
    def _do_clos_create(self, i: ClosureCreate) -> None:
        # Strip % from lambda function names
        if i.fn_name.startswith("%"):
            i.fn_name = i.fn_name[1:]
        ctypes = [self._rty(ct) for ct in i.capture_types]
        if not ctypes:
            fnp = "null"
            if i.fn_name in self._sigs:
                fnp = f"@{i.fn_name}"  # function is already ptr
            s0 = self._f("cc")
            self._L(f"{s0} = insertvalue {{ptr, ptr}} undef, ptr {fnp}, 0")
            s1 = self._f("cc")
            self._L(f"{s1} = insertvalue {{ptr, ptr}} {s0}, ptr null, 1")
            self._put(i.dest, s1, CLOS)
            return
        esty = "{" + ", ".join(ctypes) + "}"
        esz = sum(_tsz(t) for t in ctypes)
        esz = max(esz, 8)
        self._ensure("malloc", PTR, [I64])
        raw = self._f("ce")
        self._L(f"{raw} = call ptr @malloc(i64 {esz})")
        etp = raw  # opaque ptr, no bitcast
        for j, cv in enumerate(i.captures):
            v, t = self._get(cv)
            et = ctypes[j]
            if t != et:
                v = self._coerce(v, t, et)
            fp = self._f("cf")
            self._L(f"{fp} = getelementptr inbounds {esty}, ptr {etp}, i32 0, i32 {j}")
            self._L(f"store {et} {v}, ptr {fp}")
        fnp = "null"
        if i.fn_name in self._sigs:
            fnp = f"@{i.fn_name}"  # function is already ptr
        s0 = self._f("cc")
        self._L(f"{s0} = insertvalue {{ptr, ptr}} undef, ptr {fnp}, 0")
        s1 = self._f("cc")
        self._L(f"{s1} = insertvalue {{ptr, ptr}} {s0}, ptr {raw}, 1")
        self._track_closure(s1)
        self._put(i.dest, s1, CLOS)

    def _do_clos_call(self, i: ClosureCall) -> None:
        cv, ct = self._get(i.closure)
        args = [self._get(a) for a in i.args]
        cv = self._coerce(cv, ct, CLOS) if ct != CLOS else cv
        fnr = self._f("cfn")
        self._L(f"{fnr} = extractvalue {{ptr, ptr}} {cv}, 0")
        envr = self._f("cen")
        self._L(f"{envr} = extractvalue {{ptr, ptr}} {cv}, 1")
        rty = self._rty(i.dest.ty)
        if rty == VOID or rty == PTR:
            # Try to infer return type from the lambda function signature
            # by scanning the current function for ClosureCreate that produced this closure
            inferred = self._infer_closure_ret(i.closure.name)
            rty = inferred if inferred else I64
        ftp = fnr  # opaque ptr, function is already ptr
        astr = ", ".join(f"{t} {v}" for v, t in args)
        astr = f"ptr {envr}, {astr}" if astr else f"ptr {envr}"
        r = self._f("ccr")
        self._L(f"{r} = call {rty} {ftp}({astr})")
        self._put(i.dest, r, rty)

    def _infer_closure_ret(self, closure_name: str) -> str | None:
        """Find the return type of a closure by tracing ClosureCreate → fn signature."""
        if self._fn is None:
            return None
        for bb in self._fn.blocks:
            for inst in bb.instructions:
                if isinstance(inst, ClosureCreate) and inst.dest.name == closure_name:
                    fn_name = inst.fn_name.lstrip("%")
                    if fn_name in self._sigs:
                        ret, _, _ = self._sigs[fn_name]
                        if ret != VOID and ret != PTR:
                            return ret
        return None

    def _do_env_load(self, i: EnvLoad) -> None:
        ev, et = self._get(i.env)
        ft = self._rty(i.val_type)
        pflds: list[str] = []
        for j in range(i.index + 1):
            pflds.append(ft if j == i.index else I64)
        esty = "{" + ", ".join(pflds) + "}"
        fp = self._f("elf")
        self._L(f"{fp} = getelementptr inbounds {esty}, ptr {ev}, i32 0, i32 {i.index}")
        r = self._f("elv")
        self._L(f"{r} = load {ft}, ptr {fp}")
        self._put(i.dest, r, ft)

    # --- Agent ---
    def _do_agent_spawn(self, i: AgentSpawn) -> None:
        atn = i.agent_type.type_info.name or "agent"
        ns, _ = self._mkstr(atn)
        np = self._f("anp")
        self._L(f"{np} = extractvalue {{ptr, i64}} {ns}, 0")
        hn = f"__mn_handler_{atn}"
        hp = "null"
        if hn in self._sigs:
            hp = f"@{hn}"  # function is already ptr
        self._ensure("mapanare_agent_new", PTR, [PTR, PTR, PTR, I32, I32])
        self._ensure("mapanare_agent_spawn", I32, [PTR])
        ap = self._rt(
            "mapanare_agent_new",
            PTR,
            [PTR, PTR, PTR, I32, I32],
            [(np, PTR), (hp, PTR), ("null", PTR), ("256", I32), ("256", I32)],
        )
        self._rt("mapanare_agent_spawn", I32, [PTR], [(ap, PTR)])
        self._put(i.dest, ap, PTR)

    def _do_agent_send(self, i: AgentSend) -> None:
        av, at = self._get(i.agent)
        vv, vt = self._get(i.val)
        va = self._alloca(vt, "as")
        self._L(f"store {vt} {vv}, ptr {va}")
        vp = va  # opaque ptr, no bitcast
        self._ensure("mapanare_agent_send", I32, [PTR, PTR])
        self._rt("mapanare_agent_send", I32, [PTR, PTR], [(av, at), (vp, PTR)])

    def _do_agent_sync(self, i: AgentSync) -> None:
        av, at = self._get(i.agent)
        op = self._alloca(PTR, "ao")
        self._ensure("mapanare_agent_recv_blocking", I32, [PTR, "ptr"])
        self._rt("mapanare_agent_recv_blocking", I32, [PTR, "ptr"], [(av, at), (op, "ptr")])
        raw = self._f("ar")
        self._L(f"{raw} = load ptr, ptr {op}")
        tt = self._rty(i.dest.ty)
        if tt == VOID:
            self._put(i.dest, "0", I1)
        else:
            tp = raw  # opaque ptr, no bitcast
            r = self._f("arv")
            self._L(f"{r} = load {tt}, ptr {tp}")
            self._put(i.dest, r, tt)

    # --- Signal ---
    def _do_sig_init(self, i: SignalInit) -> None:
        v, t = self._get(i.initial_val)
        vsz = _tsz(t)
        va = self._alloca(t, "sv")
        self._L(f"store {t} {v}, ptr {va}")
        vp = va  # opaque ptr, no bitcast
        r = self._rt("__mn_signal_new", PTR, [PTR, I64], [(vp, PTR), (str(vsz), I64)])
        self._track_container(i.dest.name, "signal")
        self._put(i.dest, r, PTR)

    def _do_sig_get(self, i: SignalGet) -> None:
        sv, st = self._get(i.signal)
        raw = self._rt("__mn_signal_get", PTR, [PTR], [(sv, st)])
        tt = self._rty(i.dest.ty)
        if tt == VOID:
            self._put(i.dest, "0", I1)
        else:
            tp = raw  # opaque ptr, no bitcast
            r = self._f("sgv")
            self._L(f"{r} = load {tt}, ptr {tp}")
            self._put(i.dest, r, tt)

    def _do_sig_set(self, i: SignalSet) -> None:
        sv, st = self._get(i.signal)
        vv, vt = self._get(i.val)
        va = self._alloca(vt, "ssv")
        self._L(f"store {vt} {vv}, ptr {va}")
        vp = va  # opaque ptr, no bitcast
        self._rt("__mn_signal_set", VOID, [PTR, PTR], [(sv, st), (vp, PTR)])

    def _do_sig_comp(self, i: SignalComputed) -> None:
        fp = "null"
        if i.compute_fn in self._sigs:
            fp = f"@{i.compute_fn}"  # function is already ptr
        nd = len(i.deps)
        if nd > 0:
            dat = f"[{nd} x ptr]"
            da = self._alloca(dat, "sda")
            for j, dv in enumerate(i.deps):
                d, dt = self._get(dv)
                gp = self._f("sdg")
                self._L(f"{gp} = getelementptr inbounds {dat}, ptr {da}, i64 0, i64 {j}")
                dc = self._coerce(d, dt, PTR) if dt != PTR else d
                self._L(f"store ptr {dc}, ptr {gp}")
            dp = da  # opaque ptr, no bitcast
        else:
            dp = "null"
        r = self._rt(
            "__mn_signal_computed",
            PTR,
            [PTR, PTR, PTR, I64, I64],
            [(fp, PTR), ("null", PTR), (dp, PTR), (str(nd), I64), (str(i.val_size), I64)],
        )
        self._put(i.dest, r, PTR)

    def _do_sig_sub(self, i: SignalSubscribe) -> None:
        sv, st = self._get(i.signal)
        sub, subt = self._get(i.subscriber)
        self._rt("__mn_signal_subscribe", VOID, [PTR, PTR], [(sv, st), (sub, subt)])

    # --- Stream ---
    def _do_stream_init(self, i: StreamInit) -> None:
        sv, st = self._get(i.source)
        sv = self._coerce(sv, st, LIST) if st != LIST else sv
        la = self._alloca(LIST, "slp")
        self._L(f"store {LIST} {sv}, ptr {la}")
        r = self._rt("__mn_stream_from_list", PTR, ["ptr", I64], [(la, "ptr"), ("8", I64)])
        self._track_container(i.dest.name, "stream")
        self._put(i.dest, r, PTR)

    def _do_stream_op(self, i: StreamOp) -> None:
        sv, st = self._get(i.source)
        if i.op_kind == StreamOpKind.MAP:
            fp = self._stream_fn(i)
            r = self._rt(
                "__mn_stream_map",
                PTR,
                [PTR, PTR, PTR, I64],
                [(sv, st), (fp, PTR), ("null", PTR), ("8", I64)],
            )
            self._track_container(i.dest.name, "stream")
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.FILTER:
            fp = self._stream_fn(i)
            r = self._rt(
                "__mn_stream_filter", PTR, [PTR, PTR, PTR], [(sv, st), (fp, PTR), ("null", PTR)]
            )
            self._track_container(i.dest.name, "stream")
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.TAKE:
            nv, nt = self._get(i.args[0]) if i.args else ("0", I64)
            r = self._rt("__mn_stream_take", PTR, [PTR, I64], [(sv, st), (nv, nt)])
            self._track_container(i.dest.name, "stream")
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.SKIP:
            nv, nt = self._get(i.args[0]) if i.args else ("0", I64)
            r = self._rt("__mn_stream_skip", PTR, [PTR, I64], [(sv, st), (nv, nt)])
            self._track_container(i.dest.name, "stream")
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.COLLECT:
            r = self._rt("__mn_stream_collect", LIST, [PTR, I64], [(sv, st), ("8", I64)])
            self._track_container(i.dest.name, "list")
            self._put(i.dest, r, LIST)
        elif i.op_kind == StreamOpKind.FOLD:
            if len(i.args) >= 2:
                iv, it = self._get(i.args[0])
                fp = self._stream_fn(i, 1)
                ia = self._alloca(it, "fi")
                self._L(f"store {it} {iv}, ptr {ia}")
                ip = ia  # opaque ptr, no bitcast
                oa = self._alloca(it, "fo")
                op = oa  # opaque ptr, no bitcast
                self._rt(
                    "__mn_stream_fold",
                    VOID,
                    [PTR, PTR, I64, PTR, PTR, PTR],
                    [
                        (sv, st),
                        (ip, PTR),
                        (str(_tsz(it)), I64),
                        (fp, PTR),
                        ("null", PTR),
                        (op, PTR),
                    ],
                )
                r = self._f("fv")
                self._L(f"{r} = load {it}, ptr {oa}")
                self._put(i.dest, r, it)
            else:
                self._put(i.dest, "0", I64)
        else:
            self._put(i.dest, sv, st)

    def _stream_fn(self, i: StreamOp, idx: int = 0) -> str:
        if i.fn_name and i.fn_name in self._sigs:
            r = f"@{i.fn_name}"  # function is already ptr
            return r
        return "null"

    # --- Coroutine await (v4.73.0 — inline resume) ---

    def _do_await_suspend(self, i: AwaitSuspend) -> None:
        """Emit await expression with real coroutine suspension or inline-resume.

        v4.92.0: inside an async function, emits a real coro.save +
        coro.suspend + switch that yields control back to the scheduler.
        The scheduler resumes us when the awaited future becomes Ready.

        In non-async context (should not happen — semantic checker
        prevents this), falls back to inline-resume for safety.
        """
        fv, _ft = self._get(i.future)
        n = self._c
        self._c += 1

        if self._fn_is_async:
            # ── Real suspension (v4.92.0) ──
            # First, resume the inner coroutine once to start it (it begins
            # at its initial suspend point and needs one resume to enter its body).
            drive_lbl = f"await.drive.{n}"
            check_lbl = f"await.check.{n}"
            suspend_lbl = f"await.suspend.{n}"
            resume_lbl = f"await.resume.{n}"
            ready_lbl = f"await.ready.{n}"

            # Check if future is already ready (fast path)
            st_ptr = self._f("aw.st.ptr")
            st_val = self._f("aw.st")
            is_rdy = self._f("aw.rdy")
            self._L(f"{st_ptr} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 0")
            self._L(f"{st_val} = load i8, ptr {st_ptr}")
            self._L(f"{is_rdy} = icmp eq i8 {st_val}, 1")
            self._L(f"br i1 {is_rdy}, label %{ready_lbl}, label %{drive_lbl}")

            # Drive: resume the inner coroutine once, then check again
            self._blk[drive_lbl] = []
            self._cb = drive_lbl
            hdl_ptr = self._f("aw.hdl.ptr")
            hdl = self._f("aw.hdl")
            self._L(f"{hdl_ptr} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
            self._L(f"{hdl} = load ptr, ptr {hdl_ptr}")
            self._L(f"call void @llvm.coro.resume(ptr {hdl})")
            self._L(f"br label %{check_lbl}")

            # Check: is the future ready after driving?
            self._blk[check_lbl] = []
            self._cb = check_lbl
            st2 = self._f("aw.st2")
            rdy2 = self._f("aw.rdy2")
            self._L(f"{st2} = load i8, ptr {st_ptr}")
            self._L(f"{rdy2} = icmp eq i8 {st2}, 1")
            self._L(f"br i1 {rdy2}, label %{ready_lbl}, label %{suspend_lbl}")

            # Suspend: register wait and yield to scheduler
            self._blk[suspend_lbl] = []
            self._cb = suspend_lbl
            # Register that our coroutine is waiting on this future
            self._L(f"call void @__mn_coro_register_wait(ptr %coro.hdl, ptr {fv})")
            # Save + suspend the outer coroutine
            save_tok = self._f("aw.save")
            susp_val = self._f("aw.susp")
            self._L(f"{save_tok} = call token @llvm.coro.save(ptr %coro.hdl)")
            self._L(f"{susp_val} = call i8 @llvm.coro.suspend(token {save_tok}, i1 false)")
            self._L(f"switch i8 {susp_val}, label %coro.ret [")
            self._L(f"  i8 0, label %{resume_lbl}")
            self._L("  i8 1, label %coro.cleanup")
            self._L("]")

            # Resume: scheduler woke us up — future should be ready now
            self._blk[resume_lbl] = []
            self._cb = resume_lbl
            self._L(f"br label %{ready_lbl}")

            # Ready: extract value from future
            self._blk[ready_lbl] = []
            self._cb = ready_lbl
            val_ptr = self._f("aw.val.ptr")
            val_box = self._f("aw.val.box")
            val_raw = self._f("aw.val")
            self._L(f"{val_ptr} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
            self._L(f"{val_box} = load ptr, ptr {val_ptr}")
            self._L(f"{val_raw} = load i64, ptr {val_box}")
            self._put(i.dest, val_raw, "i64")
        else:
            # ── Inline-resume fallback (non-async context) ──
            # Should not normally happen (semantic checker rejects await
            # outside async fn), but kept for robustness.
            check_lbl = f"await.check.{n}"
            drive_lbl = f"await.drive.{n}"
            ready_lbl = f"await.ready.{n}"

            st_ptr = self._f("aw.st.ptr")
            st_val = self._f("aw.st")
            is_rdy = self._f("aw.rdy")
            self._L(f"{st_ptr} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 0")
            self._L(f"{st_val} = load i8, ptr {st_ptr}")
            self._L(f"{is_rdy} = icmp eq i8 {st_val}, 1")
            self._L(f"br i1 {is_rdy}, label %{ready_lbl}, label %{drive_lbl}")

            self._blk[drive_lbl] = []
            self._cb = drive_lbl
            hdl_ptr = self._f("aw.hdl.ptr")
            hdl = self._f("aw.hdl")
            self._L(f"{hdl_ptr} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
            self._L(f"{hdl} = load ptr, ptr {hdl_ptr}")
            self._L(f"call void @llvm.coro.resume(ptr {hdl})")
            self._L(f"br label %{check_lbl}")

            self._blk[check_lbl] = []
            self._cb = check_lbl
            st2 = self._f("aw.st2")
            rdy2 = self._f("aw.rdy2")
            self._L(f"{st2} = load i8, ptr {st_ptr}")
            self._L(f"{rdy2} = icmp eq i8 {st2}, 1")
            self._L(f"br i1 {rdy2}, label %{ready_lbl}, label %{drive_lbl}")

            self._blk[ready_lbl] = []
            self._cb = ready_lbl
            val_ptr = self._f("aw.val.ptr")
            val_box = self._f("aw.val.box")
            val_raw = self._f("aw.val")
            self._L(f"{val_ptr} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
            self._L(f"{val_box} = load ptr, ptr {val_ptr}")
            self._L(f"{val_raw} = load i64, ptr {val_box}")
            self._put(i.dest, val_raw, "i64")

    def _do_block_on(self, i: BlockOn) -> None:
        """Emit block_on(future): drive coroutine to completion, extract result.

        v4.92.0: registers the coroutine with the scheduler and calls
        __mn_coro_scheduler_run() to drive all pending coroutines.
        Falls back to inline resume loop if no scheduler is available
        (module without async functions — shouldn't happen in practice).
        """
        fv, _ft = self._get(i.future)
        n = self._c
        self._c += 1
        done_lbl = f"block_on.done.{n}"

        if getattr(self, "_module_has_async", False):
            # ── Scheduler-driven block_on (v4.92.0) ──
            # Extract handle from future and register with scheduler
            hp = self._f("bo.hdl.ptr")
            hd = self._f("bo.hdl")
            self._L(f"{hp} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
            self._L(f"{hd} = load ptr, ptr {hp}")
            # Register the coroutine; scheduler will resume it
            self._L(f"call void @__mn_coro_scheduler_register(ptr {hd})")
            # Run the scheduler — this drives ALL pending coroutines
            # including the one we just registered, until they all complete.
            self._L("call void @__mn_coro_scheduler_run()")
            self._L(f"br label %{done_lbl}")
        else:
            # ── Inline resume fallback ──
            loop_lbl = f"block_on.loop.{n}"
            hp = self._f("bo.hdl.ptr")
            hd = self._f("bo.hdl")
            self._L(f"{hp} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
            self._L(f"{hd} = load ptr, ptr {hp}")
            self._L(f"br label %{loop_lbl}")

            self._blk[loop_lbl] = []
            self._cb = loop_lbl
            self._L(f"call void @llvm.coro.resume(ptr {hd})")
            dn = self._f("bo.done")
            self._L(f"{dn} = call i1 @llvm.coro.done(ptr {hd})")
            self._L(f"br i1 {dn}, label %{done_lbl}, label %{loop_lbl}")

        # Done — extract value, destroy, free.
        # v4.102.0: the coroutine's final-suspend path overwrites
        # ``future.payload`` (slot 1 of the {i8, ptr} Future) with the
        # boxed return value — so after scheduler_run completes, that
        # slot no longer holds the coroutine handle. The old code
        # reloaded slot 1 a second time for llvm.coro.destroy, which
        # handed the destroy intrinsic a pointer to an 8-byte malloc'd
        # int and segfaulted at destroy_fn. Reuse the ``hd`` loaded
        # before scheduler_run — that's the real handle.
        self._blk[done_lbl] = []
        self._cb = done_lbl
        vp = self._f("bo.val.ptr")
        vb = self._f("bo.val.box")
        vr = self._f("bo.val")
        self._L(f"{vp} = getelementptr inbounds {{i8, ptr}}, ptr {fv}, i32 0, i32 1")
        self._L(f"{vb} = load ptr, ptr {vp}")
        self._L(f"{vr} = load i64, ptr {vb}")
        # Destroy coroutine frame + free future and box. ``hd`` was
        # loaded above (before scheduler_run / resume loop) and still
        # points to the coroutine frame — safe to pass to
        # llvm.coro.destroy. The destroy intrinsic lowers to
        # handle[8](handle) — the destroy_fn pointer, still valid
        # after the resume-fn slot was nulled on final suspend.
        self._L(f"call void @llvm.coro.destroy(ptr {hd})")
        self._L(f"call void @free(ptr {vb})")
        self._L(f"call void @free(ptr {fv})")
        self._put(i.dest, vr, "i64")

    # --- Assert ---
    def _do_assert(self, i: Assert) -> None:
        cv, ct = self._get(i.cond)
        cv = self._coerce(cv, ct, I1) if ct != I1 else cv
        pb = self._f("ap").lstrip("%")
        fb = self._f("af").lstrip("%")
        self._L(f"br i1 {cv}, label %{pb}, label %{fb}")
        # fail block
        self._blk[fb] = []
        self._cb = fb
        # v5.13.1 At.1: surface the user-supplied message (if any) so
        # `mapanare test` can show meaningful failure context. Pre-v5.13.1
        # this only printed location, dropping the message Value built
        # by lower._lower_assert (a real-bug, not a missing feature).
        if i.message is not None:
            self._printf(f"assertion failed at {i.filename}:{i.line}: ", [])
            mv, mt = self._get(i.message)
            mv = self._coerce(mv, mt, STR) if mt != STR else mv
            self._rt("__mn_str_println", VOID, [STR], [(mv, STR)])
        else:
            self._printf(f"assertion failed at {i.filename}:{i.line}\\n", [])
        self._ensure("exit", VOID, [I64])
        self._L("call void @exit(i64 1)")
        self._L("unreachable")
        # pass block
        self._blk[pb] = []
        self._cb = pb
        # continue emitting in pass block — the caller's block is now pb
        # We need to add these blocks to the function
        assert self._fn is not None
        # These dynamic blocks will be emitted since they're in self._blk

    # ── agent handler wrapper ───────────────────────────────────────
    def _emit_agent_wrap(self, agent_name: str, info: Any) -> str:
        """Generate the per-agent ``__mn_handler_<name>`` thunk.

        v4.30.0 Phase 2: previously this was a no-op stub — it stored
        ``null`` into ``*out_msg`` and returned ``0``, which meant
        spawned agents received messages from the runtime worker but
        produced no reply, the outbox was never pushed, and
        ``sync a.reply`` deadlocked or returned garbage (v4.26.0 panel:
        Rattler #3 HIGH). The stub shipped for nine releases because
        grammar-level agents parse and the scheduler path runs —
        nothing *crashed*, so nobody noticed the dispatch path was
        dead.

        The real wrapper:

        1. Finds the agent's ``handle`` method in ``info.method_names``
           (convention: ``{agent_name}_handle``, built by
           ``lower._lower_agent``).
        2. Looks up its MIR signature — the single input type is the
           agent's ``input`` channel payload, the return type is the
           ``output`` channel payload.
        3. Loads the caller-stored input value from ``msg`` (``msg`` is
           a ``ptr`` to an alloca the sender wrote via
           ``_do_agent_send``).
        4. Calls the user's handle function.
        5. ``malloc``'s a stable buffer sized for the output type,
           stores the result there, writes the buffer pointer into
           ``*out_msg``, and returns ``0``. The buffer leaks per
           message — a leak is the right trade-off here because the
           receiver side (``_do_agent_sync``) loads the value directly
           from the buffer and has no ownership story. Free-on-receive
           is a v5.x arena-reuse item, not a v4.30.0 recovery item.
        6. Signals ABI errors (missing ``handle``, sret disagreements)
           by falling back to the historical null-and-zero stub so the
           compile keeps moving; every fallback is logged in
           ``self._agent_wrap_fallbacks`` for the session report.

        Large (>8-byte) return types use the LLVM ``sret`` ABI: the
        caller allocates, we pass the buffer as the sret arg, and the
        function returns ``void``. We mirror that convention by
        allocating ``result_buf`` *first* and passing it as the sret
        parameter; for scalar returns we capture the return value and
        ``store`` into the buffer manually.
        """
        hn = f"__mn_handler_{agent_name}"
        # The wrapper's own signature is fixed by the runtime ABI.
        self._sigs[hn] = (I32, [PTR, PTR, "ptr"], False)

        # 1. Find the handle method. Convention: ``{agent_name}_handle``.
        method_names = getattr(info, "method_names", None) or []
        handle_fn: str | None = None
        for mn_name in method_names:
            if mn_name == f"{agent_name}_handle" or mn_name.endswith("_handle"):
                handle_fn = mn_name
                break
        if handle_fn is None:
            return self._emit_agent_wrap_fallback(
                hn, agent_name, reason="no handle method in method_names"
            )

        sig = self._sigs.get(handle_fn)
        if sig is None:
            return self._emit_agent_wrap_fallback(
                hn, agent_name, reason=f"{handle_fn} signature not registered"
            )
        ret_ty, param_tys, _is_va = sig
        if len(param_tys) != 1:
            # The agent handle method convention is (input) -> output.
            # If lowering produced a different shape (e.g. because of
            # ``self`` threading), fall back rather than guess.
            return self._emit_agent_wrap_fallback(
                hn,
                agent_name,
                reason=f"{handle_fn} has {len(param_tys)} params, expected 1",
            )
        in_ty = param_tys[0]

        large_ret = self._is_large_struct(ret_ty)
        ret_sz = max(_tsz(ret_ty), 1)  # malloc(0) is implementation-defined

        # Ensure malloc is available to the wrapper.
        self._ensure("malloc", PTR, [I64])

        lines: list[str] = [
            f"define i32 @{hn}(ptr %agent_data, ptr %msg, ptr %out_msg) {{",
            "entry:",
            f"  ; v4.30.0 wired dispatch → {handle_fn}({in_ty}) -> {ret_ty}",
            # Load the input value from %msg.
            f"  %in_val = load {in_ty}, ptr %msg",
            # Allocate a heap buffer for the reply.
            f"  %result_buf = call ptr @malloc(i64 {ret_sz})",
        ]

        if ret_ty == "void":
            # Void-returning handle: just invoke, store null into out.
            lines.append(f"  call void @{handle_fn}({in_ty} %in_val)")
            lines.append("  store ptr null, ptr %out_msg")
        elif large_ret:
            # sret ABI: function returns void, first arg is the sret
            # buffer. %result_buf is already the right shape.
            lines.append(
                f"  call void @{handle_fn}(ptr sret({ret_ty}) %result_buf, {in_ty} %in_val)"
            )
            lines.append("  store ptr %result_buf, ptr %out_msg")
        else:
            # Scalar return: capture it and store through the buffer.
            lines.append(f"  %ret_val = call {ret_ty} @{handle_fn}({in_ty} %in_val)")
            lines.append(f"  store {ret_ty} %ret_val, ptr %result_buf")
            lines.append("  store ptr %result_buf, ptr %out_msg")

        lines.append("  ret i32 0")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)

    def _emit_agent_wrap_fallback(self, hn: str, agent_name: str, reason: str) -> str:
        """Emit the historical null-and-zero stub and record the reason.

        Used when ``_emit_agent_wrap`` cannot find a usable ``handle``
        method. Keeps the build moving — the old stub is what shipped
        through v4.29.0 — and logs the reason so the session report
        can show which agents (if any) fell back. On the golden corpus
        the list should be empty; a non-empty list is a signal that
        the lowering contract drifted.
        """
        if not hasattr(self, "_agent_wrap_fallbacks"):
            self._agent_wrap_fallbacks: list[tuple[str, str]] = []
        self._agent_wrap_fallbacks.append((agent_name, reason))
        out = [
            f"define i32 @{hn}(ptr %agent_data, ptr %msg, ptr %out_msg) {{",
            "entry:",
            f"  ; v4.30.0 fallback stub — {reason}",
            "  store ptr null, ptr %out_msg",
            "  ret i32 0",
            "}",
            "",
        ]
        return "\n".join(out)

    # ── pipe definition ─────────────────────────────────────────────
    def _emit_pipe(self, pipe_name: str, pipe_info: MIRPipeInfo) -> str:
        self._sigs[pipe_name] = (PTR, [PTR], False)
        if not pipe_info.stages:
            return (
                f"define internal ptr @{pipe_name}(ptr %input) {{\nentry:\n  ret ptr %input\n}}\n"
            )
        # Emit agent spawn chain: spawn each stage, send data through, recv result
        self._ensure("mapanare_agent_new", PTR, [PTR, PTR, PTR, I32, I32])
        self._ensure("mapanare_agent_spawn", I32, [PTR])
        self._ensure("mapanare_agent_send", I32, [PTR, PTR])
        self._ensure("mapanare_agent_recv_blocking", I32, [PTR, "ptr"])
        self._ensure("mapanare_agent_stop", VOID, [PTR])
        lines = [
            f"define internal ptr @{pipe_name}(ptr %input) {{",
            "entry:",
        ]
        cur = "%input"
        for i, stage in enumerate(pipe_info.stages):
            hn = f"__mn_handler_{stage}"
            hp = "null"
            if hn in self._sigs:
                hp = f"@{hn}"
            lines.append(f"  %name.{i} = alloca [1 x i8], align 1")
            lines.append(
                f"  %np.{i} = getelementptr inbounds [1 x i8], ptr %name.{i}, i64 0, i64 0"
            )
            lines.append(
                f"  %ag.{i} = call ptr @mapanare_agent_new(ptr %np.{i}, ptr {hp},"
                f" ptr null, i32 256, i32 256)"
            )
            lines.append(f"  call i32 @mapanare_agent_spawn(ptr %ag.{i})")
            lines.append(f"  call i32 @mapanare_agent_send(ptr %ag.{i}, ptr {cur})")
            lines.append(f"  %outp.{i} = alloca ptr, align 8")
            lines.append(f"  call i32 @mapanare_agent_recv_blocking(ptr %ag.{i}, ptr %outp.{i})")
            lines.append(f"  %out.{i} = load ptr, ptr %outp.{i}")
            lines.append(f"  call void @mapanare_agent_stop(ptr %ag.{i})")
            cur = f"%out.{i}"
        lines.append(f"  ret ptr {cur}")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)
