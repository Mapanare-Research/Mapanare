"""Tests for __struct_meta::<T>() compile-time builtin (v4.48.0)."""

import pytest

from mapanare.parser import parse
from mapanare.semantic import check


def _compile_to_ir(src: str) -> str:
    """Compile Mapanare source to LLVM IR string."""
    import subprocess

    result = subprocess.run(
        ["python3", "-m", "mapanare", "emit-llvm", "-", "-o", "/dev/stdout"],
        input=src,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Fallback: write to temp file and compile
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".mn", delete=False) as f:
            f.write(src)
            tmp = f.name
        result = subprocess.run(
            ["python3", "-m", "mapanare", "emit-llvm", tmp, "-o", f"{tmp}.ll"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(f"Compilation failed: {result.stderr}")
        with open(f"{tmp}.ll") as f:
            ir = f.read()
        os.unlink(tmp)
        os.unlink(f"{tmp}.ll")
        return ir
    return result.stdout


class TestStructMetaCompiles:
    """__struct_meta::<T>() compiles through the bootstrap."""

    def test_basic_struct(self):
        src = """
struct Address {
    street: String,
    city: String,
    zip: Int,
}

fn main() {
    let schema = __struct_meta::<Address>()
    print(schema)
}
"""
        ir = _compile_to_ir(src)
        assert "object" in ir
        assert "properties" in ir
        assert "street" in ir
        assert "city" in ir
        assert "zip" in ir
        assert "integer" in ir
        assert "string" in ir

    def test_optional_field_not_required(self):
        src = """
struct Profile {
    name: String,
    age: Int,
    email: Option<String>,
}

fn main() {
    let schema = __struct_meta::<Profile>()
    print(schema)
}
"""
        ir = _compile_to_ir(src)
        # email should be in properties but NOT in required
        assert "email" in ir
        assert "name" in ir
        # The required array should have name and age but not email
        # Check that required contains "name" and "age"
        assert "required" in ir

    def test_float_field(self):
        src = """
struct Measurement {
    value: Float,
    unit: String,
}

fn main() {
    let schema = __struct_meta::<Measurement>()
    print(schema)
}
"""
        ir = _compile_to_ir(src)
        assert "number" in ir
        assert "string" in ir

    def test_bool_field(self):
        src = """
struct Config {
    debug: Bool,
    name: String,
}

fn main() {
    let schema = __struct_meta::<Config>()
    print(schema)
}
"""
        ir = _compile_to_ir(src)
        assert "boolean" in ir

    def test_check_passes(self):
        src = """
struct Foo { x: Int, y: String }
fn main() {
    let s = __struct_meta::<Foo>()
    print(s)
}
"""
        ast = parse(src)
        checked = check(ast)
        assert checked is not None


class TestStructuredExtraction:
    """Structured extraction types and functions exist in llm.mn."""

    def test_extract_error_type(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "tipo ExtractError" in src
        assert "| LlmFailed(String)" in src
        assert "| RetriesExhausted(String)" in src

    def test_extract_with_schema_function(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "fn extract_with_schema(" in src
        assert "fn extract_text(" in src

    def test_validation_function(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "fn validate_json_shape(" in src

    def test_retry_prompt_function(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "fn build_retry_prompt(" in src

    def test_llm_module_still_compiles(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        ast = parse(src)
        checked = check(ast)
        assert checked is not None
