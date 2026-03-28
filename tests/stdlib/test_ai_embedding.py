"""ai/embedding.mn — Vector Embeddings tests.

Tests verify that the embedding stdlib module compiles to valid LLVM IR
via the MIR-based emitter.

Covers:
  - Core types: EmbedProvider, EmbeddingError, EmbedConfig, EmbeddingResult
  - Config constructors: openai_embed, ollama_embed, custom_embed
  - Config modifiers: with_dimensions, with_embed_timeout
  - Vector math: dot_product, magnitude, cosine_similarity, euclidean_distance,
                 normalize, vector_add, vector_scale, vector_mean
  - JSON helpers: parse_float_array, jget, jget_str, jget_int
  - VectorStore: new_store, store_add, store_search, store_remove
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

_EMBED_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "ai" / "embedding.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_embedding.mn", use_mir=True)


def _embed_source_with_main(main_body: str) -> str:
    """Prepend the embedding module source and wrap main_body in fn main()."""
    return _EMBED_MN + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_embed_provider_enum(self) -> None:
        """EmbedProvider enum compiles."""
        src = _embed_source_with_main("""\
            let p: EmbedProvider = OpenAI()
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_embedding_error_enum(self) -> None:
        """EmbeddingError enum compiles."""
        src = _embed_source_with_main("""\
            let e: EmbeddingError = ApiError("test")
            println(error_message(e))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_all_error_variants(self) -> None:
        """All EmbeddingError variants compile."""
        src = _embed_source_with_main("""\
            let e1: EmbeddingError = ApiError("a")
            let e2: EmbeddingError = NetworkError("b")
            let e3: EmbeddingError = ParseError("c")
            let e4: EmbeddingError = AuthError("d")
            let e5: EmbeddingError = RateLimited("e")
            let e6: EmbeddingError = InvalidInput("f")
            println(error_message(e1))
            println(error_message(e6))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_embedding_result_struct(self) -> None:
        """EmbeddingResult struct compiles."""
        src = _embed_source_with_main("""\
            let vec: List<Float> = [0.1, 0.2, 0.3]
            let r: EmbeddingResult = new_embedding_result(vec, 10, "test-model")
            println(str(r.dimensions))
            println(str(r.tokens_used))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Config constructors and modifiers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestConfig:
    def test_openai_embed_config(self) -> None:
        """openai_embed() compiles."""
        src = _embed_source_with_main("""\
            let c: EmbedConfig = openai_embed("sk-test", "text-embedding-3-small")
            println(c.model)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ollama_embed_config(self) -> None:
        """ollama_embed() compiles."""
        src = _embed_source_with_main("""\
            let c: EmbedConfig = ollama_embed("nomic-embed-text")
            println(str(c.port))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_with_dimensions(self) -> None:
        """with_dimensions() compiles."""
        src = _embed_source_with_main("""\
            let c: EmbedConfig = openai_embed("sk-test", "text-embedding-3-small")
            let c2: EmbedConfig = with_dimensions(c, 256)
            println(str(c2.dimensions))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_with_embed_timeout(self) -> None:
        """with_embed_timeout() compiles."""
        src = _embed_source_with_main("""\
            let c: EmbedConfig = openai_embed("sk-test", "text-embedding-3-small")
            let c2: EmbedConfig = with_embed_timeout(c, 30000)
            println(str(c2.timeout_ms))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Vector math
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestVectorMath:
    def test_dot_product(self) -> None:
        """dot_product compiles."""
        src = _embed_source_with_main("""\
            let a: List<Float> = [1.0, 2.0, 3.0]
            let b: List<Float> = [4.0, 5.0, 6.0]
            let result: Float = dot_product(a, b)
            println(str(result))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_magnitude(self) -> None:
        """magnitude compiles."""
        src = _embed_source_with_main("""\
            let v: List<Float> = [3.0, 4.0]
            let mag: Float = magnitude(v)
            println(str(mag))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_cosine_similarity(self) -> None:
        """cosine_similarity compiles."""
        src = _embed_source_with_main("""\
            let a: List<Float> = [1.0, 0.0]
            let b: List<Float> = [0.0, 1.0]
            let sim: Float = cosine_similarity(a, b)
            println(str(sim))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_euclidean_distance(self) -> None:
        """euclidean_distance compiles."""
        src = _embed_source_with_main("""\
            let a: List<Float> = [0.0, 0.0]
            let b: List<Float> = [3.0, 4.0]
            let dist: Float = euclidean_distance(a, b)
            println(str(dist))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_normalize(self) -> None:
        """normalize compiles."""
        src = _embed_source_with_main("""\
            let v: List<Float> = [3.0, 4.0]
            let n: List<Float> = normalize(v)
            println(str(len(n)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_vector_add(self) -> None:
        """vector_add compiles."""
        src = _embed_source_with_main("""\
            let a: List<Float> = [1.0, 2.0]
            let b: List<Float> = [3.0, 4.0]
            let c: List<Float> = vector_add(a, b)
            println(str(len(c)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_vector_scale(self) -> None:
        """vector_scale compiles."""
        src = _embed_source_with_main("""\
            let v: List<Float> = [1.0, 2.0, 3.0]
            let scaled: List<Float> = vector_scale(v, 2.0)
            println(str(len(scaled)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_vector_mean(self) -> None:
        """vector_mean compiles."""
        src = _embed_source_with_main("""\
            let vecs: List<List<Float>> = [[1.0, 2.0], [3.0, 4.0]]
            let m: List<Float> = vector_mean(vecs)
            println(str(len(m)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sqrt_approx(self) -> None:
        """sqrt_approx (internal) compiles."""
        src = _embed_source_with_main("""\
            let r: Float = sqrt_approx(25.0)
            println(str(r))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestJSONHelpers:
    def test_parse_float_array(self) -> None:
        """parse_float_array compiles."""
        src = _embed_source_with_main("""\
            let arr: List<Float> = parse_float_array("[1.0, 2.5, -3.0]")
            println(str(len(arr)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_escape_json(self) -> None:
        """escape_json compiles."""
        src = _embed_source_with_main("""\
            let escaped: String = escape_json("hello \\"world\\"")
            println(escaped)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# VectorStore
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestVectorStore:
    def test_new_store(self) -> None:
        """new_store compiles."""
        src = _embed_source_with_main("""\
            let store: VectorStore = new_store()
            println(str(store_size(store)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_store_add(self) -> None:
        """store_add compiles."""
        src = _embed_source_with_main("""\
            let mut store: VectorStore = new_store()
            let vec: List<Float> = [0.1, 0.2, 0.3]
            store = store_add(store, "id1", "Hello world", vec)
            println(str(store_size(store)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_store_search(self) -> None:
        """store_search compiles."""
        src = _embed_source_with_main("""\
            let mut store: VectorStore = new_store()
            store = store_add(store, "id1", "text1", [1.0, 0.0, 0.0])
            store = store_add(store, "id2", "text2", [0.0, 1.0, 0.0])
            let query: List<Float> = [1.0, 0.0, 0.0]
            let results: List<SearchResult> = store_search(store, query, 2)
            println(str(len(results)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_store_search_threshold(self) -> None:
        """store_search_threshold compiles."""
        src = _embed_source_with_main("""\
            let mut store: VectorStore = new_store()
            store = store_add(store, "id1", "text1", [1.0, 0.0])
            let results: List<SearchResult> = store_search_threshold(store, [1.0, 0.0], 0.5)
            println(str(len(results)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_store_remove(self) -> None:
        """store_remove compiles."""
        src = _embed_source_with_main("""\
            let mut store: VectorStore = new_store()
            store = store_add(store, "id1", "text1", [1.0, 0.0])
            store = store_add(store, "id2", "text2", [0.0, 1.0])
            store = store_remove(store, "id1")
            println(str(store_size(store)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_store_add_with_meta(self) -> None:
        """store_add_with_meta compiles."""
        src = _embed_source_with_main("""\
            let mut store: VectorStore = new_store()
            let meta: Map<String, String> = #{"source": "doc1"}
            store = store_add_with_meta(store, "id1", "text1", [0.1, 0.2], meta)
            println(str(store_size(store)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
