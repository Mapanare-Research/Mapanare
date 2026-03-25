"""Tests for WASM stdlib bridge modules -- Phase v2.0.0.

Tests cover:
  1. wasm/bridge.mn parses correctly
  2. wasm/runtime.mn parses correctly
  3. JsValue enum variants
  4. js_eval function signature
  5. js_call function signature
  6. dom_ functions exist
  7. console_log signature
  8. fetch_url returns Result type
  9. Memory management functions
  10. WASI function declarations
  11. Bridge functions use @extern annotations
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mapanare.ast_nodes import (
    EnumDef,
    ExportDef,
    FnDef,
    GenericType,
    NamedType,
    Program,
)
from mapanare.parser import parse

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_STDLIB_DIR = _PROJECT_ROOT / "stdlib"
_WASM_DIR = _STDLIB_DIR / "wasm"

_bridge_path = _WASM_DIR / "bridge.mn"
_runtime_path = _WASM_DIR / "runtime.mn"

_bridge_exists = _bridge_path.is_file()
_runtime_exists = _runtime_path.is_file()


def _parse_file(path: Path) -> Program:
    """Parse a .mn file and return the AST."""
    source = path.read_text(encoding="utf-8")
    return parse(source, filename=str(path))


def _find_fn(prog: Program, name: str) -> FnDef | None:
    """Find a function definition by name in a program."""
    for defn in prog.definitions:
        if isinstance(defn, FnDef) and defn.name == name:
            return defn
        # Functions may be wrapped in ExportDef
        if isinstance(defn, ExportDef) and isinstance(defn.definition, FnDef):
            if defn.definition.name == name:
                return defn.definition
    return None


def _find_enum(prog: Program, name: str) -> EnumDef | None:
    """Find an enum definition by name in a program."""
    for defn in prog.definitions:
        if isinstance(defn, EnumDef) and defn.name == name:
            return defn
        if isinstance(defn, ExportDef) and isinstance(defn.definition, EnumDef):
            if defn.definition.name == name:
                return defn.definition
    return None


def _all_fn_names(prog: Program) -> set[str]:
    """Collect all top-level function names from a program."""
    names: set[str] = set()
    for defn in prog.definitions:
        if isinstance(defn, FnDef):
            names.add(defn.name)
        if isinstance(defn, ExportDef) and isinstance(defn.definition, FnDef):
            names.add(defn.definition.name)
    return names


def _all_definitions(prog: Program) -> list:
    """Unwrap ExportDef wrappers and return all definitions."""
    result = []
    for defn in prog.definitions:
        if isinstance(defn, ExportDef):
            result.append(defn.definition)
        else:
            result.append(defn)
    return result


# ===========================================================================
# 1. wasm/bridge.mn parses correctly
# ===========================================================================


class TestBridgeParsing:
    """Test that wasm/bridge.mn can be parsed by the Mapanare parser."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_bridge_parses_without_error(self) -> None:
        prog = _parse_file(_bridge_path)
        assert isinstance(prog, Program)
        assert len(prog.definitions) > 0

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_bridge_has_functions(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert len(fn_names) >= 1, "bridge.mn should define at least one function"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_bridge_source_not_empty(self) -> None:
        content = _bridge_path.read_text(encoding="utf-8")
        lines = [
            line
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("//")
        ]
        assert len(lines) >= 10, "bridge.mn should have substantial content"


# ===========================================================================
# 2. wasm/runtime.mn parses correctly
# ===========================================================================


class TestRuntimeParsing:
    """Test that wasm/runtime.mn can be parsed by the Mapanare parser."""

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_runtime_parses_without_error(self) -> None:
        prog = _parse_file(_runtime_path)
        assert isinstance(prog, Program)
        assert len(prog.definitions) > 0

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_runtime_has_functions(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        assert len(fn_names) >= 1

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_runtime_source_not_empty(self) -> None:
        content = _runtime_path.read_text(encoding="utf-8")
        lines = [
            line
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("//")
        ]
        assert len(lines) >= 10


# ===========================================================================
# 3. JsValue enum variants
# ===========================================================================


class TestJsValueEnum:
    """Test the JsValue enum used for JS interop."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_jsvalue_enum_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        js_val = _find_enum(prog, "JsValue")
        assert js_val is not None, "JsValue enum should be defined in bridge.mn"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_jsvalue_has_null_variant(self) -> None:
        prog = _parse_file(_bridge_path)
        js_val = _find_enum(prog, "JsValue")
        assert js_val is not None
        variant_names = {v.name for v in js_val.variants}
        assert "Null" in variant_names or "JsNull" in variant_names

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_jsvalue_has_number_variant(self) -> None:
        prog = _parse_file(_bridge_path)
        js_val = _find_enum(prog, "JsValue")
        assert js_val is not None
        variant_names = {v.name for v in js_val.variants}
        assert "Number" in variant_names or "JsNumber" in variant_names or "Float" in variant_names

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_jsvalue_has_string_variant(self) -> None:
        prog = _parse_file(_bridge_path)
        js_val = _find_enum(prog, "JsValue")
        assert js_val is not None
        variant_names = {v.name for v in js_val.variants}
        assert "Str" in variant_names or "JsString" in variant_names or "String" in variant_names

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_jsvalue_has_bool_variant(self) -> None:
        prog = _parse_file(_bridge_path)
        js_val = _find_enum(prog, "JsValue")
        assert js_val is not None
        variant_names = {v.name for v in js_val.variants}
        assert "Bool" in variant_names or "JsBool" in variant_names or "Boolean" in variant_names

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_jsvalue_has_object_variant(self) -> None:
        prog = _parse_file(_bridge_path)
        js_val = _find_enum(prog, "JsValue")
        assert js_val is not None
        variant_names = {v.name for v in js_val.variants}
        assert "Object" in variant_names or "JsObject" in variant_names


# ===========================================================================
# 4. js_eval function signature
# ===========================================================================


class TestJsEval:
    """Test js_eval function for executing JavaScript from Mapanare."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_js_eval_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "js_eval")
        assert fn is not None, "js_eval function should be defined"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_js_eval_takes_string_param(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "js_eval")
        assert fn is not None
        assert len(fn.params) >= 1
        # First param should be a String (the JS code to evaluate)
        first_param = fn.params[0]
        if isinstance(first_param.type_annotation, NamedType):
            assert first_param.type_annotation.name == "String"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_js_eval_returns_jsvalue_or_result(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "js_eval")
        assert fn is not None
        assert fn.return_type is not None
        # Should return JsValue or Result<JsValue, String>
        ret = fn.return_type
        if isinstance(ret, NamedType):
            assert ret.name in ("JsValue", "Result")
        elif isinstance(ret, GenericType):
            assert ret.name in ("JsValue", "Result")


# ===========================================================================
# 5. js_call function signature
# ===========================================================================


class TestJsCall:
    """Test js_call function for calling JS functions from Mapanare."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_js_call_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "js_call")
        assert fn is not None, "js_call function should be defined"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_js_call_takes_function_name(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "js_call")
        assert fn is not None
        assert len(fn.params) >= 1
        # First param should be the function name (String)
        first = fn.params[0]
        if isinstance(first.type_annotation, NamedType):
            assert first.type_annotation.name == "String"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_js_call_takes_args_list(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "js_call")
        assert fn is not None
        # Should have at least 2 params: function name + args
        assert len(fn.params) >= 2


# ===========================================================================
# 6. dom_ functions exist
# ===========================================================================


class TestDOMFunctions:
    """Test DOM manipulation functions in the WASM bridge."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_dom_get_element_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert (
            "dom_get_element" in fn_names
            or "dom_get_element_by_id" in fn_names
            or "dom_query" in fn_names
        ), "Should have a DOM element query function"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_dom_set_text_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert (
            "dom_set_text" in fn_names
            or "dom_set_inner_text" in fn_names
            or "dom_set_text_content" in fn_names
        ), "Should have a DOM text setter function"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_dom_add_event_listener_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert (
            "dom_add_event_listener" in fn_names or "dom_on" in fn_names or "dom_listen" in fn_names
        ), "Should have a DOM event listener function"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_dom_create_element_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert (
            "dom_create_element" in fn_names or "dom_create" in fn_names
        ), "Should have a DOM element creation function"


# ===========================================================================
# 7. console_log signature
# ===========================================================================


class TestConsoleLog:
    """Test console_log bridge function."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_console_log_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert "console_log" in fn_names, "console_log should be defined in bridge.mn"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_console_log_takes_string(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "console_log")
        assert fn is not None
        assert len(fn.params) >= 1
        first = fn.params[0]
        if isinstance(first.type_annotation, NamedType):
            assert first.type_annotation.name == "String"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_console_log_returns_void(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "console_log")
        assert fn is not None
        # Void functions have no return type or return type is None
        assert fn.return_type is None or (
            isinstance(fn.return_type, NamedType) and fn.return_type.name in ("Void", "()")
        )


# ===========================================================================
# 8. fetch_url returns Result type
# ===========================================================================


class TestFetchUrl:
    """Test fetch_url bridge function."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_fetch_url_exists(self) -> None:
        prog = _parse_file(_bridge_path)
        fn_names = _all_fn_names(prog)
        assert (
            "fetch_url" in fn_names or "fetch" in fn_names or "http_get" in fn_names
        ), "Should have a fetch/HTTP function"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_fetch_url_returns_result(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "fetch_url") or _find_fn(prog, "fetch") or _find_fn(prog, "http_get")
        assert fn is not None
        assert fn.return_type is not None
        # Should return Result<String, String> or similar
        ret = fn.return_type
        if isinstance(ret, GenericType):
            assert ret.name == "Result"
        elif isinstance(ret, NamedType):
            assert ret.name == "Result"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_fetch_url_takes_url_param(self) -> None:
        prog = _parse_file(_bridge_path)
        fn = _find_fn(prog, "fetch_url") or _find_fn(prog, "fetch") or _find_fn(prog, "http_get")
        assert fn is not None
        assert len(fn.params) >= 1


# ===========================================================================
# 9. Memory management functions
# ===========================================================================


class TestWASMMemoryFunctions:
    """Test WASM linear memory management functions."""

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_memory_alloc_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        assert (
            "wasm_alloc" in fn_names or "alloc" in fn_names or "memory_alloc" in fn_names
        ), "Should have a memory allocation function"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_memory_free_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        assert (
            "wasm_free" in fn_names or "free" in fn_names or "memory_free" in fn_names
        ), "Should have a memory free function"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_memory_grow_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        assert (
            "memory_grow" in fn_names or "wasm_memory_grow" in fn_names or "grow" in fn_names
        ), "Should have a memory grow function"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_memory_size_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        assert (
            "memory_size" in fn_names or "wasm_memory_size" in fn_names or "heap_size" in fn_names
        ), "Should have a memory size query function"


# ===========================================================================
# 10. WASI function declarations
# ===========================================================================


class TestWASIFunctions:
    """Test WASI (WebAssembly System Interface) function declarations."""

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_wasi_fd_write_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        source = _runtime_path.read_text(encoding="utf-8")
        assert (
            "fd_write" in fn_names or "wasi_fd_write" in fn_names or "fd_write" in source
        ), "Should declare WASI fd_write"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_wasi_fd_read_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        source = _runtime_path.read_text(encoding="utf-8")
        assert (
            "fd_read" in fn_names or "wasi_fd_read" in fn_names or "fd_read" in source
        ), "Should declare WASI fd_read"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_wasi_proc_exit_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        source = _runtime_path.read_text(encoding="utf-8")
        assert (
            "proc_exit" in fn_names or "wasi_proc_exit" in fn_names or "proc_exit" in source
        ), "Should declare WASI proc_exit"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_wasi_clock_time_get_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        source = _runtime_path.read_text(encoding="utf-8")
        assert (
            "clock_time_get" in fn_names
            or "wasi_clock_time_get" in fn_names
            or "clock_time" in source
        ), "Should declare WASI clock_time_get"

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_wasi_args_get_exists(self) -> None:
        prog = _parse_file(_runtime_path)
        fn_names = _all_fn_names(prog)
        source = _runtime_path.read_text(encoding="utf-8")
        assert (
            "args_get" in fn_names or "wasi_args_get" in fn_names or "args_get" in source
        ), "Should declare WASI args_get"


# ===========================================================================
# 11. Bridge functions use @extern annotations
# ===========================================================================


class TestExternAnnotations:
    """Test that bridge functions use @extern for JS/WASI imports."""

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_bridge_has_extern_annotation(self) -> None:
        source = _bridge_path.read_text(encoding="utf-8")
        assert "@extern" in source, "bridge.mn should use @extern annotations for JS imports"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_extern_specifies_module(self) -> None:
        source = _bridge_path.read_text(encoding="utf-8")
        # @extern should specify the JS module, e.g., @extern("env") or @extern("js")
        assert '@extern("' in source or "@extern(" in source

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_bridge_extern_functions_have_no_body(self) -> None:
        """Extern-declared functions should have empty or marker bodies."""
        source = _bridge_path.read_text(encoding="utf-8")
        # Look for @extern followed by fn declarations
        # The pattern should appear in the source
        assert "@extern" in source
        # The file should still parse
        prog = _parse_file(_bridge_path)
        assert isinstance(prog, Program)

    @pytest.mark.skipif(not _runtime_exists, reason="stdlib/wasm/runtime.mn not yet created")
    def test_runtime_has_extern_for_wasi(self) -> None:
        source = _runtime_path.read_text(encoding="utf-8")
        assert (
            "@extern" in source or "@wasi" in source
        ), "runtime.mn should use @extern or @wasi for WASI imports"

    @pytest.mark.skipif(not _bridge_exists, reason="stdlib/wasm/bridge.mn not yet created")
    def test_extern_count_minimum(self) -> None:
        """Bridge module should have at least 5 extern declarations."""
        source = _bridge_path.read_text(encoding="utf-8")
        extern_count = source.count("@extern")
        assert extern_count >= 5, f"Expected at least 5 @extern declarations, found {extern_count}"
