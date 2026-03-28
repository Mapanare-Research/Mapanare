"""JIT compiler for Mapanare — compiles LLVM IR to native code and executes via MCJIT."""

from __future__ import annotations

import ctypes
import os
import sys
from typing import Any, Callable

import llvmlite.binding as llvm

_initialized = False
_runtime_loaded = False


def _find_runtime_dll() -> str | None:
    """Locate the native runtime shared library (libmapanare_core)."""
    # Check relative to this file first (installed layout), then project layout
    this_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(this_dir, "..", "runtime", "native"),  # dev / project root
        os.path.join(this_dir, "runtime", "native"),
    ]
    dll_name = "libmapanare_core.dll" if sys.platform == "win32" else "libmapanare_core.so"
    for d in candidates:
        path = os.path.join(d, dll_name)
        if os.path.isfile(path):
            return os.path.abspath(path)
    return None


def _load_runtime() -> None:
    """Load the Mapanare native runtime and register symbols with LLVM."""
    global _runtime_loaded
    if _runtime_loaded:
        return
    dll_path = _find_runtime_dll()
    if dll_path is None:
        return  # runtime not found — external symbols will fail at call time
    _runtime_loaded = True
    dll = ctypes.CDLL(dll_path)
    # Register all exported __mn_ symbols with LLVM so MCJIT can resolve them.
    # On Windows, ctypes.CDLL alone doesn't make symbols visible to the JIT.
    if sys.platform == "win32":
        import ctypes.wintypes as wintypes

        kernel32 = ctypes.windll.kernel32
        GetProcAddress = kernel32.GetProcAddress
        GetProcAddress.argtypes = [wintypes.HMODULE, ctypes.c_char_p]
        GetProcAddress.restype = ctypes.c_void_p
        handle = dll._handle
        _register_dll_symbols(handle, GetProcAddress)
    else:
        # On Unix, RTLD_GLOBAL would suffice, but be explicit
        handle = dll._handle
        _register_dll_symbols_unix(handle)


def _register_dll_symbols(handle: Any, get_proc: Callable[[Any, bytes], Any]) -> None:
    """Register known runtime symbols from the DLL with llvm.add_symbol (Windows)."""
    # Exhaustive list of symbols the LLVM codegen may reference
    symbols = [
        "__mn_str_from_cstr",
        "__mn_str_from_parts",
        "__mn_str_empty",
        "__mn_str_concat",
        "__mn_str_char_at",
        "__mn_str_byte_at",
        "__mn_str_len",
        "__mn_str_eq",
        "__mn_str_cmp",
        "__mn_str_substr",
        "__mn_str_starts_with",
        "__mn_str_ends_with",
        "__mn_str_find",
        "__mn_str_contains",
        "__mn_str_trim",
        "__mn_str_trim_start",
        "__mn_str_trim_end",
        "__mn_str_to_upper",
        "__mn_str_to_lower",
        "__mn_str_replace",
        "__mn_str_from_bool",
        "__mn_str_from_int",
        "__mn_str_from_float",
        "__mn_str_to_int",
        "__mn_str_to_float",
        "__mn_str_free",
        "__mn_str_print",
        "__mn_str_println",
        "__mn_str_eprintln",
        "__mn_str_ord",
        "__mn_str_chr",
        "__mn_str_split",
        "__mn_str_join",
        "__mn_list_new",
        "__mn_list_push",
        "__mn_list_get",
        "__mn_list_set",
        "__mn_list_len",
        "__mn_list_pop",
        "__mn_list_clear",
        "__mn_list_free",
        "__mn_list_concat",
        "__mn_list_free_strings",
        "__mn_list_str_new",
        "__mn_list_str_push",
        "__mn_list_str_get",
        "__mn_file_read",
        "__mn_file_write",
        "__mn_alloc",
        "__mn_realloc",
        "__mn_free",
        "mn_arena_create",
        "mn_arena_alloc",
        "mn_arena_destroy",
        "mn_agent_arena_create",
        "mn_agent_arena_destroy",
        "__mn_map_new",
        "__mn_map_set",
        "__mn_map_get",
        "__mn_map_del",
        "__mn_map_len",
        "__mn_map_contains",
        "__mn_map_iter_new",
        "__mn_map_iter_next",
        "__mn_map_iter_free",
        "__mn_map_free",
        "__mn_hash_int",
        "__mn_hash_str",
        "__mn_hash_float",
        "__mn_signal_new",
        "__mn_signal_get",
        "__mn_signal_set",
        "__mn_signal_computed",
        "__mn_signal_subscribe",
        "__mn_signal_unsubscribe",
        "__mn_signal_on_change",
        "__mn_signal_batch_begin",
        "__mn_signal_batch_end",
        "__mn_signal_free",
        "__mn_stream_from_list",
        "__mn_stream_map",
        "__mn_stream_filter",
        "__mn_stream_take",
        "__mn_stream_skip",
        "__mn_stream_collect",
        "__mn_stream_fold",
        "__mn_stream_next",
        "__mn_stream_bounded",
        "__mn_stream_free",
        "__mn_exit",
        "__mn_panic",
        "__mn_range",
        "__iter_has_next",
        "__iter_next",
    ]
    for name in symbols:
        addr = get_proc(handle, name.encode())
        if addr:
            llvm.add_symbol(name, addr)


def _register_dll_symbols_unix(handle: int) -> None:
    """Register runtime symbols on Unix via dlsym."""
    libdl = ctypes.CDLL(None)
    dlsym = libdl.dlsym
    dlsym.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    dlsym.restype = ctypes.c_void_p
    _register_dll_symbols(handle, dlsym)


_c_runtime: ctypes.CDLL | None = None


def _flush_c_stdio() -> None:
    """Flush all C stdio streams from every loaded C runtime."""
    global _c_runtime
    if _c_runtime is None:
        try:
            if sys.platform == "win32":
                _c_runtime = ctypes.CDLL("msvcrt")
            else:
                _c_runtime = ctypes.CDLL(None)
        except OSError:
            return
    _c_runtime.fflush(None)


def _init_llvm() -> None:
    """Initialize LLVM targets (once per process)."""
    global _initialized
    if _initialized:
        return
    try:
        llvm.initialize()
    except RuntimeError:
        pass  # Newer llvmlite auto-initializes; the call is deprecated
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    _initialized = True


def jit_compile_and_run(llvm_ir: str, opt_level: int = 2) -> int:
    """JIT-compile LLVM IR and execute the main() function.

    Returns 0 on success.
    """
    _init_llvm()
    _load_runtime()

    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine(opt=opt_level)

    # Override module triple/layout to match host (avoids MCJIT mismatch)
    mod = llvm.parse_assembly(llvm_ir)
    mod.triple = target_machine.triple
    mod.data_layout = str(target_machine.target_data)
    mod.verify()

    # Run LLVM optimization passes
    if hasattr(llvm, "create_pass_manager_builder"):
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = opt_level
        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        pm.run(mod)
    elif hasattr(llvm, "create_pass_builder"):
        pb = llvm.create_pass_builder(target_machine)
        pb.run(mod)

    engine = llvm.create_mcjit_compiler(mod, target_machine)
    engine.finalize_object()
    engine.run_static_constructors()

    main_ptr = engine.get_function_address("main")
    if main_ptr == 0:
        raise RuntimeError("No main() function found in compiled module")

    # main() returns void in Mapanare
    cfunc = ctypes.CFUNCTYPE(None)(main_ptr)
    cfunc()

    # Flush all C stdio streams — on Windows the runtime DLL may use a
    # different C runtime (MSVCRT vs UCRT) so Python's flush won't cover it.
    sys.stdout.flush()
    sys.stderr.flush()
    _flush_c_stdio()

    return 0


def jit_compile_to_object(llvm_ir: str, opt_level: int = 2) -> bytes:
    """Compile LLVM IR to native object code bytes."""
    _init_llvm()

    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()

    # Use triple from module if present, otherwise default to host
    triple = mod.triple if mod.triple else llvm.get_process_triple()
    target = llvm.Target.from_triple(triple)

    # Use 'static' relocation model on Windows to avoid _GLOBAL_OFFSET_TABLE_
    # and other Linux-specific symbols that confuse MinGW.
    reloc = "static" if "windows" in triple else "default"
    target_machine = target.create_target_machine(opt=opt_level, reloc=reloc)

    # Run LLVM optimization passes
    if hasattr(llvm, "create_pass_manager_builder"):
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = opt_level
        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        pm.run(mod)
    elif hasattr(llvm, "create_pass_builder"):
        pto = llvm.PipelineTuningOptions(speed_level=opt_level, size_level=0)
        pb = llvm.create_pass_builder(target_machine, pto)
        pm = pb.getModulePassManager()
        pm.run(mod, pb)

    return bytes(target_machine.emit_object(mod))
