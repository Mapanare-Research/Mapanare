"""Tests for the Mapanare structured error codes (mapanare/error_codes.py).

Verifies:
  - All error codes have valid format
  - Phase letter matches the phase field
  - No duplicate codes
  - Lookup function works
  - String representation
"""

from __future__ import annotations

from mapanare.error_codes import ALL_ERROR_CODES, ErrorCode, lookup_error_code


class TestErrorCodeFormat:
    def test_all_codes_have_valid_format(self) -> None:
        """Every code matches MN-XNNNN pattern."""
        import re

        pattern = re.compile(r"^MN-[PSLCRT]\d{4}$")
        for ec in ALL_ERROR_CODES:
            assert pattern.match(ec.code), f"Invalid format: {ec.code}"

    def test_phase_letter_matches_phase(self) -> None:
        """The letter in the code matches the phase field."""
        phase_map = {
            "P": "parse",
            "S": "semantic",
            "L": "lowering",
            "C": "codegen",
            "R": "runtime",
            "T": "tooling",
        }
        for ec in ALL_ERROR_CODES:
            letter = ec.code[3]
            expected_phase = phase_map.get(letter)
            assert ec.phase == expected_phase, (
                f"{ec.code}: phase letter '{letter}' should map to '{expected_phase}', "
                f"got '{ec.phase}'"
            )

    def test_no_duplicate_codes(self) -> None:
        codes = [ec.code for ec in ALL_ERROR_CODES]
        assert len(codes) == len(set(codes)), "Duplicate error codes found"

    def test_all_codes_have_title(self) -> None:
        for ec in ALL_ERROR_CODES:
            assert ec.title, f"{ec.code} has no title"

    def test_all_codes_have_explanation(self) -> None:
        for ec in ALL_ERROR_CODES:
            assert ec.explanation, f"{ec.code} has no explanation"


class TestErrorCodeLookup:
    def test_lookup_existing(self) -> None:
        result = lookup_error_code("MN-S0001")
        assert result is not None
        assert result.title == "undefined variable"

    def test_lookup_nonexistent(self) -> None:
        result = lookup_error_code("MN-X9999")
        assert result is None

    def test_lookup_all(self) -> None:
        for ec in ALL_ERROR_CODES:
            found = lookup_error_code(ec.code)
            assert found is ec


class TestErrorCodeStr:
    def test_str_representation(self) -> None:
        ec = ErrorCode(code="MN-S0001", title="test error", phase="semantic")
        assert str(ec) == "[MN-S0001] test error"

    def test_all_codes_have_str(self) -> None:
        for ec in ALL_ERROR_CODES:
            s = str(ec)
            assert s.startswith(f"[{ec.code}]")


class TestErrorCodeCoverage:
    def test_parse_codes_exist(self) -> None:
        parse_codes = [ec for ec in ALL_ERROR_CODES if ec.phase == "parse"]
        assert len(parse_codes) >= 5

    def test_semantic_codes_exist(self) -> None:
        sem_codes = [ec for ec in ALL_ERROR_CODES if ec.phase == "semantic"]
        assert len(sem_codes) >= 10

    def test_runtime_codes_exist(self) -> None:
        rt_codes = [ec for ec in ALL_ERROR_CODES if ec.phase == "runtime"]
        assert len(rt_codes) >= 5

    def test_codegen_codes_exist(self) -> None:
        cg_codes = [ec for ec in ALL_ERROR_CODES if ec.phase == "codegen"]
        assert len(cg_codes) >= 3
