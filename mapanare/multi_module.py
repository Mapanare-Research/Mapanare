"""Multi-module LLVM compilation for the Mapanare compiler.

Resolves imports transitively, lowers each module to MIR, merges all MIR
modules into a single combined module with name-mangled symbols, and emits
one LLVM IR module.

Name mangling scheme:
    Module ``stdlib/encoding/json.mn`` gets prefix ``encoding_json__``.
    Function ``decode`` becomes ``encoding_json__decode``.
    Struct ``JsonToken`` becomes ``encoding_json__JsonToken``.
    Enum ``JsonError`` becomes ``encoding_json__JsonError``.

The root (entry) module's symbols are NOT mangled.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field
from typing import Any

from mapanare.ast_nodes import ImportDef, Program
from mapanare.mir import (
    AgentSpawn,
    Call,
    ClosureCreate,
    EnumInit,
    EnumPayload,
    EnumTag,
    FieldGet,
    FieldSet,
    Instruction,
    ListPush,
    MIRModule,
    MIRType,
    SignalComputed,
    StreamOp,
    StructInit,
    Value,
)
from mapanare.modules import ModuleResolver, ResolvedModule
from mapanare.types import TypeInfo, TypeKind

# ---------------------------------------------------------------------------
# Dependency graph
# ---------------------------------------------------------------------------


def build_dependency_order(
    resolver: ModuleResolver,
    root_file: str,
    root_program: Program,
) -> list[tuple[str, ResolvedModule]]:
    """Return all imported modules in topological order (dependencies first).

    The root module is NOT included in the result — only its dependencies.
    """
    visited: set[str] = set()
    order: list[tuple[str, ResolvedModule]] = []
    root_abs = os.path.abspath(root_file)

    def _visit(filepath: str) -> None:
        if filepath in visited:
            return
        visited.add(filepath)

        cached = resolver.get_cached(filepath)
        if cached is None:
            return

        # Visit this module's imports first (depth-first)
        for defn in cached.program.definitions:
            if isinstance(defn, ImportDef):
                dep_path = resolver.resolve_path(defn.path, os.path.dirname(filepath))
                if dep_path and dep_path not in visited:
                    _visit(dep_path)

        # Don't include the root module
        if filepath != root_abs:
            order.append((filepath, cached))

    # Seed: walk root module's imports
    for defn in root_program.definitions:
        if isinstance(defn, ImportDef):
            dep_path = resolver.resolve_path(defn.path, os.path.dirname(root_abs))
            if dep_path:
                _visit(dep_path)

    return order


# ---------------------------------------------------------------------------
# Module prefix computation
# ---------------------------------------------------------------------------

_STDLIB_DIR: str | None = None


def _get_stdlib_dir() -> str:
    global _STDLIB_DIR
    if _STDLIB_DIR is None:
        _STDLIB_DIR = os.path.normpath(
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stdlib")
        )
    return _STDLIB_DIR


def module_prefix(filepath: str) -> str:
    """Compute the name-mangling prefix for a module file.

    ``stdlib/encoding/json.mn`` → ``encoding_json__``
    ``stdlib/crypto.mn``        → ``crypto__``
    ``/tmp/mylib/utils.mn``     → ``utils__``
    """
    abs_path = os.path.abspath(filepath)
    stdlib = _get_stdlib_dir()

    # Try to make path relative to stdlib
    try:
        rel = os.path.relpath(abs_path, stdlib)
        if not rel.startswith(".."):
            # Inside stdlib
            parts = rel.replace("\\", "/").replace(".mn", "").split("/")
            # Remove "mod" if it's a directory module (foo/mod.mn → foo)
            if parts and parts[-1] == "mod":
                parts = parts[:-1]
            return "_".join(parts) + "__"
    except ValueError:
        pass

    # Not in stdlib — use basename
    basename = os.path.splitext(os.path.basename(abs_path))[0]
    return basename + "__"


def module_short_name(filepath: str) -> str:
    """Get the short name used for namespace access.

    ``stdlib/encoding/json.mn`` → ``json``
    ``stdlib/crypto.mn``        → ``crypto``
    """
    abs_path = os.path.abspath(filepath)
    basename = os.path.splitext(os.path.basename(abs_path))[0]
    if basename == "mod":
        # Directory module: use parent directory name
        return os.path.basename(os.path.dirname(abs_path))
    return basename


# ---------------------------------------------------------------------------
# MIR symbol renaming
# ---------------------------------------------------------------------------


def _rename_type_name(type_info: TypeInfo, rename_map: dict[str, str]) -> TypeInfo:
    """Return a new TypeInfo with renamed struct/enum name if applicable."""
    if type_info.kind in (TypeKind.STRUCT, TypeKind.ENUM, TypeKind.AGENT):
        name = type_info.name
        if name in rename_map:
            new_ti = copy.copy(type_info)
            new_ti.name = rename_map[name]
            return new_ti
    return type_info


def _rename_mir_type(mir_type: MIRType, rename_map: dict[str, str]) -> MIRType:
    """Return a new MIRType with renamed type name if applicable."""
    new_ti = _rename_type_name(mir_type.type_info, rename_map)
    if new_ti is not mir_type.type_info:
        return MIRType(type_info=new_ti)
    return mir_type


def _rename_value_type(val: Value, rename_map: dict[str, str]) -> None:
    """Mutate a Value's type name if it matches the rename map."""
    new_ty = _rename_mir_type(val.ty, rename_map)
    if new_ty is not val.ty:
        val.ty = new_ty


def _rename_instruction(
    inst: Instruction, fn_map: dict[str, str], type_map: dict[str, str]
) -> None:
    """Mutate an instruction's name references in-place."""
    if isinstance(inst, Call):
        if inst.fn_name in fn_map:
            inst.fn_name = fn_map[inst.fn_name]
        # Rename dest type
        _rename_value_type(inst.dest, type_map)
        for arg in inst.args:
            _rename_value_type(arg, type_map)
    elif isinstance(inst, StructInit):
        inst.struct_type = _rename_mir_type(inst.struct_type, type_map)
        _rename_value_type(inst.dest, type_map)
    elif isinstance(inst, EnumInit):
        inst.enum_type = _rename_mir_type(inst.enum_type, type_map)
        _rename_value_type(inst.dest, type_map)
    elif isinstance(inst, EnumTag):
        _rename_value_type(inst.dest, type_map)
        _rename_value_type(inst.enum_val, type_map)
    elif isinstance(inst, EnumPayload):
        _rename_value_type(inst.dest, type_map)
        _rename_value_type(inst.enum_val, type_map)
    elif isinstance(inst, ClosureCreate):
        if inst.fn_name in fn_map:
            inst.fn_name = fn_map[inst.fn_name]
    elif isinstance(inst, StreamOp):
        if inst.fn_name and inst.fn_name in fn_map:
            inst.fn_name = fn_map[inst.fn_name]
    elif isinstance(inst, SignalComputed):
        if inst.compute_fn in fn_map:
            inst.compute_fn = fn_map[inst.compute_fn]
    elif isinstance(inst, FieldGet):
        _rename_value_type(inst.dest, type_map)
        _rename_value_type(inst.obj, type_map)
    elif isinstance(inst, FieldSet):
        _rename_value_type(inst.obj, type_map)
        _rename_value_type(inst.val, type_map)
    elif isinstance(inst, ListPush):
        _rename_value_type(inst.dest, type_map)
        _rename_value_type(inst.list_val, type_map)
        _rename_value_type(inst.element, type_map)
    elif isinstance(inst, AgentSpawn):
        inst.agent_type = _rename_mir_type(inst.agent_type, type_map)


def rename_mir_module(
    mir: MIRModule,
    prefix: str,
) -> tuple[dict[str, str], dict[str, str]]:
    """Rename all symbols in a MIR module with a prefix. Mutates in-place.

    Returns:
        (fn_rename_map, type_rename_map) — old_name → new_name mappings.
    """
    fn_map: dict[str, str] = {}
    type_map: dict[str, str] = {}

    # Build rename maps
    for fn in mir.functions:
        if fn.name == "main":
            continue  # Never rename main from imported modules (skip it later)
        old = fn.name
        new = prefix + old
        fn_map[old] = new

    for name in list(mir.structs.keys()):
        new_name = prefix + name
        type_map[name] = new_name

    for name in list(mir.enums.keys()):
        new_name = prefix + name
        type_map[name] = new_name

    # Apply renames to functions
    for fn in mir.functions:
        if fn.name in fn_map:
            fn.name = fn_map[fn.name]
        # Rename return type
        fn.return_type = _rename_mir_type(fn.return_type, type_map)
        # Rename param types
        for param in fn.params:
            param.ty = _rename_mir_type(param.ty, type_map)
        # Rename instructions
        for block in fn.blocks:
            for inst in block.instructions:
                _rename_instruction(inst, fn_map, type_map)

    # Rename struct definitions
    new_structs: dict[str, list[tuple[str, MIRType]]] = {}
    for name, fields in mir.structs.items():
        new_name = type_map.get(name, name)
        new_fields = [(fname, _rename_mir_type(ftype, type_map)) for fname, ftype in fields]
        new_structs[new_name] = new_fields
    mir.structs = new_structs

    # Rename enum definitions
    new_enums: dict[str, list[tuple[str, list[MIRType]]]] = {}
    for name, variants in mir.enums.items():
        new_name = type_map.get(name, name)
        new_variants = [
            (vname, [_rename_mir_type(t, type_map) for t in vtypes]) for vname, vtypes in variants
        ]
        new_enums[new_name] = new_variants
    mir.enums = new_enums

    # Rename agent info
    new_agents = {}
    for name, info in mir.agents.items():
        new_name = type_map.get(name, prefix + name)
        new_agents[new_name] = info
    mir.agents = new_agents

    return fn_map, type_map


# ---------------------------------------------------------------------------
# Import remapping for the root module
# ---------------------------------------------------------------------------


@dataclass
class ImportMapping:
    """Maps import names to their mangled equivalents."""

    fn_map: dict[str, str] = field(default_factory=dict)
    type_map: dict[str, str] = field(default_factory=dict)


def build_import_remap(
    root_program: Program,
    resolver: ModuleResolver,
    root_file: str,
    dep_renames: dict[str, tuple[dict[str, str], dict[str, str]]],
) -> ImportMapping:
    """Build the name-remapping for the root module based on its imports.

    Args:
        root_program: The root module's AST.
        resolver: Module resolver with cached modules.
        root_file: Absolute path of the root file.
        dep_renames: filepath → (fn_rename_map, type_rename_map) from rename_mir_module.

    Returns:
        ImportMapping with fn_map and type_map for the root module.
    """
    mapping = ImportMapping()
    root_dir = os.path.dirname(os.path.abspath(root_file))

    for defn in root_program.definitions:
        if not isinstance(defn, ImportDef):
            continue

        dep_path = resolver.resolve_path(defn.path, root_dir)
        if dep_path is None:
            continue

        renames = dep_renames.get(dep_path)
        if renames is None:
            continue

        fn_rename, type_rename = renames
        mod_name = module_short_name(dep_path)
        prefix = module_prefix(dep_path)

        cached = resolver.get_cached(dep_path)
        if cached is None:
            continue

        if defn.items:
            # Selective import: `import encoding::json { decode, encode }`
            for item in defn.items:
                export = cached.exports.get(item)
                if export is None or not export.public:
                    continue
                # Bare name → mangled name
                if item in fn_rename:
                    mapping.fn_map[item] = fn_rename[item]
                if item in type_rename:
                    mapping.type_map[item] = type_rename[item]
                # Also handle enum variant names for selective enum imports
                from mapanare.ast_nodes import EnumDef

                if isinstance(export.definition, EnumDef):
                    # Register the enum type mapping
                    mapping.type_map[item] = type_rename.get(item, prefix + item)
                    # Register variant names as function mappings
                    for variant in export.definition.variants:
                        # Variant constructor calls are lowered as EnumInit,
                        # not Call — the enum_type is what needs remapping
                        pass
        else:
            # Full module import: `import encoding::json`
            # Namespace access: json.decode → lowered as Call(fn_name="json_decode")
            for export_name, export in cached.exports.items():
                if not export.public:
                    continue
                # Namespace access pattern: {mod_name}_{export_name}
                ns_name = f"{mod_name}_{export_name}"
                if export_name in fn_rename:
                    mapping.fn_map[ns_name] = fn_rename[export_name]
                if export_name in type_rename:
                    mapping.type_map[export_name] = type_rename[export_name]
                    # Also map namespace access for types
                    ns_type = f"{mod_name}_{export_name}"
                    mapping.type_map[ns_type] = type_rename[export_name]

            # For `self::` imports, symbols are registered directly (no namespace prefix)
            is_self_import = defn.path and defn.path[0] == "self"
            if is_self_import:
                for export_name, export in cached.exports.items():
                    if export_name in fn_rename:
                        mapping.fn_map[export_name] = fn_rename[export_name]
                    if export_name in type_rename:
                        mapping.type_map[export_name] = type_rename[export_name]
                # Register namespace access patterns: {TypeName}_{fn} → mangled_fn
                for type_name in type_rename:
                    for fn_name, mangled_fn in fn_rename.items():
                        ns_key = f"{type_name}_{fn_name}"
                        mapping.fn_map[ns_key] = mangled_fn

    return mapping


def remap_mir_references(mir: MIRModule, mapping: ImportMapping) -> None:
    """Rewrite name references in a MIR module using the import mapping. Mutates in-place."""
    for fn in mir.functions:
        fn.return_type = _rename_mir_type(fn.return_type, mapping.type_map)
        for param in fn.params:
            param.ty = _rename_mir_type(param.ty, mapping.type_map)
        for block in fn.blocks:
            for inst in block.instructions:
                _rename_instruction(inst, mapping.fn_map, mapping.type_map)


# ---------------------------------------------------------------------------
# MIR merging
# ---------------------------------------------------------------------------


def resolve_cross_dep_references(
    dep_mirs: list[MIRModule],
    dep_renames: dict[str, tuple[dict[str, str], dict[str, str]]],
    deps: list[tuple[str, Any]],
    resolver: Any,
) -> None:
    """Fix cross-dependency references between imported modules.

    When module A imports module B, A's calls to B's functions still use the
    un-mangled names after A is renamed.  This pass builds a global rename map
    from all dependency rename maps and applies it to every dependency module.

    Also converts Call instructions that target known enum variant constructors
    into proper EnumInit instructions.
    """
    # Build global type_map across all deps (types are globally unique)
    global_type_map: dict[str, str] = {}
    for filepath, (fn_map, type_map) in dep_renames.items():
        global_type_map.update(type_map)

    # Build per-module fn_maps: each module can only resolve calls to functions
    # from modules that come BEFORE it in topological order (its dependencies).
    # This prevents name collisions when different modules define the same
    # unqualified function name (e.g. fresh_tmp in lower_state vs emit_llvm).
    per_module_fn_map: list[dict[str, str]] = []
    cumulative_fn_map: dict[str, str] = {}
    for filepath, _ in deps:
        per_module_fn_map.append(dict(cumulative_fn_map))
        if filepath in dep_renames:
            fn_map, _ = dep_renames[filepath]
            cumulative_fn_map.update(fn_map)
    # Full map for fallback (used by root module and type renaming)
    global_fn_map = cumulative_fn_map

    # Build call_key → (mangled_enum_name, variant_name, field_types) from all dep modules.
    # Call targets use "{OriginalEnumName}_{VariantName}" format (e.g., "Expr_Ident").
    # Enum names are mangled (e.g., "ast__Expr"), so invert type_map to get originals.
    inv_type_map: dict[str, str] = {v: k for k, v in global_type_map.items()}
    variant_call_map: dict[str, tuple[str, str, list[MIRType]]] = {}
    for mir in dep_mirs:
        for mangled_enum_name, variants in mir.enums.items():
            orig_enum_name = inv_type_map.get(mangled_enum_name, mangled_enum_name)
            for _idx, (vname, vtypes) in enumerate(variants):
                call_key = f"{orig_enum_name}_{vname}"
                variant_call_map[call_key] = (mangled_enum_name, vname, vtypes)
                # Also try bare variant name (for non-namespace access patterns)
                if vname not in variant_call_map:
                    variant_call_map[vname] = (mangled_enum_name, vname, vtypes)

    # Build namespace access map: {TypeName}_{fn} → mangled_fn
    # Handles patterns like Program::start(defs) → Call(fn_name="Program_start")
    # where Program is a struct from module X and start is a function in module X.
    ns_fn_map: dict[str, str] = {}
    for filepath, (fn_map, type_map) in dep_renames.items():
        for orig_fn, mangled_fn in fn_map.items():
            for orig_type in type_map:
                ns_key = f"{orig_type}_{orig_fn}"
                ns_fn_map[ns_key] = mangled_fn

    # Apply per-module renames and convert enum variant Calls to EnumInit
    for mod_idx, mir in enumerate(dep_mirs):
        # Collect defined function names for this module
        defined_fns = {fn.name for fn in mir.functions}
        # Use per-module fn_map: only resolve to functions from earlier modules
        mod_fn_map = per_module_fn_map[mod_idx] if mod_idx < len(per_module_fn_map) else global_fn_map

        for fn in mir.functions:
            for block in fn.blocks:
                new_instructions: list[Instruction] = []
                for inst in block.instructions:
                    if isinstance(inst, Call):
                        # Remap function name if it's an unresolved cross-dep reference
                        if inst.fn_name not in defined_fns:
                            if inst.fn_name in mod_fn_map:
                                inst.fn_name = mod_fn_map[inst.fn_name]
                            elif inst.fn_name in ns_fn_map:
                                inst.fn_name = ns_fn_map[inst.fn_name]
                            elif inst.fn_name in variant_call_map:
                                # Convert to EnumInit
                                ename, vname, _vtypes = variant_call_map[inst.fn_name]
                                enum_ti = TypeInfo(kind=TypeKind.ENUM, name=ename)
                                enum_mir_type = MIRType(type_info=enum_ti)
                                new_inst = EnumInit(
                                    dest=inst.dest,
                                    enum_type=enum_mir_type,
                                    variant=vname,
                                    payload=inst.args,
                                )
                                inst.dest.ty = enum_mir_type
                                new_instructions.append(new_inst)
                                continue
                        # Remap dest/arg types
                        _rename_value_type(inst.dest, global_type_map)
                        for arg in inst.args:
                            _rename_value_type(arg, global_type_map)
                    elif isinstance(inst, StructInit):
                        inst.struct_type = _rename_mir_type(inst.struct_type, global_type_map)
                        _rename_value_type(inst.dest, global_type_map)
                    elif isinstance(inst, FieldGet):
                        _rename_value_type(inst.dest, global_type_map)
                        _rename_value_type(inst.obj, global_type_map)
                    elif isinstance(inst, FieldSet):
                        _rename_value_type(inst.obj, global_type_map)
                        _rename_value_type(inst.val, global_type_map)
                    elif isinstance(inst, EnumInit):
                        inst.enum_type = _rename_mir_type(inst.enum_type, global_type_map)
                        _rename_value_type(inst.dest, global_type_map)
                    elif isinstance(inst, EnumTag):
                        _rename_value_type(inst.dest, global_type_map)
                        _rename_value_type(inst.enum_val, global_type_map)
                    elif isinstance(inst, EnumPayload):
                        _rename_value_type(inst.dest, global_type_map)
                        _rename_value_type(inst.enum_val, global_type_map)
                    new_instructions.append(inst)
                block.instructions = new_instructions

            # Also remap return type and param types
            fn.return_type = _rename_mir_type(fn.return_type, global_type_map)
            for param in fn.params:
                param.ty = _rename_mir_type(param.ty, global_type_map)


def merge_mir_modules(base: MIRModule, additions: list[MIRModule]) -> None:
    """Merge additional MIR modules into the base module. Mutates base in-place.

    Skips ``main`` functions from additions (only root module has main).
    Deduplicates extern function declarations.
    """
    seen_externs: set[str] = {name for _, _, name, _, _ in base.extern_fns}

    for add in additions:
        # Functions (skip main from imported modules)
        for fn in add.functions:
            if fn.name == "main":
                continue
            base.functions.append(fn)

        # Structs
        for name, fields in add.structs.items():
            if name not in base.structs:
                base.structs[name] = fields

        # Enums
        for name, variants in add.enums.items():
            if name not in base.enums:
                base.enums[name] = variants

        # Extern functions (deduplicate by name)
        for ext in add.extern_fns:
            ext_name = ext[2]  # (abi, module, name, params, ret)
            if ext_name not in seen_externs:
                base.extern_fns.append(ext)
                seen_externs.add(ext_name)

        # Agents
        for agent_name, agent_info in add.agents.items():
            if agent_name not in base.agents:
                base.agents[agent_name] = agent_info

        # Pipes
        for pipe_name, pipe_info in add.pipes.items():
            if pipe_name not in base.pipes:
                base.pipes[pipe_name] = pipe_info


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _emit_with_backend(
    backend: str, module_name: str, target: Any, mir_module: MIRModule, debug: bool
) -> str:
    """Emit LLVM IR using the selected backend."""
    if backend == "text":
        from mapanare.emit_llvm_text import LLVMTextEmitter

        emitter = LLVMTextEmitter(
            module_name=module_name,
            target_triple=target.triple,
            data_layout=target.data_layout,
            debug=debug,
        )
        return emitter.emit(mir_module)
    from mapanare.emit_llvm_mir import LLVMMIREmitter

    emitter_mir = LLVMMIREmitter(
        module_name=module_name,
        target_triple=target.triple,
        data_layout=target.data_layout,
        debug=debug,
    )
    llvm_module = emitter_mir.emit(mir_module)
    return str(llvm_module)


def compile_multi_module_mir(
    root_source: str,
    root_file: str,
    opt_level: int = 2,
    target_name: str | None = None,
    debug: bool = False,
    emitter_backend: str = "text",
) -> str:
    """Compile a root .mn file and all its imports into a single LLVM IR string.

    Pipeline:
        1. Parse + semantic check root file (resolver caches all imports)
        2. Build dependency order (topological sort)
        3. Lower each dependency to MIR, rename symbols with module prefix
        4. Lower root module to MIR
        5. Remap root module's references to imported symbols
        6. Merge all MIR modules
        7. Optimize merged MIR
        8. Emit LLVM IR via LLVMMIREmitter
    """
    from mapanare.lower import lower as build_mir
    from mapanare.mir_opt import MIROptLevel
    from mapanare.mir_opt import optimize_module as mir_optimize
    from mapanare.parser import parse
    from mapanare.semantic import check_or_raise
    from mapanare.targets import get_target

    # 1. Parse and semantic check (resolver resolves all imports)
    resolver = ModuleResolver()
    ast = parse(root_source, filename=root_file)
    check_or_raise(ast, filename=root_file, resolver=resolver)

    # 2. Build dependency order
    deps = build_dependency_order(resolver, root_file, ast)

    if not deps:
        # No imports — single file compilation
        module_name = os.path.splitext(os.path.basename(root_file))[0]
        source_file = os.path.basename(root_file)
        source_dir = os.path.dirname(os.path.abspath(root_file))
        mir_module = build_mir(
            ast, module_name=module_name, source_file=source_file, source_directory=source_dir
        )
        mir_opt_level = MIROptLevel(opt_level)
        mir_module, _ = mir_optimize(mir_module, mir_opt_level)
        target = get_target(target_name)
        return _emit_with_backend(emitter_backend, module_name, target, mir_module, debug)

    # 3. Lower each dependency, rename symbols.
    #   Dependencies are in topological order, so when we lower module B that
    #   imports module A, A's functions are already available.  We accumulate
    #   return-type info from previously-lowered modules so each module's
    #   lowerer knows the return types of functions it calls cross-module.
    dep_mirs: list[MIRModule] = []
    dep_renames: dict[str, tuple[dict[str, str], dict[str, str]]] = {}
    # Accumulates orig_fn_name → MIRType across all lowered deps
    cross_dep_ret_types: dict[str, MIRType] = {}
    # Accumulates struct definitions across all lowered deps
    cross_dep_struct_defs: dict[str, list[tuple[str, MIRType]]] = {}
    # Accumulates enum definitions across all lowered deps
    cross_dep_enum_defs: dict[str, list[tuple[str, list[MIRType]]]] = {}

    for filepath, resolved in deps:
        dep_source: str
        with open(filepath, encoding="utf-8") as f:
            dep_source = f.read()

        dep_ast = parse(dep_source, filename=filepath)
        dep_module_name = os.path.splitext(os.path.basename(filepath))[0]
        dep_mir = build_mir(
            dep_ast,
            module_name=dep_module_name,
            source_file=os.path.basename(filepath),
            source_directory=os.path.dirname(filepath),
            imported_return_types=cross_dep_ret_types if cross_dep_ret_types else None,
            imported_struct_defs=cross_dep_struct_defs if cross_dep_struct_defs else None,
            imported_enum_defs=cross_dep_enum_defs if cross_dep_enum_defs else None,
        )

        # Record this module's function return types (by original name)
        # BEFORE renaming, so subsequent modules can resolve cross-dep calls.
        for fn in dep_mir.functions:
            cross_dep_ret_types[fn.name] = fn.return_type

        # Record this module's struct definitions (by original name)
        for sname, sfields in dep_mir.structs.items():
            cross_dep_struct_defs[sname] = sfields

        # Record this module's enum definitions (by original name)
        for ename, evariants in dep_mir.enums.items():
            cross_dep_enum_defs[ename] = evariants

        prefix = module_prefix(filepath)
        fn_map, type_map = rename_mir_module(dep_mir, prefix)
        dep_renames[filepath] = (fn_map, type_map)
        dep_mirs.append(dep_mir)

        # Also record mangled names for completeness
        for fn in dep_mir.functions:
            cross_dep_ret_types[fn.name] = fn.return_type

    # 3.5. Resolve cross-dependency references (cross-module calls + enum variants)
    resolve_cross_dep_references(dep_mirs, dep_renames, deps, resolver)

    # 3.6. Build imported function return types for the root module lowerer.
    #   The root module calls imported functions by their ORIGINAL names (before
    #   mangling).  We invert the rename maps to build orig_name → return_type.
    imported_ret_types: dict[str, MIRType] = {}
    for dep_mir in dep_mirs:
        for fn in dep_mir.functions:
            imported_ret_types[fn.name] = fn.return_type
    # Also map original (pre-mangled) names so the lowerer resolves them
    for filepath, (fn_map, _type_map) in dep_renames.items():
        inv_fn = {v: k for k, v in fn_map.items()}
        for dep_mir_item in dep_mirs:
            for fn in dep_mir_item.functions:
                orig = inv_fn.get(fn.name)
                if orig:
                    imported_ret_types[orig] = fn.return_type

    # 3.7. Build imported struct definitions for the root module lowerer.
    #   The root module references imported structs by their ORIGINAL names.
    #   We collect both mangled and original names so field type inference works.
    imported_struct_defs: dict[str, list[tuple[str, MIRType]]] = {}
    for dep_mir in dep_mirs:
        for sname, sfields in dep_mir.structs.items():
            imported_struct_defs[sname] = sfields
    # Also map original (pre-mangled) names
    for filepath, (_fn_map, type_map) in dep_renames.items():
        inv_type = {v: k for k, v in type_map.items()}
        for dep_mir_item in dep_mirs:
            for sname, sfields in dep_mir_item.structs.items():
                orig = inv_type.get(sname)
                if orig:
                    imported_struct_defs[orig] = sfields

    # 3.8. Build imported enum definitions for the root module lowerer.
    imported_enum_defs: dict[str, list[tuple[str, list[MIRType]]]] = {}
    for dep_mir in dep_mirs:
        for ename, evariants in dep_mir.enums.items():
            imported_enum_defs[ename] = evariants
    for filepath, (_fn_map, type_map) in dep_renames.items():
        inv_type = {v: k for k, v in type_map.items()}
        for dep_mir_item in dep_mirs:
            for ename, evariants in dep_mir_item.enums.items():
                orig = inv_type.get(ename)
                if orig:
                    imported_enum_defs[orig] = evariants

    # 4. Lower root module
    root_module_name = os.path.splitext(os.path.basename(root_file))[0]
    root_mir = build_mir(
        ast,
        module_name=root_module_name,
        source_file=os.path.basename(root_file),
        source_directory=os.path.dirname(os.path.abspath(root_file)),
        imported_return_types=imported_ret_types,
        imported_struct_defs=imported_struct_defs,
        imported_enum_defs=imported_enum_defs,
    )

    # 5. Remap root module's references to imported symbols
    import_mapping = build_import_remap(ast, resolver, root_file, dep_renames)
    remap_mir_references(root_mir, import_mapping)

    # 5.5. Convert any remaining enum variant Calls in root module to EnumInit
    #   Build variant map using {OriginalEnumName}_{VariantName} call keys
    root_variant_map: dict[str, tuple[str, str, list[MIRType]]] = {}
    for dep_mir in dep_mirs:
        for mangled_enum_name, variants in dep_mir.enums.items():
            # Invert type renames to get original names
            orig_name = mangled_enum_name
            for filepath, (_, type_map) in dep_renames.items():
                for k, v in type_map.items():
                    if v == mangled_enum_name:
                        orig_name = k
                        break
            for _idx, (vname, vtypes) in enumerate(variants):
                call_key = f"{orig_name}_{vname}"
                root_variant_map[call_key] = (mangled_enum_name, vname, vtypes)
                if vname not in root_variant_map:
                    root_variant_map[vname] = (mangled_enum_name, vname, vtypes)
    for fn in root_mir.functions:
        for block in fn.blocks:
            new_insts: list[Instruction] = []
            for inst in block.instructions:
                if isinstance(inst, Call) and inst.fn_name in root_variant_map:
                    ename, vname, _vtypes = root_variant_map[inst.fn_name]
                    enum_ti = TypeInfo(kind=TypeKind.ENUM, name=ename)
                    enum_mir_type = MIRType(type_info=enum_ti)
                    new_inst = EnumInit(
                        dest=inst.dest,
                        enum_type=enum_mir_type,
                        variant=vname,
                        payload=inst.args,
                    )
                    inst.dest.ty = enum_mir_type
                    new_insts.append(new_inst)
                    continue
                new_insts.append(inst)
            block.instructions = new_insts

    # 5.6. Propagate return types from dependency functions to root module Calls.
    #   When the root module calls an imported function, the MIR lowerer doesn't
    #   know the return type (it only sees the call, not the definition) so the
    #   Call dest type defaults to UNKNOWN.  Fix that here using the actual
    #   function signatures from the dependency modules.
    dep_fn_ret: dict[str, MIRType] = {}
    for dep_mir in dep_mirs:
        for fn in dep_mir.functions:
            dep_fn_ret[fn.name] = fn.return_type
    for fn in root_mir.functions:
        for block in fn.blocks:
            for inst in block.instructions:
                if isinstance(inst, Call) and inst.dest.ty.type_info.kind == TypeKind.UNKNOWN:
                    if inst.fn_name in dep_fn_ret:
                        inst.dest.ty = dep_fn_ret[inst.fn_name]

    # 6. Merge all modules (dependencies first, then root)
    merge_mir_modules(root_mir, dep_mirs)

    # 7. Optimize merged MIR
    mir_opt_level = MIROptLevel(opt_level)
    root_mir, _ = mir_optimize(root_mir, mir_opt_level)

    # 8. Emit LLVM IR
    target = get_target(target_name)
    return _emit_with_backend(emitter_backend, root_module_name, target, root_mir, debug)
