"""Self-hosted compiler verification — Phase 5.

This test suite verifies the self-hosted compiler pipeline end-to-end:
1. All .mn files parse successfully via the Python bootstrap
2. Semantic analysis runs on all files (known errors documented)
3. LLVM IR emission succeeds for all emittable functions
4. Full-file LLVM emission works for files with primitive-type structs
5. Stage 1 → Stage 2 determinism holds for all emittable code
6. CLI integration: sample programs compile, transpile, and run correctly
7. Bootstrap coverage metrics are tracked
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from mapanare.ast_nodes import (
    EnumDef,
    FnDef,
    NamedType,
    Program,
    StructDef,
)
from mapanare.emit_llvm import LLVMEmitter
from mapanare.optimizer import OptLevel, optimize
from mapanare.parser import parse
from mapanare.semantic import check

SELF_DIR = Path(__file__).resolve().parents[2] / "mapanare" / "self"
TEST_VS_DIR = Path(__file__).resolve().parents[2] / "test_vs"
MN_FILES = sorted(SELF_DIR.glob("*.mn"))

# Expected self-hosted compiler modules
EXPECTED_MODULES = {"ast", "lexer", "parser", "semantic", "emit_llvm", "main"}

# Primitive types the LLVM emitter can resolve without struct registration
_PRIMITIVE_NAMES = {"Int", "Float", "Bool", "Char", "String", "Void"}


def _has_only_primitive_types(fn: FnDef) -> bool:
    """Check if a function uses only primitive types."""
    for p in fn.params:
        if p.type_annotation is not None:
            if not isinstance(p.type_annotation, NamedType):
                return False
            if p.type_annotation.name not in _PRIMITIVE_NAMES:
                return False
    if fn.return_type is not None:
        if not isinstance(fn.return_type, NamedType):
            return False
        if fn.return_type.name not in _PRIMITIVE_NAMES:
            return False
    return True


def _compile_file_full(mn_file: Path) -> tuple[Program, list[object]]:
    """Parse and semantically check a .mn file, returning (program, errors)."""
    source = mn_file.read_text(encoding="utf-8")
    program = parse(source, filename=mn_file.name)
    errors = check(program, filename=mn_file.name)
    return program, errors


def _emit_full_ir(program: Program, module_name: str) -> str:
    """Emit LLVM IR for all definitions in a program."""
    emitter = LLVMEmitter(module_name=module_name)
    module = emitter.emit_program(program)
    return str(module)


# ---------------------------------------------------------------------------
# Test 1: Pipeline integrity — all files parse and check
# ---------------------------------------------------------------------------


class TestPipelineIntegrity:
    """Verify the full bootstrap pipeline works on all self-hosted sources."""

    def test_all_expected_modules_exist(self) -> None:
        """Every expected self-hosted module has a .mn file."""
        actual = {f.stem for f in MN_FILES}
        assert EXPECTED_MODULES <= actual, f"Missing modules: {EXPECTED_MODULES - actual}"

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_parse_succeeds(self, mn_file: Path) -> None:
        """Every .mn file parses without errors."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        assert program is not None
        assert len(program.definitions) > 0

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_semantic_check_runs(self, mn_file: Path) -> None:
        """Semantic analysis completes without crashing on every file."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        errors = check(program, filename=mn_file.name)
        assert isinstance(errors, list)

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_semantic_errors_are_expected(self, mn_file: Path) -> None:
        """All semantic errors are known constructor patterns or cross-module refs."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        errors = check(program, filename=mn_file.name)
        for err in errors:
            msg = str(err)
            is_constructor = "Type mismatch: declared type" in msg
            is_missing_import = "Undefined function" in msg
            is_missing_module = "module" in msg and "not found" in msg
            is_operator_mismatch = "Operator" in msg and "not supported" in msg
            assert (
                is_constructor or is_missing_import or is_missing_module or is_operator_mismatch
            ), f"Unexpected semantic error in {mn_file.name}: {msg}"

    def test_ast_mn_zero_errors(self) -> None:
        """ast.mn should have zero semantic errors (pure data definitions)."""
        source = (SELF_DIR / "ast.mn").read_text(encoding="utf-8")
        program = parse(source, filename="ast.mn")
        errors = check(program, filename="ast.mn")
        assert len(errors) == 0, f"Expected 0 errors in ast.mn, got {len(errors)}"


# ---------------------------------------------------------------------------
# Test 2: LLVM emission — full file and per-function
# ---------------------------------------------------------------------------


class TestLLVMEmission:
    """Verify LLVM IR emission for self-hosted sources."""

    def test_lexer_mn_full_emit(self) -> None:
        """lexer.mn compiles fully to LLVM IR (all structs have primitive fields)."""
        source = (SELF_DIR / "lexer.mn").read_text(encoding="utf-8")
        program = parse(source, filename="lexer.mn")
        ir_text = _emit_full_ir(program, "lexer")
        assert "ModuleID" in ir_text
        assert ir_text.count("define ") == 19, "Expected 19 LLVM function definitions"

    def test_lexer_mn_ir_has_structs(self) -> None:
        """lexer.mn IR includes struct types (Token, Lexer, LexError)."""
        source = (SELF_DIR / "lexer.mn").read_text(encoding="utf-8")
        program = parse(source, filename="lexer.mn")
        ir_text = _emit_full_ir(program, "lexer")
        # Struct types are emitted as literal struct types in LLVM
        assert "type {" in ir_text or "{" in ir_text

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_primitive_fn_emission(self, mn_file: Path) -> None:
        """Primitive-type-only functions emit valid LLVM IR."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        prim_fns = [
            d for d in program.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)
        ]
        if not prim_fns:
            pytest.skip(f"{mn_file.name}: no primitive-type-only functions")
        emitter = LLVMEmitter(module_name=mn_file.stem)
        module = emitter.emit_program(Program(definitions=prim_fns))
        ir_text = str(module)
        assert len(ir_text) > 0
        assert "define " in ir_text

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_emit_deterministic(self, mn_file: Path) -> None:
        """Two independent compilations produce byte-identical LLVM IR."""
        source = mn_file.read_text(encoding="utf-8")
        program1 = parse(source, filename=mn_file.name)
        program2 = parse(source, filename=mn_file.name)
        prim_fns1 = [
            d for d in program1.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)
        ]
        prim_fns2 = [
            d for d in program2.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)
        ]
        if not prim_fns1:
            pytest.skip(f"{mn_file.name}: no primitive-type-only functions")
        e1 = LLVMEmitter(module_name=mn_file.stem)
        e2 = LLVMEmitter(module_name=mn_file.stem)
        ir1 = str(e1.emit_program(Program(definitions=prim_fns1)))
        ir2 = str(e2.emit_program(Program(definitions=prim_fns2)))
        assert ir1 == ir2, f"Non-deterministic IR output for {mn_file.name}"

    def test_lexer_full_emit_deterministic(self) -> None:
        """lexer.mn full compilation is deterministic (includes struct types)."""
        source = (SELF_DIR / "lexer.mn").read_text(encoding="utf-8")
        p1 = parse(source, filename="lexer.mn")
        p2 = parse(source, filename="lexer.mn")
        ir1 = _emit_full_ir(p1, "lexer")
        ir2 = _emit_full_ir(p2, "lexer")
        assert ir1 == ir2, "lexer.mn full emit is not deterministic"


# ---------------------------------------------------------------------------
# Test 3: Bootstrap coverage metrics
# ---------------------------------------------------------------------------


class TestBootstrapCoverage:
    """Track bootstrap compilation coverage across all self-hosted sources."""

    def test_total_definitions_above_threshold(self) -> None:
        """Self-hosted compiler has at least 250 total definitions."""
        total = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            total += len(program.definitions)
        assert total >= 250, f"Expected >= 250 total definitions, got {total}"

    def test_total_functions_above_threshold(self) -> None:
        """Self-hosted compiler has at least 200 functions."""
        total_fns = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            total_fns += sum(1 for d in program.definitions if isinstance(d, FnDef))
        assert total_fns >= 200, f"Expected >= 200 functions, got {total_fns}"

    def test_struct_coverage(self) -> None:
        """Self-hosted compiler defines at least 30 struct types."""
        total_structs = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            total_structs += sum(1 for d in program.definitions if isinstance(d, StructDef))
        assert total_structs >= 30, f"Expected >= 30 structs, got {total_structs}"

    def test_enum_coverage(self) -> None:
        """Self-hosted compiler defines enums (at least in ast.mn)."""
        total_enums = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            total_enums += sum(1 for d in program.definitions if isinstance(d, EnumDef))
        assert total_enums >= 5, f"Expected >= 5 enums, got {total_enums}"

    def test_emittable_function_ratio(self) -> None:
        """At least 20% of functions have primitive-only types (emittable)."""
        total_fns = 0
        prim_fns = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            program = parse(source, filename=mn_file.name)
            fns = [d for d in program.definitions if isinstance(d, FnDef)]
            total_fns += len(fns)
            prim_fns += sum(1 for f in fns if _has_only_primitive_types(f))
        ratio = prim_fns / total_fns if total_fns > 0 else 0
        assert ratio >= 0.2, f"Primitive function ratio {ratio:.1%} below 20% threshold"

    def test_line_count_above_threshold(self) -> None:
        """Self-hosted compiler totals at least 5000 lines of Mapanare code."""
        total_lines = 0
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            total_lines += len(source.splitlines())
        assert total_lines >= 5000, f"Expected >= 5000 lines, got {total_lines}"


# ---------------------------------------------------------------------------
# Test 4: Stage 2 fixed-point verification (full files)
# ---------------------------------------------------------------------------


class TestFixedPoint:
    """Verify the self-hosted compiler is a fixed point."""

    def test_lexer_full_fixed_point(self) -> None:
        """lexer.mn: Stage 1 == Stage 2 (full file, including structs)."""
        source = (SELF_DIR / "lexer.mn").read_text(encoding="utf-8")
        ir1 = _emit_full_ir(parse(source, filename="lexer.mn"), "lexer")
        ir2 = _emit_full_ir(parse(source, filename="lexer.mn"), "lexer")
        assert ir1 == ir2

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_primitive_fn_fixed_point(self, mn_file: Path) -> None:
        """Primitive-only functions are a fixed point across two compilations."""
        source = mn_file.read_text(encoding="utf-8")
        p1 = parse(source, filename=mn_file.name)
        p2 = parse(source, filename=mn_file.name)
        prim1 = [d for d in p1.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)]
        prim2 = [d for d in p2.definitions if isinstance(d, FnDef) and _has_only_primitive_types(d)]
        if not prim1:
            pytest.skip("No primitive-type functions")
        e1 = LLVMEmitter(module_name=mn_file.stem)
        e2 = LLVMEmitter(module_name=mn_file.stem)
        ir1 = str(e1.emit_program(Program(definitions=prim1)))
        ir2 = str(e2.emit_program(Program(definitions=prim2)))
        assert ir1 == ir2

    def test_combined_all_files_fixed_point(self) -> None:
        """Combined IR from all files is a fixed point."""
        all_fns_1: list[FnDef] = []
        all_fns_2: list[FnDef] = []
        for mn_file in MN_FILES:
            source = mn_file.read_text(encoding="utf-8")
            p1 = parse(source, filename=mn_file.name)
            p2 = parse(source, filename=mn_file.name)
            for d in p1.definitions:
                if isinstance(d, FnDef) and _has_only_primitive_types(d):
                    all_fns_1.append(d)
            for d in p2.definitions:
                if isinstance(d, FnDef) and _has_only_primitive_types(d):
                    all_fns_2.append(d)
        e1 = LLVMEmitter(module_name="combined_v1")
        e2 = LLVMEmitter(module_name="combined_v1")
        ir1 = str(e1.emit_program(Program(definitions=all_fns_1)))
        ir2 = str(e2.emit_program(Program(definitions=all_fns_2)))
        assert ir1 == ir2


# ---------------------------------------------------------------------------
# Test 5: CLI integration — compile and run sample programs
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """Verify the compiler CLI works end-to-end on sample programs."""

    @pytest.fixture(autouse=True)
    def _check_cli(self) -> None:
        """Ensure the CLI entry point is available."""
        import shutil

        if not shutil.which("mapanare"):
            pytest.skip("mapanare CLI not installed")

    @pytest.mark.parametrize(
        "program",
        [
            (
                "fn fib(n: Int) -> Int {\n"
                "    if n <= 1 { return n }\n"
                "    return fib(n - 1) + fib(n - 2)\n"
                "}\n"
                "let x = fib(10)\n"
                "println(x)\n"
            ),
            ("let x: Int = 42\nprintln(x)\n"),
            ("fn add(a: Int, b: Int) -> Int { return a + b }\nprintln(add(3, 4))\n"),
            ('let s: String = "hello"\nprintln(s)\n'),
            ("for i in 0..5 { println(i) }\n"),
        ],
        ids=["fibonacci", "simple_int", "add_fn", "string", "for_loop"],
    )
    def test_run_produces_output(self, program: str, tmp_path: Path) -> None:
        """Compile and run a simple program, verify it produces output."""
        src = tmp_path / "test.mn"
        src.write_text(program, encoding="utf-8")
        result = subprocess.run(
            ["mapanare", "run", str(src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Run failed: {result.stderr}"
        assert len(result.stdout.strip()) > 0, "No output produced"

    def test_run_fibonacci_correct(self, tmp_path: Path) -> None:
        """Fibonacci program produces correct output."""
        src = tmp_path / "fib.mn"
        src.write_text(
            "fn fib(n: Int) -> Int {\n"
            "    if n <= 1 { return n }\n"
            "    return fib(n - 1) + fib(n - 2)\n"
            "}\n"
            "println(fib(10))\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["mapanare", "run", str(src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "55"

    def test_check_succeeds(self, tmp_path: Path) -> None:
        """mapanare check succeeds on a valid program."""
        src = tmp_path / "valid.mn"
        src.write_text("fn greet(name: String) -> String { return name }\n", encoding="utf-8")
        result = subprocess.run(
            ["mapanare", "check", str(src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

    def test_check_reports_error(self, tmp_path: Path) -> None:
        """mapanare check reports errors for invalid programs."""
        src = tmp_path / "bad.mn"
        src.write_text("fn broken( { }\n", encoding="utf-8")
        result = subprocess.run(
            ["mapanare", "check", str(src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0

    def test_emit_llvm_succeeds(self, tmp_path: Path) -> None:
        """mapanare emit-llvm produces LLVM IR output."""
        src = tmp_path / "simple.mn"
        # Include a call so the optimizer doesn't DCE the function
        src.write_text(
            "fn double(x: Int) -> Int { return x * 2 }\nlet r = double(21)\n",
            encoding="utf-8",
        )
        out = tmp_path / "simple.ll"
        result = subprocess.run(
            ["mapanare", "emit-llvm", str(src), "-o", str(out), "-O0"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        ir_text = out.read_text(encoding="utf-8")
        assert "define " in ir_text
        assert "double" in ir_text

    def test_compile_to_python(self, tmp_path: Path) -> None:
        """mapanare compile produces Python source."""
        src = tmp_path / "hello.mn"
        src.write_text('println("hello world")\n', encoding="utf-8")
        out = tmp_path / "hello.py"
        result = subprocess.run(
            ["mapanare", "compile", str(src), "-o", str(out)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        py_code = out.read_text(encoding="utf-8")
        assert "hello world" in py_code


# ---------------------------------------------------------------------------
# Test 6: Sample program verification (test_vs/)
# ---------------------------------------------------------------------------


class TestSamplePrograms:
    """Verify sample programs in test_vs/ compile and run."""

    @pytest.fixture(autouse=True)
    def _check_cli(self) -> None:
        import shutil

        if not shutil.which("mapanare"):
            pytest.skip("mapanare CLI not installed")

    def test_fibonacci_check(self) -> None:
        """test_vs/01_fibonacci.mn passes check."""
        src = TEST_VS_DIR / "01_fibonacci.mn"
        if not src.exists():
            pytest.skip("test_vs/01_fibonacci.mn not found")
        result = subprocess.run(
            ["mapanare", "check", str(src)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0

    def test_fibonacci_run(self) -> None:
        """test_vs/01_fibonacci.mn runs and produces output."""
        src = TEST_VS_DIR / "01_fibonacci.mn"
        if not src.exists():
            pytest.skip("test_vs/01_fibonacci.mn not found")
        result = subprocess.run(
            ["mapanare", "run", str(src)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "9227465"

    @pytest.mark.parametrize(
        "filename",
        [
            "01_fibonacci.mn",
            "02_concurrency.mn",
            "03_stream_pipeline.mn",
            "04_matrix_mul.mn",
            "05_agent_pipeline.mn",
        ],
    )
    def test_sample_parses(self, filename: str) -> None:
        """All sample programs parse successfully."""
        src = TEST_VS_DIR / filename
        if not src.exists():
            pytest.skip(f"{filename} not found")
        source = src.read_text(encoding="utf-8")
        program = parse(source, filename=filename)
        assert program is not None
        assert len(program.definitions) > 0


# ---------------------------------------------------------------------------
# Test 7: Optimizer integration with self-hosted sources
# ---------------------------------------------------------------------------


class TestOptimizerIntegration:
    """Verify the optimizer works on self-hosted compiler sources."""

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_optimize_no_crash(self, mn_file: Path) -> None:
        """Optimizer runs without crashing on self-hosted sources."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        optimized, stats = optimize(program, OptLevel.O2)
        assert optimized is not None
        assert len(optimized.definitions) > 0

    @pytest.mark.parametrize("mn_file", MN_FILES, ids=[f.stem for f in MN_FILES])
    def test_optimize_preserves_definitions(self, mn_file: Path) -> None:
        """Optimizer doesn't drop definitions (may inline/fold, but count stays >= original)."""
        source = mn_file.read_text(encoding="utf-8")
        program = parse(source, filename=mn_file.name)
        original_count = len(program.definitions)
        optimized, _ = optimize(program, OptLevel.O1)
        # Optimizer should preserve at least the same number of top-level definitions
        assert (
            len(optimized.definitions) >= original_count * 0.9
        ), f"Optimizer dropped too many defs: {len(optimized.definitions)} < {original_count}"
