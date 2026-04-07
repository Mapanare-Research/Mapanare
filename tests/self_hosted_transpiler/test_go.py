"""Tests for the self-hosted Go transpiler (from_go.mn)."""

from __future__ import annotations

from pathlib import Path

SELF_DIR = Path(__file__).resolve().parent.parent.parent / "mapanare" / "self"
FROM_GO_MN = SELF_DIR / "from_go.mn"


class TestFromGoMnExists:
    def test_file_exists(self) -> None:
        assert FROM_GO_MN.exists()

    def test_has_tokenizer(self) -> None:
        src = FROM_GO_MN.read_text(encoding="utf-8")
        assert "fn tokenize_go(" in src

    def test_has_translate_go(self) -> None:
        src = FROM_GO_MN.read_text(encoding="utf-8")
        assert "fn translate_go(" in src

    def test_has_go_token_struct(self) -> None:
        src = FROM_GO_MN.read_text(encoding="utf-8")
        assert "struct GoToken" in src

    def test_uses_transpiler_framework(self) -> None:
        src = FROM_GO_MN.read_text(encoding="utf-8")
        assert "go_type_mappings()" in src

    def test_has_struct_translation(self) -> None:
        src = FROM_GO_MN.read_text(encoding="utf-8")
        assert "fn translate_go_struct(" in src

    def test_has_interface_translation(self) -> None:
        src = FROM_GO_MN.read_text(encoding="utf-8")
        assert "fn translate_go_interface(" in src


class TestFromGoMnCompiles:
    def test_parse_succeeds(self) -> None:
        from mapanare.parser import parse

        src = FROM_GO_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_go.mn")
        assert program is not None
        assert len(program.definitions) > 0

    def test_ir_emission(self) -> None:
        from mapanare.lower import MIRLowerer
        from mapanare.parser import parse

        src = FROM_GO_MN.read_text(encoding="utf-8")
        program = parse(src, filename="from_go.mn")
        lowerer = MIRLowerer()
        mir_module = lowerer.lower(program)
        assert mir_module is not None
        assert len(mir_module.functions) > 0
