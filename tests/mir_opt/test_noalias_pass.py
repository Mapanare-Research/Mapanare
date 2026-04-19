"""Tests for E3 parameter-level noalias pass (v4.147.0).

Verifies the escape-analysis precision rules in mark_noalias_params:
- Fresh alloca / non-escaping params get marked noalias_ok
- Recursive self-call params are NOT marked
- Closure-captured params are NOT marked
- Agent-sent params are NOT marked
- Same-SSA-passed-twice at call site is NOT marked
- Signal/Stream/Agent-typed params are NOT marked
- Scalar params are NOT marked (noalias is meaningless for non-pointers)
"""

from __future__ import annotations

from mapanare.mir import (
    AgentSend,
    BasicBlock,
    Call,
    ClosureCreate,
    FieldSet,
    IndexSet,
    ListPush,
    MIRFunction,
    MIRModule,
    MIRParam,
    MIRType,
    Return,
    Value,
    mir_int,
)
from mapanare.mir_opt import mark_noalias_params
from mapanare.types import TypeInfo, TypeKind


def _v(name: str, ty: MIRType | None = None) -> Value:
    return Value(name=name, ty=ty or mir_int())


def _list_ty() -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.LIST))


def _signal_ty() -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.SIGNAL))


def _stream_ty() -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.STREAM))


def _agent_ty() -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.AGENT))


def _struct_ty() -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.STRUCT))


def _fn_ty() -> MIRType:
    return MIRType(TypeInfo(kind=TypeKind.FN))


class TestEscapeAnalysisPrecision:
    """Test the precision rules of the noalias escape analysis."""

    def test_non_escaping_list_param_marked(self) -> None:
        """A List param that doesn't escape should be marked noalias_ok."""
        fn = MIRFunction(
            name="process",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        # Just read the param (IndexGet would be here in real code)
                        # and return a scalar — param doesn't escape
                        Return(val=_v("%result")),
                    ],
                )
            ],
        )
        caller = MIRFunction(
            name="main",
            params=[],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        Call(dest=_v("%r"), fn_name="process", args=[_v("%my_list", _list_ty())]),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn, caller])
        count = mark_noalias_params(module)
        assert count == 1
        assert "noalias_ok" in fn.params[0].attrs

    def test_returned_param_not_marked(self) -> None:
        """A param that is returned escapes — must NOT be marked."""
        fn = MIRFunction(
            name="identity",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%data", _list_ty()))],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0
        assert "noalias_ok" not in fn.params[0].attrs

    def test_recursive_self_call_not_marked(self) -> None:
        """A param passed to a recursive self-call must NOT be marked."""
        fn = MIRFunction(
            name="recurse",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        Call(
                            dest=_v("%r"),
                            fn_name="recurse",
                            args=[_v("%data", _list_ty())],
                        ),
                        Return(val=_v("%r")),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_closure_captured_param_not_marked(self) -> None:
        """A param captured by a closure escapes — must NOT be marked."""
        fn = MIRFunction(
            name="make_closure",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        ClosureCreate(
                            dest=_v("%clos"),
                            fn_name="lambda1",
                            captures=[_v("%data", _list_ty())],
                        ),
                        Return(val=_v("%clos")),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_field_stored_param_not_marked(self) -> None:
        """A param stored into a struct field escapes — must NOT be marked."""
        fn = MIRFunction(
            name="store_it",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        FieldSet(
                            obj=_v("%obj", _struct_ty()),
                            field_name="items",
                            val=_v("%data", _list_ty()),
                        ),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_same_ssa_passed_twice_not_marked(self) -> None:
        """If a call site passes the same SSA name for two params, neither
        should be marked (they alias at the call site)."""
        fn = MIRFunction(
            name="compare",
            params=[
                MIRParam(name="a", ty=_list_ty()),
                MIRParam(name="b", ty=_list_ty()),
            ],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        # Caller passes same list for both params
        caller = MIRFunction(
            name="main",
            params=[],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        Call(
                            dest=_v("%r"),
                            fn_name="compare",
                            args=[
                                _v("%same_list", _list_ty()),
                                _v("%same_list", _list_ty()),
                            ],
                        ),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn, caller])
        count = mark_noalias_params(module)
        assert count == 0

    def test_two_distinct_allocas_marked(self) -> None:
        """Two List params with distinct SSA names at all call sites
        should both be marked noalias_ok."""
        fn = MIRFunction(
            name="merge",
            params=[
                MIRParam(name="left", ty=_list_ty()),
                MIRParam(name="right", ty=_list_ty()),
            ],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        caller = MIRFunction(
            name="main",
            params=[],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        Call(
                            dest=_v("%r"),
                            fn_name="merge",
                            args=[
                                _v("%list_a", _list_ty()),
                                _v("%list_b", _list_ty()),
                            ],
                        ),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn, caller])
        count = mark_noalias_params(module)
        assert count == 2
        assert "noalias_ok" in fn.params[0].attrs
        assert "noalias_ok" in fn.params[1].attrs

    def test_signal_param_excluded(self) -> None:
        """Signal-typed params are excluded even if they don't escape."""
        fn = MIRFunction(
            name="read_signal",
            params=[MIRParam(name="sig", ty=_signal_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_stream_param_excluded(self) -> None:
        """Stream-typed params are excluded even if they don't escape."""
        fn = MIRFunction(
            name="read_stream",
            params=[MIRParam(name="s", ty=_stream_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_agent_param_excluded(self) -> None:
        """Agent-typed params are excluded even if they don't escape."""
        fn = MIRFunction(
            name="use_agent",
            params=[MIRParam(name="ag", ty=_agent_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_scalar_param_not_marked(self) -> None:
        """Int/Float/Bool params are never marked (noalias is meaningless
        for non-pointer types)."""
        fn = MIRFunction(
            name="add",
            params=[
                MIRParam(name="a", ty=mir_int()),
                MIRParam(name="b", ty=mir_int()),
            ],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_agent_sent_param_not_marked(self) -> None:
        """A param sent to an agent escapes — must NOT be marked."""
        fn = MIRFunction(
            name="send_data",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        AgentSend(
                            agent=_v("%agent", _agent_ty()),
                            channel="input",
                            val=_v("%data", _list_ty()),
                        ),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_list_pushed_param_not_marked(self) -> None:
        """A param pushed into a list escapes — must NOT be marked."""
        fn = MIRFunction(
            name="collect",
            params=[MIRParam(name="item", ty=_struct_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        ListPush(
                            dest=_v("%updated"),
                            list_val=_v("%container", _list_ty()),
                            element=_v("%item", _struct_ty()),
                        ),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_index_stored_param_not_marked(self) -> None:
        """A param stored via IndexSet escapes — must NOT be marked."""
        fn = MIRFunction(
            name="replace",
            params=[MIRParam(name="item", ty=_struct_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[
                        IndexSet(
                            obj=_v("%arr", _list_ty()),
                            index=_v("%idx"),
                            val=_v("%item", _struct_ty()),
                        ),
                        Return(val=None),
                    ],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_main_function_skipped(self) -> None:
        """main() params are never marked."""
        fn = MIRFunction(
            name="main",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=None)],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count = mark_noalias_params(module)
        assert count == 0

    def test_idempotent(self) -> None:
        """Running the pass twice should not double-mark."""
        fn = MIRFunction(
            name="process",
            params=[MIRParam(name="data", ty=_list_ty())],
            blocks=[
                BasicBlock(
                    label="entry",
                    instructions=[Return(val=_v("%result"))],
                )
            ],
        )
        module = MIRModule(functions=[fn])
        count1 = mark_noalias_params(module)
        count2 = mark_noalias_params(module)
        assert count1 == 1
        assert count2 == 0  # already marked, no new marks
