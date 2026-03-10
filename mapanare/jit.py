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
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = opt_level
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(mod)

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

    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine(opt=opt_level)

    # Run LLVM optimization passes
    pmb = llvm.create_pass_manager_builder()
    pmb.opt_level = opt_level
    pm = llvm.create_module_pass_manager()
    pmb.populate(pm)
    pm.run(mod)

    return bytes(target_machine.emit_object(mod))
