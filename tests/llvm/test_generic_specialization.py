"""Generic bodies must use each invocation's concrete types.

The schema case used to return an empty object: signature substitution alone
leaves the nested intrinsic's explicit type argument as the literal `T`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir
from mapanare.mir_opt import MIROptLevel as OptLevel

ROOT = Path(__file__).resolve().parents[2]

SCHEMA_SOURCE = """
struct Answer:
    value: Int

struct Label:
    text: String

struct Holder<T>:
    value: T

impl<T> Holder<T>:
    fn schema(self) -> String:
        return __struct_meta::<T>()

fn schema<T>(x: T) -> String:
    if true:
        return __struct_meta::<T>()
    return "unreachable"

fn main():
    print(schema(Answer(42)))
    print(schema(Label("hello")))
    print(schema(Answer(7)))
    let held = new Holder { value: Answer(9) }
    print(held.schema())
"""


@pytest.mark.parametrize("opt_level", [OptLevel.O0, OptLevel.O2])
def test_generic_schema_execution(tmp_path: Path, opt_level: OptLevel) -> None:
    """Exercise nested bodies and independent instantiations, before and after MIR optimization."""
    clang = shutil.which("clang")
    runtime = ROOT / "runtime/native/libmapanare_rt.a"
    if not clang or not runtime.exists() or sys.platform == "win32":
        pytest.skip("requires a Unix native runtime archive and clang")
    ir_path = tmp_path / "schema.ll"
    ir_path.write_text(_compile_to_llvm_ir(SCHEMA_SOURCE, "schema.mn", opt_level=opt_level))
    executable = tmp_path / "schema"
    link_flags = ["-lm", "-lpthread"]
    if sys.platform != "darwin":
        link_flags.append("-ldl")
    subprocess.run(
        [clang, "-O2", str(ir_path), str(runtime), *link_flags, "-o", str(executable)],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    result = subprocess.run(
        [str(executable)],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    schemas = [json.loads(line) for line in result.stdout.splitlines()]
    assert schemas == [
        {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]},
        {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]},
        {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]},
    ]
