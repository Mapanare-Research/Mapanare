"""db/redis.mn — Redis Driver tests.

Tests verify that the Redis KV driver module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation is not yet ready, tests
inline the module source code within test programs.

All tests are skipped if:
  - llvmlite is not installed
  - Redis is not reachable on localhost:6379

Covers:
  - connect to Redis
  - set/get roundtrip
  - del removes key
  - exists
  - set_ex with TTL
  - incr/decr atomic counters
  - keys pattern matching
  - close connection
"""

from __future__ import annotations

import socket
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
# Redis availability check
# ---------------------------------------------------------------------------


def _redis_available() -> bool:
    """Return True if a Redis server is reachable on localhost:6379."""
    try:
        s = socket.create_connection(("127.0.0.1", 6379), timeout=1)
        s.close()
        return True
    except (OSError, ConnectionRefusedError):
        return False


_HAS_REDIS = _redis_available()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KV_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "kv.mn").read_text(
    encoding="utf-8"
)

_EMBEDDED_KV_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "embedded_kv.mn"
).read_text(encoding="utf-8")

_JSON_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "encoding" / "json.mn"
).read_text(encoding="utf-8")

_REDIS_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "redis.mn"
).read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_kv_redis.mn", use_mir=True)


def _strip_imports(source: str) -> str:
    """Remove import lines since we inline all module sources."""
    return "\n".join(line for line in source.splitlines() if not line.strip().startswith("import "))


def _strip_redis_stubs(source: str) -> str:
    """Remove redis stub functions from kv.mn (replaced by real redis.mn)."""
    lines = source.splitlines()
    result: list[str] = []
    skip_depth = 0
    skipping = False
    for line in lines:
        if not skipping and line.startswith("fn redis_"):
            skipping = True
            skip_depth = 0
        if skipping:
            skip_depth += line.count("{") - line.count("}")
            if skip_depth <= 0 and ("}" in line or "{" in line):
                skipping = False
            continue
        result.append(line)
    return "\n".join(result)


def _stub_externs(src: str) -> str:
    """Replace extern declarations with stub functions returning 0."""
    lines = src.splitlines()
    result: list[str] = []
    for line in lines:
        if line.startswith("extern "):
            stub = line.replace('extern "C" ', "")
            result.append(stub.rstrip() + " { return 0 }")
        else:
            result.append(line)
    return "\n".join(result)


def _redis_source() -> str:
    """Return inlined JSON + KV + EmbeddedKV + Redis module sources."""
    kv_no_stubs = _strip_redis_stubs(_strip_imports(_KV_MN))
    json_src = _strip_imports(_JSON_MN)
    embedded = _strip_imports(_EMBEDDED_KV_MN)
    redis = _stub_externs(_strip_imports(_REDIS_MN))
    return json_src + "\n\n" + kv_no_stubs + "\n\n" + embedded + "\n\n" + redis


def _redis_source_with_main(main_body: str) -> str:
    """Prepend the Redis module sources and wrap main_body in fn main()."""
    return _redis_source() + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Core types compile (no Redis needed)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRedisTypesCompile:
    def test_redis_store_struct_compiles(self) -> None:
        """RedisStore struct compiles."""
        src = _redis_source_with_main("""\
            let rs: RedisStore = new_redis_store(0, "127.0.0.1", 6379)
            println(rs.host)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_kv_store_redis_variant_compiles(self) -> None:
        """KVStore::Redis variant compiles."""
        src = _redis_source_with_main("""\
            let rs: RedisStore = new_redis_store(0, "localhost", 6379)
            let store: KVStore = Redis(rs)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_redis_error_compiles(self) -> None:
        """Redis error constructor compiles."""
        src = _redis_source_with_main("""\
            let e: KVError = new_redis_error("connection failed")
            println(e.message)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Internal helpers compile (no Redis needed)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestRedisHelpers:
    def test_build_command_compiles(self) -> None:
        """build_command helper compiles."""
        src = _redis_source_with_main("""\
            let cmd: String = build_command(["SET", "key", "val"])
            println(cmd)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_quote_value_compiles(self) -> None:
        """quote_value helper compiles."""
        src = _redis_source_with_main("""\
            let quoted: String = quote_value("hello world")
            println(quoted)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_int_simple_compiles(self) -> None:
        """parse_int_simple helper compiles."""
        src = _redis_source_with_main("""\
            let v: Int = parse_int_simple("42")
            println(str(v))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_parse_int_simple_negative_compiles(self) -> None:
        """parse_int_simple with negative number compiles."""
        src = _redis_source_with_main("""\
            let v: Int = parse_int_simple("-7")
            println(str(v))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_split_lines_compiles(self) -> None:
        """split_lines helper compiles."""
        src = _redis_source_with_main("""\
            let lines: List<String> = split_lines("a\\nb\\nc")
            println(str(len(lines)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Connect to Redis
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisConnect:
    def test_connect_compiles(self) -> None:
        """redis.connect compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(s) => { println("connected") },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Set/Get roundtrip
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisSetGet:
    def test_set_get_roundtrip_compiles(self) -> None:
        """redis.set then redis.get roundtrip compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let sr: Result<Bool, KVError> = redis_set(rs, "__mn_test_key", "test_value")
                            let val: Option<String> = redis_get(rs, "__mn_test_key")
                            match val {
                                Some(v) => { println(v) },
                                _ => { println("not found") }
                            }
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Del removes key
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisDel:
    def test_del_compiles(self) -> None:
        """redis.del compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let sr: Result<Bool, KVError> = redis_set(rs, "__mn_test_del", "to_delete")
                            let dr: Result<Bool, KVError> = redis_del(rs, "__mn_test_del")
                            match dr {
                                Ok(b) => { println("deleted") },
                                Err(e) => { println(e.message) }
                            }
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Exists
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisExists:
    def test_exists_compiles(self) -> None:
        """redis.exists compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let sr: Result<Bool, KVError> = redis_set(rs, "__mn_test_exists", "val")
                            let found: Bool = redis_exists(rs, "__mn_test_exists")
                            println(str(found))
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Set with TTL (set_ex)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisSetEx:
    def test_set_ex_compiles(self) -> None:
        """redis.set_ex with TTL compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let sr: Result<Bool, KVError> = set_ex(rs, "__mn_test_ttl", "expires_soon", 60)
                            match sr {
                                Ok(b) => { println("set with ttl") },
                                Err(e) => { println(e.message) }
                            }
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Incr/Decr atomic counters
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisIncrDecr:
    def test_incr_compiles(self) -> None:
        """redis.incr atomic increment compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let ir: Result<Int, KVError> = redis_incr(rs, "__mn_test_counter")
                            match ir {
                                Ok(v) => { println(str(v)) },
                                Err(e) => { println(e.message) }
                            }
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_decr_compiles(self) -> None:
        """redis.decr atomic decrement compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let dr: Result<Int, KVError> = redis_decr(rs, "__mn_test_counter")
                            match dr {
                                Ok(v) => { println(str(v)) },
                                Err(e) => { println(e.message) }
                            }
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Keys pattern matching
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisKeys:
    def test_keys_pattern_compiles(self) -> None:
        """redis.keys with pattern compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let sr: Result<Bool, KVError> = redis_set(rs, "__mn_keys_a", "1")
                            let sr2: Result<Bool, KVError> = redis_set(rs, "__mn_keys_b", "2")
                            let matched: List<String> = redis_keys(rs, "__mn_keys_*")
                            println(str(len(matched)))
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Close connection
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
@pytest.mark.skipif(not _HAS_REDIS, reason="Redis not available on localhost:6379")
class TestRedisClose:
    def test_close_compiles(self) -> None:
        """redis.close compiles."""
        src = _redis_source_with_main("""\
            let r: Result<KVStore, KVError> = redis_connect("127.0.0.1", 6379)
            match r {
                Ok(store) => {
                    match store {
                        Redis(rs) => {
                            let cr: Result<Bool, KVError> = redis_close(rs)
                            match cr {
                                Ok(b) => { println("closed") },
                                Err(e) => { println(e.message) }
                            }
                        },
                        Embedded(es) => { println("wrong variant") }
                    }
                },
                Err(e) => { println(e.message) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
