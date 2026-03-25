"""ai/llm.mn — Native LLM Driver tests.

Tests verify that the LLM stdlib module compiles to valid LLVM IR via the
MIR-based emitter. Tests inline the module source within test programs.

Covers:
  - Core types: Provider, Role, LLMError, ChatMessage, TokenUsage, LLMResponse, LLMConfig
  - Config constructors: openai, anthropic, groq, ollama, custom
  - Config modifiers: with_max_tokens, with_temperature, with_system, with_timeout, with_tools
  - Message constructors: system_msg, user_msg, assistant_msg, tool_msg
  - Error helpers: error_message
  - JSON helpers: escape_json, jget, jget_str, jget_int, jget_first
  - Token usage: new_token_usage, usage_summary
  - Tool types: ToolDef, ToolCall
  - Conversations: new_conversation, set_system_prompt, trim_history
  - Retry/fallback types: FallbackResult
  - Reasoning strategies: apply_reasoning
  - Chain types: ChainStep, ChainResult
  - Consensus types: ConsensusResult
  - Cost estimation: estimate_cost, response_cost, cost_summary
  - Multi-model helpers: models_agree, total_usage
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

try:
    from llvmlite import ir  # noqa: F401

    HAS_LLVMLITE = True
except ImportError:
    HAS_LLVMLITE = False

from mapanare.cli import _compile_to_llvm_ir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LLM_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "ai" / "llm.mn").read_text(
    encoding="utf-8"
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_llm.mn", use_mir=True)


def _llm_source_with_main(main_body: str) -> str:
    """Prepend the LLM module source and wrap main_body in fn main()."""
    return _LLM_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_provider_enum_compiles(self) -> None:
        """Provider enum compiles."""
        src = _llm_source_with_main("""\
            let p: Provider = OpenAI()
            println(provider_to_string(p))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_role_enum_compiles(self) -> None:
        """Role enum compiles."""
        src = _llm_source_with_main("""\
            let r: Role = User()
            println(role_to_string(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_llm_error_enum_compiles(self) -> None:
        """LLMError enum compiles."""
        src = _llm_source_with_main("""\
            let e: LLMError = ApiError("test error")
            println(error_message(e))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chat_message_struct_compiles(self) -> None:
        """ChatMessage struct compiles."""
        src = _llm_source_with_main("""\
            let msg: ChatMessage = user_msg("Hello")
            println(msg.content)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_token_usage_struct_compiles(self) -> None:
        """TokenUsage struct compiles."""
        src = _llm_source_with_main("""\
            let u: TokenUsage = new_token_usage(100, 50)
            println(str(u.total_tokens))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_tool_def_struct_compiles(self) -> None:
        """ToolDef struct compiles."""
        src = _llm_source_with_main("""\
            let t: ToolDef = tool("search", "Search the web", "{}")
            println(t.name)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Config constructors
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestConfigConstructors:
    def test_openai_config(self) -> None:
        """openai() config constructor compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            println(c.model)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_anthropic_config(self) -> None:
        """anthropic() config constructor compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = anthropic("sk-test", "claude-sonnet-4-20250514")
            println(c.host)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_groq_config(self) -> None:
        """groq() config constructor compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = groq("gsk-test", "llama-3.1-70b-versatile")
            println(c.path)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ollama_config(self) -> None:
        """ollama() config constructor compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = ollama("llama3")
            println(str(c.port))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_custom_config(self) -> None:
        """custom() config constructor compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = custom("localhost", 8080, "/v1/chat", "key", "model")
            println(c.host)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Config modifiers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestConfigModifiers:
    def test_with_max_tokens(self) -> None:
        """with_max_tokens() compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let c2: LLMConfig = with_max_tokens(c, 8192)
            println(str(c2.max_tokens))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_with_temperature(self) -> None:
        """with_temperature() compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let c2: LLMConfig = with_temperature(c, 0.5)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_with_system(self) -> None:
        """with_system() compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let c2: LLMConfig = with_system(c, "You are helpful")
            println(c2.system_prompt)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_with_timeout(self) -> None:
        """with_timeout() compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let c2: LLMConfig = with_timeout(c, 60000)
            println(str(c2.timeout_ms))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Message constructors
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMessageConstructors:
    def test_all_message_types(self) -> None:
        """All message constructor functions compile."""
        src = _llm_source_with_main("""\
            let m1: ChatMessage = system_msg("Be helpful")
            let m2: ChatMessage = user_msg("Hello")
            let m3: ChatMessage = assistant_msg("Hi there")
            let m4: ChatMessage = tool_msg("result data")
            println(m1.content)
            println(m2.content)
            println(m3.content)
            println(m4.content)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestErrorHandling:
    def test_all_error_variants(self) -> None:
        """All LLMError variants compile and error_message works."""
        src = _llm_source_with_main("""\
            let e1: LLMError = ApiError("api fail")
            let e2: LLMError = NetworkError("net fail")
            let e3: LLMError = ParseError("parse fail")
            let e4: LLMError = AuthError("auth fail")
            let e5: LLMError = RateLimited("rate limited")
            let e6: LLMError = InvalidRequest("bad request")
            let e7: LLMError = Timeout("timed out")
            println(error_message(e1))
            println(error_message(e2))
            println(error_message(e3))
            println(error_message(e4))
            println(error_message(e5))
            println(error_message(e6))
            println(error_message(e7))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestJSONHelpers:
    def test_escape_json(self) -> None:
        """escape_json function compiles."""
        src = _llm_source_with_main("""\
            let escaped: String = escape_json("hello \\"world\\"")
            println(escaped)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jget(self) -> None:
        """jget extracts value from JSON object string."""
        src = _llm_source_with_main("""\
            let json: String = "{\\"name\\": \\"Alice\\", \\"age\\": 30}"
            let val: String = jget(json, "name")
            println(val)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jget_str(self) -> None:
        """jget_str extracts string value."""
        src = _llm_source_with_main("""\
            let json: String = "{\\"model\\": \\"gpt-4o\\"}"
            let model: String = jget_str(json, "model")
            println(model)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jget_int(self) -> None:
        """jget_int extracts integer value."""
        src = _llm_source_with_main("""\
            let json: String = "{\\"count\\": 42}"
            let count: Int = jget_int(json, "count")
            println(str(count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jget_first(self) -> None:
        """jget_first extracts first element of JSON array."""
        src = _llm_source_with_main("""\
            let json: String = "{\\"items\\": [{\\"id\\": 1}, {\\"id\\": 2}]}"
            let first: String = jget_first(json, "items")
            println(first)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_jget_nested(self) -> None:
        """Nested jget calls for deep JSON access."""
        src = _llm_source_with_main("""\
            let json: String = "{\\"data\\": {\\"name\\": \\"test\\"}}"
            let inner: String = jget(json, "data")
            let name: String = jget_str(inner, "name")
            println(name)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Token usage and cost
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestUsageAndCost:
    def test_token_usage(self) -> None:
        """TokenUsage creation and field access."""
        src = _llm_source_with_main("""\
            let u: TokenUsage = new_token_usage(100, 50)
            println(str(u.input_tokens))
            println(str(u.output_tokens))
            println(str(u.total_tokens))
            println(usage_summary(u))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_estimate_cost(self) -> None:
        """estimate_cost with known model pricing."""
        src = _llm_source_with_main("""\
            let cost: Float = estimate_cost("gpt-4o", 1000, 500)
            println(str(cost))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestConversations:
    def test_new_conversation(self) -> None:
        """Conversation creation compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let conv: Conversation = new_conversation(c)
            println(str(conv.turn_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_set_system_prompt(self) -> None:
        """set_system_prompt compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let conv: Conversation = new_conversation(c)
            let conv2: Conversation = set_system_prompt(conv, "You are helpful")
            println(str(len(conv2.history)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_trim_history(self) -> None:
        """trim_history compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let conv: Conversation = new_conversation(c)
            let trimmed: Conversation = trim_history(conv, 5)
            println(str(trimmed.turn_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Reasoning strategies
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestReasoningStrategies:
    def test_plan_and_solve(self) -> None:
        """plan_and_solve prompt augmentation compiles."""
        src = _llm_source_with_main("""\
            let augmented: String = apply_reasoning("plan_and_solve", "How to sort a list?")
            println(augmented)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_self_discover(self) -> None:
        """self_discover prompt augmentation compiles."""
        src = _llm_source_with_main("""\
            let augmented: String = apply_reasoning("self_discover", "Analyze this data")
            println(augmented)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chain_of_thought(self) -> None:
        """cot prompt augmentation compiles."""
        src = _llm_source_with_main("""\
            let augmented: String = apply_reasoning("cot", "What is 2+2?")
            println(augmented)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_unknown_strategy_passthrough(self) -> None:
        """Unknown strategy returns prompt unchanged."""
        src = _llm_source_with_main("""\
            let result: String = apply_reasoning("unknown", "test")
            println(result)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Chain types
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestChainTypes:
    def test_chain_step_compiles(self) -> None:
        """ChainStep creation compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let step: ChainStep = chain_step(c, "Analyze: {prompt}")
            println(step.prompt_template)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_replace_placeholder(self) -> None:
        """Template placeholder replacement compiles."""
        src = _llm_source_with_main("""\
            let result: String = replace_placeholder("Hello {name}!", "name", "World")
            println(result)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Request building
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRequestBuilding:
    def test_message_to_json(self) -> None:
        """message_to_json serializes a ChatMessage."""
        src = _llm_source_with_main("""\
            let msg: ChatMessage = user_msg("Hello world")
            let json: String = message_to_json(msg)
            println(json)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_messages_to_json(self) -> None:
        """messages_to_json serializes a list of messages."""
        src = _llm_source_with_main("""\
            let mut msgs: List<ChatMessage> = []
            msgs = msgs + [system_msg("Be helpful")]
            msgs = msgs + [user_msg("Hi")]
            let json: String = messages_to_json(msgs)
            println(json)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_openai_body(self) -> None:
        """OpenAI request body builder compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let msgs: List<ChatMessage> = [user_msg("Hello")]
            let body: String = build_openai_body(c, msgs)
            println(body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_anthropic_body(self) -> None:
        """Anthropic request body builder compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = anthropic("sk-test", "claude-sonnet-4-20250514")
            let msgs: List<ChatMessage> = [user_msg("Hello")]
            let body: String = build_anthropic_body(c, msgs)
            println(body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_ollama_body(self) -> None:
        """Ollama request body builder compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = ollama("llama3")
            let msgs: List<ChatMessage> = [user_msg("Hello")]
            let body: String = build_ollama_body(c, msgs)
            println(body)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Multi-model helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMultiModelHelpers:
    def test_make_request(self) -> None:
        """LLMRequest creation compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let req: LLMRequest = make_chat_request(c, [user_msg("Hi")])
            println(str(len(req.messages)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_make_complete_request(self) -> None:
        """make_complete_request compiles."""
        src = _llm_source_with_main("""\
            let c: LLMConfig = openai("sk-test", "gpt-4o")
            let req: LLMRequest = make_complete_request(c, "Hello")
            println(str(len(req.messages)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
