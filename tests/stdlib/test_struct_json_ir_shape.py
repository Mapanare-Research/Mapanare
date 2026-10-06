"""v5.39.1 Js.4.B.1 — from_json::<T> IR-shape regression.

Locks the IR-emission fix: ``from_json::<T>(s)`` compiles to valid
LLVM IR even when the user does NOT import ``stdlib/encoding/json``.
The lowerer auto-registers ``JsonValue`` + ``JsonError`` (via
``_ensure_json_types_registered``) so the emitter's proper
boxed-enum extraction path fires instead of the Result/Option
fallback in ``emit_llvm_text._do_enum_payload``'s ``else`` branch
(which ``extractvalue``'s a ``ptr`` but ``_put``s as the dest's
primitive type — invalid IR).

**IR-shape only.** Validated with ``clang -c`` (compile to object
file = full IR validation, no link). The no-import case CANNOT
link — ``decode`` is undefined without the json import — and that
is correct behaviour, not a regression. Runtime correctness for
the with-import path is gated separately in v5.39.2's link-and-run
suite.

Falsifiability: temporarily disable ``self._ensure_json_types_registered()``
in ``mapanare/lower.py::_lower_decode_to`` and ``_lower_from_json``
→ these tests fail with the exact pre-fix clang error
``'%pl.NN' defined with type 'ptr' but expected 'i64'`` (or 'ptr'
for String fields). Verified red-then-green during v5.39.1
release session — see ``docs/roadmap/v5/v5.39.1/SESSION_REPORT.md``.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir


def _have_clang() -> bool:
    return shutil.which("clang") is not None


@pytest.mark.skipif(not _have_clang(), reason="clang required for IR validation")
@pytest.mark.parametrize(
    "source,label",
    [
        (
            "struct P { x: Int }\n"
            "fn main() {\n"
            '    let s: String = "{\\"x\\": 42}"\n'
            "    let r: Result<P, JsonError> = from_json::<P>(s)\n"
            "    match r {\n"
            '        Ok(p) => { print("ok") },\n'
            '        Err(e) => { print("err") }\n'
            "    }\n"
            "}\n",
            "int_field",
        ),
        (
            "struct Q { name: String }\n"
            "fn main() {\n"
            '    let s: String = "{\\"name\\": \\"alice\\"}"\n'
            "    let r: Result<Q, JsonError> = from_json::<Q>(s)\n"
            "    match r {\n"
            '        Ok(q) => { print("ok") },\n'
            '        Err(e) => { print("err") }\n'
            "    }\n"
            "}\n",
            "string_field",
        ),
        (
            "struct R { flag: Bool }\n"
            "fn main() {\n"
            '    let s: String = "{\\"flag\\": true}"\n'
            "    let r: Result<R, JsonError> = from_json::<R>(s)\n"
            "    match r {\n"
            '        Ok(r2) => { print("ok") },\n'
            '        Err(e) => { print("err") }\n'
            "    }\n"
            "}\n",
            "bool_field",
        ),
    ],
)
def test_from_json_no_import_ir_validates(source: str, label: str, tmp_path: Path) -> None:
    """``from_json::<T>(s)`` emits valid LLVM IR without json import."""
    ir = _compile_to_llvm_ir(source, f"{label}.mn")
    ir_path = tmp_path / f"{label}.ll"
    ir_path.write_text(ir)

    obj_path = tmp_path / f"{label}.o"
    result = subprocess.run(
        ["clang", "-c", str(ir_path), "-o", str(obj_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            f"IR validation failed for {label} — v5.39.1 Js.4.B.1 regression:\n" f"{result.stderr}"
        )
    assert obj_path.exists(), f"object file not produced for {label}"


@pytest.mark.skipif(not _have_clang(), reason="clang required for IR validation")
def test_decode_to_no_import_ir_validates(tmp_path: Path) -> None:
    """``decode_to::<T>(jv)`` (the inner step of from_json) also validates.

    Exercises the same ``_ensure_json_types_registered`` hook through
    the ``_lower_decode_to`` entry point (separate caller from
    ``_lower_from_json``).
    """
    source = (
        "struct U { a: Int, b: String }\n"
        "fn main() {\n"
        '    let s: String = "{\\"a\\": 1, \\"b\\": \\"hi\\"}"\n'
        "    let r: Result<U, JsonError> = from_json::<U>(s)\n"
        "    match r {\n"
        '        Ok(u) => { print("ok") },\n'
        '        Err(e) => { print("err") }\n'
        "    }\n"
        "}\n"
    )
    ir = _compile_to_llvm_ir(source, "mixed_fields.mn")
    ir_path = tmp_path / "mixed_fields.ll"
    ir_path.write_text(ir)

    obj_path = tmp_path / "mixed_fields.o"
    result = subprocess.run(
        ["clang", "-c", str(ir_path), "-o", str(obj_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            "IR validation failed for mixed Int+String — v5.39.1 Js.4.B.1 regression:\n"
            f"{result.stderr}"
        )
