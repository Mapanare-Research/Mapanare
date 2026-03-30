"""Phase 5 — String method codegen tests for LLVM backend.

Tests verify that string methods (contains, split, trim, to_upper, to_lower,
replace) are emitted correctly to LLVM IR on both emitters.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _compile_ast(source: str) -> str:
    """Compile via AST-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test.mn", use_mir=False)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test.mn", use_mir=True)


# ---------------------------------------------------------------------------
# .contains()
# ---------------------------------------------------------------------------


class TestStringContains:
    def test_contains_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello world"
                let needle: String = "world"
                let r: Bool = s.contains(needle)
                print(r)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_contains" in ir

    def test_contains_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello world"
                let needle: String = "world"
                let r: Bool = s.contains(needle)
                print(r)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_contains" in ir


# ---------------------------------------------------------------------------
# .split()
# ---------------------------------------------------------------------------


class TestStringSplit:
    def test_split_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "a,b,c"
                let delim: String = ","
                let parts: List<String> = s.split(delim)
                print(len(parts))
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_split" in ir

    def test_split_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "a,b,c"
                let delim: String = ","
                let parts: List<String> = s.split(delim)
                print(len(parts))
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_split" in ir


# ---------------------------------------------------------------------------
# .trim() / .trim_start() / .trim_end()
# ---------------------------------------------------------------------------


class TestStringTrim:
    def test_trim_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "  hello  "
                let t: String = s.trim()
                print(t)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_trim" in ir

    def test_trim_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "  hello  "
                let t: String = s.trim()
                print(t)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_trim" in ir

    def test_trim_start_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "  hello"
                let t: String = s.trim_start()
                print(t)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_trim_start" in ir

    def test_trim_start_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "  hello"
                let t: String = s.trim_start()
                print(t)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_trim_start" in ir

    def test_trim_end_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello  "
                let t: String = s.trim_end()
                print(t)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_trim_end" in ir

    def test_trim_end_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello  "
                let t: String = s.trim_end()
                print(t)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_trim_end" in ir


# ---------------------------------------------------------------------------
# .to_upper() / .to_lower()
# ---------------------------------------------------------------------------


class TestStringCase:
    def test_to_upper_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello"
                let u: String = s.to_upper()
                print(u)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_to_upper" in ir

    def test_to_upper_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello"
                let u: String = s.to_upper()
                print(u)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_to_upper" in ir

    def test_to_lower_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "HELLO"
                let l: String = s.to_lower()
                print(l)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_to_lower" in ir

    def test_to_lower_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "HELLO"
                let l: String = s.to_lower()
                print(l)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_to_lower" in ir


# ---------------------------------------------------------------------------
# .replace()
# ---------------------------------------------------------------------------


class TestStringReplace:
    def test_replace_ast(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello world"
                let r: String = s.replace("world", "earth")
                print(r)
            }
        """)
        ir = _compile_ast(src)
        assert "__mn_str_replace" in ir

    def test_replace_mir(self) -> None:
        src = textwrap.dedent("""\
            fn main() {
                let s: String = "hello world"
                let r: String = s.replace("world", "earth")
                print(r)
            }
        """)
        ir = _compile_mir(src)
        assert "__mn_str_replace" in ir
