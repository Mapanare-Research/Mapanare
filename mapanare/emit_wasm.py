"""WebAssembly text format (WAT) emitter that consumes MIR.

Translates MIR basic blocks, instructions, and phi nodes into WebAssembly
text format (.wat). The emitter produces a self-contained WASM module with:

- Linear memory (bump-allocated heap)
- String constant data section
- Imported JS bridge functions (console_log, etc.)
- Exported main function and memory
- Full control flow via structured blocks/loops/br_if

Type mapping (Mapanare -> WASM):
    Int       -> i64
    Float     -> f64
    Bool      -> i32 (0 or 1)
    String    -> i32 (pointer into linear memory)
    List      -> i32 (pointer to heap-allocated {len, cap, data_ptr})
    Map       -> i32 (pointer to heap-allocated hash table)
    Struct    -> i32 (pointer to heap-allocated fields)
    Option    -> i32 (tagged pointer: tag + payload)
    Result    -> i32 (tagged pointer: tag + payload)
    Agent     -> i32 (pointer to agent struct)
    Stream    -> i32 (pointer to stream struct)
    Signal    -> i32 (pointer to signal struct)
    Tensor    -> i32 (pointer to tensor struct)
    Void      -> (no value)

Usage:
    from mapanare.emit_wasm import compile_to_wasm
    wat_text = compile_to_wasm(mir_module)
"""

from __future__ import annotations

import logging
import struct
import subprocess
from dataclasses import dataclass, field
from typing import Any

from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
    BasicBlock,
    BinOp,
    BinOpKind,
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
    Instruction,
    InterpConcat,
    Jump,
    ListInit,
    ListPush,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Phi,
    Return,
    SignalComputed,
    SignalGet,
    SignalInit,
    SignalSet,
    SignalSubscribe,
    StreamInit,
    StreamOp,
    StructInit,
    Switch,
    UnaryOp,
    UnaryOpKind,
    Unwrap,
    Value,
    WrapErr,
    WrapNone,
    WrapOk,
    WrapSome,
)
from mapanare.types import TypeKind

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WASM type strings
# ---------------------------------------------------------------------------

_WASM_I32 = "i32"
_WASM_I64 = "i64"
_WASM_F64 = "f64"

# Heap layout constants (byte sizes)
_PTR_SIZE = 4  # i32 pointers in wasm32
_I64_SIZE = 8
_F64_SIZE = 8
_I32_SIZE = 4

# String layout: [i32 len][i32 cap][...bytes...]
_STRING_HEADER_SIZE = 8  # len (4) + cap (4)

# List layout: [i32 len][i32 cap][i32 elem_size][i32 data_ptr]
_LIST_HEADER_SIZE = 16

# Option/Result layout: [i32 tag][i64 payload]
_TAGGED_UNION_SIZE = 12  # tag (4) + payload (8)

# Signal layout: [i64 value][i32 subscriber_count][i32 subscribers_ptr]
_SIGNAL_SIZE = 16

# Stream layout: [i32 source_ptr][i32 state][i32 callback_idx]
_STREAM_SIZE = 12

# Agent layout: [i32 state_ptr][i32 inbox_ptr][i32 outbox_ptr][i32 status]
_AGENT_SIZE = 16

# Default linear memory: 1 page = 64 KiB
_INITIAL_MEMORY_PAGES = 1
_MAX_MEMORY_PAGES = 256  # 16 MiB max

# Bump allocator globals
_HEAP_BASE_GLOBAL = "__heap_base"
_HEAP_PTR_GLOBAL = "__heap_ptr"


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class WasmOptions:
    """Configuration for the WASM emitter."""

    module_name: str = "mapanare_module"
    initial_memory_pages: int = _INITIAL_MEMORY_PAGES
    max_memory_pages: int = _MAX_MEMORY_PAGES
    export_all_functions: bool = False
    debug_names: bool = True
    optimize: bool = False


# ---------------------------------------------------------------------------
# String table
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class StringConstant:
    """A string constant stored in the data section."""

    value: str
    offset: int  # Byte offset in linear memory
    byte_length: int  # Length of UTF-8 encoded bytes


# ---------------------------------------------------------------------------
# Struct layout
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class StructLayout:
    """Memory layout for a struct type."""

    name: str
    fields: list[tuple[str, str]]  # (field_name, wasm_type)
    field_offsets: dict[str, int] = field(default_factory=dict)
    total_size: int = 0


# ---------------------------------------------------------------------------
# WasmEmitter
# ---------------------------------------------------------------------------


class WasmEmitter:
    """Emits WebAssembly text format (WAT) from a MIR module.

    The emitter walks MIR functions and basic blocks, translating each
    instruction into WAT instructions. Control flow is restructured from
    the CFG into WASM's structured control flow (block/loop/br/br_if).

    Phi nodes are lowered to local variables with assignments inserted
    in predecessor blocks before branches.
    """

    def __init__(self, options: WasmOptions | None = None) -> None:
        self._options = options or WasmOptions()

        # Module-level state
        self._string_table: list[StringConstant] = []
        self._string_cache: dict[str, int] = {}  # string value -> offset
        self._data_offset: int = 0  # Next free byte in data section
        self._struct_layouts: dict[str, StructLayout] = {}
        self._enum_variants: dict[str, dict[str, int]] = {}  # enum -> {variant: tag}
        self._func_types: dict[str, tuple[list[str], str | None]] = {}  # fn -> (params, ret)
        self._func_indices: dict[str, int] = {}
        self._import_count: int = 0

        # Per-function state
        self._locals: dict[str, str] = {}  # local name -> wasm type
        self._local_indices: dict[str, int] = {}
        self._param_count: int = 0
        self._body_lines: list[str] = []
        self._indent_level: int = 0
        self._block_map: dict[str, BasicBlock] = {}
        self._block_indices: dict[str, int] = {}
        self._phi_locals: dict[str, str] = {}  # phi dest -> wasm type
        self._current_fn: MIRFunction | None = None
        self._visited_blocks: set[str] = set()

        # Instruction dispatch table
        self._dispatch: dict[type, Any] = {}
        self._init_dispatch()

    # ------------------------------------------------------------------
    # Dispatch table
    # ------------------------------------------------------------------

    def _init_dispatch(self) -> None:
        """Build instruction dispatch table mapping MIR types to handlers."""
        d = self._dispatch
        d[Const] = self._emit_const
        d[Copy] = self._emit_copy
        d[Cast] = self._emit_cast
        d[BinOp] = self._emit_binop
        d[UnaryOp] = self._emit_unaryop
        d[Call] = self._emit_call
        d[ExternCall] = self._emit_extern_call
        d[Return] = self._emit_return
        d[Jump] = self._emit_jump
        d[Branch] = self._emit_branch
        d[Switch] = self._emit_switch
        d[StructInit] = self._emit_struct_init
        d[FieldGet] = self._emit_field_get
        d[FieldSet] = self._emit_field_set
        d[ListInit] = self._emit_list_init
        d[ListPush] = self._emit_list_push
        d[IndexGet] = self._emit_index_get
        d[IndexSet] = self._emit_index_set
        d[MapInit] = self._emit_map_init
        d[EnumInit] = self._emit_enum_init
        d[EnumTag] = self._emit_enum_tag
        d[EnumPayload] = self._emit_enum_payload
        d[WrapSome] = self._emit_wrap_some
        d[WrapNone] = self._emit_wrap_none
        d[WrapOk] = self._emit_wrap_ok
        d[WrapErr] = self._emit_wrap_err
        d[Unwrap] = self._emit_unwrap
        d[InterpConcat] = self._emit_interp_concat
        d[AgentSpawn] = self._emit_agent_spawn
        d[AgentSend] = self._emit_agent_send
        d[AgentSync] = self._emit_agent_sync
        d[SignalInit] = self._emit_signal_init
        d[SignalGet] = self._emit_signal_get
        d[SignalSet] = self._emit_signal_set
        d[SignalComputed] = self._emit_signal_computed
        d[SignalSubscribe] = self._emit_signal_subscribe
        d[StreamInit] = self._emit_stream_init
        d[StreamOp] = self._emit_stream_op
        d[ClosureCreate] = self._emit_closure_create
        d[ClosureCall] = self._emit_closure_call
        d[EnvLoad] = self._emit_env_load
        d[Assert] = self._emit_assert
        d[Phi] = self._emit_phi

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def emit(self, module: MIRModule) -> str:
        """Emit a complete WAT module from a MIR module.

        Returns the WebAssembly text format as a string.
        """
        self._reset_module_state()
        self._register_types(module)
        self._collect_strings(module)
        self._collect_function_signatures(module)

        lines: list[str] = []
        lines.append(f"(module ${self._options.module_name}")

        # Memory declaration
        lines.extend(self._emit_memory_section())

        # Imports (JS bridge)
        lines.extend(self._emit_import_section())

        # Global variables (heap pointer)
        lines.extend(self._emit_globals_section())

        # Function type declarations
        lines.extend(self._emit_type_section(module))

        # Function bodies
        for mir_fn in module.functions:
            lines.extend(self._emit_function(mir_fn))

        # Bump allocator helper
        lines.extend(self._emit_bump_alloc())

        # Builtin function stubs
        lines.extend(self._emit_builtin_stubs())

        # Data section (string constants)
        lines.extend(self._emit_data_section())

        # Exports
        lines.extend(self._emit_export_section(module))

        lines.append(")")
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Module-level reset
    # ------------------------------------------------------------------

    def _reset_module_state(self) -> None:
        """Reset all module-level state for a fresh emission."""
        self._string_table = []
        self._string_cache = {}
        self._data_offset = _STRING_HEADER_SIZE  # Reserve space for data section header
        self._struct_layouts = {}
        self._enum_variants = {}
        self._func_types = {}
        self._func_indices = {}
        self._import_count = 0

    # ------------------------------------------------------------------
    # Type registration
    # ------------------------------------------------------------------

    def _register_types(self, module: MIRModule) -> None:
        """Register struct and enum layouts from the MIR module."""
        for name, fields in module.structs.items():
            self._register_struct(name, fields)
        for name, variants in module.enums.items():
            self._register_enum(name, variants)

    def _register_struct(self, name: str, fields: list[tuple[str, MIRType]]) -> None:
        """Compute memory layout for a struct type."""
        layout = StructLayout(name=name, fields=[])
        offset = 0
        for field_name, field_type in fields:
            wasm_ty = self._mir_type_to_wasm(field_type)
            size = self._wasm_type_size(wasm_ty)
            # Align to natural boundary
            alignment = size if size <= 8 else 8
            if offset % alignment != 0:
                offset += alignment - (offset % alignment)
            layout.fields.append((field_name, wasm_ty))
            layout.field_offsets[field_name] = offset
            offset += size
        # Round up total size to 8-byte alignment
        if offset % 8 != 0:
            offset += 8 - (offset % 8)
        layout.total_size = max(offset, _PTR_SIZE)
        self._struct_layouts[name] = layout

    def _register_enum(self, name: str, variants: list[tuple[str, list[MIRType]]]) -> None:
        """Register enum variant tags."""
        self._enum_variants[name] = {}
        for tag, (variant_name, _payload_types) in enumerate(variants):
            self._enum_variants[name][variant_name] = tag

    # ------------------------------------------------------------------
    # String collection
    # ------------------------------------------------------------------

    def _collect_strings(self, module: MIRModule) -> None:
        """Scan all MIR functions for string constants and build the string table."""
        for fn in module.functions:
            for bb in fn.blocks:
                for inst in bb.instructions:
                    if isinstance(inst, Const) and isinstance(inst.value, str):
                        self._intern_string(inst.value)
                    elif isinstance(inst, Assert) and inst.message is None:
                        # Default assertion message
                        msg = f"assertion failed at {inst.filename}:{inst.line}"
                        self._intern_string(msg)

    def _intern_string(self, value: str) -> int:
        """Add a string to the constant table, returning its memory offset.

        The string is stored as: [i32 byte_length][UTF-8 bytes]
        The returned offset points to the length prefix.
        """
        if value in self._string_cache:
            return self._string_cache[value]
        encoded = value.encode("utf-8")
        byte_len = len(encoded)
        # Align to 4-byte boundary
        if self._data_offset % 4 != 0:
            self._data_offset += 4 - (self._data_offset % 4)
        offset = self._data_offset
        self._string_table.append(StringConstant(value=value, offset=offset, byte_length=byte_len))
        self._string_cache[value] = offset
        # Layout: [i32 length][bytes...]
        self._data_offset += _I32_SIZE + byte_len
        # Align next entry
        if self._data_offset % 4 != 0:
            self._data_offset += 4 - (self._data_offset % 4)
        return offset

    # ------------------------------------------------------------------
    # Function signature collection
    # ------------------------------------------------------------------

    def _collect_function_signatures(self, module: MIRModule) -> None:
        """Build function type maps from MIR function signatures."""
        idx = self._import_count
        for mir_fn in module.functions:
            param_types = [self._mir_type_to_wasm(p.ty) for p in mir_fn.params]
            ret_type = self._mir_type_to_wasm_ret(mir_fn.return_type)
            self._func_types[mir_fn.name] = (param_types, ret_type)
            self._func_indices[mir_fn.name] = idx
            idx += 1

    # ------------------------------------------------------------------
    # Type mapping
    # ------------------------------------------------------------------

    def _mir_type_to_wasm(self, mir_type: MIRType) -> str:
        """Map a MIR type to a WASM value type string.

        Primitives map to native WASM types. All heap-allocated types
        (String, List, Map, Struct, Agent, etc.) map to i32 pointers.
        """
        kind = mir_type.kind
        if kind == TypeKind.INT:
            return _WASM_I64
        if kind == TypeKind.FLOAT:
            return _WASM_F64
        if kind == TypeKind.BOOL:
            return _WASM_I32
        if kind == TypeKind.VOID:
            return ""  # No WASM type for void
        # All heap-allocated types use i32 pointer
        if kind in (
            TypeKind.STRING,
            TypeKind.LIST,
            TypeKind.MAP,
            TypeKind.STRUCT,
            TypeKind.ENUM,
            TypeKind.OPTION,
            TypeKind.RESULT,
            TypeKind.AGENT,
            TypeKind.SIGNAL,
            TypeKind.STREAM,
            TypeKind.TENSOR,
            TypeKind.PIPE,
            TypeKind.CHANNEL,
            TypeKind.FN,
        ):
            return _WASM_I32
        # Unknown / generic fallback
        if kind == TypeKind.UNKNOWN:
            return _WASM_I64  # Default to i64 for unknown types
        return _WASM_I64

    def _mir_type_to_wasm_ret(self, mir_type: MIRType) -> str | None:
        """Map a MIR return type. Returns None for void."""
        wasm_ty = self._mir_type_to_wasm(mir_type)
        return wasm_ty if wasm_ty else None

    @staticmethod
    def _wasm_type_size(wasm_ty: str) -> int:
        """Return the byte size of a WASM value type."""
        if wasm_ty == _WASM_I64:
            return _I64_SIZE
        if wasm_ty == _WASM_F64:
            return _F64_SIZE
        if wasm_ty == _WASM_I32:
            return _I32_SIZE
        return _I32_SIZE  # Default for pointers

    # ------------------------------------------------------------------
    # Module sections
    # ------------------------------------------------------------------

    def _emit_memory_section(self) -> list[str]:
        """Emit the linear memory declaration."""
        return [
            f'  (memory (export "memory") {self._options.initial_memory_pages}'
            f" {self._options.max_memory_pages})"
        ]

    def _emit_import_section(self) -> list[str]:
        """Emit JS bridge imports.

        Imported functions provide host-side capabilities:
        - env.console_log_i32: print an i32 value
        - env.console_log_i64: print an i64 value
        - env.console_log_f64: print an f64 value
        - env.console_log_str: print a string at (ptr, len)
        - env.console_log_newline: print a newline
        - env.abort: abort execution with a message
        """
        lines: list[str] = []
        imports = [
            ("env", "console_log_i32", [_WASM_I32], None),
            ("env", "console_log_i64", [_WASM_I64], None),
            ("env", "console_log_f64", [_WASM_F64], None),
            ("env", "console_log_str", [_WASM_I32, _WASM_I32], None),
            ("env", "console_log_newline", [], None),
            ("env", "console_log_bool", [_WASM_I32], None),
            ("env", "abort", [_WASM_I32, _WASM_I32], None),
        ]
        for mod, name, params, ret in imports:
            param_str = " ".join(f"(param {p})" for p in params)
            result_str = f" (result {ret})" if ret else ""
            lines.append(f'  (import "{mod}" "{name}" (func ${name} {param_str}{result_str}))')
            self._func_indices[name] = self._import_count
            self._import_count += 1
        return lines

    def _emit_globals_section(self) -> list[str]:
        """Emit global variables for the bump allocator."""
        # Heap pointer starts after the data section
        # We'll patch this value once we know data section size
        return [
            f"  (global ${_HEAP_PTR_GLOBAL} (mut i32) (i32.const 0))",
        ]

    def _emit_type_section(self, module: MIRModule) -> list[str]:
        """Emit function type declarations for indirect calls."""
        lines: list[str] = []
        # Table for indirect calls (closures, callbacks)
        if any(
            isinstance(inst, (ClosureCreate, ClosureCall))
            for fn in module.functions
            for bb in fn.blocks
            for inst in bb.instructions
        ):
            lines.append("  (table funcref (elem))")
        return lines

    def _emit_data_section(self) -> list[str]:
        """Emit the data section with string constants."""
        if not self._string_table:
            return []
        lines: list[str] = []
        for sc in self._string_table:
            encoded = sc.value.encode("utf-8")
            # Encode length prefix as little-endian i32
            len_bytes = struct.pack("<I", sc.byte_length)
            all_bytes = len_bytes + encoded
            hex_str = "".join(f"\\{b:02x}" for b in all_bytes)
            lines.append(f'  (data (i32.const {sc.offset}) "{hex_str}")')
        return lines

    def _emit_export_section(self, module: MIRModule) -> list[str]:
        """Emit exports: main function and optionally all public functions."""
        lines: list[str] = []
        # Export main if it exists
        main_fn = module.get_function("main")
        if main_fn is not None:
            lines.append('  (export "main" (func $main))')
        # Export the bump allocator for testing
        lines.append('  (export "__alloc" (func $__alloc))')
        # Export all public or all functions if requested
        if self._options.export_all_functions:
            for fn in module.functions:
                if fn.name != "main":
                    safe_name = _sanitize_name(fn.name)
                    lines.append(f'  (export "{fn.name}" (func ${safe_name}))')
        else:
            for fn in module.functions:
                if fn.is_public and fn.name != "main":
                    safe_name = _sanitize_name(fn.name)
                    lines.append(f'  (export "{fn.name}" (func ${safe_name}))')
        # Start function: initialize heap pointer then call main
        if main_fn is not None:
            lines.append('  (export "_start" (func $_start))')
            start_lines = [
                "  (func $_start",
                f"    (global.set ${_HEAP_PTR_GLOBAL} (i32.const {self._data_offset}))",
                "    (call $main)",
            ]
            # If main returns a value, drop it
            ret = self._mir_type_to_wasm_ret(main_fn.return_type)
            if ret:
                start_lines.append("    drop")
            start_lines.append("  )")
            lines.extend(start_lines)
        else:
            # No main: just an init function for heap
            lines.append('  (export "_initialize" (func $_initialize))')
            lines.append("  (func $_initialize")
            lines.append(f"    (global.set ${_HEAP_PTR_GLOBAL} (i32.const {self._data_offset}))")
            lines.append("  )")
        return lines

    # ------------------------------------------------------------------
    # Bump allocator
    # ------------------------------------------------------------------

    def _emit_bump_alloc(self) -> list[str]:
        """Emit the bump allocator function.

        Signature: __alloc(size: i32, align: i32) -> i32
        Returns a pointer to the allocated block. Bumps the heap pointer
        forward. Does not support freeing.
        """
        return [
            "  (func $__alloc (param $size i32) (param $align i32) (result i32)",
            "    (local $ptr i32)",
            "    ;; Align the current heap pointer",
            "    (local.set $ptr",
            "      (i32.and",
            "        (i32.add",
            f"          (global.get ${_HEAP_PTR_GLOBAL})",
            "          (i32.sub (local.get $align) (i32.const 1))",
            "        )",
            "        (i32.xor (i32.sub (local.get $align) (i32.const 1)) (i32.const -1))",
            "      )",
            "    )",
            "    ;; Bump heap pointer past the allocation",
            f"    (global.set ${_HEAP_PTR_GLOBAL}",
            "      (i32.add (local.get $ptr) (local.get $size))",
            "    )",
            "    ;; Check for OOM (heap exceeds memory size)",
            f"    (if (i32.gt_u (global.get ${_HEAP_PTR_GLOBAL})"
            f" (i32.mul (memory.size) (i32.const 65536)))",
            "      (then",
            "        ;; Try to grow memory",
            "        (if (i32.eq (memory.grow (i32.const 1)) (i32.const -1))",
            "          (then (unreachable))",
            "        )",
            "      )",
            "    )",
            "    (local.get $ptr)",
            "  )",
        ]

    # ------------------------------------------------------------------
    # Builtin stubs
    # ------------------------------------------------------------------

    def _emit_builtin_stubs(self) -> list[str]:
        """Emit builtin function implementations.

        These are WASM-native implementations of Mapanare builtins that
        delegate to imported JS bridge functions or operate on linear memory.
        """
        lines: list[str] = []

        # print(value) — polymorphic, we emit typed variants
        # The MIR-level Call to "print" is dispatched by type at emit time.

        # len(string) -> Int: read i32 length from string pointer
        lines.extend(
            [
                "  (func $__builtin_len_str (param $ptr i32) (result i64)",
                "    (i64.extend_i32_u (i32.load (local.get $ptr)))",
                "  )",
            ]
        )

        # len(list) -> Int: read i32 length from list header
        lines.extend(
            [
                "  (func $__builtin_len_list (param $ptr i32) (result i64)",
                "    (i64.extend_i32_u (i32.load (local.get $ptr)))",
                "  )",
            ]
        )

        # int(float) -> Int: truncate f64 to i64
        lines.extend(
            [
                "  (func $__builtin_int_f64 (param $v f64) (result i64)",
                "    (i64.trunc_f64_s (local.get $v))",
                "  )",
            ]
        )

        # float(int) -> Float: convert i64 to f64
        lines.extend(
            [
                "  (func $__builtin_float_i64 (param $v i64) (result f64)",
                "    (f64.convert_i64_s (local.get $v))",
                "  )",
            ]
        )

        # str(int) -> String: convert integer to string (heap-allocated)
        # This is a stub that delegates to a more complex runtime function.
        # For now, allocate space and write the decimal representation.
        lines.extend(
            [
                "  (func $__builtin_str_i64 (param $v i64) (result i32)",
                "    (local $ptr i32)",
                "    (local $buf i32)",
                "    (local $len i32)",
                "    (local $neg i32)",
                "    (local $digit i64)",
                "    (local $tmp i64)",
                "    (local $i i32)",
                "    ;; Allocate 24 bytes: 4 (len) + 20 (max i64 decimal digits)",
                "    (local.set $ptr (call $__alloc (i32.const 24) (i32.const 4)))",
                "    (local.set $buf (i32.add (local.get $ptr) (i32.const 4)))",
                "    (local.set $tmp (local.get $v))",
                "    ;; Handle negative",
                "    (if (i64.lt_s (local.get $tmp) (i64.const 0))",
                "      (then",
                "        (local.set $neg (i32.const 1))",
                "        (local.set $tmp (i64.sub (i64.const 0) (local.get $tmp)))",
                "      )",
                "    )",
                "    ;; Handle zero",
                "    (if (i64.eqz (local.get $tmp))",
                "      (then",
                "        (i32.store8 (local.get $buf) (i32.const 48))",
                "        (local.set $len (i32.const 1))",
                "      )",
                "      (else",
                "        ;; Write digits in reverse",
                "        (local.set $i (i32.const 0))",
                "        (block $done",
                "          (loop $digits",
                "            (br_if $done (i64.eqz (local.get $tmp)))",
                "            (local.set $digit (i64.rem_u (local.get $tmp) (i64.const 10)))",
                "            (i32.store8",
                "              (i32.add (local.get $buf) (local.get $i))",
                "              (i32.add (i32.const 48) (i32.wrap_i64 (local.get $digit)))",
                "            )",
                "            (local.set $tmp (i64.div_u (local.get $tmp) (i64.const 10)))",
                "            (local.set $i (i32.add (local.get $i) (i32.const 1)))",
                "            (br $digits)",
                "          )",
                "        )",
                "        ;; Reverse the digits in place",
                "        (local.set $len (local.get $i))",
                "        (block $rev_done",
                "          (loop $rev",
                "            (local.set $i (i32.sub (local.get $i) (i32.const 1)))",
                "            (br_if $rev_done (i32.lt_s (local.get $i)"
                " (i32.div_u (local.get $len) (i32.const 2))))",
                "            ;; Swap buf[len-1-i] and buf[i] — simplified: skip for now",
                "            (br $rev)",
                "          )",
                "        )",
                "      )",
                "    )",
                "    ;; Write length prefix",
                "    (i32.store (local.get $ptr) (local.get $len))",
                "    (local.get $ptr)",
                "  )",
            ]
        )

        # __builtin_print_str: print string via imported console_log_str
        lines.extend(
            [
                "  (func $__builtin_print_str (param $ptr i32)",
                "    (call $console_log_str",
                "      (i32.add (local.get $ptr) (i32.const 4))  ;; skip length prefix",
                "      (i32.load (local.get $ptr))                ;; length",
                "    )",
                "  )",
            ]
        )

        # __builtin_println_str: print string + newline
        lines.extend(
            [
                "  (func $__builtin_println_str (param $ptr i32)",
                "    (call $__builtin_print_str (local.get $ptr))",
                "    (call $console_log_newline)",
                "  )",
            ]
        )

        return lines

    # ------------------------------------------------------------------
    # Function emission
    # ------------------------------------------------------------------

    def _emit_function(self, mir_fn: MIRFunction) -> list[str]:
        """Emit a single WASM function from its MIR representation.

        Steps:
        1. Build block map and assign block indices
        2. Collect all SSA values as locals
        3. Lower phi nodes to local assignments
        4. Emit structured control flow
        """
        self._reset_function_state(mir_fn)
        safe_name = _sanitize_name(mir_fn.name)

        # Build param and result type strings
        param_parts: list[str] = []
        for p in mir_fn.params:
            wasm_ty = self._mir_type_to_wasm(p.ty)
            if wasm_ty:
                local_name = _sanitize_name(p.name)
                param_parts.append(f"(param ${local_name} {wasm_ty})")
                self._locals[p.name] = wasm_ty
                self._local_indices[p.name] = len(self._local_indices)

        ret_type = self._mir_type_to_wasm_ret(mir_fn.return_type)
        result_part = f" (result {ret_type})" if ret_type else ""

        # Collect all locals from instructions
        self._collect_locals(mir_fn)

        # Build local declarations (excluding params)
        local_decls: list[str] = []
        param_names = {p.name for p in mir_fn.params}
        for local_name, wasm_ty in self._locals.items():
            if local_name not in param_names and wasm_ty:
                safe_local = _sanitize_name(local_name)
                local_decls.append(f"    (local ${safe_local} {wasm_ty})")

        # Header
        param_str = " ".join(param_parts)
        if param_str:
            param_str = " " + param_str
        lines: list[str] = [f"  (func ${safe_name}{param_str}{result_part}"]
        lines.extend(local_decls)

        # Emit body from basic blocks using structured control flow
        body = self._emit_function_body(mir_fn)
        lines.extend(body)

        lines.append("  )")
        return lines

    def _reset_function_state(self, mir_fn: MIRFunction) -> None:
        """Reset per-function state before emitting a new function."""
        self._locals = {}
        self._local_indices = {}
        self._param_count = len(mir_fn.params)
        self._body_lines = []
        self._indent_level = 2
        self._current_fn = mir_fn
        self._visited_blocks = set()
        self._phi_locals = {}

        # Build block map
        self._block_map = {}
        self._block_indices = {}
        for i, bb in enumerate(mir_fn.blocks):
            self._block_map[bb.label] = bb
            self._block_indices[bb.label] = i

    def _collect_locals(self, mir_fn: MIRFunction) -> None:
        """Scan all instructions and register every dest Value as a local.

        This flattens SSA into WASM locals — phi nodes become regular
        assignments. Each unique Value name gets exactly one local.
        """
        for bb in mir_fn.blocks:
            for inst in bb.instructions:
                dest = getattr(inst, "dest", None)
                if dest is not None and isinstance(dest, Value) and dest.name:
                    if dest.name not in self._locals:
                        wasm_ty = self._mir_type_to_wasm(dest.ty)
                        if not wasm_ty:
                            wasm_ty = _WASM_I64  # Fallback for void-typed dests
                        self._locals[dest.name] = wasm_ty

    # ------------------------------------------------------------------
    # Function body: linearized block emission
    # ------------------------------------------------------------------

    def _emit_function_body(self, mir_fn: MIRFunction) -> list[str]:
        """Emit the function body as a sequence of blocks.

        Uses a simple linearization strategy: emit blocks in order,
        using WASM block/loop constructs for branches. Forward jumps
        use (block ... (br N)), backward jumps use (loop ... (br N)).
        """
        lines: list[str] = []
        if not mir_fn.blocks:
            return lines

        # Detect loop headers (blocks targeted by backward edges)
        loop_headers = self._find_loop_headers(mir_fn)

        # Emit blocks in linear order using a label-indexed block stack
        # Strategy: wrap the entire body in nested blocks, one per BB.
        # Each block label maps to a br depth. Forward branches break out
        # of blocks; backward branches use loop constructs.
        num_blocks = len(mir_fn.blocks)

        # Open block wrappers for forward branching
        for i in range(num_blocks - 1, -1, -1):
            bb = mir_fn.blocks[i]
            if bb.label in loop_headers:
                lines.append(f"    (loop $L_{_sanitize_name(bb.label)}")
            else:
                lines.append(f"    (block $L_{_sanitize_name(bb.label)}")

        # Emit each block's instructions
        for i, bb in enumerate(mir_fn.blocks):
            lines.append(f"      ;; -- {bb.label} --")
            for inst in bb.instructions:
                inst_lines = self._emit_instruction(inst, bb.label, mir_fn)
                lines.extend(inst_lines)

        # Close all block wrappers
        for _i in range(num_blocks):
            lines.append("    )")

        return lines

    def _find_loop_headers(self, mir_fn: MIRFunction) -> set[str]:
        """Identify basic blocks that are targets of backward edges (loop headers)."""
        headers: set[str] = set()
        block_order = {bb.label: i for i, bb in enumerate(mir_fn.blocks)}
        for i, bb in enumerate(mir_fn.blocks):
            term = bb.instructions[-1] if bb.instructions else None
            if term is None:
                continue
            targets: list[str] = []
            if isinstance(term, Jump):
                targets.append(term.target)
            elif isinstance(term, Branch):
                targets.extend([term.true_block, term.false_block])
            elif isinstance(term, Switch):
                targets.extend(lbl for _, lbl in term.cases)
                if term.default_block:
                    targets.append(term.default_block)
            for target in targets:
                if target in block_order and block_order[target] <= i:
                    headers.add(target)
        return headers

    # ------------------------------------------------------------------
    # Instruction dispatch
    # ------------------------------------------------------------------

    def _emit_instruction(self, inst: Instruction, block_label: str, fn: MIRFunction) -> list[str]:
        """Dispatch a single MIR instruction to its handler."""
        handler = self._dispatch.get(type(inst))
        if handler is not None:
            return list(handler(inst, block_label, fn))
        _logger.warning("Unhandled MIR instruction: %s", type(inst).__name__)
        return [f"      ;; TODO: {type(inst).__name__}"]

    # ------------------------------------------------------------------
    # Instruction emitters
    # ------------------------------------------------------------------

    def _emit_const(self, inst: Const, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a constant load."""
        dest = _sanitize_name(inst.dest.name)
        wasm_ty = self._locals.get(inst.dest.name, _WASM_I64)

        if isinstance(inst.value, bool):
            val = 1 if inst.value else 0
            return [f"      (local.set ${dest} (i32.const {val}))"]

        if isinstance(inst.value, int):
            if wasm_ty == _WASM_I32:
                return [f"      (local.set ${dest} (i32.const {inst.value}))"]
            return [f"      (local.set ${dest} (i64.const {inst.value}))"]

        if isinstance(inst.value, float):
            return [f"      (local.set ${dest} (f64.const {inst.value}))"]

        if isinstance(inst.value, str):
            offset = self._string_cache.get(inst.value, 0)
            return [f"      (local.set ${dest} (i32.const {offset}))"]

        if inst.value is None:
            if wasm_ty == _WASM_F64:
                return [f"      (local.set ${dest} (f64.const 0))"]
            if wasm_ty == _WASM_I32:
                return [f"      (local.set ${dest} (i32.const 0))"]
            return [f"      (local.set ${dest} (i64.const 0))"]

        # Fallback
        return [f"      ;; const {dest} = {inst.value!r} (unsupported type)"]

    def _emit_copy(self, inst: Copy, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a value copy (local.set from local.get)."""
        dest = _sanitize_name(inst.dest.name)
        src = _sanitize_name(inst.src.name)
        src_ty = self._locals.get(inst.src.name, _WASM_I64)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        lines: list[str] = []
        if src_ty == dest_ty:
            lines.append(f"      (local.set ${dest} (local.get ${src}))")
        else:
            lines.extend(self._emit_type_coerce(src, src_ty, dest, dest_ty))
        return lines

    def _emit_cast(self, inst: Cast, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a type cast."""
        dest = _sanitize_name(inst.dest.name)
        src = _sanitize_name(inst.src.name)
        src_ty = self._locals.get(inst.src.name, _WASM_I64)
        target_wasm = self._mir_type_to_wasm(inst.target_type)
        if not target_wasm:
            target_wasm = _WASM_I64
        return self._emit_type_coerce(src, src_ty, dest, target_wasm)

    def _emit_type_coerce(self, src: str, src_ty: str, dest: str, dest_ty: str) -> list[str]:
        """Emit instructions to coerce a value from one WASM type to another."""
        if src_ty == dest_ty:
            return [f"      (local.set ${dest} (local.get ${src}))"]

        # i64 -> i32
        if src_ty == _WASM_I64 and dest_ty == _WASM_I32:
            return [f"      (local.set ${dest} (i32.wrap_i64 (local.get ${src})))"]

        # i32 -> i64
        if src_ty == _WASM_I32 and dest_ty == _WASM_I64:
            return [f"      (local.set ${dest} (i64.extend_i32_s (local.get ${src})))"]

        # i64 -> f64
        if src_ty == _WASM_I64 and dest_ty == _WASM_F64:
            return [f"      (local.set ${dest} (f64.convert_i64_s (local.get ${src})))"]

        # f64 -> i64
        if src_ty == _WASM_F64 and dest_ty == _WASM_I64:
            return [f"      (local.set ${dest} (i64.trunc_f64_s (local.get ${src})))"]

        # i32 -> f64
        if src_ty == _WASM_I32 and dest_ty == _WASM_F64:
            return [f"      (local.set ${dest} (f64.convert_i32_s (local.get ${src})))"]

        # f64 -> i32
        if src_ty == _WASM_F64 and dest_ty == _WASM_I32:
            return [f"      (local.set ${dest} (i32.trunc_f64_s (local.get ${src})))"]

        # Fallback: reinterpret bits
        return [
            f"      ;; coerce {src_ty} -> {dest_ty}",
            f"      (local.set ${dest} (local.get ${src}))  ;; WARNING: type mismatch",
        ]

    def _emit_binop(self, inst: BinOp, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a binary operation."""
        dest = _sanitize_name(inst.dest.name)
        lhs = _sanitize_name(inst.lhs.name)
        rhs = _sanitize_name(inst.rhs.name)
        lhs_ty = self._locals.get(inst.lhs.name, _WASM_I64)

        # Determine if this is float or integer arithmetic
        is_float = lhs_ty == _WASM_F64

        op_map_i64: dict[BinOpKind, str] = {
            BinOpKind.ADD: "i64.add",
            BinOpKind.SUB: "i64.sub",
            BinOpKind.MUL: "i64.mul",
            BinOpKind.DIV: "i64.div_s",
            BinOpKind.MOD: "i64.rem_s",
            BinOpKind.EQ: "i64.eq",
            BinOpKind.NE: "i64.ne",
            BinOpKind.LT: "i64.lt_s",
            BinOpKind.GT: "i64.gt_s",
            BinOpKind.LE: "i64.le_s",
            BinOpKind.GE: "i64.ge_s",
        }

        op_map_f64: dict[BinOpKind, str] = {
            BinOpKind.ADD: "f64.add",
            BinOpKind.SUB: "f64.sub",
            BinOpKind.MUL: "f64.mul",
            BinOpKind.DIV: "f64.div",
            BinOpKind.EQ: "f64.eq",
            BinOpKind.NE: "f64.ne",
            BinOpKind.LT: "f64.lt",
            BinOpKind.GT: "f64.gt",
            BinOpKind.LE: "f64.le",
            BinOpKind.GE: "f64.ge",
        }

        op_map_i32: dict[BinOpKind, str] = {
            BinOpKind.AND: "i32.and",
            BinOpKind.OR: "i32.or",
            BinOpKind.EQ: "i32.eq",
            BinOpKind.NE: "i32.ne",
        }

        # Boolean operations (AND/OR) use i32
        if inst.op in (BinOpKind.AND, BinOpKind.OR):
            wasm_op = op_map_i32.get(inst.op)
            if wasm_op:
                return [
                    f"      (local.set ${dest} ({wasm_op}"
                    f" (local.get ${lhs}) (local.get ${rhs})))"
                ]

        if is_float:
            wasm_op = op_map_f64.get(inst.op)
            if wasm_op:
                # Comparison ops return i32 in WASM
                dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
                if inst.op in (
                    BinOpKind.EQ,
                    BinOpKind.NE,
                    BinOpKind.LT,
                    BinOpKind.GT,
                    BinOpKind.LE,
                    BinOpKind.GE,
                ):
                    return [
                        f"      (local.set ${dest} ({wasm_op}"
                        f" (local.get ${lhs}) (local.get ${rhs})))"
                    ]
                return [
                    f"      (local.set ${dest} ({wasm_op}"
                    f" (local.get ${lhs}) (local.get ${rhs})))"
                ]
        else:
            wasm_op = op_map_i64.get(inst.op)
            if wasm_op:
                # Comparison ops return i32, but we might need i64 or i32
                dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
                if inst.op in (
                    BinOpKind.EQ,
                    BinOpKind.NE,
                    BinOpKind.LT,
                    BinOpKind.GT,
                    BinOpKind.LE,
                    BinOpKind.GE,
                ):
                    # WASM comparison returns i32
                    if dest_ty == _WASM_I32:
                        return [
                            f"      (local.set ${dest} ({wasm_op}"
                            f" (local.get ${lhs}) (local.get ${rhs})))"
                        ]
                    # Need to extend to i64 if dest is i64
                    return [
                        f"      (local.set ${dest} (i64.extend_i32_u ({wasm_op}"
                        f" (local.get ${lhs}) (local.get ${rhs}))))"
                    ]
                return [
                    f"      (local.set ${dest} ({wasm_op}"
                    f" (local.get ${lhs}) (local.get ${rhs})))"
                ]

        return [f"      ;; TODO: binop {inst.op.value} for {lhs_ty}"]

    def _emit_unaryop(self, inst: UnaryOp, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a unary operation."""
        dest = _sanitize_name(inst.dest.name)
        operand = _sanitize_name(inst.operand.name)
        op_ty = self._locals.get(inst.operand.name, _WASM_I64)

        if inst.op == UnaryOpKind.NEG:
            if op_ty == _WASM_F64:
                return [f"      (local.set ${dest} (f64.neg (local.get ${operand})))"]
            if op_ty == _WASM_I64:
                return [
                    f"      (local.set ${dest} (i64.sub" f" (i64.const 0) (local.get ${operand})))"
                ]
            return [f"      (local.set ${dest} (i32.sub" f" (i32.const 0) (local.get ${operand})))"]

        if inst.op == UnaryOpKind.NOT:
            if op_ty == _WASM_I32:
                return [
                    f"      (local.set ${dest} (i32.xor" f" (local.get ${operand}) (i32.const 1)))"
                ]
            return [
                f"      (local.set ${dest} (i64.extend_i32_u (i32.xor"
                f" (i32.wrap_i64 (local.get ${operand})) (i32.const 1))))"
            ]

        return [f"      ;; TODO: unary {inst.op.value}"]

    def _emit_call(self, inst: Call, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a function call."""
        dest = _sanitize_name(inst.dest.name)
        fn_name = inst.fn_name
        args = [_sanitize_name(a.name) for a in inst.args]

        # Handle builtins
        builtin_lines = self._try_emit_builtin_call(inst, dest, args)
        if builtin_lines is not None:
            return builtin_lines

        # Regular function call
        safe_fn = _sanitize_name(fn_name)
        arg_gets = " ".join(f"(local.get ${a})" for a in args)
        call_expr = f"(call ${safe_fn} {arg_gets})" if arg_gets else f"(call ${safe_fn})"

        ret_type = self._func_types.get(fn_name, ([], None))[1]
        if ret_type:
            return [f"      (local.set ${dest} {call_expr})"]
        else:
            return [f"      {call_expr}"]

    def _try_emit_builtin_call(self, inst: Call, dest: str, args: list[str]) -> list[str] | None:
        """Try to emit a builtin function call. Returns None if not a builtin."""
        fn = inst.fn_name

        if fn == "print" or fn == "println":
            return self._emit_print_call(inst, fn == "println")

        if fn == "len":
            if inst.args:
                arg = _sanitize_name(inst.args[0].name)
                arg_ty = self._locals.get(inst.args[0].name, _WASM_I32)
                if arg_ty == _WASM_I32:
                    # Pointer type: could be string or list
                    return [
                        f"      (local.set ${dest} (call $__builtin_len_str (local.get ${arg})))"
                    ]
            return [f"      (local.set ${dest} (i64.const 0))"]

        if fn == "str":
            if inst.args:
                arg = _sanitize_name(inst.args[0].name)
                arg_ty = self._locals.get(inst.args[0].name, _WASM_I64)
                if arg_ty == _WASM_I64:
                    return [
                        f"      (local.set ${dest}"
                        f" (call $__builtin_str_i64 (local.get ${arg})))"
                    ]
            return [f"      (local.set ${dest} (i32.const 0))"]

        if fn == "int":
            if inst.args:
                arg = _sanitize_name(inst.args[0].name)
                arg_ty = self._locals.get(inst.args[0].name, _WASM_F64)
                if arg_ty == _WASM_F64:
                    return [
                        f"      (local.set ${dest}"
                        f" (call $__builtin_int_f64 (local.get ${arg})))"
                    ]
            return [f"      (local.set ${dest} (i64.const 0))"]

        if fn == "float":
            if inst.args:
                arg = _sanitize_name(inst.args[0].name)
                arg_ty = self._locals.get(inst.args[0].name, _WASM_I64)
                if arg_ty == _WASM_I64:
                    return [
                        f"      (local.set ${dest}"
                        f" (call $__builtin_float_i64 (local.get ${arg})))"
                    ]
            return [f"      (local.set ${dest} (f64.const 0))"]

        if fn == "Some":
            # Wrapper: allocate tagged union with tag=1
            if inst.args:
                return self._emit_wrap_some_call(dest, inst.args[0])
            return None

        if fn == "Ok":
            if inst.args:
                return self._emit_wrap_ok_call(dest, inst.args[0])
            return None

        if fn == "Err":
            if inst.args:
                return self._emit_wrap_err_call(dest, inst.args[0])
            return None

        if fn == "signal":
            if inst.args:
                arg = _sanitize_name(inst.args[0].name)
                return [
                    "      ;; signal init",
                    f"      (local.set ${dest}"
                    f" (call $__alloc (i32.const {_SIGNAL_SIZE}) (i32.const 4)))",
                    f"      (i64.store (local.get ${dest}) (local.get ${arg}))",
                ]
            return None

        if fn == "stream":
            if inst.args:
                arg = _sanitize_name(inst.args[0].name)
                return [
                    "      ;; stream init",
                    f"      (local.set ${dest}"
                    f" (call $__alloc (i32.const {_STREAM_SIZE}) (i32.const 4)))",
                    f"      (i32.store (local.get ${dest}) (local.get ${arg}))",
                ]
            return None

        return None

    def _emit_print_call(self, inst: Call, with_newline: bool) -> list[str]:
        """Emit a print/println call, dispatching by argument type."""
        lines: list[str] = []
        for arg_val in inst.args:
            arg = _sanitize_name(arg_val.name)
            arg_ty = self._locals.get(arg_val.name, _WASM_I64)

            if arg_ty == _WASM_I64:
                lines.append(f"      (call $console_log_i64 (local.get ${arg}))")
            elif arg_ty == _WASM_F64:
                lines.append(f"      (call $console_log_f64 (local.get ${arg}))")
            elif arg_ty == _WASM_I32:
                # Could be bool or string pointer; check MIR type
                mir_kind = arg_val.ty.kind if arg_val.ty else TypeKind.UNKNOWN
                if mir_kind == TypeKind.BOOL:
                    lines.append(f"      (call $console_log_bool (local.get ${arg}))")
                elif mir_kind == TypeKind.STRING:
                    lines.append(f"      (call $__builtin_print_str (local.get ${arg}))")
                else:
                    lines.append(f"      (call $console_log_i32 (local.get ${arg}))")

        if with_newline:
            lines.append("      (call $console_log_newline)")
        return lines

    def _emit_extern_call(self, inst: ExternCall, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit an external function call (FFI)."""
        dest = _sanitize_name(inst.dest.name)
        safe_fn = _sanitize_name(inst.fn_name)
        args = " ".join(f"(local.get ${_sanitize_name(a.name)})" for a in inst.args)
        call_expr = f"(call ${safe_fn} {args})" if args else f"(call ${safe_fn})"
        dest_ty = self._locals.get(inst.dest.name)
        if dest_ty:
            return [f"      (local.set ${dest} {call_expr})"]
        return [f"      {call_expr}"]

    def _emit_return(self, inst: Return, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a return instruction."""
        if inst.val is not None:
            val = _sanitize_name(inst.val.name)
            return [f"      (return (local.get ${val}))"]
        return ["      (return)"]

    def _emit_jump(self, inst: Jump, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit an unconditional jump as a br to the target block."""
        target = _sanitize_name(inst.target)
        # Emit phi assignments for the target block before branching
        lines = self._emit_phi_assignments(inst.target, _bl, _fn)
        lines.append(f"      (br $L_{target})")
        return lines

    def _emit_branch(self, inst: Branch, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a conditional branch as br_if / br."""
        cond = _sanitize_name(inst.cond.name)
        cond_ty = self._locals.get(inst.cond.name, _WASM_I32)
        true_target = _sanitize_name(inst.true_block)
        false_target = _sanitize_name(inst.false_block)

        lines: list[str] = []

        # Get the condition as i32 for br_if
        if cond_ty == _WASM_I64:
            lines.append(f"      (if (i32.wrap_i64 (local.get ${cond}))")
        elif cond_ty == _WASM_I32:
            lines.append(f"      (if (local.get ${cond})")
        else:
            lines.append(f"      (if (i32.trunc_f64_s (local.get ${cond}))")

        # True branch: emit phi assignments then branch
        true_phis = self._emit_phi_assignments(inst.true_block, _bl, _fn)
        lines.append("        (then")
        for phi_line in true_phis:
            lines.append(f"    {phi_line}")
        lines.append(f"          (br $L_{true_target})")
        lines.append("        )")

        # False branch
        false_phis = self._emit_phi_assignments(inst.false_block, _bl, _fn)
        lines.append("        (else")
        for phi_line in false_phis:
            lines.append(f"    {phi_line}")
        lines.append(f"          (br $L_{false_target})")
        lines.append("        )")
        lines.append("      )")

        return lines

    def _emit_switch(self, inst: Switch, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a multi-way branch (match/switch)."""
        tag = _sanitize_name(inst.tag.name)
        tag_ty = self._locals.get(inst.tag.name, _WASM_I32)
        lines: list[str] = []

        # Use nested if-else for small case counts
        for case_val, case_label in inst.cases:
            safe_label = _sanitize_name(case_label)
            if tag_ty == _WASM_I64:
                cmp = f"(i64.eq (local.get ${tag}) (i64.const {case_val}))"
                lines.append(f"      (if (i32.wrap_i64 {cmp})")
            else:
                cmp = f"(i32.eq (local.get ${tag}) (i32.const {case_val}))"
                lines.append(f"      (if {cmp}")

            phi_lines = self._emit_phi_assignments(case_label, _bl, _fn)
            lines.append("        (then")
            for pl in phi_lines:
                lines.append(f"    {pl}")
            lines.append(f"          (br $L_{safe_label})")
            lines.append("        )")
            lines.append("      )")

        # Default case
        if inst.default_block:
            default_label = _sanitize_name(inst.default_block)
            default_phis = self._emit_phi_assignments(inst.default_block, _bl, _fn)
            for pl in default_phis:
                lines.append(f"      {pl}")
            lines.append(f"      (br $L_{default_label})")

        return lines

    def _emit_phi_assignments(
        self, target_label: str, from_label: str, fn: MIRFunction
    ) -> list[str]:
        """Emit local.set assignments for phi nodes in the target block.

        Phi nodes are lowered by inserting assignments in the predecessor
        block. For each phi in the target, we find the incoming value from
        from_label and emit the assignment.
        """
        target_bb = self._block_map.get(target_label)
        if target_bb is None:
            return []
        lines: list[str] = []
        for inst in target_bb.instructions:
            if not isinstance(inst, Phi):
                break
            for lbl, val in inst.incoming:
                if lbl == from_label:
                    dest = _sanitize_name(inst.dest.name)
                    src = _sanitize_name(val.name)
                    lines.append(f"      (local.set ${dest} (local.get ${src}))")
                    break
        return lines

    def _emit_phi(self, inst: Phi, _bl: str, _fn: MIRFunction) -> list[str]:
        """Phi nodes are handled by _emit_phi_assignments. No-op here."""
        return [f"      ;; phi {inst.dest.name} (handled at branch sites)"]

    # ------------------------------------------------------------------
    # Memory / Aggregate instructions
    # ------------------------------------------------------------------

    def _emit_struct_init(self, inst: StructInit, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit struct construction: allocate and initialize fields."""
        dest = _sanitize_name(inst.dest.name)
        type_name = inst.struct_type.type_info.name if inst.struct_type.type_info.name else ""
        layout = self._struct_layouts.get(type_name)

        lines: list[str] = []
        if layout:
            # Allocate struct on heap
            lines.append(
                f"      (local.set ${dest}"
                f" (call $__alloc (i32.const {layout.total_size}) (i32.const 8)))"
            )
            # Initialize fields
            for field_name, field_val in inst.fields:
                offset = layout.field_offsets.get(field_name, 0)
                val = _sanitize_name(field_val.name)
                val_ty = self._locals.get(field_val.name, _WASM_I32)
                store_op = self._store_op_for_type(val_ty)
                lines.append(
                    f"      ({store_op}"
                    f" (i32.add (local.get ${dest}) (i32.const {offset}))"
                    f" (local.get ${val}))"
                )
        else:
            # Unknown struct: allocate generic block
            size = max(len(inst.fields) * 8, _PTR_SIZE)
            lines.append(
                f"      (local.set ${dest}" f" (call $__alloc (i32.const {size}) (i32.const 8)))"
            )
            for i, (field_name, field_val) in enumerate(inst.fields):
                val = _sanitize_name(field_val.name)
                val_ty = self._locals.get(field_val.name, _WASM_I64)
                store_op = self._store_op_for_type(val_ty)
                lines.append(
                    f"      ({store_op}"
                    f" (i32.add (local.get ${dest}) (i32.const {i * 8}))"
                    f" (local.get ${val}))"
                )
        return lines

    def _emit_field_get(self, inst: FieldGet, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit struct field read."""
        dest = _sanitize_name(inst.dest.name)
        obj = _sanitize_name(inst.obj.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)

        # Find field offset from struct layout
        offset = self._resolve_field_offset(inst.obj, inst.field_name)

        return [
            f"      (local.set ${dest} ({load_op}"
            f" (i32.add (local.get ${obj}) (i32.const {offset}))))"
        ]

    def _emit_field_set(self, inst: FieldSet, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit struct field write."""
        obj = _sanitize_name(inst.obj.name)
        val = _sanitize_name(inst.val.name)
        val_ty = self._locals.get(inst.val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)

        offset = self._resolve_field_offset(inst.obj, inst.field_name)

        return [
            f"      ({store_op}"
            f" (i32.add (local.get ${obj}) (i32.const {offset}))"
            f" (local.get ${val}))"
        ]

    def _resolve_field_offset(self, obj: Value, field_name: str) -> int:
        """Resolve the byte offset of a struct field."""
        type_name = obj.ty.type_info.name if obj.ty and obj.ty.type_info.name else ""
        layout = self._struct_layouts.get(type_name)
        if layout and field_name in layout.field_offsets:
            return layout.field_offsets[field_name]
        # Fallback: estimate by field position
        _logger.warning(
            "Unknown struct layout for %s.%s, using generic offset", type_name, field_name
        )
        return 0

    def _emit_list_init(self, inst: ListInit, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit list construction: allocate header + data, store elements."""
        dest = _sanitize_name(inst.dest.name)
        elem_ty = self._mir_type_to_wasm(inst.elem_type)
        elem_size = self._wasm_type_size(elem_ty)
        count = len(inst.elements)
        cap = max(count, 4)  # Minimum capacity of 4

        lines: list[str] = []
        # Allocate header: [len: i32, cap: i32, elem_size: i32, data_ptr: i32]
        lines.append(
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_LIST_HEADER_SIZE}) (i32.const 4)))"
        )
        # Write header fields
        lines.append(f"      (i32.store (local.get ${dest}) (i32.const {count}))")
        lines.append(
            f"      (i32.store (i32.add (local.get ${dest}) (i32.const 4))" f" (i32.const {cap}))"
        )
        lines.append(
            f"      (i32.store (i32.add (local.get ${dest}) (i32.const 8))"
            f" (i32.const {elem_size}))"
        )

        if count > 0:
            # Allocate data array
            data_size = cap * elem_size
            # We need a temp local for data_ptr
            data_local = f"_list_data_{id(inst) & 0xFFFF}"
            if data_local not in self._locals:
                self._locals[data_local] = _WASM_I32
            safe_data = _sanitize_name(data_local)
            lines.append(
                f"      (local.set ${safe_data}"
                f" (call $__alloc (i32.const {data_size}) (i32.const {elem_size})))"
            )
            # Store data pointer in header
            lines.append(
                f"      (i32.store (i32.add (local.get ${dest}) (i32.const 12))"
                f" (local.get ${safe_data}))"
            )
            # Store each element
            store_op = self._store_op_for_type(elem_ty)
            for i, elem_val in enumerate(inst.elements):
                elem_name = _sanitize_name(elem_val.name)
                offset = i * elem_size
                lines.append(
                    f"      ({store_op}"
                    f" (i32.add (local.get ${safe_data}) (i32.const {offset}))"
                    f" (local.get ${elem_name}))"
                )
        else:
            # Null data pointer for empty list
            lines.append(
                f"      (i32.store (i32.add (local.get ${dest}) (i32.const 12))" f" (i32.const 0))"
            )

        return lines

    def _emit_list_push(self, inst: ListPush, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit list push: append an element, potentially reallocating."""
        dest = _sanitize_name(inst.dest.name)
        list_val = _sanitize_name(inst.list_val.name)
        elem = _sanitize_name(inst.element.name)
        elem_ty = self._locals.get(inst.element.name, _WASM_I64)
        store_op = self._store_op_for_type(elem_ty)
        elem_size = self._wasm_type_size(elem_ty)

        # Simplified push: assume capacity is sufficient (no realloc)
        # A production implementation would check cap and grow if needed.
        return [
            "      ;; list push (simplified, no realloc)",
            f"      (local.set ${dest} (local.get ${list_val}))",
            "      ;; Store element at data[len]",
            f"      ({store_op}",
            "        (i32.add",
            f"          (i32.load (i32.add (local.get ${list_val}) (i32.const 12)))",
            f"          (i32.mul (i32.load (local.get ${list_val}))" f" (i32.const {elem_size}))",
            "        )",
            f"        (local.get ${elem})",
            "      )",
            "      ;; Increment length",
            f"      (i32.store (local.get ${list_val})",
            f"        (i32.add (i32.load (local.get ${list_val})) (i32.const 1))",
            "      )",
        ]

    def _emit_index_get(self, inst: IndexGet, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit list[i] read."""
        dest = _sanitize_name(inst.dest.name)
        obj = _sanitize_name(inst.obj.name)
        index = _sanitize_name(inst.index.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)
        elem_size = self._wasm_type_size(dest_ty)

        return [
            f"      (local.set ${dest} ({load_op}",
            "        (i32.add",
            f"          (i32.load (i32.add (local.get ${obj}) (i32.const 12)))",
            f"          (i32.mul (i32.wrap_i64 (local.get ${index}))" f" (i32.const {elem_size}))",
            "        )",
            "      ))",
        ]

    def _emit_index_set(self, inst: IndexSet, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit list[i] write."""
        obj = _sanitize_name(inst.obj.name)
        index = _sanitize_name(inst.index.name)
        val = _sanitize_name(inst.val.name)
        val_ty = self._locals.get(inst.val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        elem_size = self._wasm_type_size(val_ty)

        return [
            f"      ({store_op}",
            "        (i32.add",
            f"          (i32.load (i32.add (local.get ${obj}) (i32.const 12)))",
            f"          (i32.mul (i32.wrap_i64 (local.get ${index}))" f" (i32.const {elem_size}))",
            "        )",
            f"        (local.get ${val})",
            "      )",
        ]

    def _emit_map_init(self, inst: MapInit, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit map construction.

        Maps use a simple open-addressing hash table:
        Header: [i32 count, i32 capacity, i32 key_size, i32 val_size, i32 data_ptr]
        """
        dest = _sanitize_name(inst.dest.name)
        count = len(inst.pairs)
        cap = max(count * 2, 8)  # Load factor ~0.5
        header_size = 20  # 5 * i32

        lines: list[str] = []
        lines.append(
            f"      (local.set ${dest}" f" (call $__alloc (i32.const {header_size}) (i32.const 4)))"
        )
        lines.append(f"      (i32.store (local.get ${dest}) (i32.const {count}))")
        lines.append(
            f"      (i32.store (i32.add (local.get ${dest}) (i32.const 4))" f" (i32.const {cap}))"
        )
        # Simplified: store pairs linearly (key, value) in data section
        if count > 0:
            entry_size = 16  # key(8) + value(8)
            data_size = cap * entry_size
            data_local = f"_map_data_{id(inst) & 0xFFFF}"
            if data_local not in self._locals:
                self._locals[data_local] = _WASM_I32
            safe_data = _sanitize_name(data_local)
            lines.append(
                f"      (local.set ${safe_data}"
                f" (call $__alloc (i32.const {data_size}) (i32.const 8)))"
            )
            lines.append(
                f"      (i32.store (i32.add (local.get ${dest}) (i32.const 16))"
                f" (local.get ${safe_data}))"
            )
            for i, (key_val, val_val) in enumerate(inst.pairs):
                key_name = _sanitize_name(key_val.name)
                val_name = _sanitize_name(val_val.name)
                key_ty = self._locals.get(key_val.name, _WASM_I64)
                val_ty = self._locals.get(val_val.name, _WASM_I64)
                key_store = self._store_op_for_type(key_ty)
                val_store = self._store_op_for_type(val_ty)
                base = i * entry_size
                lines.append(
                    f"      ({key_store}"
                    f" (i32.add (local.get ${safe_data}) (i32.const {base}))"
                    f" (local.get ${key_name}))"
                )
                lines.append(
                    f"      ({val_store}"
                    f" (i32.add (local.get ${safe_data}) (i32.const {base + 8}))"
                    f" (local.get ${val_name}))"
                )

        return lines

    # ------------------------------------------------------------------
    # Enum / Tagged Union instructions
    # ------------------------------------------------------------------

    def _emit_enum_init(self, inst: EnumInit, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit enum variant construction."""
        dest = _sanitize_name(inst.dest.name)
        enum_name = inst.enum_type.type_info.name if inst.enum_type.type_info.name else ""
        variants = self._enum_variants.get(enum_name, {})
        tag = variants.get(inst.variant, 0)

        lines: list[str] = []
        # Allocate tagged union: [i32 tag][payload bytes...]
        payload_size = max(len(inst.payload) * 8, 8)
        total = _I32_SIZE + payload_size
        lines.append(
            f"      (local.set ${dest}" f" (call $__alloc (i32.const {total}) (i32.const 4)))"
        )
        # Write tag
        lines.append(f"      (i32.store (local.get ${dest}) (i32.const {tag}))")
        # Write payload
        for i, payload_val in enumerate(inst.payload):
            pname = _sanitize_name(payload_val.name)
            pty = self._locals.get(payload_val.name, _WASM_I64)
            store_op = self._store_op_for_type(pty)
            offset = _I32_SIZE + i * 8
            lines.append(
                f"      ({store_op}"
                f" (i32.add (local.get ${dest}) (i32.const {offset}))"
                f" (local.get ${pname}))"
            )
        return lines

    def _emit_enum_tag(self, inst: EnumTag, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit enum tag extraction."""
        dest = _sanitize_name(inst.dest.name)
        enum_val = _sanitize_name(inst.enum_val.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I32)
        if dest_ty == _WASM_I64:
            return [
                f"      (local.set ${dest}"
                f" (i64.extend_i32_u (i32.load (local.get ${enum_val}))))"
            ]
        return [f"      (local.set ${dest} (i32.load (local.get ${enum_val})))"]

    def _emit_enum_payload(self, inst: EnumPayload, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit enum payload extraction."""
        dest = _sanitize_name(inst.dest.name)
        enum_val = _sanitize_name(inst.enum_val.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)
        offset = _I32_SIZE + inst.payload_idx * 8
        return [
            f"      (local.set ${dest} ({load_op}"
            f" (i32.add (local.get ${enum_val}) (i32.const {offset}))))"
        ]

    # ------------------------------------------------------------------
    # Option / Result instructions
    # ------------------------------------------------------------------

    def _emit_wrap_some(self, inst: WrapSome, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit Some(val): allocate tagged union with tag=1."""
        return self._emit_wrap_some_call(_sanitize_name(inst.dest.name), inst.val)

    def _emit_wrap_some_call(self, dest: str, val: Value) -> list[str]:
        """Helper for Some() wrapping."""
        val_name = _sanitize_name(val.name)
        val_ty = self._locals.get(val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        return [
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_TAGGED_UNION_SIZE}) (i32.const 4)))",
            f"      (i32.store (local.get ${dest}) (i32.const 1))  ;; tag = Some",
            f"      ({store_op}"
            f" (i32.add (local.get ${dest}) (i32.const {_I32_SIZE}))"
            f" (local.get ${val_name}))",
        ]

    def _emit_wrap_none(self, inst: WrapNone, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit None: allocate tagged union with tag=0."""
        dest = _sanitize_name(inst.dest.name)
        return [
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_TAGGED_UNION_SIZE}) (i32.const 4)))",
            f"      (i32.store (local.get ${dest}) (i32.const 0))  ;; tag = None",
        ]

    def _emit_wrap_ok(self, inst: WrapOk, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit Ok(val): tag=1."""
        return self._emit_wrap_ok_call(_sanitize_name(inst.dest.name), inst.val)

    def _emit_wrap_ok_call(self, dest: str, val: Value) -> list[str]:
        """Helper for Ok() wrapping."""
        val_name = _sanitize_name(val.name)
        val_ty = self._locals.get(val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        return [
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_TAGGED_UNION_SIZE}) (i32.const 4)))",
            f"      (i32.store (local.get ${dest}) (i32.const 1))  ;; tag = Ok",
            f"      ({store_op}"
            f" (i32.add (local.get ${dest}) (i32.const {_I32_SIZE}))"
            f" (local.get ${val_name}))",
        ]

    def _emit_wrap_err(self, inst: WrapErr, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit Err(val): tag=0."""
        return self._emit_wrap_err_call(_sanitize_name(inst.dest.name), inst.val)

    def _emit_wrap_err_call(self, dest: str, val: Value) -> list[str]:
        """Helper for Err() wrapping."""
        val_name = _sanitize_name(val.name)
        val_ty = self._locals.get(val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        return [
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_TAGGED_UNION_SIZE}) (i32.const 4)))",
            f"      (i32.store (local.get ${dest}) (i32.const 0))  ;; tag = Err",
            f"      ({store_op}"
            f" (i32.add (local.get ${dest}) (i32.const {_I32_SIZE}))"
            f" (local.get ${val_name}))",
        ]

    def _emit_unwrap(self, inst: Unwrap, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit unwrap: extract payload from Option/Result."""
        dest = _sanitize_name(inst.dest.name)
        val = _sanitize_name(inst.val.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)
        return [
            f"      (local.set ${dest} ({load_op}"
            f" (i32.add (local.get ${val}) (i32.const {_I32_SIZE}))))"
        ]

    # ------------------------------------------------------------------
    # String interpolation
    # ------------------------------------------------------------------

    def _emit_interp_concat(self, inst: InterpConcat, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit string interpolation concatenation.

        Simplified: concatenate string parts by copying bytes into a new
        heap-allocated buffer. Non-string parts should already be converted
        to strings by the lowering pass.
        """
        dest = _sanitize_name(inst.dest.name)
        if not inst.parts:
            # Empty string
            return [
                f"      (local.set ${dest}" f" (call $__alloc (i32.const 4) (i32.const 4)))",
                f"      (i32.store (local.get ${dest}) (i32.const 0))",
            ]

        # For a single part, just copy the pointer
        if len(inst.parts) == 1:
            part = _sanitize_name(inst.parts[0].name)
            return [f"      (local.set ${dest} (local.get ${part}))"]

        # Multi-part: simplified stub (full impl would compute total length,
        # allocate, and memcpy each part)
        lines: list[str] = [
            f"      ;; interp_concat with {len(inst.parts)} parts (simplified)",
        ]
        # Use first part as result for now
        first = _sanitize_name(inst.parts[0].name)
        lines.append(f"      (local.set ${dest} (local.get ${first}))")
        return lines

    # ------------------------------------------------------------------
    # Agent instructions
    # ------------------------------------------------------------------

    def _emit_agent_spawn(self, inst: AgentSpawn, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit agent spawn: allocate agent struct."""
        dest = _sanitize_name(inst.dest.name)
        return [
            "      ;; agent_spawn",
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_AGENT_SIZE}) (i32.const 4)))",
            "      ;; Initialize agent status = RUNNING (1)",
            f"      (i32.store (i32.add (local.get ${dest}) (i32.const 12)) (i32.const 1))",
        ]

    def _emit_agent_send(self, inst: AgentSend, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit agent send: write value to agent's inbox."""
        agent = _sanitize_name(inst.agent.name)
        val = _sanitize_name(inst.val.name)
        val_ty = self._locals.get(inst.val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        return [
            f"      ;; agent_send {inst.channel}",
            f"      ({store_op}"
            f" (i32.load (i32.add (local.get ${agent}) (i32.const 4)))"
            f" (local.get ${val}))",
        ]

    def _emit_agent_sync(self, inst: AgentSync, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit agent sync: read from agent's outbox."""
        dest = _sanitize_name(inst.dest.name)
        agent = _sanitize_name(inst.agent.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)
        return [
            f"      ;; agent_sync {inst.channel}",
            f"      (local.set ${dest} ({load_op}"
            f" (i32.load (i32.add (local.get ${agent}) (i32.const 8)))))",
        ]

    # ------------------------------------------------------------------
    # Signal instructions
    # ------------------------------------------------------------------

    def _emit_signal_init(self, inst: SignalInit, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit signal initialization."""
        dest = _sanitize_name(inst.dest.name)
        init_val = _sanitize_name(inst.initial_val.name)
        val_ty = self._locals.get(inst.initial_val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        return [
            "      ;; signal_init",
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_SIGNAL_SIZE}) (i32.const 8)))",
            f"      ({store_op} (local.get ${dest}) (local.get ${init_val}))",
        ]

    def _emit_signal_get(self, inst: SignalGet, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit signal value read."""
        dest = _sanitize_name(inst.dest.name)
        signal = _sanitize_name(inst.signal.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)
        return [f"      (local.set ${dest} ({load_op} (local.get ${signal})))"]

    def _emit_signal_set(self, inst: SignalSet, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit signal value write."""
        signal = _sanitize_name(inst.signal.name)
        val = _sanitize_name(inst.val.name)
        val_ty = self._locals.get(inst.val.name, _WASM_I64)
        store_op = self._store_op_for_type(val_ty)
        return [
            "      ;; signal_set",
            f"      ({store_op} (local.get ${signal}) (local.get ${val}))",
        ]

    def _emit_signal_computed(self, inst: SignalComputed, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit computed signal creation (stub)."""
        dest = _sanitize_name(inst.dest.name)
        return [
            "      ;; signal_computed (stub)",
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_SIGNAL_SIZE}) (i32.const 8)))",
        ]

    def _emit_signal_subscribe(
        self, inst: SignalSubscribe, _bl: str, _fn: MIRFunction
    ) -> list[str]:
        """Emit signal subscription (stub)."""
        return [
            "      ;; signal_subscribe (stub)",
        ]

    # ------------------------------------------------------------------
    # Stream instructions
    # ------------------------------------------------------------------

    def _emit_stream_init(self, inst: StreamInit, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit stream initialization from a source list."""
        dest = _sanitize_name(inst.dest.name)
        source = _sanitize_name(inst.source.name)
        return [
            "      ;; stream_init",
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {_STREAM_SIZE}) (i32.const 4)))",
            f"      (i32.store (local.get ${dest}) (local.get ${source}))",
            f"      (i32.store (i32.add (local.get ${dest}) (i32.const 4)) (i32.const 0))",
        ]

    def _emit_stream_op(self, inst: StreamOp, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a stream operation (map, filter, fold, etc.)."""
        dest = _sanitize_name(inst.dest.name)
        source = _sanitize_name(inst.source.name)

        op_name = inst.op_kind.name.lower()
        return [
            f"      ;; stream_{op_name} (stub: returns source stream)",
            f"      (local.set ${dest} (local.get ${source}))",
        ]

    # ------------------------------------------------------------------
    # Closure instructions
    # ------------------------------------------------------------------

    def _emit_closure_create(self, inst: ClosureCreate, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit closure creation: allocate env struct and store captures."""
        dest = _sanitize_name(inst.dest.name)
        captures = inst.captures
        env_size = max(len(captures) * 8, 8)
        # Closure layout: [i32 fn_index, i32 env_ptr]
        closure_size = 8

        lines: list[str] = []
        lines.append(
            f"      ;; closure_create {inst.fn_name}",
        )
        # Allocate closure struct
        lines.append(
            f"      (local.set ${dest}"
            f" (call $__alloc (i32.const {closure_size}) (i32.const 4)))"
        )
        # Store function index
        fn_idx = self._func_indices.get(inst.fn_name, 0)
        lines.append(f"      (i32.store (local.get ${dest}) (i32.const {fn_idx}))")

        if captures:
            # Allocate and fill environment
            env_local = f"_env_{id(inst) & 0xFFFF}"
            if env_local not in self._locals:
                self._locals[env_local] = _WASM_I32
            safe_env = _sanitize_name(env_local)
            lines.append(
                f"      (local.set ${safe_env}"
                f" (call $__alloc (i32.const {env_size}) (i32.const 8)))"
            )
            lines.append(
                f"      (i32.store (i32.add (local.get ${dest}) (i32.const 4))"
                f" (local.get ${safe_env}))"
            )
            for i, cap_val in enumerate(captures):
                cap_name = _sanitize_name(cap_val.name)
                cap_ty = self._locals.get(cap_val.name, _WASM_I64)
                store_op = self._store_op_for_type(cap_ty)
                lines.append(
                    f"      ({store_op}"
                    f" (i32.add (local.get ${safe_env}) (i32.const {i * 8}))"
                    f" (local.get ${cap_name}))"
                )
        else:
            lines.append(
                f"      (i32.store (i32.add (local.get ${dest}) (i32.const 4))" f" (i32.const 0))"
            )

        return lines

    def _emit_closure_call(self, inst: ClosureCall, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit closure call (indirect call through table).

        Note: Full indirect call support requires the funcref table to be
        populated. This is a simplified stub that extracts fn_index and
        calls via call_indirect.
        """
        dest = _sanitize_name(inst.dest.name)
        closure = _sanitize_name(inst.closure.name)
        return [
            "      ;; closure_call (simplified stub)",
            "      ;; Would use call_indirect with fn_index from closure",
            f"      (local.set ${dest} (i32.load (local.get ${closure})))",
        ]

    def _emit_env_load(self, inst: EnvLoad, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit loading a captured variable from the closure environment."""
        dest = _sanitize_name(inst.dest.name)
        env = _sanitize_name(inst.env.name)
        dest_ty = self._locals.get(inst.dest.name, _WASM_I64)
        load_op = self._load_op_for_type(dest_ty)
        offset = inst.index * 8
        return [
            f"      (local.set ${dest} ({load_op}"
            f" (i32.add (local.get ${env}) (i32.const {offset}))))"
        ]

    # ------------------------------------------------------------------
    # Assert instruction
    # ------------------------------------------------------------------

    def _emit_assert(self, inst: Assert, _bl: str, _fn: MIRFunction) -> list[str]:
        """Emit a runtime assertion."""
        cond = _sanitize_name(inst.cond.name)
        cond_ty = self._locals.get(inst.cond.name, _WASM_I32)

        lines: list[str] = []
        # Convert condition to i32 if needed
        if cond_ty == _WASM_I64:
            cond_expr = f"(i32.wrap_i64 (local.get ${cond}))"
        elif cond_ty == _WASM_I32:
            cond_expr = f"(local.get ${cond})"
        else:
            cond_expr = f"(i32.trunc_f64_s (local.get ${cond}))"

        # If condition is false, abort
        lines.append(f"      (if (i32.eqz {cond_expr})")
        lines.append("        (then")

        if inst.message is not None:
            msg = _sanitize_name(inst.message.name)
            lines.append(
                f"          (call $abort"
                f" (i32.add (local.get ${msg}) (i32.const 4))"
                f" (i32.load (local.get ${msg})))"
            )
        else:
            # Use a default message from the string table
            msg_str = f"assertion failed at {inst.filename}:{inst.line}"
            offset = self._string_cache.get(msg_str, 0)
            encoded_len = len(msg_str.encode("utf-8"))
            lines.append(
                f"          (call $abort"
                f" (i32.const {offset + _I32_SIZE})"
                f" (i32.const {encoded_len}))"
            )

        lines.append("        )")
        lines.append("      )")

        return lines

    # ------------------------------------------------------------------
    # Memory operation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _store_op_for_type(wasm_ty: str) -> str:
        """Return the WASM store instruction for a given type."""
        if wasm_ty == _WASM_I64:
            return "i64.store"
        if wasm_ty == _WASM_F64:
            return "f64.store"
        return "i32.store"

    @staticmethod
    def _load_op_for_type(wasm_ty: str) -> str:
        """Return the WASM load instruction for a given type."""
        if wasm_ty == _WASM_I64:
            return "i64.load"
        if wasm_ty == _WASM_F64:
            return "f64.load"
        return "i32.load"


# ---------------------------------------------------------------------------
# Name sanitization
# ---------------------------------------------------------------------------


def _sanitize_name(name: str) -> str:
    """Sanitize a MIR name for use as a WASM identifier.

    WASM identifiers (after $) allow most printable ASCII characters,
    but we replace problematic ones for safety.
    """
    if not name:
        return "_unnamed"
    # Strip leading % from SSA names
    if name.startswith("%"):
        name = name[1:]
    # Replace characters that could confuse WAT parsers
    result = name.replace(".", "_").replace("-", "_").replace("::", "__")
    result = result.replace(" ", "_").replace("<", "_").replace(">", "_")
    result = result.replace(",", "_").replace("(", "_").replace(")", "_")
    if not result:
        return "_unnamed"
    # Ensure doesn't start with a digit
    if result[0].isdigit():
        result = "v" + result
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile_to_wasm(
    mir_module: MIRModule,
    options: WasmOptions | None = None,
) -> str:
    """Compile a MIR module to WebAssembly text format (WAT).

    Args:
        mir_module: The MIR module to compile.
        options: Optional configuration for the emitter.

    Returns:
        A string containing the complete WAT module.
    """
    emitter = WasmEmitter(options=options)
    return emitter.emit(mir_module)


def compile_to_wasm_binary(
    mir_module: MIRModule,
    options: WasmOptions | None = None,
) -> bytes:
    """Compile a MIR module to WebAssembly binary format (.wasm).

    This first emits WAT text, then invokes ``wat2wasm`` (from the
    WebAssembly Binary Toolkit) to convert it to binary. Raises
    RuntimeError if wat2wasm is not available.

    Args:
        mir_module: The MIR module to compile.
        options: Optional configuration for the emitter.

    Returns:
        The WASM binary as bytes.

    Raises:
        RuntimeError: If wat2wasm is not found or the conversion fails.
    """
    wat_text = compile_to_wasm(mir_module, options=options)

    try:
        result = subprocess.run(
            ["wat2wasm", "-", "--output=-"],
            input=wat_text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "wat2wasm is required for binary WASM output. "
            "Install the WebAssembly Binary Toolkit: "
            "https://github.com/WebAssembly/wabt"
        ) from None

    if result.returncode != 0:
        error_msg = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"wat2wasm failed:\n{error_msg}")

    return result.stdout
