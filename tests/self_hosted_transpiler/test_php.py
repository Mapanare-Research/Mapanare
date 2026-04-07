"""Tests for the self-hosted PHP transpiler (from_php.mn)."""

from __future__ import annotations

from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
FROM_PHP_MN = SELF_DIR / "from_php.mn"


class TestFromPhpMnExists:
    def test_file_exists(self) -> None:
        assert FROM_PHP_MN.exists()

    def test_has_tokenizer(self) -> None:
        src = FROM_PHP_MN.read_text(encoding="utf-8")
        assert "fn tokenize_php(" in src

    def test_has_translate_php(self) -> None:
        src = FROM_PHP_MN.read_text(encoding="utf-8")
        assert "fn translate_php(" in src

    def test_has_php_token_struct(self) -> None:
        src = FROM_PHP_MN.read_text(encoding="utf-8")
        assert "struct PhpToken" in src

    def test_has_php_parser_struct(self) -> None:
        src = FROM_PHP_MN.read_text(encoding="utf-8")
        assert "struct PhpParser" in src

    def test_uses_transpiler_framework(self) -> None:
        src = FROM_PHP_MN.read_text(encoding="utf-8")
        assert "php_type_mappings()" in src

    def test_has_stdlib_shims(self) -> None:
        src = FROM_PHP_MN.read_text(encoding="utf-8")
        assert "fn php_stdlib_shims(" in src


class TestFromPhpMnCompiles:
    def test_parse_succeeds(self) -> None:
        from mapanare.parser import parse

        src = FROM_PHP_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_php.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_ir_emission(self) -> None:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        src = FROM_PHP_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_php.mn")
        lowerer = MIRLowerer()
        mir_module = lowerer.lower(program)
        assert mir_module is not None
        assert len(mir_module.functions) > 0
