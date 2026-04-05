import os
import shutil
import textwrap
from pathlib import Path

import pytest

from mapanare.cli import _compile_to_llvm_ir

# ---------------------------------------------------------------------------
# Compiler and path detection
# ---------------------------------------------------------------------------

_CC = os.environ.get("CC") or shutil.which("gcc") or shutil.which("clang") or shutil.which("cc")
_IS_WINDOWS = os.name == "nt"

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parent.parent
_STDLIB_DIR = _REPO_ROOT / "stdlib"


def _redis_available() -> bool:
    """Check if a local Redis server is running."""
    import socket

    try:
        with socket.create_connection(("127.0.0.1", 6379), timeout=0.1):
            return True
    except (OSError, ConnectionRefusedError):
        return False


_HAS_REDIS = _redis_available()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KV_MN = (_STDLIB_DIR / "db" / "kv.mn").read_text(encoding="utf-8")
_EMBEDDED_KV_MN = (_STDLIB_DIR / "db" / "embedded_kv.mn").read_text(encoding="utf-8")
_JSON_MN = (_STDLIB_DIR / "encoding" / "json.mn").read_text(encoding="utf-8")
_STRING_UTILS_MN = (_STDLIB_DIR / "text" / "string_utils.mn").read_text(encoding="utf-8")
_REDIS_MN = (_STDLIB_DIR / "db" / "redis.mn").read_text(encoding="utf-8")


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_kv_redis.mn", use_mir=True)


def _strip_imports(source: str) -> str:
    """Remove import/usa lines since we inline all module sources."""
    return "\n".join(
        line for line in source.splitlines() if not line.strip().startswith(("import ", "usa "))
    )


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
    """Return inlined JSON + StringUtils + KV + EmbeddedKV + Redis module sources."""
    kv_no_stubs = _strip_redis_stubs(_strip_imports(_KV_MN))
    json_src = _strip_imports(_JSON_MN)
    string_utils = _strip_imports(_STRING_UTILS_MN)
    embedded = _strip_imports(_EMBEDDED_KV_MN)
    redis = _stub_externs(_strip_imports(_REDIS_MN))

    source = (
        json_src + "\n\n" + string_utils + "\n\n" + kv_no_stubs + "\n\n" + embedded + "\n\n" + redis
    )
    # Since we inline all modules into one file, we must remove module prefixes
    return source.replace("string_utils.", "")


def _redis_source_with_main(main_body: str) -> str:
    """Prepend the Redis module sources and wrap main_body in fn main()."""
    return _redis_source() + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestRedisTypesCompile:
    """Verify that Redis-related types and functions compile correctly."""

    def test_redis_store_struct_compiles(self) -> None:
        """RedisStore struct compiles."""
        src = _redis_source_with_main("""\
            let rs: RedisStore = new_redis_store(0, "127.0.0.1", 6379)
            print(rs.host)
        """)
        _compile_mir(src)

    def test_kv_store_redis_variant_compiles(self) -> None:
        """KVStore::Redis variant compiles."""
        src = _redis_source_with_main("""\
            let rs: RedisStore = new_redis_store(0, "localhost", 6379)
            let store: KVStore = Redis(rs)
            print("ok")
        """)
        _compile_mir(src)

    def test_redis_error_compiles(self) -> None:
        """Redis error constructor compiles."""
        src = _redis_source_with_main("""\
            let e: KVError = new_redis_error("connection failed")
            print(e.message)
        """)
        _compile_mir(src)


class TestRedisHelpers:
    """Verify that Redis helper functions compile and have correct signatures."""

    def test_build_command_compiles(self) -> None:
        """build_command helper compiles."""
        src = _redis_source_with_main("""\
            let cmd: String = build_command(["SET", "key", "val"])
            print(cmd)
        """)
        ir_out = _compile_mir(src)
        assert "build_command" in ir_out

    def test_quote_value_compiles(self) -> None:
        """quote_value helper compiles."""
        src = _redis_source_with_main("""\
            let quoted: String = quote_value("hello world")
            print(quoted)
        """)
        ir_out = _compile_mir(src)
        assert "quote_value" in ir_out

    def test_parse_int_simple_compiles(self) -> None:
        """parse_int_simple helper compiles."""
        src = _redis_source_with_main("""\
            let v: Int = parse_int_simple("42")
            print(str(v))
        """)
        ir_out = _compile_mir(src)
        assert "parse_int_simple" in ir_out

    def test_parse_int_simple_negative_compiles(self) -> None:
        """parse_int_simple with negative number compiles."""
        src = _redis_source_with_main("""\
            let v: Int = parse_int_simple("-7")
            print(str(v))
        """)
        ir_out = _compile_mir(src)
        assert "parse_int_simple" in ir_out

    def test_split_lines_compiles(self) -> None:
        """split_lines helper compiles."""
        src = _redis_source_with_main("""\
            let lines: List<String> = split_lines("a\\nb\\nc")
            print(str(len(lines)))
        """)
        ir_out = _compile_mir(src)
        assert "split_lines" in ir_out


@pytest.mark.skipif(not _HAS_REDIS, reason="Redis server not running on localhost:6379")
class TestRedisIntegration:
    """Integration tests with a real Redis server."""

    def test_redis_ping(self, tmp_path: Path) -> None:
        """Test basic Redis PING command."""
        # This test would require a full compiler + execution setup
        pass
