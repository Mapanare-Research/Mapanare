"""Offline tests for stdlib/ai/embedding.mn — no network required (v4.49.0).

Verifies module compiles, types exist, vector math functions are defined,
and the API surface matches expectations.
"""

from mapanare.parser import parse
from mapanare.semantic import check


class TestEmbeddingModuleCompiles:
    """embedding.mn compiles through the Python bootstrap."""

    def test_module_parses(self):
        with open("stdlib/ai/embedding.mn") as f:
            src = f.read()
        ast = parse(src)
        assert ast is not None

    def test_module_checks(self):
        with open("stdlib/ai/embedding.mn") as f:
            src = f.read()
        ast = parse(src)
        checked = check(ast)
        assert checked is not None


class TestEmbeddingTypes:
    """Embedding types are well-defined."""

    def test_error_type(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "tipo EmbeddingError" in src
        assert "| ApiError(String)" in src
        assert "| NetworkError(String)" in src
        assert "| ParseError(String)" in src

    def test_provider_enum(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "tipo EmbedProvider" in src
        assert "| OpenAI" in src
        assert "| Ollama" in src

    def test_config_struct(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "tipo EmbedConfig" in src
        assert "dimensions: Int" in src
        assert "has_dimensions: Bool" in src

    def test_result_struct(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "tipo EmbeddingResult" in src
        assert "vector: List<Float>" in src
        assert "dimensions: Int" in src

    def test_batch_result_struct(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "tipo BatchEmbeddingResult" in src


class TestEmbeddingAPI:
    """Core embedding API functions exist."""

    def test_config_constructors(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn openai_embed(" in src
        assert "fn ollama_embed(" in src
        assert "fn ollama_embed_at(" in src
        assert "fn custom_embed(" in src

    def test_embed_function(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn embed(config: EmbedConfig, text: String)" in src

    def test_embed_batch_function(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn embed_batch(" in src

    def test_dimension_config(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn with_dimensions(" in src
        assert "fn with_embed_timeout(" in src


class TestVectorMath:
    """Vector similarity and utility functions exist."""

    def test_dot_product(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn dot_product(a: List<Float>, b: List<Float>) -> Float" in src

    def test_cosine_similarity(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn cosine_similarity(a: List<Float>, b: List<Float>) -> Float" in src

    def test_euclidean_distance(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn euclidean_distance(a: List<Float>, b: List<Float>) -> Float" in src

    def test_normalize(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn normalize(v: List<Float>) -> List<Float>" in src

    def test_magnitude(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn magnitude(v: List<Float>) -> Float" in src

    def test_vector_add(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn vector_add(" in src

    def test_vector_scale(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn vector_scale(" in src

    def test_vector_mean(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn vector_mean(" in src


class TestVectorStore:
    """Vector store with linear-scan search exists."""

    def test_store_types(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "tipo VectorStore" in src
        assert "tipo VectorEntry" in src

    def test_store_operations(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "fn new_store()" in src or "fn store_new()" in src or "new_store" in src
        assert "store_add" in src
        assert "store_search" in src

    def test_store_search_threshold(self):
        src = open("stdlib/ai/embedding.mn").read()
        assert "store_search_threshold" in src or "search_threshold" in src
