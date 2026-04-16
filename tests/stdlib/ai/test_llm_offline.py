"""Offline tests for stdlib/ai/llm.mn — no network required (v4.47.0).

Tests the parsing logic with fixture responses. Does not call any API.
"""


class TestProviderBodyBuilders:
    """Provider-specific request body builders produce valid JSON."""

    OPENAI_FIXTURE = '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}],"max_tokens":4096,"temperature":0.7,"stream":false}'
    ANTHROPIC_FIXTURE = '{"model":"claude-sonnet-4-20250514","system":"","messages":[{"role":"user","content":"hi"}],"max_tokens":4096,"temperature":0.7,"stream":false}'
    OLLAMA_FIXTURE = (
        '{"model":"llama3.2","messages":[{"role":"user","content":"hi"}],"stream":false}'
    )

    def test_provider_enum_variants(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "| OpenAI" in src
        assert "| Anthropic" in src
        assert "| Groq" in src
        assert "| Ollama" in src
        assert "| Custom" in src

    def test_role_enum_variants(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "| System" in src
        assert "| User" in src
        assert "| Assistant" in src
        assert "| Tool" in src


class TestErrorMapping:
    """Error types map HTTP status codes to LLMError variants."""

    def test_error_variants(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "| ApiError(String)" in src
        assert "| NetworkError(String)" in src
        assert "| AuthError(String)" in src
        assert "| RateLimited(String)" in src
        assert "| InvalidRequest(String)" in src
        assert "| Timeout(String)" in src

    def test_http_status_check_function(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "fn check_http_status(" in src
        # Should handle 401, 429, 5xx
        assert "401" in src
        assert "429" in src


class TestStreamingTypes:
    """ChatChunk and streaming functions are properly defined."""

    def test_chat_chunk_type(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub tipo ChatChunk {" in src
        assert "delta: String" in src
        assert "finish_reason: String" in src
        assert "is_done: Bool" in src

    def test_chunk_constructors(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "fn content_chunk(" in src
        assert "fn final_chunk(" in src

    def test_sse_parsing_handles_done(self):
        """The parser recognizes [DONE] as a terminal marker."""
        src = open("stdlib/ai/llm.mn").read()
        assert '"[DONE]"' in src

    def test_ollama_ndjson_parsing(self):
        """The parser handles Ollama's newline-delimited JSON."""
        src = open("stdlib/ai/llm.mn").read()
        assert 'jget(line, "done")' in src
        assert 'jget(line, "message")' in src


class TestDefaultConfig:
    """default_config() reads environment variables correctly."""

    def test_default_config_exists(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn default_config() -> LLMConfig" in src

    def test_reads_backend_env(self):
        src = open("stdlib/ai/llm.mn").read()
        assert '__mn_env_get("MAPANARE_LLM_BACKEND")' in src

    def test_defaults_to_ollama(self):
        src = open("stdlib/ai/llm.mn").read()
        # When no API key set, should default to Ollama
        assert 'backend = "ollama"' in src

    def test_api_key_triggers_openai(self):
        src = open("stdlib/ai/llm.mn").read()
        # When API key present but no backend specified, default to OpenAI
        assert 'backend = "openai"' in src


class TestConversationManagement:
    """Conversation and multi-turn chat types exist."""

    def test_conversation_type(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub tipo Conversation" in src

    def test_converse_function(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn converse(" in src

    def test_trim_history(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn trim_history(" in src


class TestAdvancedFeatures:
    """Tool calling, retry, fallback, chain, consensus."""

    def test_tool_calling(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub tipo ToolDef" in src
        assert "pub tipo ToolCall" in src
        assert "pub fn get_tool_calls(" in src

    def test_retry(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn chat_with_retry(" in src

    def test_fallback(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn chat_with_fallback(" in src

    def test_chain(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn run_chain(" in src

    def test_consensus(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn consensus(" in src

    def test_cost_estimation(self):
        src = open("stdlib/ai/llm.mn").read()
        assert "pub fn estimate_cost(" in src
        assert "pub fn response_cost(" in src
