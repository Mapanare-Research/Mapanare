"""Retained parent plans reject escaping or mixed-origin borrowed Strings."""

import pytest

from mapanare.lower import lower
from mapanare.map_views import retained_map_views
from mapanare.parser import parse
from mapanare.types import TypeKind


@pytest.mark.parametrize(
    "consumer,accepted",
    [
        ("print(saved)", True),
        ("print(len(saved))", True),
        ('print(saved == "value")', True),
        ("let copy = saved\n    print(copy)", True),
        ("capture(saved)", False),
        ("let box = [saved]", False),
        ("return saved", False),
        ("saved = input", False),
        ('saved = "prefix" + saved', False),
    ],
)
def test_string_view_consumers(consumer: str, accepted: bool) -> None:
    fn = lower(parse("""
fn main(input: String):
    let values: Map<Int, String> = #{1: "value"}
    let mut saved = ""
    saved = values[1]
    """ + consumer + "\n")).functions[0]
    maps = {
        inst.dest.name
        for block in fn.blocks
        for inst in block.instructions
        if getattr(inst, "dest", None) is not None and inst.dest.ty.kind == TypeKind.MAP
    }
    plan = retained_map_views(fn, maps)
    assert (plan is not None) is accepted
    if plan is not None:
        assert "%saved" in plan.strings


def test_cursor_and_retained_key_plan() -> None:
    fn = lower(parse("""
fn main():
    let values = #{"key": 1}
    let mut saved = ""
    for key in values:
        saved = key
    print(saved)
""")).functions[0]
    maps = {
        inst.dest.name
        for block in fn.blocks
        for inst in block.instructions
        if getattr(inst, "dest", None) is not None and inst.dest.ty.kind == TypeKind.MAP
    }
    plan = retained_map_views(fn, maps)
    assert plan is not None and plan.cursors and "%saved" in plan.strings
