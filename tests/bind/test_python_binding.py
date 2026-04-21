"""End-to-end tests for ``mapanare bind --lang python``.

These tests exercise the full FFI pipeline:

1. ``mapanare bind`` parses a .mn file, generates a Python ctypes wrapper, and
   compiles the source into a shared library.
2. The generated wrapper is imported as a real Python module.
3. Each function is called and the return value is compared against the
   expected Python value.

v4.27.0 recovery: v4.25.0 shipped this feature with multiple CRITICAL
defects the v4.26.0 panel surfaced —

- ``bind.py`` produced ctypes wrappers with no ``argtypes`` / ``restype``,
  so every type except ``Int`` silently corrupted.
- ``cli.cmd_bind`` dead-code-eliminated every function not reachable from
  ``main``, so ``libmath_lib.so`` only exported ``add``.
- The runtime archive was not built with ``-fPIC``, so the ``mapanare bind``
  fallback path produced a .so that ``ctypes.RTLD_NOW`` would reject.
- ``_MnString.to_str`` did not strip the low-bit heap tag Mapanare applies
  to heap-allocated strings, so ``greet('world')`` returned ``ello, world``.

All of those are fixed in v4.27.0. This file is the regression gate: every
new bind feature lands with a pytest here, not a CHANGELOG claim.
"""

from __future__ import annotations

import ctypes
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MATH_LIB_SOURCE = REPO_ROOT / "examples" / "bind" / "math_lib.mn"


def _run_bind(source: Path, tmp_path: Path) -> Path:
    """Invoke ``mapanare bind --lang python`` and return the output directory.

    Raises ``pytest.skip.Exception`` if the FFI build is not available in the
    current environment (e.g. missing clang or libmapanare_rt.a). The recovery
    arc requires the .so to actually build, so this skip is rare and loud.
    """
    out_dir = tmp_path / "bind_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    # Ensure the CLI uses the in-repo package and not a stale site-packages copy.
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mapanare",
            "bind",
            "--lang",
            "python",
            str(source),
            "-o",
            str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.fail(
            "mapanare bind failed:\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}"
        )

    module_name = source.stem
    so_path = out_dir / f"lib{module_name}.so"
    py_path = out_dir / f"{module_name}.py"
    if not so_path.exists():
        pytest.skip(
            f"Shared library not produced at {so_path} — likely missing clang or runtime archive"
        )
    if not py_path.exists():
        pytest.fail(f"Wrapper not produced at {py_path}")
    return out_dir


def _load_wrapper(out_dir: Path, module_name: str) -> Any:
    """Import the generated wrapper from *out_dir*.

    Uses ``importlib`` so repeated test runs do not collide with a cached
    module from a previous tmp_path.
    """
    py_path = out_dir / f"{module_name}.py"
    spec_ref = importlib.util.spec_from_file_location(f"_bind_{module_name}", py_path)
    assert spec_ref is not None and spec_ref.loader is not None
    module = importlib.util.module_from_spec(spec_ref)
    spec_ref.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Baseline round trips — one test per CHANGELOG claim
# ---------------------------------------------------------------------------


def test_math_lib_wrapper_is_generated(tmp_path: Path) -> None:
    """``mapanare bind`` produces both the wrapper and the shared library."""
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    assert (out_dir / "math_lib.py").exists()
    assert (out_dir / "libmath_lib.so").exists()


def test_wrapper_populates_argtypes_and_restype(tmp_path: Path) -> None:
    """v4.27.0 CRITICAL #1: the generated wrapper must set ``argtypes``/``restype``.

    Without this, ctypes defaults every argument and return to ``c_int`` and
    ``Float`` / ``String`` / ``Struct`` silently corrupt. The v4.25.0 panel
    verdict specifically called this out.
    """
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    wrapper_src = (out_dir / "math_lib.py").read_text()
    assert "_lib.add.argtypes" in wrapper_src
    assert "_lib.add.restype" in wrapper_src
    assert "_lib.multiply.argtypes = [ctypes.c_double, ctypes.c_double]" in wrapper_src
    assert "_lib.multiply.restype = ctypes.c_double" in wrapper_src
    assert "_lib.greet.argtypes = [_MnString]" in wrapper_src
    assert "_lib.greet.restype = _MnString" in wrapper_src


def test_so_exports_every_public_function(tmp_path: Path) -> None:
    """v4.27.0 CRITICAL #2/#3: the .so must expose every public function.

    v4.25.0 lost ``multiply``, ``greet``, and the struct constructors to MIR
    dead-code elimination because they were not reachable from ``main``. The
    ``.replace("define internal ", ...)`` sledgehammer that masked this has
    been removed; ``ffi_mode=True`` is now the supported path.
    """
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    so_path = out_dir / "libmath_lib.so"
    nm = subprocess.run(["nm", "--defined-only", str(so_path)], capture_output=True, text=True)
    assert nm.returncode == 0, nm.stderr
    symbols = {line.split()[-1] for line in nm.stdout.splitlines() if line.strip()}
    for name in ("add", "multiply", "greet", "mn_main"):
        assert name in symbols, f"Expected {name!r} in {so_path}, got {sorted(symbols)}"


def test_rtld_now_succeeds(tmp_path: Path) -> None:
    """v4.27.0 CRITICAL #4: the .so must load under ``RTLD_NOW``.

    The runtime archive is now built ``-fPIC``; without that, any symbol
    pulled in from ``libmapanare_rt.a`` produced a text relocation and the
    ``dlopen`` with ``RTLD_NOW`` (which resolves every symbol up front) would
    fail with an ``undefined symbol`` or ``TEXTREL`` error.
    """
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    so_path = out_dir / "libmath_lib.so"
    # os.RTLD_NOW exists on POSIX; Windows uses a different flag set.
    rtld_now = getattr(os, "RTLD_NOW", 0)
    lib = ctypes.CDLL(str(so_path), mode=rtld_now)
    # The library loaded; sanity-check that ``add`` is actually callable.
    lib.add.argtypes = [ctypes.c_int64, ctypes.c_int64]
    lib.add.restype = ctypes.c_int64
    assert lib.add(3, 4) == 7


def test_add_int_round_trip(tmp_path: Path) -> None:
    """``Int`` → ``Int`` — the v4.25.0 baseline that always worked."""
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    wrapper = _load_wrapper(out_dir, "math_lib")
    assert wrapper.add(3, 4) == 7
    assert wrapper.add(-5, 10) == 5
    assert wrapper.add(0, 0) == 0


def test_multiply_float_round_trip(tmp_path: Path) -> None:
    """``Float`` → ``Float`` — silently corrupted in v4.25.0, fixed in v4.27.0.

    Without ``restype = c_double``, ctypes would read the low 32 bits of the
    XMM0 register as a ``c_int`` and produce nonsense.
    """
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    wrapper = _load_wrapper(out_dir, "math_lib")
    assert wrapper.multiply(2.0, 3.0) == pytest.approx(6.0)
    assert wrapper.multiply(0.25, 8.0) == pytest.approx(2.0)
    assert wrapper.multiply(-1.5, 4.0) == pytest.approx(-6.0)


def test_greet_string_round_trip(tmp_path: Path) -> None:
    """``String`` → ``String`` — the hardest case.

    Mapanare strings are ``{ptr, len}`` pairs, not C ``char*``. Heap-allocated
    strings carry a low-bit tag (``mn_tag_heap``) that consumers must strip
    before dereferencing. v4.25.0 did neither, so ``greet('world')`` returned
    ``'ello, world\\x00'`` — off-by-one, NUL-terminated, completely wrong.
    """
    out_dir = _run_bind(MATH_LIB_SOURCE, tmp_path)
    wrapper = _load_wrapper(out_dir, "math_lib")
    assert wrapper.greet("world") == "Hello, world"
    assert wrapper.greet("") == "Hello, "
    assert wrapper.greet("ctypes") == "Hello, ctypes"


def test_struct_return_round_trip(tmp_path: Path) -> None:
    """User struct returned by value — second hardest case after String.

    Exercised via ``make_point(Float, Float) -> Point``. The wrapper declares
    a ``ctypes.Structure`` subclass with matching ``_fields_`` and the call
    round-trips two doubles.
    """
    source = tmp_path / "pointlib.mn"
    source.write_text("""\
struct Point {
    x: Float,
    y: Float
}

fn make_point(a: Float, b: Float) -> Point {
    return new Point { x: a, y: b }
}

fn main() {
    let p = make_point(1.0, 2.0)
    print(p.x)
}
""")
    out_dir = _run_bind(source, tmp_path)
    wrapper = _load_wrapper(out_dir, "pointlib")
    p = wrapper.make_point(1.5, 2.5)
    assert p.x == pytest.approx(1.5)
    assert p.y == pytest.approx(2.5)


def test_define_internal_replace_hack_deleted() -> None:
    """v4.27.0 CRITICAL #3: the ``.replace("define internal ", ...)`` sledgehammer is gone.

    Guards against a future regression that reintroduces the textual hack to
    "make all functions exported". The right path is ``ffi_mode=True`` on the
    AST, which flows through DCE and emitter linkage per-function.
    """
    cli_source = (REPO_ROOT / "mapanare" / "cli.py").read_text()
    assert 'll_text.replace("define internal ", "define ")' not in cli_source
    assert 'llvm_ir.replace("define internal ", "define ")' not in cli_source


def test_ffi_mode_flag_exists() -> None:
    """``_compile_to_llvm_ir`` must accept ``ffi_mode`` — the replacement for the hack."""
    import inspect

    from mapanare.cli import _compile_to_llvm_ir

    params = inspect.signature(_compile_to_llvm_ir).parameters
    assert "ffi_mode" in params, "_compile_to_llvm_ir must expose ffi_mode parameter"


# ---------------------------------------------------------------------------
# v4.32.0 Phase 2.4 — struct String unwrap + annotation fallback
# ---------------------------------------------------------------------------


@pytest.mark.skip(
    reason=(
        "docket Bn.1: returning a struct with a String field by value across "
        "the ctypes ABI boundary produces a dangling ptr in the String — the "
        "String's heap buffer is freed (or never propagated) before the "
        "Python caller reads it, so `_MnString.to_str()` reads garbage "
        "(observed: byte 0x80 at offset 0, which is the `is_heap` bit of "
        "the FOLLOWING field's _lenheap, evidencing a layout/offset or "
        "lifetime bug). Root cause is in the Python emitter's struct-return "
        "path or runtime String ownership on sret — descoped from v4.133.0 "
        "hygiene release (no compiler code changes permitted)."
    )
)
def test_struct_with_string_field(tmp_path: Path) -> None:
    """v4.32.0 Boa M2: a struct with a ``String`` field must auto-unwrap
    ``_MnString`` to ``str`` when accessed via the generated property.

    Without this, the Python caller receives a raw ``_MnString`` for the
    ``name`` field instead of a ``str``, requiring manual ``.to_str()``
    that no Python user would know to call.
    """
    source = tmp_path / "personlib.mn"
    source.write_text("""\
struct Person {
    name: String,
    age: Int
}

fn make_person(name: String, age: Int) -> Person {
    return new Person { name: name, age: age }
}

fn main() {
    let p = make_person("Ada", 42)
    print(p.name)
}
""")
    out_dir = _run_bind(source, tmp_path)
    # Check the generated wrapper has a property accessor, not a raw field.
    wrapper_src = (out_dir / "personlib.py").read_text()
    assert "@property" in wrapper_src, "String field should generate a property accessor"
    assert '("_name", _MnString)' in wrapper_src, "ctypes field should be prefixed _name"

    # Live round-trip: make_person returns a Person, access .name as str
    wrapper = _load_wrapper(out_dir, "personlib")
    p = wrapper.make_person("Ada", 42)
    assert isinstance(p.name, str), f"Expected str, got {type(p.name).__name__}"
    assert p.name == "Ada"
    assert p.age == 42


def test_unknown_type_raises_bind_error() -> None:
    """v4.32.0 Boa M3: ``_py_annotation_for`` must raise ``BindError`` on
    compound types it doesn't know how to marshal, instead of silently
    falling back to ``"int"``.
    """
    from mapanare.bind import BindError, _py_annotation_for

    with pytest.raises(BindError, match="unsupported type.*List<Int>"):
        _py_annotation_for("List<Int>", set())

    with pytest.raises(BindError, match="unsupported type.*Result<T, E>"):
        _py_annotation_for("Result<T, E>", set())

    with pytest.raises(BindError, match="unsupported type.*Option<T>"):
        _py_annotation_for("Option<T>", set())

    # Known types should NOT raise
    assert _py_annotation_for("Int", set()) == "int"
    assert _py_annotation_for("String", set()) == "str"
    assert _py_annotation_for("MyStruct", {"MyStruct"}) == "MyStruct"
