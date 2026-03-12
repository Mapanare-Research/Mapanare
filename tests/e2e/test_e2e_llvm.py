"""End-to-end tests for LLVM backend — Phase 3.3, Task 5.

Since the LLVM backend cannot easily produce runnable executables in CI
(requires linking with the C runtime), these tests verify that:
1. Source code compiles all the way to valid LLVM IR without errors
2. The IR contains expected function definitions and runtime calls
3. Agent codegen produces the correct runtime function calls

For actual execution tests, see test_e2e.py (Python backend).
"""

from __future__ import annotations

import textwrap

from mapanare.cli import _compile_to_llvm_ir


def _to_llvm_ir(source: str, filename: str = "test.mn") -> str:
    """Compile Mapanare source to LLVM IR string."""
    return _compile_to_llvm_ir(source, filename, use_mir=False)


# ── LLVM: basic functions and arithmetic ─────────────────────────────────────


class TestLLVMBasicCodegen:
    """LLVM e2e: basic features compile to valid IR."""

    def test_hello_world(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                print("Hello, LLVM!")
            }
        """)
        ir = _to_llvm_ir(source)
        assert "define" in ir
        assert '@"main"' in ir or '@"main"' in ir

    def test_integer_arithmetic(self) -> None:
        source = textwrap.dedent("""\
            fn add(a: Int, b: Int) -> Int {
                return a + b
            }
            fn main() {
                let x = add(10, 20)
                print(x)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "add" in ir.lower()
        assert "i64" in ir

    def test_float_arithmetic(self) -> None:
        source = textwrap.dedent("""\
            fn mul(a: Float, b: Float) -> Float {
                return a * b
            }
            fn main() {
                let x = mul(2.5, 4.0)
                print(x)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "double" in ir
        assert "fmul" in ir

    def test_string_operations(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let a: String = "hello"
                let b: String = " world"
                let c: String = a + b
                print(c)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "mn_str" in ir or "__mn_str" in ir

    def test_boolean_comparison(self) -> None:
        source = textwrap.dedent("""\
            fn check(x: Int) -> Int {
                if x > 3 {
                    return 1
                } else {
                    return 0
                }
            }
            fn main() {
                print(check(5))
            }
        """)
        ir = _to_llvm_ir(source)
        assert "icmp" in ir
        assert "br" in ir


# ── LLVM: control flow ──────────────────────────────────────────────────────


class TestLLVMControlFlow:
    """LLVM e2e: control flow compiles correctly."""

    def test_while_loop(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut i: Int = 0
                while i < 10 {
                    i += 1
                }
                print(i)
            }
        """)
        ir = _to_llvm_ir(source)
        # While loop should produce comparison + conditional branch
        assert "icmp" in ir
        assert "br" in ir

    def test_for_range_loop(self) -> None:
        source = textwrap.dedent("""\
            fn main() {
                let mut sum: Int = 0
                for i in 0..10 {
                    sum += i
                }
                print(sum)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "icmp" in ir

    def test_match_expression(self) -> None:
        source = textwrap.dedent("""\
            fn classify(n: Int) -> Int {
                match n {
                    0 => { return 0 },
                    1 => { return 1 },
                    _ => { return 99 }
                }
                return -1
            }
            fn main() {
                print(classify(1))
            }
        """)
        ir = _to_llvm_ir(source)
        assert "classify" in ir

    def test_recursion(self) -> None:
        source = textwrap.dedent("""\
            fn factorial(n: Int) -> Int {
                if n <= 1 {
                    return 1
                }
                return n * factorial(n - 1)
            }
            fn main() {
                print(factorial(5))
            }
        """)
        ir = _to_llvm_ir(source)
        assert "factorial" in ir
        # Recursive call should be present
        assert "call i64" in ir

    def test_nested_if_else(self) -> None:
        source = textwrap.dedent("""\
            fn classify(n: Int) -> Int {
                if n > 0 {
                    if n > 100 {
                        return 2
                    } else {
                        return 1
                    }
                } else {
                    return 0
                }
            }
            fn main() {
                print(classify(50))
            }
        """)
        ir = _to_llvm_ir(source)
        assert "classify" in ir
        # Multiple branch blocks
        assert ir.count("br") >= 3


# ── LLVM: agent codegen ─────────────────────────────────────────────────────


class TestLLVMAgentCodegen:
    """LLVM e2e: agent spawn/send/sync compile to correct runtime calls."""

    def test_agent_spawn_send_sync(self) -> None:
        source = textwrap.dedent("""\
            agent Doubler {
                input val: Int
                output result: Int

                fn handle(val: Int) -> Int {
                    return val * 2
                }
            }

            fn main() {
                let d = spawn Doubler()
                d.val <- 21
                let r = sync d.result
                print(r)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "agent_new" in ir
        assert "agent_spawn" in ir
        assert "agent_send" in ir
        assert "agent_recv" in ir

    def test_agent_handler_generated(self) -> None:
        source = textwrap.dedent("""\
            agent Echo {
                input msg: String
                output reply: String

                fn handle(msg: String) -> String {
                    return msg
                }
            }

            fn main() {
                let e = spawn Echo()
                e.msg <- "test"
                let r = sync e.reply
                print(r)
            }
        """)
        ir = _to_llvm_ir(source)
        # Handler wrapper function should be generated
        assert "Echo" in ir
        assert "agent_new" in ir

    def test_multiple_agents(self) -> None:
        source = textwrap.dedent("""\
            agent Add10 {
                input val: Int
                output result: Int

                fn handle(val: Int) -> Int {
                    return val + 10
                }
            }

            agent Double {
                input val: Int
                output result: Int

                fn handle(val: Int) -> Int {
                    return val * 2
                }
            }

            fn main() {
                let a = spawn Add10()
                let d = spawn Double()
                a.val <- 5
                let mid = sync a.result
                d.val <- mid
                let r = sync d.result
                print(r)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "Add10" in ir
        assert "Double" in ir
        # Two agent_new calls
        assert ir.count("agent_new") >= 2


# ── LLVM: multiple functions ────────────────────────────────────────────────


class TestLLVMMultipleFunctions:
    """LLVM e2e: multi-function programs compile correctly."""

    def test_function_call_chain(self) -> None:
        source = textwrap.dedent("""\
            fn double(x: Int) -> Int {
                return x * 2
            }
            fn add_one(x: Int) -> Int {
                return x + 1
            }
            fn main() {
                let r = double(add_one(5))
                print(r)
            }
        """)
        ir = _to_llvm_ir(source)
        assert "double" in ir
        assert "add_one" in ir

    def test_many_parameters(self) -> None:
        source = textwrap.dedent("""\
            fn sum4(a: Int, b: Int, c: Int, d: Int) -> Int {
                return a + b + c + d
            }
            fn main() {
                print(sum4(1, 2, 3, 4))
            }
        """)
        ir = _to_llvm_ir(source)
        assert "sum4" in ir

    def test_void_function(self) -> None:
        source = textwrap.dedent("""\
            fn say_hello() {
                print("hi")
            }
            fn main() {
                say_hello()
            }
        """)
        ir = _to_llvm_ir(source)
        assert "say_hello" in ir
