"""Text-based LLVM IR emitter — no llvmlite dependency.

Generates alloca/load/store IR. clang mem2reg optimizes to SSA.
This avoids llvmlite's codegen bugs with large struct values.
"""

from __future__ import annotations

import os
import struct as pystruct
from typing import Any

from mapanare.mir import (
    AgentSend,
    AgentSpawn,
    AgentSync,
    Assert,
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
    InterpConcat,
    Jump,
    ListInit,
    ListPush,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRPipeInfo,
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
    StreamOpKind,
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
from mapanare.types import TypeInfo, TypeKind

# ── LLVM type string constants ──────────────────────────────────────
I1 = "i1"
I8 = "i8"
I32 = "i32"
I64 = "i64"
DBL = "double"
VOID = "void"
PTR = "i8*"
STR = "{i8*, i64}"
LIST = "{i8*, i64, i64, i64}"
CLOS = "{i8*, i8*}"
ENUM = "{i64, i8*}"


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
    if t.endswith("*"):
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
    if t.endswith("*"):
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
    if ty.endswith("*"):
        return "null"
    if ty in (I1, I8, I32, I64):
        return "0"
    if ty in (DBL, "float"):
        return "0.000000e+00"
    if ty.startswith("{") or ty.startswith("["):
        return "zeroinitializer"
    return "0"


# ── Emitter ─────────────────────────────────────────────────────────
class LLVMTextEmitter:
    """Emit LLVM IR as text from a MIR module. No llvmlite dependency."""

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
        # 3) forward-declare MIR functions (strip % from names)
        for f in mir.functions:
            if f.name.startswith("%"):
                f.name = f.name[1:]
            self._sigs[f.name] = (
                self._rty(f.return_type),
                [self._rty(p.ty) for p in f.params],
                False,
            )
        # 4) emit bodies
        fns: list[str] = []
        for f in mir.functions:
            if f.blocks:
                fns.append(self._emit_fn(f))
        # 5) agent wrappers
        for aname, ainfo in mir.agents.items():
            fns.append(self._emit_agent_wrap(aname, ainfo))
        # 6) pipe defs
        for pname, pinfo in mir.pipes.items():
            fns.append(self._emit_pipe(pname, pinfo))
        # 7) assemble
        hdr = [
            f"; ModuleID = '{self._name}'",
            f'source_filename = "{self._name}"',
            f'target datalayout = "{self._layout}"',
            f'target triple = "{self._triple}"',
            "",
        ]
        ver = self._version()
        tail = ["", "!mapanare.version = !{!0}", f'!0 = !{{!"{ver}"}}', ""]
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
            return ENUM
        if k == TypeKind.OPTION:
            a = mt.type_info.args
            inner = self._rti(a[0]) if a else PTR
            return "{" + f"i1, {inner}" + "}"
        if k == TypeKind.RESULT:
            a = mt.type_info.args
            if len(a) >= 2:
                return "{" + f"i1, {{{self._rti(a[0])}, {self._rti(a[1])}}}" + "}"
            return "{i1, {i8*, i8*}}"
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
            return ENUM
        for e in self._enums:
            if e.endswith("__" + nm):
                return ENUM
        return PTR

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
    def _win64(self) -> bool:
        return "windows" in self._triple

    @staticmethod
    def _is_large_struct(ty: str) -> bool:
        """True if *ty* is a struct that exceeds 8 bytes (Win64 indirect ABI)."""
        return ty.startswith("{") and ty.endswith("}") and _tsz(ty) > 8

    def _decl_fn(self, nm: str, ret: str, pts: list[str], va: bool = False) -> None:
        if nm in self._declared:
            return
        self._declared.add(nm)
        self._sigs[nm] = (ret, pts, va)

        if self._win64:
            # Win64 ABI: large structs passed by pointer, returned via sret
            abi_pts = [f"{t}*" if self._is_large_struct(t) else t for t in pts]
            if self._is_large_struct(ret):
                sret = f"{ret}* sret({ret})"
                abi_pts = [sret] + abi_pts
                abi_ret = "void"
            else:
                abi_ret = ret
        else:
            abi_pts = list(pts)
            abi_ret = ret

        ps = ", ".join(abi_pts)
        if va:
            ps += ", ..." if ps else "..."
        self._decls.append(f"declare {abi_ret} @{nm}({ps})")

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
        self._blk[self._cb].append(f"  {txt}")

    @staticmethod
    def _san(nm: str) -> str:
        return nm.lstrip("%").replace(".", "_").replace("-", "_")

    def _get(self, v: Value) -> tuple[str, str]:
        """Load MIR value from alloca → (tmp, type)."""
        for k in (v.name, v.name.lstrip("%"), "%" + v.name.lstrip("%")):
            if k in self._alloc:
                a, ty = self._alloc[k]
                t = self._f("l")
                self._L(f"{t} = load {ty}, {ty}* {a}")
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
            self._ent.append(f"  store {ty} {_zero(ty)}, {ty}* {a}")
        a, aty = self._alloc[nm]
        # If new value is larger, upgrade the alloca BUT keep the old one
        # accessible. Create a new alloca sized for the larger type, but
        # DON'T discard the old alloca mapping — instead, keep BOTH and
        # store the larger value in the new alloca.
        if ty != aty and _tsz(ty) > _tsz(aty):
            a = self._f(f"{self._san(nm)}.up")
            self._alloc[nm] = (a, ty)
            self._ent.append(f"  {a} = alloca {ty}, align 8")
            self._ent.append(f"  store {ty} {_zero(ty)}, {ty}* {a}")
            aty = ty
        if ty == aty:
            self._L(f"store {ty} {val}, {ty}* {a}")
        else:
            c = self._coerce(val, ty, aty)
            self._L(f"store {aty} {c}, {aty}* {a}")

    def _coerce(self, val: str, fr: str, to: str) -> str:
        if fr == to:
            return val
        if fr.endswith("*") and to.endswith("*"):
            t = self._f("bc")
            self._L(f"{t} = bitcast {fr} {val} to {to}")
            return t
        if fr.endswith("*") and to == I64:
            t = self._f("p2i")
            self._L(f"{t} = ptrtoint {fr} {val} to i64")
            return t
        if fr == I64 and to.endswith("*"):
            t = self._f("i2p")
            self._L(f"{t} = inttoptr i64 {val} to {to}")
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
            self._L(f"store {fr} {val}, {fr}* {a}")
            p = self._f("rp")
            self._L(f"{p} = bitcast {fr}* {a} to {to}*")
            v = self._f("rv")
            self._L(f"{v} = load {to}, {to}* {p}")
            return v
        else:
            a = self._f("rc")
            self._ent.append(f"  {a} = alloca {to}, align 8")
            self._L(f"store {to} {_zero(to)}, {to}* {a}")
            p = self._f("rp")
            self._L(f"{p} = bitcast {to}* {a} to {fr}*")
            self._L(f"store {fr} {val}, {fr}* {p}")
            v = self._f("rv")
            self._L(f"{v} = load {to}, {to}* {a}")
            return v

    # ── string / printf helpers ─────────────────────────────────────
    def _mkstr(self, text: str) -> tuple[str, str]:
        raw = text.encode("utf-8")
        n = len(raw)
        esc = _esc(raw)
        gn = f"@.str.{self._strc}"
        self._strc += 1
        at = f"[{n} x i8]"
        self._globals.append(f'{gn} = private constant {at} c"{esc}", align 2')
        p = self._f("sp")
        self._L(f"{p} = getelementptr inbounds {at}, {at}* {gn}, i64 0, i64 0")
        s0 = self._f("s")
        self._L(f"{s0} = insertvalue {{i8*, i64}} undef, i8* {p}, 0")
        s1 = self._f("s")
        self._L(f"{s1} = insertvalue {{i8*, i64}} {s0}, i64 {n}, 1")
        return s1, STR

    def _fmtptr(self, fmt: str) -> str:
        if fmt not in self._fmts:
            raw = fmt.encode("utf-8") + b"\x00"
            n = len(raw)
            gn = f"@.fmt.{len(self._fmts)}"
            self._fmts[fmt] = gn
            at = f"[{n} x i8]"
            self._globals.append(f'{gn} = private constant {at} c"{_esc(raw)}", align 2')
        gn = self._fmts[fmt]
        raw = fmt.encode("utf-8") + b"\x00"
        at = f"[{len(raw)} x i8]"
        p = self._f("fp")
        self._L(f"{p} = getelementptr inbounds {at}, {at}* {gn}, i64 0, i64 0")
        return p

    def _printf(self, fmt: str, args: list[tuple[str, str]]) -> None:
        self._ensure("printf", I32, [PTR], va=True)
        p = self._fmtptr(fmt)
        a = "".join(f", {ty} {v}" for v, ty in args)
        r = self._f("pf")
        self._L(f"{r} = call i32 (i8*, ...) @printf(i8* {p}{a})")

    def _rt(
        self, fn: str, ret: str, pts: list[str], args: list[tuple[str, str]], nm: str = ""
    ) -> str:
        """Call runtime fn, coerce args. Returns result name (empty for void)."""
        self._ensure(fn, ret, pts)
        coerced: list[tuple[str, str]] = []
        for i, (v, t) in enumerate(args):
            et = pts[i] if i < len(pts) else t
            coerced.append((self._coerce(v, t, et) if t != et else v, et))

        if self._win64:
            # Win64 ABI: pass large structs by pointer, return via sret
            abi_args: list[tuple[str, str]] = []
            for v, t in coerced:
                if self._is_large_struct(t):
                    a = self._alloca(t, "sarg")
                    self._L(f"store {t} {v}, {t}* {a}")
                    abi_args.append((a, f"{t}*"))
                else:
                    abi_args.append((v, t))

            if self._is_large_struct(ret):
                sret_a = self._alloca(ret, nm or "sret")
                sret_arg = f"{ret}* sret({ret}) {sret_a}"
                rest = ", ".join(f"{t} {v}" for v, t in abi_args)
                a_str = f"{sret_arg}, {rest}" if rest else sret_arg
                self._L(f"call void @{fn}({a_str})")
                r = self._f(nm or "rt")
                self._L(f"{r} = load {ret}, {ret}* {sret_a}")
                return r

            a_str = ", ".join(f"{t} {v}" for v, t in abi_args)
            if ret == VOID:
                self._L(f"call void @{fn}({a_str})")
                return ""
            r = self._f(nm or "rt")
            self._L(f"{r} = call {ret} @{fn}({a_str})")
            return r

        a = ", ".join(f"{t} {v}" for v, t in coerced)
        if ret == VOID:
            self._L(f"call void @{fn}({a})")
            return ""
        r = self._f(nm or "rt")
        self._L(f"{r} = call {ret} @{fn}({a})")
        return r

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

        # param allocas
        for p in fn.params:
            ty = self._rty(p.ty)
            s = self._san(p.name)
            a = f"%{s}.addr"
            self._alloc[p.name] = (a, ty)
            self._alloc[f"%{p.name}"] = (a, ty)
            self._ent.append(f"  {a} = alloca {ty}, align 8")

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
                self._ent.append(f"  store {ty} {_zero(ty)}, {ty}* {a}")
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
                self._ent.append(f"  store {ty} {_zero(ty)}, {ty}* {a}")

        # emit blocks
        for bb in fn.blocks:
            self._cb = bb.label
            self._blk[bb.label] = []
            for inst in bb.instructions:
                if isinstance(inst, Phi):
                    continue
                h = self._disp.get(type(inst))
                if h:
                    h(inst)

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
                        ins.append(f"  {t} = load {st}, {st}* {sa}")
                        if st == ty:
                            ins.append(f"  store {ty} {t}, {ty}* {addr}")
                        else:
                            bp = self._f("pb")
                            ins.append(f"  {bp} = bitcast {st}* {sa} to {ty}*")
                            cv = self._f("pv")
                            ins.append(f"  {cv} = load {ty}, {ty}* {bp}")
                            ins.append(f"  store {ty} {cv}, {ty}* {addr}")
                        done = True
                        break
                if not done:
                    ins.append(f"  store {ty} {_zero(ty)}, {ty}* {addr}")
                # Insert before the terminator (last line)
                pos = max(len(lines) - 1, 0)
                for idx_ins, ln in enumerate(ins):
                    lines.insert(pos + idx_ins, ln)

        # ensure terminated
        for bb in fn.blocks:
            ls = self._blk[bb.label]
            if not ls or not self._is_term(ls[-1]):
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
            for lbl in self._blk:
                for idx, ln in enumerate(self._blk[lbl]):
                    if ln.strip() == "ret void":
                        self._blk[lbl][idx] = "  ret i64 0"
        ps = ", ".join(f"{self._rty(p.ty)} %{self._san(p.name)}" for p in fn.params)
        lk = "internal " if (not fn.is_public and fn.name != "main") else ""
        out: list[str] = [f"define {lk}{rt} @{fn.name}({ps}) {{", "pre_entry:"]
        out.extend(self._ent)
        for p in fn.params:
            ty = self._rty(p.ty)
            s = self._san(p.name)
            out.append(f"  store {ty} %{s}, {ty}* %{s}.addr")
        if fn.blocks:
            out.append(f"  br label %{fn.blocks[0].label}")
        for bb in fn.blocks:
            out.append(f"{bb.label}:")
            out.extend(self._blk[bb.label])
        out.append("}")
        out.append("")
        return "\n".join(out)

    @staticmethod
    def _is_term(line: str) -> bool:
        s = line.strip()
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
                rt, pts, _ = self._sigs[v]
                ft = f"{rt} ({', '.join(pts)})*"
                t = self._f("fr")
                self._L(f"{t} = bitcast {ft} @{v} to i8*")
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
        # Deep-clone list fields inside structs to avoid aliased data
        # pointers.  Without this, two copies of a struct share the same
        # list data buffer; a realloc in one invalidates the other.
        if i.src.ty.kind == TypeKind.STRUCT:
            sn = self._res_struct(i.src.ty.type_info.name)
            if sn in self._structs:
                self._clone_list_fields(i.dest, sn)

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
            bc = self._f("clbc")
            self._L(f"{bc} = bitcast {aty}* {addr} to {sty}*")
            addr = bc
        self._ensure("__mn_list_clone", LIST, [f"{LIST}*"])
        for idx, (fn, ft) in enumerate(fields):
            if ft == LIST:
                fp = self._f("clf")
                self._L(f"{fp} = getelementptr inbounds {sty}, {sty}* {addr}, i32 0, i32 {idx}")
                cloned = self._f("clr")
                self._L(f"{cloned} = call {LIST} @__mn_list_clone({LIST}* {fp})")
                self._L(f"store {LIST} {cloned}, {LIST}* {fp}")
        # Note: MIRModule's list fields (enums, structs, extern_fns, etc.) are
        # static after registration pass 1 — they don't need cloning because
        # they're never modified during pass 2. Cloning them causes OOM.

    def _struct_name_for_llvm_type(self, llvm_ty: str) -> str | None:
        """Find the struct name whose LLVM type matches."""
        for sn, sty in self._struct_ty.items():
            if sty == llvm_ty:
                return sn
        return None

    def _clone_nested_struct_lists(self, ptr: str, sty: str, sn: str) -> None:
        """Clone list fields inside a struct-typed field (e.g., MIRModule inside LowerState)."""
        fields = self._structs[sn]
        self._ensure("__mn_list_clone", LIST, [f"{LIST}*"])
        for idx, (_, ft) in enumerate(fields):
            if ft != LIST:
                continue
            fp = self._f("nclf")
            self._L(f"{fp} = getelementptr inbounds {sty}, {sty}* {ptr}, i32 0, i32 {idx}")
            cloned = self._f("nclr")
            self._L(f"{cloned} = call {LIST} @__mn_list_clone({LIST}* {fp})")
            self._L(f"store {LIST} {cloned}, {LIST}* {fp}")

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
        elem_ty = self._struct_ty[elem_name]
        offsets: list[int] = []
        running_offset = 0
        for _, eft in elem_fields:
            if eft == LIST:
                offsets.append(running_offset)
            running_offset += _tsz(eft)
        return offsets

    def _emit_offset_array(self, offsets: list[int]) -> str:
        """Emit a global constant array of i64 offsets and return its name."""
        name = f"@.list_offsets.{self._ctr}"
        self._ctr += 1
        vals = ", ".join(f"i64 {o}" for o in offsets)
        self._globals.append(f"{name} = private constant [{len(offsets)} x i64] [{vals}]")
        gep = self._f("offp")
        self._L(f"{gep} = getelementptr [{len(offsets)} x i64], [{len(offsets)} x i64]* {name}, i64 0, i64 0")
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
            self._put(i.dest, r, STR)
        elif sk == TypeKind.FLOAT and tk == TypeKind.STRING:
            r = self._rt("__mn_str_from_float", STR, [DBL], [(sv, st)])
            self._put(i.dest, r, STR)
        elif sk == TypeKind.BOOL and tk == TypeKind.STRING:
            r = self._rt("__mn_str_from_bool", STR, [I1], [(sv, st)])
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
            self._L(f"store {LIST} {lv}, {LIST}* {la}")
            ra = self._alloca(LIST, "rp")
            self._L(f"store {LIST} {rv}, {LIST}* {ra}")
            r = self._rt(
                "__mn_list_concat",
                LIST,
                [f"{LIST}*", f"{LIST}*"],
                [(la, f"{LIST}*"), (ra, f"{LIST}*")],
            )
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
                    self._L(f"{bc} = bitcast {lt}* {la} to {LIST}*")
                    la = bc
                ev, et = self._get(elem_val)
                ea = self._alloca(et, "pea")
                self._L(f"store {et} {ev}, {et}* {ea}")
                ep = self._f("pep")
                self._L(f"{ep} = bitcast {et}* {ea} to i8*")
                self._ensure("__mn_list_push", VOID, [f"{LIST}*", PTR])
                self._L(f"call void @__mn_list_push({LIST}* {la}, i8* {ep})")
                self._put(i.dest, "0", I1)  # push returns void
                return

        args = [(self._get(a)) for a in i.args]  # [(val, ty)]
        self._san(i.dest.name)

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
                s = self._rt("__mn_str_from_bool", STR, [I1], [args[0]])
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
                self._L(f"store {LIST} {lv}, {LIST}* {la}")
                r = self._rt("__mn_list_len", I64, [f"{LIST}*"], [(la, f"{LIST}*")])
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
            elif ak == TypeKind.FLOAT:
                r = self._rt("__mn_str_from_float", STR, [DBL], [args[0]])
            elif ak == TypeKind.BOOL:
                r = self._rt("__mn_str_from_bool", STR, [I1], [args[0]])
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
            self._put(i.dest, r, STR)
            return

        # join
        if fn == "join" and len(i.args) >= 2:
            sep = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
            lv = self._coerce(args[1][0], args[1][1], LIST) if args[1][1] != LIST else args[1][0]
            la = self._alloca(LIST, "jl")
            self._L(f"store {LIST} {lv}, {LIST}* {la}")
            r = self._rt("__mn_str_join", STR, [STR, f"{LIST}*"], [(sep, STR), (la, f"{LIST}*")])
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
            rt = f"{{i1, {{{t}, i8*}}}}"
            s0 = self._f("ok")
            self._L(f"{s0} = insertvalue {rt} undef, i1 1, 0")
            s1 = self._f("ok")
            self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 0")
            self._put(i.dest, s1, rt)
            return
        if fn == "Err" and args:
            v, t = args[0]
            rt = f"{{i1, {{i8*, {t}}}}}"
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
                self._ent.append(f"  %{self._san(itn)}.addr = alloca i8*, align 8")
                self._L(f"store i8* {mi}, i8** %{self._san(itn)}.addr")
                ko = self._alloca(PTR, "ko")
                self._alloc[f"{itn}.kout"] = (ko, PTR)
                vo = self._alloca(PTR, "vo")
                self._alloc[f"{itn}.vout"] = (vo, PTR)
            ia, _ = self._alloc[itn]
            iv = self._f("mi")
            self._L(f"{iv} = load i8*, i8** {ia}")
            ka, _ = self._alloc[f"{itn}.kout"]
            va_, _ = self._alloc[f"{itn}.vout"]
            ri = self._rt(
                "__mn_map_iter_next",
                I64,
                [PTR, f"{PTR}*", f"{PTR}*"],
                [(iv, PTR), (ka, f"{PTR}*"), (va_, f"{PTR}*")],
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
                self._L(f"{kp} = load i8*, i8** {ka}")
                ety = self._rty(i.dest.ty)
                tp = self._f("tp")
                self._L(f"{tp} = bitcast i8* {kp} to {ety}*")
                r = self._f("kv")
                self._L(f"{r} = load {ety}, {ety}* {tp}")
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
            op = self._f("sop")
            self._L(f"{op} = bitcast i64* {oa} to i8*")
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
                    tp = self._f("tp")
                    self._L(f"{tp} = bitcast {oat}* {oa} to {ety}*")
                    r = self._f("sv")
                    self._L(f"{r} = load {ety}, {ety}* {tp}")
                    self._put(i.dest, r, ety)
            else:
                self._put(i.dest, "0", I64)
            return

        # User function
        if fn in self._sigs:
            ret, pts, va = self._sigs[fn]
            coerced: list[tuple[str, str]] = []
            for j, (v, t) in enumerate(args):
                et = pts[j] if j < len(pts) else t
                coerced.append((self._coerce(v, t, et) if t != et else v, et))
            astr = ", ".join(f"{t} {v}" for v, t in coerced)
            if ret == VOID:
                self._L(f"call void @{fn}({astr})")
                self._put(i.dest, "0", I1)
            else:
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

        # Auto-declare unknown function
        pts_auto = [self._rty(a.ty) for a in i.args]
        for j, pt in enumerate(pts_auto):
            if pt == PTR and j < len(args) and args[j][1] != PTR:
                pts_auto[j] = args[j][1]
        ret_auto = self._rty(i.dest.ty)
        self._decl_fn(fn, ret_auto, pts_auto)
        coerced2: list[tuple[str, str]] = []
        for j, (v, t) in enumerate(args):
            et = pts_auto[j] if j < len(pts_auto) else t
            coerced2.append((self._coerce(v, t, et) if t != et else v, et))
        astr = ", ".join(f"{t} {v}" for v, t in coerced2)
        if ret_auto == VOID:
            self._L(f"call void @{fn}({astr})")
            self._put(i.dest, "0", I1)
        else:
            r = self._f("c")
            self._L(f"{r} = call {ret_auto} @{fn}({astr})")
            self._put(i.dest, r, ret_auto)

    # --- ExternCall ---
    def _do_extern(self, i: ExternCall) -> None:
        args = [self._get(a) for a in i.args]
        full = f"{i.module}__{i.fn_name}" if i.module else i.fn_name
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
                self._L("ret void")
            else:
                v = self._coerce(v, t, rt) if t != rt else v
                self._L(f"ret {rt} {v}")
        else:
            self._L("ret void")

    # --- Jump / Branch / Switch ---
    def _do_jump(self, i: Jump) -> None:
        self._L(f"br label %{i.target}")

    def _do_branch(self, i: Branch) -> None:
        cv, ct = self._get(i.cond)
        if ct != I1:
            if ct.endswith("*"):
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
                    tp = self._f("bx")
                    self._L(f"{tp} = bitcast i8* {raw} to {t}*")
                    self._L(f"store {t} {v}, {t}* {tp}")
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
            if aty != sty:
                bc = self._f("fbc")
                self._L(f"{bc} = bitcast {aty}* {addr} to {sty}*")
                addr = bc
            idx = self._struct_idx[sn][i.field_name]
            fp = self._f("fg")
            self._L(f"{fp} = getelementptr inbounds {sty}, {sty}* {addr}, i32 0, i32 {idx}")
            ft = self._structs[sn][idx][1]
            boxed = self._boxed_struct.get(sn, set())
            if idx in boxed:
                raw = self._f("fr")
                self._L(f"{raw} = load i8*, i8** {fp}")
                at = (
                    self._rty(self._boxed_struct_mir[sn][idx])
                    if sn in self._boxed_struct_mir and idx in self._boxed_struct_mir[sn]
                    else PTR
                )
                if at != PTR:
                    tp = self._f("fu")
                    self._L(f"{tp} = bitcast i8* {raw} to {at}*")
                    r = self._f("fv")
                    self._L(f"{r} = load {at}, {at}* {tp}")
                    self._put(i.dest, r, at)
                else:
                    self._put(i.dest, raw, PTR)
            else:
                r = self._f("fv")
                self._L(f"{r} = load {ft}, {ft}* {fp}")
                self._put(i.dest, r, ft)
            return
        # fallback: extractvalue
        ov, ot = self._get(i.obj)
        # If value is a pointer, dereference through the struct type
        if ot.endswith("*") and sn in self._struct_ty:
            sty = self._struct_ty[sn]
            tp = self._f("fbc")
            self._L(f"{tp} = bitcast {ot} {ov} to {sty}*")
            sv = self._f("fld")
            self._L(f"{sv} = load {sty}, {sty}* {tp}")
            ov, ot = sv, sty
        if sn in self._struct_idx and i.field_name in self._struct_idx[sn]:
            idx = self._struct_idx[sn][i.field_name]
            ft = self._structs[sn][idx][1] if sn in self._structs else PTR
            if ot.endswith("*"):
                # Still a pointer — can't extractvalue, return as-is
                self._put(i.dest, ov, ot)
            else:
                r = self._f("ev")
                self._L(f"{r} = extractvalue {ot} {ov}, {idx}")
                self._put(i.dest, r, ft)
        else:
            if ot.endswith("*"):
                self._put(i.dest, ov, ot)
            elif ot.startswith("{"):
                r = self._f("ev")
                self._L(f"{r} = extractvalue {ot} {ov}, 0")
                self._put(i.dest, r, PTR)
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
            if aty != sty:
                bc = self._f("sbc")
                self._L(f"{bc} = bitcast {aty}* {addr} to {sty}*")
                addr = bc
            idx = self._struct_idx[sn][i.field_name]
            fp = self._f("fs")
            self._L(f"{fp} = getelementptr inbounds {sty}, {sty}* {addr}, i32 0, i32 {idx}")
            ft = self._structs[sn][idx][1]
            boxed = self._boxed_struct.get(sn, set())
            if idx in boxed:
                sz = _tsz(vt)
                raw = self._rt("malloc", PTR, [I64], [(str(sz), I64)], "box")
                tp = self._f("fb")
                self._L(f"{tp} = bitcast i8* {raw} to {vt}*")
                self._L(f"store {vt} {vv}, {vt}* {tp}")
                self._L(f"store i8* {raw}, i8** {fp}")
            else:
                if vt != ft:
                    vv = self._coerce(vv, vt, ft)
                self._L(f"store {ft} {vv}, {ft}* {fp}")
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

    # --- ListInit ---
    def _do_list_init(self, i: ListInit) -> None:
        ety = self._rty(i.elem_type)
        if ety == PTR and i.elements:
            ev, et = self._get(i.elements[0])
            if et != PTR:
                ety = et
        esz = _tsz(ety)
        lv = self._rt("__mn_list_new", LIST, [I64], [(str(esz), I64)], "ln")
        if i.elements:
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {lv}, {LIST}* {la}")
            self._ensure("__mn_list_push", VOID, [f"{LIST}*", PTR])
            for j, elem in enumerate(i.elements):
                ev, et = self._get(elem)
                ea = self._alloca(et, "ea")
                self._L(f"store {et} {ev}, {et}* {ea}")
                ep = self._f("ep")
                self._L(f"{ep} = bitcast {et}* {ea} to i8*")
                self._L(f"call void @__mn_list_push({LIST}* {la}, i8* {ep})")
            r = self._f("ll")
            self._L(f"{r} = load {LIST}, {LIST}* {la}")
            lv = r
        self._put(i.dest, lv, LIST)

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
            self._L(f"store {et} {ev}, {et}* {ea}")
            ep = self._f("ep")
            self._L(f"{ep} = bitcast {et}* {ea} to i8*")
            self._ensure("__mn_list_push", VOID, [f"{LIST}*", PTR])
            # Use the SOURCE alloca directly for push (not a copy)
            if t != LIST:
                bc = self._f("lbc")
                self._L(f"{bc} = bitcast {t}* {a} to {LIST}*")
                self._L(f"call void @__mn_list_push({LIST}* {bc}, i8* {ep})")
            else:
                self._L(f"call void @__mn_list_push({LIST}* {a}, i8* {ep})")
            # Load updated list
            r = self._f("ul")
            self._L(f"{r} = load {LIST}, {LIST}* {a}" if t == LIST else f"{r} = load {t}, {t}* {a}")
            self._put(i.dest, r, LIST)
            self._lroots[i.dest.name] = root
            # Write-back to source and root aliases
            for tn in {root, src, i.list_val.name}:
                for k in (tn, tn.lstrip("%"), "%" + tn.lstrip("%")):
                    if k in self._alloc and k != i.dest.name:
                        ta, tt = self._alloc[k]
                        if ta != a:
                            wv = self._coerce(r, LIST, tt) if LIST != tt else r
                            self._L(f"store {tt} {wv}, {tt}* {ta}")
        else:
            # Fallback: original approach with temp alloca
            lv, lt = self._get(i.list_val)
            lv = self._coerce(lv, lt, LIST) if lt != LIST else lv
            la = self._alloca(LIST, "lp")
            self._L(f"store {LIST} {lv}, {LIST}* {la}")
            ev, et = self._get(i.element)
            ea = self._alloca(et, "ea")
            self._L(f"store {et} {ev}, {et}* {ea}")
            ep = self._f("ep")
            self._L(f"{ep} = bitcast {et}* {ea} to i8*")
            self._ensure("__mn_list_push", VOID, [f"{LIST}*", PTR])
            self._L(f"call void @__mn_list_push({LIST}* {la}, i8* {ep})")
            r = self._f("ul")
            self._L(f"{r} = load {LIST}, {LIST}* {la}")
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
            self._L(f"store {LIST} {ov}, {LIST}* {la}")
            iv = self._coerce(iv, it, I64) if it != I64 else iv
            raw = self._rt("__mn_list_get", PTR, [f"{LIST}*", I64], [(la, f"{LIST}*"), (iv, I64)])
            ety = self._rty(i.dest.ty)
            if ety == PTR:
                self._put(i.dest, raw, PTR)
            else:
                tp = self._f("tp")
                self._L(f"{tp} = bitcast i8* {raw} to {ety}*")
                r = self._f("el")
                self._L(f"{r} = load {ety}, {ety}* {tp}")
                self._put(i.dest, r, ety)
        elif ok == TypeKind.STRING:
            r = self._rt("__mn_str_byte_at", I64, [STR, I64], [(ov, ot), (iv, it)])
            self._put(i.dest, r, I64)
        elif ok == TypeKind.MAP:
            ka = self._alloca(it, "ka")
            self._L(f"store {it} {iv}, {it}* {ka}")
            kp = self._f("kp")
            self._L(f"{kp} = bitcast {it}* {ka} to i8*")
            raw = self._rt("__mn_map_get", PTR, [PTR, PTR], [(ov, ot), (kp, PTR)])
            ety = self._rty(i.dest.ty)
            tp = self._f("tp")
            self._L(f"{tp} = bitcast i8* {raw} to {ety}*")
            r = self._f("mv")
            self._L(f"{r} = load {ety}, {ety}* {tp}")
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
            self._L(f"store {LIST} {ov}, {LIST}* {la}")
            raw = self._rt("__mn_list_get", PTR, [f"{LIST}*", I64], [(la, f"{LIST}*"), (iv, it)])
            tp = self._f("tp")
            self._L(f"{tp} = bitcast i8* {raw} to {vt}*")
            self._L(f"store {vt} {vv}, {vt}* {tp}")
        elif i.obj.ty.kind == TypeKind.MAP:
            ka = self._alloca(it, "ka")
            self._L(f"store {it} {iv}, {it}* {ka}")
            kp = self._f("kp")
            self._L(f"{kp} = bitcast {it}* {ka} to i8*")
            va = self._alloca(vt, "va")
            self._L(f"store {vt} {vv}, {vt}* {va}")
            vp = self._f("vp")
            self._L(f"{vp} = bitcast {vt}* {va} to i8*")
            self._rt("__mn_map_set", VOID, [PTR, PTR, PTR], [(ov, ot), (kp, PTR), (vp, PTR)])

    # --- MapInit ---
    def _do_map_init(self, i: MapInit) -> None:
        if i.pairs:
            fk, _ = self._get(i.pairs[0][0])
            fv, fvt = self._get(i.pairs[0][1])
            ksz = _tsz(self._rty(i.key_type))
            vsz = _tsz(fvt)
            ktag = (
                1
                if i.key_type.kind == TypeKind.STRING
                else (2 if i.key_type.kind == TypeKind.FLOAT else 0)
            )
        else:
            ksz, vsz, ktag = 8, 8, 0
        mp = self._rt(
            "__mn_map_new",
            PTR,
            [I64, I64, I64],
            [(str(ksz), I64), (str(vsz), I64), (str(ktag), I64)],
        )
        for kv, vv in i.pairs:
            k, kt = self._get(kv)
            v, vt = self._get(vv)
            ka = self._alloca(kt, "mk")
            self._L(f"store {kt} {k}, {kt}* {ka}")
            kp = self._f("mkp")
            self._L(f"{kp} = bitcast {kt}* {ka} to i8*")
            va = self._alloca(vt, "mv")
            self._L(f"store {vt} {v}, {vt}* {va}")
            vp = self._f("mvp")
            self._L(f"{vp} = bitcast {vt}* {va} to i8*")
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
                self._L(f"{raw} = call i8* @malloc(i64 {psz})")
                tp = self._f("ept")
                self._L(f"{tp} = bitcast i8* {raw} to {psty}*")
                for j, pval in enumerate(i.payload):
                    # For list values, check if there's a root alloca from push
                    # write-backs (the copy alias may be stale)
                    root_name = self._lroots.get(pval.name)
                    if root_name and root_name in self._alloc:
                        a_root, t_root = self._alloc[root_name]
                        v = self._f("rl")
                        self._L(f"{v} = load {t_root}, {t_root}* {a_root}")
                        t = t_root
                    else:
                        v, t = self._get(pval)
                    fp = self._f("ef")
                    self._L(f"{fp} = getelementptr inbounds {psty}, {psty}* {tp}, i32 0, i32 {j}")
                    if (i.variant, j) in boxed:
                        bsz = _tsz(t)
                        bp = self._f("eb")
                        self._L(f"{bp} = call i8* @malloc(i64 {bsz})")
                        btp = self._f("ebt")
                        self._L(f"{btp} = bitcast i8* {bp} to {t}*")
                        self._L(f"store {t} {v}, {t}* {btp}")
                        self._L(f"store i8* {bp}, i8** {fp}")
                    else:
                        ft = pflds[j]
                        if t != ft:
                            v = self._coerce(v, t, ft)
                        self._L(f"store {ft} {v}, {ft}* {fp}")
                pp = raw
            else:
                pp = "null"
            # Build {tag, payload_ptr}
            s0 = self._f("ei")
            self._L(f"{s0} = insertvalue {{i64, i8*}} undef, i64 {tag}, 0")
            s1 = self._f("ei")
            pp_c = self._coerce(pp, PTR, PTR) if pp != "null" else "null"
            self._L(f"{s1} = insertvalue {{i64, i8*}} {s0}, i8* {pp_c}, 1")
            self._put(i.dest, s1, ENUM)
        else:
            self._put(i.dest, "0", I64)

    # --- EnumTag ---
    def _do_enum_tag(self, i: EnumTag) -> None:
        ev, et = self._get(i.enum_val)
        if et == I64:
            self._put(i.dest, ev, I64)
            return
        if et.endswith("*"):
            r = self._f("et")
            self._L(f"{r} = ptrtoint {et} {ev} to i64")
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
            ev, et = self._get(i.enum_val)
            if et.endswith("*"):
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
            tp = self._f("pp")
            self._L(f"{tp} = bitcast i8* {raw} to {psty}*")
            idx = i.payload_idx if len(ptypes) > 1 else 0
            fp = self._f("pf")
            self._L(f"{fp} = getelementptr inbounds {psty}, {psty}* {tp}, i32 0, i32 {idx}")
            ft = pflds[idx]
            r = self._f("pv")
            self._L(f"{r} = load {ft}, {ft}* {fp}")
            if (i.variant, idx) in boxed:
                at = self._rty(ptypes[idx])
                utp = self._f("pu")
                self._L(f"{utp} = bitcast i8* {r} to {at}*")
                r2 = self._f("puv")
                self._L(f"{r2} = load {at}, {at}* {utp}")
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
        v, t = self._get(i.val)
        rt = f"{{i1, {{{t}, i8*}}}}"
        s0 = self._f("wo")
        self._L(f"{s0} = insertvalue {rt} undef, i1 1, 0")
        s1 = self._f("wo")
        self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 0")
        self._put(i.dest, s1, rt)

    def _do_wrap_err(self, i: WrapErr) -> None:
        v, t = self._get(i.val)
        rt = f"{{i1, {{i8*, {t}}}}}"
        s0 = self._f("we")
        self._L(f"{s0} = insertvalue {rt} undef, i1 0, 0")
        s1 = self._f("we")
        self._L(f"{s1} = insertvalue {rt} {s0}, {t} {v}, 1, 1")
        self._put(i.dest, s1, rt)

    def _do_unwrap(self, i: Unwrap) -> None:
        v, t = self._get(i.val)
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
                parts.append((s, STR))
            elif pk == TypeKind.FLOAT:
                s = self._rt("__mn_str_from_float", STR, [DBL], [(v, t)])
                parts.append((s, STR))
            elif pk == TypeKind.BOOL:
                s = self._rt("__mn_str_from_bool", STR, [I1], [(v, t)])
                parts.append((s, STR))
            else:
                s = self._rt("__mn_str_from_int", STR, [I64], [(self._coerce(v, t, I64), I64)])
                parts.append((s, STR))
        cur = parts[0][0]
        self._ensure("__mn_str_concat", STR, [STR, STR])
        for pstr, _ in parts[1:]:
            r = self._f("ic")
            self._L(
                f"{r} = call {{i8*, i64}} @__mn_str_concat({{i8*, i64}} {cur}, {{i8*, i64}} {pstr})"
            )
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
                rt, pts, _ = self._sigs[i.fn_name]
                ft = f"{rt} ({', '.join(pts)})*"
                fnp = self._f("cfp")
                self._L(f"{fnp} = bitcast {ft} @{i.fn_name} to i8*")
            s0 = self._f("cc")
            self._L(f"{s0} = insertvalue {{i8*, i8*}} undef, i8* {fnp}, 0")
            s1 = self._f("cc")
            self._L(f"{s1} = insertvalue {{i8*, i8*}} {s0}, i8* null, 1")
            self._put(i.dest, s1, CLOS)
            return
        esty = "{" + ", ".join(ctypes) + "}"
        esz = sum(_tsz(t) for t in ctypes)
        esz = max(esz, 8)
        self._ensure("malloc", PTR, [I64])
        raw = self._f("ce")
        self._L(f"{raw} = call i8* @malloc(i64 {esz})")
        etp = self._f("cet")
        self._L(f"{etp} = bitcast i8* {raw} to {esty}*")
        for j, cv in enumerate(i.captures):
            v, t = self._get(cv)
            et = ctypes[j]
            if t != et:
                v = self._coerce(v, t, et)
            fp = self._f("cf")
            self._L(f"{fp} = getelementptr inbounds {esty}, {esty}* {etp}, i32 0, i32 {j}")
            self._L(f"store {et} {v}, {et}* {fp}")
        fnp = "null"
        if i.fn_name in self._sigs:
            rt, pts, _ = self._sigs[i.fn_name]
            ft = f"{rt} ({', '.join(pts)})*"
            fnp = self._f("cfp")
            self._L(f"{fnp} = bitcast {ft} @{i.fn_name} to i8*")
        s0 = self._f("cc")
        self._L(f"{s0} = insertvalue {{i8*, i8*}} undef, i8* {fnp}, 0")
        s1 = self._f("cc")
        self._L(f"{s1} = insertvalue {{i8*, i8*}} {s0}, i8* {raw}, 1")
        self._put(i.dest, s1, CLOS)

    def _do_clos_call(self, i: ClosureCall) -> None:
        cv, ct = self._get(i.closure)
        args = [self._get(a) for a in i.args]
        cv = self._coerce(cv, ct, CLOS) if ct != CLOS else cv
        fnr = self._f("cfn")
        self._L(f"{fnr} = extractvalue {{i8*, i8*}} {cv}, 0")
        envr = self._f("cen")
        self._L(f"{envr} = extractvalue {{i8*, i8*}} {cv}, 1")
        atypes = [t for _, t in args]
        rty = self._rty(i.dest.ty)
        if rty == VOID or rty == PTR:
            # Try to infer return type from the lambda function signature
            # by scanning the current function for ClosureCreate that produced this closure
            inferred = self._infer_closure_ret(i.closure.name)
            rty = inferred if inferred else I64
        ft = f"{rty} (i8*, {', '.join(atypes)})*" if atypes else f"{rty} (i8*)*"
        ftp = self._f("cftp")
        self._L(f"{ftp} = bitcast i8* {fnr} to {ft}")
        astr = ", ".join(f"{t} {v}" for v, t in args)
        astr = f"i8* {envr}, {astr}" if astr else f"i8* {envr}"
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
        etp = self._f("elp")
        self._L(f"{etp} = bitcast {et} {ev} to {esty}*")
        fp = self._f("elf")
        self._L(f"{fp} = getelementptr inbounds {esty}, {esty}* {etp}, i32 0, i32 {i.index}")
        r = self._f("elv")
        self._L(f"{r} = load {ft}, {ft}* {fp}")
        self._put(i.dest, r, ft)

    # --- Agent ---
    def _do_agent_spawn(self, i: AgentSpawn) -> None:
        atn = i.agent_type.type_info.name or "agent"
        ns, _ = self._mkstr(atn)
        np = self._f("anp")
        self._L(f"{np} = extractvalue {{i8*, i64}} {ns}, 0")
        hn = f"__mn_handler_{atn}"
        hp = "null"
        if hn in self._sigs:
            hp = self._f("ahp")
            rt, pts, _ = self._sigs[hn]
            ft = f"{rt} ({', '.join(pts)})*"
            self._L(f"{hp} = bitcast {ft} @{hn} to i8*")
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
        self._L(f"store {vt} {vv}, {vt}* {va}")
        vp = self._f("asp")
        self._L(f"{vp} = bitcast {vt}* {va} to i8*")
        self._ensure("mapanare_agent_send", I32, [PTR, PTR])
        self._rt("mapanare_agent_send", I32, [PTR, PTR], [(av, at), (vp, PTR)])

    def _do_agent_sync(self, i: AgentSync) -> None:
        av, at = self._get(i.agent)
        op = self._alloca(PTR, "ao")
        self._ensure("mapanare_agent_recv_blocking", I32, [PTR, f"{PTR}*"])
        self._rt("mapanare_agent_recv_blocking", I32, [PTR, f"{PTR}*"], [(av, at), (op, f"{PTR}*")])
        raw = self._f("ar")
        self._L(f"{raw} = load i8*, i8** {op}")
        tt = self._rty(i.dest.ty)
        if tt == VOID:
            self._put(i.dest, "0", I1)
        else:
            tp = self._f("atp")
            self._L(f"{tp} = bitcast i8* {raw} to {tt}*")
            r = self._f("arv")
            self._L(f"{r} = load {tt}, {tt}* {tp}")
            self._put(i.dest, r, tt)

    # --- Signal ---
    def _do_sig_init(self, i: SignalInit) -> None:
        v, t = self._get(i.initial_val)
        vsz = _tsz(t)
        va = self._alloca(t, "sv")
        self._L(f"store {t} {v}, {t}* {va}")
        vp = self._f("svp")
        self._L(f"{vp} = bitcast {t}* {va} to i8*")
        r = self._rt("__mn_signal_new", PTR, [PTR, I64], [(vp, PTR), (str(vsz), I64)])
        self._put(i.dest, r, PTR)

    def _do_sig_get(self, i: SignalGet) -> None:
        sv, st = self._get(i.signal)
        raw = self._rt("__mn_signal_get", PTR, [PTR], [(sv, st)])
        tt = self._rty(i.dest.ty)
        if tt == VOID:
            self._put(i.dest, "0", I1)
        else:
            tp = self._f("sgp")
            self._L(f"{tp} = bitcast i8* {raw} to {tt}*")
            r = self._f("sgv")
            self._L(f"{r} = load {tt}, {tt}* {tp}")
            self._put(i.dest, r, tt)

    def _do_sig_set(self, i: SignalSet) -> None:
        sv, st = self._get(i.signal)
        vv, vt = self._get(i.val)
        va = self._alloca(vt, "ssv")
        self._L(f"store {vt} {vv}, {vt}* {va}")
        vp = self._f("ssp")
        self._L(f"{vp} = bitcast {vt}* {va} to i8*")
        self._rt("__mn_signal_set", VOID, [PTR, PTR], [(sv, st), (vp, PTR)])

    def _do_sig_comp(self, i: SignalComputed) -> None:
        fp = "null"
        if i.compute_fn in self._sigs:
            rt, pts, _ = self._sigs[i.compute_fn]
            ft = f"{rt} ({', '.join(pts)})*"
            fp = self._f("scf")
            self._L(f"{fp} = bitcast {ft} @{i.compute_fn} to i8*")
        nd = len(i.deps)
        if nd > 0:
            dat = f"[{nd} x i8*]"
            da = self._alloca(dat, "sda")
            for j, dv in enumerate(i.deps):
                d, dt = self._get(dv)
                gp = self._f("sdg")
                self._L(f"{gp} = getelementptr inbounds {dat}, {dat}* {da}, i64 0, i64 {j}")
                dc = self._coerce(d, dt, PTR) if dt != PTR else d
                self._L(f"store i8* {dc}, i8** {gp}")
            dp = self._f("sdp")
            self._L(f"{dp} = bitcast {dat}* {da} to i8*")
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
        self._L(f"store {LIST} {sv}, {LIST}* {la}")
        r = self._rt(
            "__mn_stream_from_list", PTR, [f"{LIST}*", I64], [(la, f"{LIST}*"), ("8", I64)]
        )
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
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.FILTER:
            fp = self._stream_fn(i)
            r = self._rt(
                "__mn_stream_filter", PTR, [PTR, PTR, PTR], [(sv, st), (fp, PTR), ("null", PTR)]
            )
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.TAKE:
            nv, nt = self._get(i.args[0]) if i.args else ("0", I64)
            r = self._rt("__mn_stream_take", PTR, [PTR, I64], [(sv, st), (nv, nt)])
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.SKIP:
            nv, nt = self._get(i.args[0]) if i.args else ("0", I64)
            r = self._rt("__mn_stream_skip", PTR, [PTR, I64], [(sv, st), (nv, nt)])
            self._put(i.dest, r, PTR)
        elif i.op_kind == StreamOpKind.COLLECT:
            r = self._rt("__mn_stream_collect", LIST, [PTR, I64], [(sv, st), ("8", I64)])
            self._put(i.dest, r, LIST)
        elif i.op_kind == StreamOpKind.FOLD:
            if len(i.args) >= 2:
                iv, it = self._get(i.args[0])
                fp = self._stream_fn(i, 1)
                ia = self._alloca(it, "fi")
                self._L(f"store {it} {iv}, {it}* {ia}")
                ip = self._f("fip")
                self._L(f"{ip} = bitcast {it}* {ia} to i8*")
                oa = self._alloca(it, "fo")
                op = self._f("fop")
                self._L(f"{op} = bitcast {it}* {oa} to i8*")
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
                self._L(f"{r} = load {it}, {it}* {oa}")
                self._put(i.dest, r, it)
            else:
                self._put(i.dest, "0", I64)
        else:
            self._put(i.dest, sv, st)

    def _stream_fn(self, i: StreamOp, idx: int = 0) -> str:
        if i.fn_name and i.fn_name in self._sigs:
            rt, pts, _ = self._sigs[i.fn_name]
            ft = f"{rt} ({', '.join(pts)})*"
            r = self._f("sfp")
            self._L(f"{r} = bitcast {ft} @{i.fn_name} to i8*")
            return r
        return "null"

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
        msg = f"assertion failed at {i.filename}:{i.line}\\n"
        self._printf(msg, [])
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
        hn = f"__mn_handler_{agent_name}"
        self._sigs[hn] = (I32, [PTR, PTR, f"{PTR}*"], False)
        out = [
            f"define i32 @{hn}(i8* %agent_data, i8* %msg, i8** %out_msg) {{",
            "entry:",
            "  store i8* null, i8** %out_msg",
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
                f"define internal i8* @{pipe_name}(i8* %input) {{\nentry:\n  ret i8* %input\n}}\n"
            )
        # Emit agent spawn chain: spawn each stage, send data through, recv result
        self._ensure("mapanare_agent_new", PTR, [PTR, PTR, PTR, I32, I32])
        self._ensure("mapanare_agent_spawn", I32, [PTR])
        self._ensure("mapanare_agent_send", I32, [PTR, PTR])
        self._ensure("mapanare_agent_recv_blocking", I32, [PTR, f"{PTR}*"])
        self._ensure("mapanare_agent_stop", VOID, [PTR])
        lines = [
            f"define internal i8* @{pipe_name}(i8* %input) {{",
            "entry:",
        ]
        cur = "%input"
        for i, stage in enumerate(pipe_info.stages):
            hn = f"__mn_handler_{stage}"
            hp = "null"
            if hn in self._sigs:
                rt, pts, _ = self._sigs[hn]
                ft = f"{rt} ({', '.join(pts)})*"
                hp = f"bitcast ({ft} @{hn} to i8*)"
            lines.append(f"  %name.{i} = alloca [1 x i8], align 1")
            lines.append(f"  %np.{i} = getelementptr [1 x i8], [1 x i8]* %name.{i}, i64 0, i64 0")
            lines.append(
                f"  %ag.{i} = call i8* @mapanare_agent_new(i8* %np.{i}, i8* {hp},"
                f" i8* null, i32 256, i32 256)"
            )
            lines.append(f"  call i32 @mapanare_agent_spawn(i8* %ag.{i})")
            lines.append(f"  call i32 @mapanare_agent_send(i8* %ag.{i}, i8* {cur})")
            lines.append(f"  %outp.{i} = alloca i8*, align 8")
            lines.append(f"  call i32 @mapanare_agent_recv_blocking(i8* %ag.{i}, i8** %outp.{i})")
            lines.append(f"  %out.{i} = load i8*, i8** %outp.{i}")
            lines.append(f"  call void @mapanare_agent_stop(i8* %ag.{i})")
            cur = f"%out.{i}"
        lines.append(f"  ret i8* {cur}")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)
