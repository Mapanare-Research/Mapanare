"""JIT compiler for Mapanare — compiles LLVM IR to native code and executes via MCJIT."""

from __future__ import annotations

import ctypes

import llvmlite.binding as llvm

_initialized = False


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
