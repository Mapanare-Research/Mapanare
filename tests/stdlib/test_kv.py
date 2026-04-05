"""db/kv.mn + db/embedded_kv.mn — KV Store Interface & Embedded Store tests.

Tests verify that the KV store modules compile to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation is not yet ready, tests
inline the module source code within test programs.

Covers:
  - Core types: KVError, KVEntry, EmbeddedStore, RedisStore, KVStore enum
  - EmbeddedKV: create, set/get, get nonexistent, del, exists, keys, size
  - EmbeddedKV: save to file, load from file, roundtrip
  - KVStore dispatch: Embedded variant routes to embedded functions
  - Overwrite existing key
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

_KV_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "kv.mn").read_text(
    encoding="utf-8"
)

_EMBEDDED_KV_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "embedded_kv.mn"
).read_text(encoding="utf-8")

# The JSON module is a dependency of embedded_kv.mn
_JSON_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "encoding" / "json.mn"
).read_text(encoding="utf-8")

# string_utils is a dependency of json.mn
_STRING_UTILS_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "text" / "string_utils.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_kv.mn", use_mir=True)


def _strip_imports(source: str) -> str:
    """Remove import/usa lines since we inline all module sources."""
    return "\n".join(
        line
        for line in source.splitlines()
        if not line.strip().startswith(("import ", "usa "))
    )


def _kv_source() -> str:
    """Return inlined KV + EmbeddedKV + JSON + string_utils module sources."""
    return (
        _strip_imports(_STRING_UTILS_MN)
        + "\n\n"
        + _strip_imports(_JSON_MN)
        + "\n\n"
        + _strip_imports(_KV_MN)
        + "\n\n"
        + _strip_imports(_EMBEDDED_KV_MN)
    )


def _kv_source_with_main(main_body: str) -> str:
    """Prepend the KV module sources and wrap main_body in fn main()."""
    return _kv_source() + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCoreTypes:
    def test_kv_error_struct_compiles(self) -> None:
        """KVError struct compiles."""
        src = _kv_source_with_main("""\
            let e: KVError = new_kv_error("test error")
            print(e.message)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_entry_struct_compiles(self) -> None:
        """KVEntry struct compiles."""
        src = _kv_source_with_main("""\
            let entry: KVEntry = new_kv_entry("key", "value")
            print(entry.key)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_embedded_store_compiles(self) -> None:
        """EmbeddedStore struct compiles."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_store_enum_compiles(self) -> None:
        """KVStore enum with Embedded variant compiles."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# EmbeddedKV: create, set/get
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmbeddedSetGet:
    def test_create_set_get(self) -> None:
        """EmbeddedKV: create, set a key, get it back."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "hello", "world")
            let val: Option<String> = embedded_get(s2, "hello")
            match val {
                Some(v) => { print(v) },
                _ => { print("not found") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_get_nonexistent_key(self) -> None:
        """EmbeddedKV: get nonexistent key returns None."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let val: Option<String> = embedded_get(store, "missing")
            match val {
                Some(v) => { print("unexpected: " + v) },
                _ => { print("none") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# EmbeddedKV: del removes key
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmbeddedDel:
    def test_del_removes_key(self) -> None:
        """EmbeddedKV: del removes a key from the store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "a", "1")
            let s3: EmbeddedStore = embedded_set(s2, "b", "2")
            let s4: EmbeddedStore = embedded_del(s3, "a")
            let val: Option<String> = embedded_get(s4, "a")
            match val {
                Some(v) => { print("unexpected: " + v) },
                _ => { print("deleted") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# EmbeddedKV: exists
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmbeddedExists:
    def test_exists_true_false(self) -> None:
        """EmbeddedKV: exists returns true for present key, false for absent."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "x", "42")
            let found: Bool = embedded_exists(s2, "x")
            let missing: Bool = embedded_exists(s2, "y")
            print(str(found))
            print(str(missing))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# EmbeddedKV: keys
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmbeddedKeys:
    def test_keys_returns_all(self) -> None:
        """EmbeddedKV: keys returns all keys in the store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "a", "1")
            let s3: EmbeddedStore = embedded_set(s2, "b", "2")
            let s4: EmbeddedStore = embedded_set(s3, "c", "3")
            let all_keys: List<String> = embedded_keys(s4)
            print(str(len(all_keys)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# EmbeddedKV: size
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmbeddedSize:
    def test_size_tracks_count(self) -> None:
        """EmbeddedKV: size tracks the number of entries."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "a", "1")
            let s3: EmbeddedStore = embedded_set(s2, "b", "2")
            let count: Int = embedded_size(s3)
            print(str(count))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# EmbeddedKV: save and load roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEmbeddedPersistence:
    def test_save_compiles(self) -> None:
        """EmbeddedKV: save to file compiles."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "key1", "val1")
            let r: Result<Bool, KVError> = embedded_save(s2, "/tmp/test_kv.json")
            match r {
                Ok(b) => { print("saved") },
                Err(e) => { print(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_load_compiles(self) -> None:
        """EmbeddedKV: load from file compiles."""
        src = _kv_source_with_main("""\
            let r: Result<KVStore, KVError> = embedded_load("/tmp/test_kv.json")
            match r {
                Ok(s) => { print("loaded") },
                Err(e) => { print(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_save_load_roundtrip_compiles(self) -> None:
        """EmbeddedKV: save then load roundtrip compiles."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "name", "mapanare")
            let s3: EmbeddedStore = embedded_set(s2, "version", "1.0")
            let save_result: Result<Bool, KVError> = embedded_save(s3, "/tmp/test_roundtrip.json")
            let load_result: Result<KVStore, KVError> = embedded_load("/tmp/test_roundtrip.json")
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# KVStore dispatch: Embedded variant
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestKVStoreDispatch:
    def test_kv_set_embedded_dispatch(self) -> None:
        """KVStore dispatch: kv_set routes to embedded store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            let r: Result<Bool, KVError> = kv_set(store, "key", "value")
            match r {
                Ok(b) => { print("set ok") },
                Err(e) => { print(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_get_embedded_dispatch(self) -> None:
        """KVStore dispatch: kv_get routes to embedded store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            let val: Option<String> = kv_get(store, "missing")
            match val {
                Some(v) => { print(v) },
                _ => { print("none") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_del_embedded_dispatch(self) -> None:
        """KVStore dispatch: kv_del routes to embedded store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            let r: Result<Bool, KVError> = kv_del(store, "key")
            match r {
                Ok(b) => { print("del ok") },
                Err(e) => { print(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_exists_embedded_dispatch(self) -> None:
        """KVStore dispatch: kv_exists routes to embedded store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            let found: Bool = kv_exists(store, "key")
            print(str(found))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_keys_embedded_dispatch(self) -> None:
        """KVStore dispatch: kv_keys routes to embedded store."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            let all_keys: List<String> = kv_keys(store)
            print(str(len(all_keys)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_close_embedded_dispatch(self) -> None:
        """KVStore dispatch: kv_close for embedded returns Ok."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let es: EmbeddedStore = new_embedded_store(data)
            let store: KVStore = Embedded(es)
            let r: Result<Bool, KVError> = kv_close(store)
            match r {
                Ok(b) => { print("closed") },
                Err(e) => { print(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Overwrite existing key
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestOverwriteKey:
    def test_overwrite_existing_key(self) -> None:
        """EmbeddedKV: setting an existing key overwrites the value."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let store: EmbeddedStore = new_embedded_store(data)
            let s2: EmbeddedStore = embedded_set(store, "color", "red")
            let s3: EmbeddedStore = embedded_set(s2, "color", "blue")
            let val: Option<String> = embedded_get(s3, "color")
            match val {
                Some(v) => { print(v) },
                _ => { print("not found") }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Internal helpers compile
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestInternalHelpers:
    def test_map_to_json_compiles(self) -> None:
        """Internal map_to_json serializer compiles."""
        src = _kv_source_with_main("""\
            let data: Map<String, String> = #{}
            let json: String = map_to_json(data)
            print(json)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_escape_json_str_compiles(self) -> None:
        """Internal escape_json_str helper compiles."""
        src = _kv_source_with_main("""\
            let escaped: String = escape_json_str("hello\\"world")
            print(escaped)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_error_message_helper(self) -> None:
        """error_message helper extracts message from KVError."""
        src = _kv_source_with_main("""\
            let e: KVError = new_kv_error("something broke")
            let msg: String = error_message(e)
            print(msg)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
