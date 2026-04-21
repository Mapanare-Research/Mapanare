"""Tests for stdlib/ai/llm.mn type definitions and compilation (v4.47.0)."""

from mapanare.parser import parse
from mapanare.semantic import check


class TestLlmModuleCompiles:
    """stdlib/ai/llm.mn compiles through the Python bootstrap."""

    def test_llm_module_parses(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        ast = parse(src)
        assert ast is not None

    def test_llm_module_checks(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        ast = parse(src)
        checked = check(ast)
        assert checked is not None


class TestLlmExamplesExist:
    """examples/ai/*.mn files exist and have expected content."""

    def test_basic_chat_exists(self):
        import os

        assert os.path.exists("examples/ai/basic_chat.mn")
        with open("examples/ai/basic_chat.mn") as f:
            src = f.read()
        assert "llm.chat(" in src or "llm.ollama(" in src

    def test_basic_stream_exists(self):
        import os

        assert os.path.exists("examples/ai/basic_stream.mn")
        with open("examples/ai/basic_stream.mn") as f:
            src = f.read()
        assert "chat_stream(" in src or "ChatChunk" in src


class TestChatChunkType:
    """ChatChunk type is well-defined and constructible."""

    def test_chunk_fields_exist(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "tipo ChatChunk" in src
        assert "delta: String" in src
        assert "finish_reason: String" in src
        assert "is_done: Bool" in src

    def test_streaming_functions_exist(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "fn chat_stream(" in src
        assert "fn parse_stream_response(" in src
        assert "fn default_config()" in src

    def test_env_var_names(self):
        with open("stdlib/ai/llm.mn") as f:
            src = f.read()
        assert "MAPANARE_LLM_BACKEND" in src
        assert "MAPANARE_LLM_API_KEY" in src
        assert "MAPANARE_LLM_MODEL" in src
        assert "MAPANARE_LLM_BASE_URL" in src
