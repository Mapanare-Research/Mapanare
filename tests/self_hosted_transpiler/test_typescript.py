"""Tests for the self-hosted TypeScript transpiler (from_typescript.mn)."""

from __future__ import annotations

from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
FROM_TS_MN = SELF_DIR / "from_typescript.mn"


class TestFromTsMnExists:
    def test_file_exists(self) -> None:
        assert FROM_TS_MN.exists()

    def test_has_tokenizer(self) -> None:
        src = FROM_TS_MN.read_text(encoding="utf-8")
        assert "fn tokenize_ts(" in src or "fn tokenize_typescript(" in src

    def test_has_translate_typescript(self) -> None:
        src = FROM_TS_MN.read_text(encoding="utf-8")
        assert "fn translate_typescript(" in src

    def test_has_ts_token_struct(self) -> None:
        src = FROM_TS_MN.read_text(encoding="utf-8")
        assert "struct TsToken" in src

    def test_uses_transpiler_framework(self) -> None:
        src = FROM_TS_MN.read_text(encoding="utf-8")
        assert "typescript_type_mappings()" in src

    def test_has_interface_translation(self) -> None:
        src = FROM_TS_MN.read_text(encoding="utf-8")
        assert "interface" in src.lower()
        assert "trait" in src


class TestFromTsMnCompiles:
    def test_parse_succeeds(self) -> None:
        from mapanare.parser import parse

        src = FROM_TS_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_typescript.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_ir_emission(self) -> None:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        src = FROM_TS_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_typescript.mn")
        lowerer = MIRLowerer()
        mir_module = lowerer.lower(program)
        assert mir_module is not None
        assert len(mir_module.functions) > 0
