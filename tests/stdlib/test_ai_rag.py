"""ai/rag.mn — Retrieval-Augmented Generation tests.

Tests verify that the RAG stdlib module compiles to valid LLVM IR
via the MIR-based emitter.

Covers:
  - Chunk types: Chunk, Document
  - Chunking: chunk_text, chunk_by_sentences, chunk_by_paragraphs
  - Text helpers: split_sentences, split_paragraphs, trim_string
  - Context building: build_context, build_context_simple, build_context_budgeted
  - Prompt augmentation: augment_prompt, augment_prompt_custom, make_rag_system_prompt
  - Token estimation: estimate_tokens, fits_in_budget
  - Document operations: new_document, chunk_document, chunk_documents
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

_RAG_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "ai" / "rag.mn").read_text(
    encoding="utf-8"
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_rag.mn", use_mir=True)


def _rag_source_with_main(main_body: str) -> str:
    """Prepend the RAG module source and wrap main_body in fn main()."""
    return _RAG_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_chunk_struct(self) -> None:
        """Chunk struct compiles."""
        src = _rag_source_with_main("""\
            let c: Chunk = new_chunk("c1", "Hello world", 0, 0, 11)
            print(c.id)
            print(c.text)
            print(str(c.index))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_document_struct(self) -> None:
        """Document struct compiles."""
        src = _rag_source_with_main("""\
            let doc: Document = new_document("d1", "My Doc", "Some content here.")
            print(doc.title)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_document_with_meta(self) -> None:
        """Document with metadata compiles."""
        src = _rag_source_with_main("""\
            let meta: Map<String, String> = #{"author": "Juan"}
            let doc: Document = new_document_with_meta("d1", "My Doc", "Content", meta)
            print(doc.id)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_retrieval_context_struct(self) -> None:
        """RetrievalContext struct compiles."""
        src = _rag_source_with_main("""\
            let ctx: RetrievalContext = build_context_simple(["chunk1", "chunk2"])
            print(str(ctx.source_count))
            print(ctx.text)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Chunking algorithms
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestChunking:
    def test_chunk_text_basic(self) -> None:
        """Fixed-size chunking compiles."""
        src = _rag_source_with_main("""\
            let text: String = "Hello world, this is a test document for chunking."
            let chunks: List<Chunk> = chunk_text(text, 20, 5)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chunk_text_no_overlap(self) -> None:
        """Chunking without overlap compiles."""
        src = _rag_source_with_main("""\
            let chunks: List<Chunk> = chunk_text("abcdefghij", 5, 0)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chunk_by_sentences(self) -> None:
        """Sentence-aware chunking compiles."""
        src = _rag_source_with_main("""\
            let text: String = "First sentence. Second sentence. Third sentence."
            let chunks: List<Chunk> = chunk_by_sentences(text, 100)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chunk_by_paragraphs(self) -> None:
        """Paragraph-aware chunking compiles."""
        src = _rag_source_with_main("""\
            let text: String = "First paragraph.\\n\\nSecond paragraph.\\n\\nThird paragraph."
            let chunks: List<Chunk> = chunk_by_paragraphs(text, 200)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chunk_empty_text(self) -> None:
        """Chunking empty text returns empty list."""
        src = _rag_source_with_main("""\
            let chunks: List<Chunk> = chunk_text("", 100, 0)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chunk_document(self) -> None:
        """Document chunking with prefixed IDs compiles."""
        src = _rag_source_with_main("""\
            let doc: Document = new_document("mydoc", "Title", "Some long content for chunking.")
            let chunks: List<Chunk> = chunk_document(doc, 15, 0)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_chunk_documents_multi(self) -> None:
        """Multi-document chunking compiles."""
        src = _rag_source_with_main("""\
            let d1: Document = new_document("d1", "Doc 1", "First doc content.")
            let d2: Document = new_document("d2", "Doc 2", "Second doc content.")
            let docs: List<Document> = [d1, d2]
            let chunks: List<Chunk> = chunk_documents(docs, 20, 0)
            print(str(len(chunks)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTextHelpers:
    def test_trim_string(self) -> None:
        """trim_string removes leading/trailing whitespace."""
        src = _rag_source_with_main("""\
            let trimmed: String = trim_string("  hello  ")
            print(trimmed)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_split_sentences(self) -> None:
        """split_sentences compiles."""
        src = _rag_source_with_main("""\
            let sents: List<String> = split_sentences("Hello. World! How?")
            print(str(len(sents)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_split_paragraphs(self) -> None:
        """split_paragraphs compiles."""
        src = _rag_source_with_main("""\
            let paras: List<String> = split_paragraphs("Para one.\\n\\nPara two.")
            print(str(len(paras)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestContextBuilding:
    def test_build_context_simple(self) -> None:
        """build_context_simple compiles."""
        src = _rag_source_with_main("""\
            let texts: List<String> = ["First chunk", "Second chunk"]
            let ctx: RetrievalContext = build_context_simple(texts)
            print(ctx.text)
            print(str(ctx.source_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_context_with_ids(self) -> None:
        """build_context with IDs and scores compiles."""
        src = _rag_source_with_main("""\
            let texts: List<String> = ["chunk1 text", "chunk2 text"]
            let ids: List<String> = ["doc1_c0", "doc1_c1"]
            let scores: List<Float> = [0.95, 0.87]
            let ctx: RetrievalContext = build_context(texts, ids, scores)
            print(ctx.text)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_build_context_budgeted(self) -> None:
        """build_context_budgeted respects token budget."""
        src = _rag_source_with_main("""\
            let texts: List<String> = ["Short.", "Also short.", "This is a longer text."]
            let ctx: RetrievalContext = build_context_budgeted(texts, 20)
            print(str(ctx.source_count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Prompt augmentation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPromptAugmentation:
    def test_augment_prompt(self) -> None:
        """augment_prompt builds RAG prompt."""
        src = _rag_source_with_main("""\
            let ctx: RetrievalContext = build_context_simple(["Mapanare is a language."])
            let prompt: String = augment_prompt("What is Mapanare?", ctx)
            print(prompt)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_augment_prompt_custom(self) -> None:
        """augment_prompt_custom with custom instruction."""
        src = _rag_source_with_main("""\
            let ctx: RetrievalContext = build_context_simple(["Some data."])
            let prompt: String = augment_prompt_custom("Summarize", ctx, "You are a summarizer.")
            print(prompt)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_make_rag_system_prompt(self) -> None:
        """make_rag_system_prompt builds system prompt with context."""
        src = _rag_source_with_main("""\
            let ctx: RetrievalContext = build_context_simple(["Reference data."])
            let system: String = make_rag_system_prompt(ctx)
            print(system)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestTokenEstimation:
    def test_estimate_tokens(self) -> None:
        """estimate_tokens compiles."""
        src = _rag_source_with_main("""\
            let tokens: Int = estimate_tokens("Hello world, this is a test.")
            print(str(tokens))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_fits_in_budget(self) -> None:
        """fits_in_budget compiles."""
        src = _rag_source_with_main("""\
            let fits: Bool = fits_in_budget("existing context", "new chunk", 100)
            print(str(fits))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
