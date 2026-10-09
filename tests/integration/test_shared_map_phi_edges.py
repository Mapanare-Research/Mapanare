"""Execute parallel map Phis on a loop's critical branch/switch edge."""

import os
import subprocess
from pathlib import Path

import pytest

from mapanare.emit_llvm_text import LLVMTextEmitter
from mapanare.mir import (
    BasicBlock,
    BinOp,
    BinOpKind,
    Branch,
    Const,
    IndexGet,
    Jump,
    MapInit,
    MIRFunction,
    MIRModule,
    MIRType,
    Phi,
    Return,
    Switch,
    Value,
    mir_bool,
    mir_int,
)
from mapanare.types import TypeInfo, TypeKind

pytest_plugins = ["tests.integration.test_map_return_ownership"]
ROOT = Path(__file__).resolve().parents[2]


def _parallel_module(switch: bool) -> MIRModule:
    integer = mir_int()
    map_type = MIRType(TypeInfo(kind=TypeKind.MAP))
    a, b, x, y = (Value(name, map_type) for name in ("%a", "%b", "%x", "%y"))
    zero, one, two, three, four, ten, limit, expected, n, vx, vy, tens, code = (
        Value("%" + name, integer)
        for name in (
            "zero",
            "one",
            "two",
            "three",
            "four",
            "ten",
            "limit",
            "expected",
            "n",
            "vx",
            "vy",
            "tens",
            "code",
        )
    )
    again = Value("%again", mir_bool())
    constants = [
        Const(dest=v, ty=integer, value=k)
        for v, k in (
            (zero, 0),
            (one, 1),
            (two, 2),
            (three, 3),
            (four, 4),
            (ten, 10),
            (limit, 100),
            (expected, 21),
            (n, 0),
        )
    ]
    entry = BasicBlock(
        label="entry",
        instructions=constants
        + [
            MapInit(dest=a, key_type=integer, val_type=integer, pairs=[(one, one)]),
            MapInit(dest=b, key_type=integer, val_type=integer, pairs=[(one, two)]),
            Jump(target="loop"),
        ],
    )
    loop = BasicBlock(
        label="loop",
        instructions=[
            Phi(dest=x, incoming=[("entry", a), ("back", y)]),
            Phi(dest=y, incoming=[("entry", b), ("back", x)]),
            # Remove the original non-Phi owners. Only x/y retain their old maps;
            # a sequential swap would release one before acquiring it for the other.
            MapInit(dest=a, key_type=integer, val_type=integer, pairs=[(one, three)]),
            MapInit(dest=b, key_type=integer, val_type=integer, pairs=[(one, four)]),
            BinOp(dest=n, op=BinOpKind.ADD, lhs=n, rhs=one),
            Jump(target="back"),
        ],
    )
    back = BasicBlock(
        label="back",
        instructions=(
            [Switch(tag=n, cases=[(100, "exit")], default_block="loop")]
            if switch
            else [
                BinOp(dest=again, op=BinOpKind.LT, lhs=n, rhs=limit),
                Branch(cond=again, true_block="loop", false_block="exit"),
            ]
        ),
    )
    end = BasicBlock(
        label="exit",
        instructions=[
            IndexGet(dest=vx, obj=x, index=one),
            IndexGet(dest=vy, obj=y, index=one),
            BinOp(dest=tens, op=BinOpKind.MUL, lhs=vx, rhs=ten),
            BinOp(dest=code, op=BinOpKind.ADD, lhs=tens, rhs=vy),
            BinOp(dest=code, op=BinOpKind.SUB, lhs=code, rhs=expected),
            Return(val=code),
        ],
    )
    return MIRModule(
        functions=[MIRFunction(name="main", return_type=integer, blocks=[entry, loop, back, end])]
    )


@pytest.mark.parametrize("switch", [False, True])
@pytest.mark.parametrize("clang_opt", ["-O0", "-O2"])
def test_parallel_phi_critical_edge(
    switch: bool, clang_opt: str, instrumented_core: Path, tmp_path: Path
) -> None:
    ir = tmp_path / "edges.ll"
    ir.write_text(LLVMTextEmitter().emit(_parallel_module(switch)))
    executable = tmp_path / "edges"
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
            "-Wl,--wrap=__mn_map_new_copying",
            "-Wl,--wrap=__mn_map_retain",
            "-Wl,--wrap=__mn_map_free_deep",
            "-lm",
            "-lpthread",
            "-ldl",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert linked.returncode == 0, linked.stderr
    run = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "ASAN_OPTIONS": "detect_leaks=1:halt_on_error=1"},
    )
    assert run.returncode == 0, run.stdout + run.stderr
    assert "map peak:" in run.stderr
