"""Phase 5 — Pipe definition codegen tests for LLVM backend.

Tests verify that pipe definitions compile to agent spawn chain functions
on both LLVM emitters.
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _compile_ast(source: str) -> str:
    return _compile_to_llvm_ir(source, "test.mn", use_mir=False)


def _compile_mir(source: str) -> str:
    return _compile_to_llvm_ir(source, "test.mn", use_mir=True)


_PIPE_SOURCE = textwrap.dedent("""\
    agent Doubler {
        input messages: Int
        output results: Int
        fn handle(x: Int) -> Int {
            return x * 2
        }
    }

    agent Adder {
        input messages: Int
        output results: Int
        fn handle(x: Int) -> Int {
            return x + 1
        }
    }

    pipe Transform {
        Doubler |> Adder
    }

    fn main() {
        println(0)
    }
""")


class TestPipeDef:
    def test_pipe_def_ast_emits_function(self) -> None:
        ir = _compile_ast(_PIPE_SOURCE)
        assert "Transform" in ir
        assert "mapanare_agent_spawn" in ir or "mapanare_agent_new" in ir

    def test_pipe_def_mir_emits_function(self) -> None:
        ir = _compile_mir(_PIPE_SOURCE)
        assert "Transform" in ir
        assert "mapanare_agent_spawn" in ir or "mapanare_agent_new" in ir

    def test_single_stage_pipe_ast(self) -> None:
        src = textwrap.dedent("""\
            agent Echo {
                input messages: Int
                output results: Int
                fn handle(x: Int) -> Int {
                    return x
                }
            }
            pipe Single {
                Echo
            }
            fn main() {
                println(0)
            }
        """)
        ir = _compile_ast(src)
        assert "Single" in ir

    def test_single_stage_pipe_mir(self) -> None:
        src = textwrap.dedent("""\
            agent Echo {
                input messages: Int
                output results: Int
                fn handle(x: Int) -> Int {
                    return x
                }
            }
            pipe Single {
                Echo
            }
            fn main() {
                println(0)
            }
        """)
        ir = _compile_mir(src)
        assert "Single" in ir
