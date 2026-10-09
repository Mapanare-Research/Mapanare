"""String merges require ownership of every possible nonliteral parent."""

import pytest

from mapanare.lower import lower
from mapanare.map_shared import shared_map_aliases
from mapanare.parser import parse


@pytest.mark.parametrize("alternative", ["other[1]", '"literal"'])
def test_string_merge_proves_parent_component(alternative: str) -> None:
    fn = lower(
        parse(
            """
fn main(n: Int):
    let values = #{1: "value"}
    let other = #{1: "other"}
    let selected: String = match n { 0 => values[1], _ => """
            + alternative
            + """ }
    print(selected)
"""
        )
    ).functions[0]
    owners = shared_map_aliases(fn, set(), set())
    assert "%values" in owners
    if alternative == "other[1]":
        assert "%other" in owners


@pytest.mark.parametrize(
    "alternative,consumer",
    [
        ("input", "print(selected)"),
        ("unknown()", "print(selected)"),
        ('"literal"', "capture(selected)"),
        ('"literal"', "return selected"),
        ('"literal"', "let box = [selected]"),
    ],
)
def test_uncertain_merged_view_rejects_its_parent(alternative: str, consumer: str) -> None:
    fn = lower(
        parse(
            """
fn main(n: Int, input: String):
    let values = #{1: "value"}
    let selected: String = match n { 0 => values[1], _ => """
            + alternative
            + """ }
    """
            + consumer
            + "\n"
        )
    ).functions[0]
    assert "%values" not in shared_map_aliases(fn, set(), set())
