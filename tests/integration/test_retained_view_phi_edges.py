"""Parallel String Phis must swap descriptors and parent references together."""

import os
import subprocess
from pathlib import Path

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.mir import Call, Const, IndexGet, MapInit, Phi, Return, Value, mir_string, mir_void
from tests.integration.test_shared_map_phi_edges import ROOT, _parallel_module

pytest_plugins = ["tests.integration.test_map_return_ownership"]


def _parallel_view_module(switch: bool):
    module = _parallel_module(switch)
    entry, loop, _, end = module.functions[0].blocks
    ty = mir_string()
    strings = [Value("%string_" + str(i), ty) for i in range(4)]
    entry.instructions[0:0] = [
        Const(dest=value, ty=ty, value=text)
        for value, text in zip(strings, ["one", "two", "three", "four"])
    ]
    maps = [
        inst for block in (entry, loop) for inst in block.instructions if isinstance(inst, MapInit)
    ]
    for inst, value in zip(maps, strings):
        inst.val_type = ty
        inst.pairs = [(inst.pairs[0][0], value)]
    a, b = maps[0].dest, maps[1].dest
    key = maps[0].pairs[0][0]
    sa, sb, x, y = (Value(name, ty) for name in ("%sa", "%sb", "%x", "%y"))
    entry.instructions[-1:-1] = [
        IndexGet(dest=sa, obj=a, index=key),
        IndexGet(dest=sb, obj=b, index=key),
    ]
    loop.instructions[:2] = [
        Phi(dest=x, incoming=[("entry", sa), ("back", y)]),
        Phi(dest=y, incoming=[("entry", sb), ("back", x)]),
    ]
    loop.instructions[4:4] = [
        IndexGet(dest=sa, obj=a, index=key),
        IndexGet(dest=sb, obj=b, index=key),
    ]
    end.instructions = [
        Call(dest=Value("%print_x", mir_void()), fn_name="print", args=[x]),
        Call(dest=Value("%print_y", mir_void()), fn_name="print", args=[y]),
        Return(),
    ]
    module.functions[0].return_type = mir_void()
    return module


@pytest.mark.parametrize("switch", [False, True])
@pytest.mark.parametrize("clang_opt", ["-O0", "-O2"])
def test_parallel_view_phi_critical_edge(
    switch, clang_opt, instrumented_core: Path, tmp_path: Path
):
    ir = tmp_path / "view_edges.ll"
    ir.write_text(LLVMTextEmitter().emit(_parallel_view_module(switch)))
    exe = tmp_path / "view_edges"
    linked = subprocess.run(
        [
            "clang",
            clang_opt,
            "-g",
            "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all",
            "-no-pie",
            str(ir),
            str(instrumented_core),
            "-I",
            str(ROOT / "runtime/native"),
            str(ROOT / "tests/native/fixtures/map_owner_bound.c"),
            "-Wl,--wrap=__mn_map_new",
            "-Wl,--wrap=__mn_map_retain",
            "-Wl,--wrap=__mn_map_free_deep",
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(exe),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    result = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "two\none\n"
    assert "map peak:" in result.stderr
