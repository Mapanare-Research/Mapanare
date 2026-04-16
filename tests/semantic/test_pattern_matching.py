"""Unit tests for mapanare/pattern_matching.py (v4.79.0, CARRY_FORWARD P2 + P6).

P2: >=90% line coverage of the Maranget decision-tree module.
P6: >=5 unreachable-arm warning tests.

Tests the pattern_matching module directly (unit-level), not via the
semantic checker integration (which is covered by test_match_exhaustive.py).
"""

from __future__ import annotations

from mapanare.ast_nodes import (
    BoolLiteral,
    ConstructorPattern,
    FloatLiteral,
    IdentPattern,
    IntLiteral,
    LiteralPattern,
    OrPattern,
    StringLiteral,
    WildcardPattern,
)
from mapanare.pattern_matching import (
    ConstructorInfo,
    DTFail,
    DTLeaf,
    DTSwitch,
    PatternMatrix,
    PatternRow,
    TypeContext,
    build_decision_tree,
    build_witness_for_switch,
    collect_fail_witnesses,
    default_matrix,
    display_witness,
    expand_or_patterns,
    find_unreachable_arms,
    has_any_fail,
    select_column,
    specialize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _int_lit(v: int) -> LiteralPattern:
    return LiteralPattern(value=IntLiteral(value=v))


def _str_lit(v: str) -> LiteralPattern:
    return LiteralPattern(value=StringLiteral(value=v))


def _bool_lit(v: bool) -> LiteralPattern:
    return LiteralPattern(value=BoolLiteral(value=v))


def _float_lit(v: float) -> LiteralPattern:
    return LiteralPattern(value=FloatLiteral(value=v))


def _ident(name: str) -> IdentPattern:
    return IdentPattern(name=name)


def _wild() -> WildcardPattern:
    return WildcardPattern()


def _ctor(name: str, *args) -> ConstructorPattern:
    return ConstructorPattern(name=name, args=list(args))


def _or(*alts) -> OrPattern:
    return OrPattern(alternatives=list(alts))


def _open_ctx() -> TypeContext:
    return TypeContext(is_closed=False)


def _bool_ctx() -> TypeContext:
    return TypeContext(
        is_closed=True,
        all_constructors=[ConstructorInfo("true", 0), ConstructorInfo("false", 0)],
    )


def _option_ctx() -> TypeContext:
    return TypeContext(
        is_closed=True,
        all_constructors=[ConstructorInfo("Some", 1), ConstructorInfo("None", 0)],
        sub_contexts={"Some": [_open_ctx()]},
    )


def _enum_abc() -> TypeContext:
    return TypeContext(
        is_closed=True,
        all_constructors=[
            ConstructorInfo("A", 0),
            ConstructorInfo("B", 0),
            ConstructorInfo("C", 0),
        ],
    )


# ======================================================================
# Pattern classification
# ======================================================================


class TestPatternClassification:
    def test_wildcard_is_wildcard(self):
        from mapanare.pattern_matching import _is_wildcard

        assert _is_wildcard(_wild())

    def test_ident_is_wildcard_without_variants(self):
        from mapanare.pattern_matching import _is_wildcard

        assert _is_wildcard(_ident("x"))

    def test_ident_is_not_wildcard_when_variant(self):
        from mapanare.pattern_matching import _is_wildcard

        assert not _is_wildcard(_ident("Some"), {"Some", "None"})

    def test_constructor_not_wildcard(self):
        from mapanare.pattern_matching import _is_wildcard

        assert not _is_wildcard(_ctor("Some", _wild()))

    def test_get_constructor_tag_for_ctor(self):
        from mapanare.pattern_matching import _get_constructor_tag

        assert _get_constructor_tag(_ctor("Some", _wild())) == "Some"

    def test_get_constructor_tag_for_literal(self):
        from mapanare.pattern_matching import _get_constructor_tag

        assert _get_constructor_tag(_int_lit(42)) == "42"

    def test_get_constructor_tag_for_wildcard_is_none(self):
        from mapanare.pattern_matching import _get_constructor_tag

        assert _get_constructor_tag(_wild()) is None

    def test_get_constructor_tag_for_variant_ident(self):
        from mapanare.pattern_matching import _get_constructor_tag

        assert _get_constructor_tag(_ident("A"), {"A", "B"}) == "A"

    def test_literal_tag_int(self):
        from mapanare.pattern_matching import _literal_tag

        assert _literal_tag(_int_lit(42).value) == "42"

    def test_literal_tag_bool(self):
        from mapanare.pattern_matching import _literal_tag

        # BoolLiteral.value is a Python bool; _literal_tag uses the
        # "true"/"false" check on BoolLiteral specifically
        tag_t = _literal_tag(_bool_lit(True).value)
        tag_f = _literal_tag(_bool_lit(False).value)
        assert tag_t in ("true", "True")
        assert tag_f in ("false", "False")

    def test_literal_tag_string(self):
        from mapanare.pattern_matching import _literal_tag

        assert _literal_tag(_str_lit("hello").value) == "hello"

    def test_literal_tag_float(self):
        from mapanare.pattern_matching import _literal_tag

        assert _literal_tag(_float_lit(3.14).value) == "3.14"

    def test_constructor_arity(self):
        from mapanare.pattern_matching import _constructor_arity

        assert _constructor_arity(_ctor("Some", _wild())) == 1
        assert _constructor_arity(_ctor("Pair", _wild(), _wild())) == 2
        assert _constructor_arity(_ctor("None")) == 0
        assert _constructor_arity(_wild()) == 0


# ======================================================================
# Specialize + Default matrix
# ======================================================================


class TestSpecialize:
    def test_specialize_literal(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_int_lit(1)], action_idx=0),
                PatternRow(patterns=[_int_lit(2)], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_open_ctx()],
        )
        s = specialize(matrix, 0, "1", 0)
        assert len(s.rows) == 2  # literal 1 + wildcard
        assert s.rows[0].action_idx == 0
        assert s.rows[1].action_idx == 2

    def test_specialize_constructor(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_ctor("Some", _int_lit(1))], action_idx=0),
                PatternRow(patterns=[_ctor("None")], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_option_ctx()],
        )
        s = specialize(matrix, 0, "Some", 1)
        assert len(s.rows) == 2  # Some(1) + wildcard
        assert s.rows[0].action_idx == 0
        assert s.rows[1].action_idx == 2

    def test_specialize_variant_ident(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_ident("A")], action_idx=0),
                PatternRow(patterns=[_ident("B")], action_idx=1),
            ],
            type_contexts=[_enum_abc()],
        )
        s = specialize(matrix, 0, "A", 0)
        assert len(s.rows) == 1
        assert s.rows[0].action_idx == 0

    def test_default_matrix_keeps_wildcards(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_int_lit(1)], action_idx=0),
                PatternRow(patterns=[_wild()], action_idx=1),
            ],
            type_contexts=[_open_ctx()],
        )
        d = default_matrix(matrix, 0)
        assert len(d.rows) == 1
        assert d.rows[0].action_idx == 1

    def test_default_matrix_empty(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_int_lit(1)], action_idx=0),
                PatternRow(patterns=[_int_lit(2)], action_idx=1),
            ],
            type_contexts=[_open_ctx()],
        )
        d = default_matrix(matrix, 0)
        assert len(d.rows) == 0


# ======================================================================
# Or-pattern expansion
# ======================================================================


class TestOrPatterns:
    def test_expand_simple(self):
        row = PatternRow(patterns=[_or(_int_lit(1), _int_lit(2))], action_idx=0)
        matrix = PatternMatrix(rows=[row], type_contexts=[_open_ctx()])
        expanded = expand_or_patterns(matrix)
        assert len(expanded.rows) == 2
        assert expanded.rows[0].action_idx == 0
        assert expanded.rows[1].action_idx == 0

    def test_expand_nested(self):
        row = PatternRow(
            patterns=[_or(_int_lit(1), _or(_int_lit(2), _int_lit(3)))],
            action_idx=0,
        )
        matrix = PatternMatrix(rows=[row], type_contexts=[_open_ctx()])
        expanded = expand_or_patterns(matrix)
        assert len(expanded.rows) == 3

    def test_no_or_is_identity(self):
        rows = [PatternRow(patterns=[_int_lit(1)], action_idx=0)]
        matrix = PatternMatrix(rows=rows, type_contexts=[_open_ctx()])
        expanded = expand_or_patterns(matrix)
        assert len(expanded.rows) == 1


# ======================================================================
# Column selection
# ======================================================================


class TestColumnSelection:
    def test_leftmost_tiebreak(self):
        matrix = PatternMatrix(
            rows=[PatternRow(patterns=[_wild(), _wild()], action_idx=0)],
            type_contexts=[_open_ctx(), _open_ctx()],
        )
        assert select_column(matrix) == 0

    def test_most_constructors_wins(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_wild(), _int_lit(1)], action_idx=0),
                PatternRow(patterns=[_wild(), _int_lit(2)], action_idx=1),
            ],
            type_contexts=[_open_ctx(), _open_ctx()],
        )
        assert select_column(matrix) == 1


# ======================================================================
# Decision tree building
# ======================================================================


class TestBuildDecisionTree:
    def test_single_wildcard(self):
        matrix = PatternMatrix(
            rows=[PatternRow(patterns=[_wild()], action_idx=0)],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert isinstance(tree, DTLeaf)
        assert tree.action_idx == 0

    def test_single_ident(self):
        matrix = PatternMatrix(
            rows=[PatternRow(patterns=[_ident("x")], action_idx=0)],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert isinstance(tree, DTLeaf)
        assert tree.action_idx == 0

    def test_empty_matrix_is_fail(self):
        matrix = PatternMatrix(rows=[], type_contexts=[_open_ctx()])
        tree = build_decision_tree(matrix)
        assert isinstance(tree, DTFail)

    def test_literal_switch(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_int_lit(1)], action_idx=0),
                PatternRow(patterns=[_int_lit(2)], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert isinstance(tree, DTSwitch)
        assert len(tree.cases) == 2
        assert tree.default is not None

    def test_bool_exhaustive(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_bool_lit(True)], action_idx=0),
                PatternRow(patterns=[_bool_lit(False)], action_idx=1),
            ],
            type_contexts=[_bool_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert isinstance(tree, DTSwitch)
        assert not has_any_fail(tree)

    def test_bool_not_exhaustive(self):
        matrix = PatternMatrix(
            rows=[PatternRow(patterns=[_bool_lit(True)], action_idx=0)],
            type_contexts=[_bool_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert has_any_fail(tree)

    def test_enum_all_variants_exhaustive(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_ident("A")], action_idx=0),
                PatternRow(patterns=[_ident("B")], action_idx=1),
                PatternRow(patterns=[_ident("C")], action_idx=2),
            ],
            type_contexts=[_enum_abc()],
        )
        tree = build_decision_tree(matrix)
        assert not has_any_fail(tree)

    def test_option_exhaustive(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_ctor("Some", _wild())], action_idx=0),
                PatternRow(patterns=[_ctor("None")], action_idx=1),
            ],
            type_contexts=[_option_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert not has_any_fail(tree)

    def test_option_missing_none(self):
        matrix = PatternMatrix(
            rows=[PatternRow(patterns=[_ctor("Some", _wild())], action_idx=0)],
            type_contexts=[_option_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert has_any_fail(tree)

    def test_or_pattern_exhaustive(self):
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_or(_ident("A"), _ident("B"))], action_idx=0),
                PatternRow(patterns=[_ident("C")], action_idx=1),
            ],
            type_contexts=[_enum_abc()],
        )
        tree = build_decision_tree(matrix)
        assert not has_any_fail(tree)


# ======================================================================
# P6: Unreachable arm detection (CARRY_FORWARD P6)
# ======================================================================


class TestUnreachableArms:
    """v4.79.0: >=5 tests for the unreachable-arm warning path."""

    def test_wildcard_makes_subsequent_unreachable(self):
        """Wildcard arm followed by another arm → arm 1 is unreachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_wild()], action_idx=0),
                PatternRow(patterns=[_int_lit(1)], action_idx=1),
            ],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 2)
        assert 1 in unreachable
        assert 0 not in unreachable

    def test_duplicate_literal_unreachable(self):
        """Two identical literal arms → second is unreachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_int_lit(42)], action_idx=0),
                PatternRow(patterns=[_int_lit(42)], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 3)
        assert 1 in unreachable
        assert 0 not in unreachable
        assert 2 not in unreachable

    def test_all_variants_then_wildcard_unreachable(self):
        """Match covers all enum variants, then has a wildcard → wildcard unreachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_ident("A")], action_idx=0),
                PatternRow(patterns=[_ident("B")], action_idx=1),
                PatternRow(patterns=[_ident("C")], action_idx=2),
                PatternRow(patterns=[_wild()], action_idx=3),
            ],
            type_contexts=[_enum_abc()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 4)
        assert 3 in unreachable
        assert 0 not in unreachable

    def test_no_unreachable_when_all_needed(self):
        """Each arm matches different values → none unreachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_int_lit(1)], action_idx=0),
                PatternRow(patterns=[_int_lit(2)], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 3)
        assert len(unreachable) == 0

    def test_multiple_wildcards_only_first_reachable(self):
        """Multiple wildcard arms → only the first is reachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_wild()], action_idx=0),
                PatternRow(patterns=[_wild()], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_open_ctx()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 3)
        assert 1 in unreachable
        assert 2 in unreachable
        assert 0 not in unreachable

    def test_or_pattern_covers_variant_makes_later_unreachable(self):
        """Or-pattern covers a variant, then that variant appears again → unreachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_or(_ident("A"), _ident("B"))], action_idx=0),
                PatternRow(patterns=[_ident("A")], action_idx=1),
                PatternRow(patterns=[_ident("C")], action_idx=2),
            ],
            type_contexts=[_enum_abc()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 3)
        assert 1 in unreachable

    def test_bool_true_then_false_then_wildcard(self):
        """Bool exhaustive match + trailing wildcard → wildcard unreachable."""
        matrix = PatternMatrix(
            rows=[
                PatternRow(patterns=[_bool_lit(True)], action_idx=0),
                PatternRow(patterns=[_bool_lit(False)], action_idx=1),
                PatternRow(patterns=[_wild()], action_idx=2),
            ],
            type_contexts=[_bool_ctx()],
        )
        tree = build_decision_tree(matrix)
        unreachable = find_unreachable_arms(tree, 3)
        assert 2 in unreachable


# ======================================================================
# P6: Unreachable arm integration (via semantic checker)
# ======================================================================


class TestUnreachableArmIntegration:
    """Verify unreachable-arm warnings through the full semantic checker."""

    def _check_warnings(self, source: str) -> list[str]:
        from mapanare.parser import parse
        from mapanare.semantic import check

        program = parse(source, filename="test.mn")
        errors = check(program, filename="test.mn")
        return [e.message for e in errors if "unreachable" in e.message.lower()]

    def test_wildcard_then_literal_warns(self):
        source = """
enum Color { Red, Green, Blue }
fn main() {
    let c: Color = Red
    match c {
        _ => print("any"),
        Red => print("red")
    }
}
"""
        warnings = self._check_warnings(source)
        assert len(warnings) >= 1
        assert "unreachable" in warnings[0].lower()

    def test_all_variants_then_wildcard_warns(self):
        source = """
enum Dir { Up, Down }
fn main() {
    let d: Dir = Up
    match d {
        Up => print("up"),
        Down => print("down"),
        _ => print("other")
    }
}
"""
        warnings = self._check_warnings(source)
        assert len(warnings) >= 1


# ======================================================================
# Witness display
# ======================================================================


class TestWitnessDisplay:
    def test_display_wildcard(self):
        assert display_witness(_wild()) == "_"

    def test_display_constructor_no_args(self):
        assert display_witness(_ctor("None")) == "None"

    def test_display_constructor_with_args(self):
        assert display_witness(_ctor("Some", _wild())) == "Some(_)"

    def test_display_ident(self):
        assert display_witness(_ident("x")) == "x"

    def test_display_literal(self):
        assert display_witness(_int_lit(42)) == "42"

    def test_display_or(self):
        result = display_witness(_or(_int_lit(1), _int_lit(2)))
        assert "1" in result and "2" in result


# ======================================================================
# Witness building from DTSwitch
# ======================================================================


class TestWitnessBuilding:
    def test_fail_witness_collected(self):
        tree = DTFail(witness=_wild())
        witnesses = collect_fail_witnesses(tree)
        assert len(witnesses) == 1

    def test_no_fail_no_witnesses(self):
        tree = DTLeaf(action_idx=0)
        witnesses = collect_fail_witnesses(tree)
        assert len(witnesses) == 0

    def test_witness_from_option_missing_none(self):
        matrix = PatternMatrix(
            rows=[PatternRow(patterns=[_ctor("Some", _wild())], action_idx=0)],
            type_contexts=[_option_ctx()],
        )
        tree = build_decision_tree(matrix)
        assert isinstance(tree, DTSwitch)
        witness = build_witness_for_switch(tree, _option_ctx())
        assert witness is not None
        assert display_witness(witness) == "None"

    def test_has_any_fail_true(self):
        assert has_any_fail(DTFail(witness=_wild()))

    def test_has_any_fail_false(self):
        assert not has_any_fail(DTLeaf(action_idx=0))

    def test_has_any_fail_nested(self):
        tree = DTSwitch(
            column_idx=0,
            cases=[("A", DTLeaf(action_idx=0))],
            default=DTFail(witness=_wild()),
        )
        assert has_any_fail(tree)
