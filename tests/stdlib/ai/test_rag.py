"""Offline tests for stdlib/ai/rag.mn — no network required (v4.49.0).

Verifies module compiles, chunking types exist, context building functions
are defined, and the API surface matches expectations.
"""

from mapanare.parser import parse
from mapanare.semantic import check


class TestRagModuleCompiles:
    """rag.mn compiles through the Python bootstrap."""

    def test_module_parses(self):
        with open("stdlib/ai/rag.mn") as f:
            src = f.read()
        ast = parse(src)
        assert ast is not None

    def test_module_checks(self):
        with open("stdlib/ai/rag.mn") as f:
            src = f.read()
        ast = parse(src)
        checked = check(ast)
        assert checked is not None


class TestChunkingTypes:
    """Chunk types and functions are defined."""

    def test_chunk_type(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "tipo Chunk" in src
        assert "text: String" in src
        assert "index: Int" in src

    def test_document_type(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "tipo Document" in src
        assert "title: String" in src
        assert "content: String" in src


class TestChunkingStrategies:
    """All three chunking strategies exist."""

    def test_fixed_size_chunking(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn chunk_text(text: String, chunk_size: Int, overlap: Int)" in src

    def test_sentence_chunking(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn chunk_by_sentences(" in src

    def test_paragraph_chunking(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn chunk_by_paragraphs(" in src

    def test_document_chunking(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn chunk_document(" in src
        assert "fn chunk_document_sentences(" in src

    def test_multi_document_chunking(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn chunk_documents(" in src


class TestContextBuilding:
    """RAG context building and prompt augmentation."""

    def test_retrieval_context_type(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "tipo RetrievalContext" in src
        assert "source_count: Int" in src

    def test_build_context(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn build_context(" in src
        assert "fn build_context_simple(" in src

    def test_augment_prompt(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn augment_prompt(" in src
        assert "fn augment_prompt_custom(" in src

    def test_system_prompt(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn make_rag_system_prompt(" in src

    def test_token_budget(self):
        src = open("stdlib/ai/rag.mn").read()
        assert "fn estimate_tokens(" in src
        assert "fn fits_in_budget(" in src
        assert "fn build_context_budgeted(" in src


class TestUtf8Safety:
    """Chunking uses char_at for UTF-8 safety."""

    def test_uses_char_at(self):
        src = open("stdlib/ai/rag.mn").read()
        assert ".char_at(" in src
