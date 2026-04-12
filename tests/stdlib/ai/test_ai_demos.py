"""Integration tests for AI demos (v4.50.0).

Verifies demo files exist and have expected structure.
Ollama integration tests skip if Ollama is not available.
"""

import os
import pytest


class TestDemoFilesExist:
    """All AI demo files exist with expected content."""

    def test_chat_agent_exists(self):
        path = "examples/ai/chat_agent.mn"
        assert os.path.exists(path)
        src = open(path).read()
        assert "agent ChatBot" in src
        assert "spawn ChatBot" in src
        assert "sync bot.response" in src

    def test_rag_agent_exists(self):
        path = "examples/ai/rag_agent.mn"
        assert os.path.exists(path)
        src = open(path).read()
        assert "embed(" in src or "embed_config" in src
        assert "store_search(" in src
        assert "augment_prompt(" in src
        assert "build_context_simple(" in src

    def test_basic_chat_exists(self):
        assert os.path.exists("examples/ai/basic_chat.mn")

    def test_basic_stream_exists(self):
        assert os.path.exists("examples/ai/basic_stream.mn")

    def test_sample_docs_directory(self):
        path = "examples/ai/sample_docs"
        assert os.path.isdir(path)
        files = os.listdir(path)
        assert len(files) >= 7
        assert "agents.txt" in files
        assert "signals.txt" in files
        assert "streams.txt" in files
        assert "tensors.txt" in files


class TestCookbookAIChapter:
    """Cookbook AI chapter exists with sufficient content."""

    def test_chapter_exists(self):
        src = open("docs/cookbook.md").read()
        assert "Building an AI Agent in Mapanare" in src

    def test_chapter_has_steps(self):
        src = open("docs/cookbook.md").read()
        assert "Step 1: Talk to an LLM" in src
        assert "Step 2: Structured Extraction" in src
        assert "Step 3: Embed and Search" in src
        assert "Step 4: Chunk Documents for RAG" in src
        assert "Step 5: The Full RAG Pipeline" in src
        assert "Step 6: Wrap It in an Agent" in src

    def test_chapter_word_count(self):
        src = open("docs/cookbook.md").read()
        # Extract the AI chapter section
        start = src.find("## Building an AI Agent")
        end = src.find("## Tips and Patterns")
        if start >= 0 and end >= 0:
            chapter = src[start:end]
            words = len(chapter.split())
            assert words >= 750, f"AI chapter only {words} words, expected >= 750"

    def test_module_summary_table(self):
        src = open("docs/cookbook.md").read()
        assert "| `llm.mn`" in src
        assert "| `embedding.mn`" in src
        assert "| `rag.mn`" in src
        assert "| `structured.mn`" in src


class TestReadmeAISection:
    """README.md has the AI narrative."""

    def test_hello_ai_snippet(self):
        src = open("README.md").read()
        assert "Hello AI" in src
        assert 'ollama("llama3.2")' in src

    def test_ai_stdlib_bullet(self):
        src = open("README.md").read()
        assert "AI stdlib" in src

    def test_cookbook_link(self):
        src = open("README.md").read()
        assert "cookbook" in src.lower()


class TestOllamaIntegration:
    """Integration tests — skip if Ollama not available (v4.50.0-ollama-missing)."""

    @pytest.fixture(autouse=True)
    def _check_ollama(self):
        """Skip all tests in this class if Ollama is not running."""
        import subprocess

        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode != 0 or '"models"' not in result.stdout:
                pytest.skip("Ollama not available (v4.50.0-ollama-missing)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Ollama not available (v4.50.0-ollama-missing)")

    def test_ollama_is_running(self):
        """Ollama responds to /api/tags."""
        # If we get here, the fixture didn't skip — Ollama is running
        assert True
