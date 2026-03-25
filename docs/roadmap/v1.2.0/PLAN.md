# Mapanare v1.2.0 — "Data & Storage"

> v1.1.0 gave Mapanare native AI capabilities — LLM drivers, embeddings, RAG — all in `.mn`.
> v1.2.0 adds the data layer: SQL databases, key-value stores, serialization formats,
> filesystem operations, and the Dato DataFrame library. After this release, Mapanare
> programs can read, transform, and persist data end-to-end without leaving the language.
>
> Core theme: **Make data a first-class citizen. Every data operation compiles to native code.**

---

## Scope Rules

1. **All new modules are `.mn` files** — compiled via LLVM, no Python runtime dependency
2. **C runtime extensions only for OS primitives** — FFI to libpq, libsqlite3, hiredis, libarrow; everything above is pure Mapanare
3. **Security by default** — parameterized SQL queries (no string interpolation in queries), validated inputs at FFI boundaries
4. **Stream-native** — large datasets use `Stream<T>` for lazy, backpressure-aware processing; no "load everything into memory" APIs
5. **Agent-native** — connection pools are supervised agents, parallel transforms spawn agent workers
6. **Dato is a separate package** (`github.com/Mapanare-Research/dato`) — this plan covers stdlib modules that Dato depends on, plus the Dato v1.0 design itself

---

## Status Tracking

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (reason noted) |

---

## Phase Overview

| Phase | Name | Status | Effort | Platform |
|-------|------|--------|--------|----------|
| 1 | C Runtime: Database & FS Primitives | `Not Started` | Large | WSL/Linux |
| 2 | `encoding/toml.mn` — TOML Parser/Serializer | `Not Started` | Medium | Windows |
| 3 | `encoding/yaml.mn` — YAML Parser/Serializer | `Not Started` | Large | Windows |
| 4 | `fs.mn` — Filesystem Operations | `Not Started` | Medium | WSL/Linux |
| 5 | `db/sql.mn` — SQL Database Drivers | `Not Started` | X-Large | WSL/Linux |
| 6 | `db/kv.mn` — Key-Value Store Interface | `Not Started` | Medium | WSL/Linux |
| 7 | Dato v1.0 — DataFrame Library | `Not Started` | X-Large | Both |
| 8 | Integration Testing & Release | `Not Started` | Large | Both |

---

## Prerequisites (from v1.1.0)

These must be complete before v1.2.0 work begins:

| # | Prerequisite | Status | Notes |
|---|-------------|--------|-------|
| 1 | v1.1.0 released (AI native stdlib: LLM drivers, embeddings, RAG) | `[ ]` | Validates .mn stdlib pattern at scale |
| 2 | `extern "C"` FFI working for `.mn` → C library calls | `[x]` | Used by `ai/llm.mn` for TCP/TLS; same pattern for libpq, sqlite3 |
| 3 | `encoding/json.mn` stable (947 lines, RFC 8259 compliant) | `[x]` | Reference implementation for new parsers |
| 4 | `encoding/csv.mn` stable (440 lines, RFC 4180 compliant) | `[x]` | Reference for streaming row parsers |
| 5 | C runtime file I/O (`__mn_file_read`, `__mn_file_write`, `__mn_file_open`, `__mn_file_stat`, `__mn_dir_list`) | `[x]` | In `mapanare_core.h` + `mapanare_io.h` |
| 6 | Trait system working on LLVM backend | `[x]` | Required for `KVStore` trait, `SqlDriver` trait |

---

## Phase 1 — C Runtime: Database & Filesystem Primitives
**Status:** `Not Started`
**Priority:** CRITICAL — every Phase 4-6 module calls into these C functions
**Platform:** WSL/Linux (C compilation + linking)
**Effort:** Large (1-2 weeks)

Extend `runtime/native/` with thin FFI wrappers around system libraries.
Each wrapper exposes `MnString`-based APIs so `.mn` modules can call them directly.
Libraries are loaded via `dlopen` (like OpenSSL for TLS) — no hard link-time dependency.

### SQLite3 Bindings

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Add `__mn_sqlite3_open(path: MnString) -> Int` — open/create database | `[ ]` | `runtime/native/mapanare_db.c`, `mapanare_db.h` | Returns opaque handle (>0) or 0 on error |
| 2 | Add `__mn_sqlite3_close(handle: Int)` — close database | `[ ]` | `mapanare_db.c` | |
| 3 | Add `__mn_sqlite3_exec(handle, sql: MnString) -> Int` — execute non-query SQL | `[ ]` | `mapanare_db.c` | Returns 0 on success, error code on failure |
| 4 | Add `__mn_sqlite3_prepare(handle, sql: MnString) -> Int` — prepare statement | `[ ]` | `mapanare_db.c` | Returns statement handle |
| 5 | Add `__mn_sqlite3_bind_int(stmt, idx, val)`, `bind_float`, `bind_str`, `bind_null` | `[ ]` | `mapanare_db.c` | Parameterized query binding — THE security boundary |
| 6 | Add `__mn_sqlite3_step(stmt) -> Int` — step through results | `[ ]` | `mapanare_db.c` | Returns ROW (100), DONE (101), or error |
| 7 | Add `__mn_sqlite3_column_int(stmt, idx)`, `column_float`, `column_str`, `column_type` | `[ ]` | `mapanare_db.c` | Read result columns with proper type tagging |
| 8 | Add `__mn_sqlite3_finalize(stmt)` — finalize prepared statement | `[ ]` | `mapanare_db.c` | |
| 9 | Add `__mn_sqlite3_errmsg(handle) -> MnString` — last error message | `[ ]` | `mapanare_db.c` | |
| 10 | Add `__mn_sqlite3_column_count(stmt) -> Int` — number of result columns | `[ ]` | `mapanare_db.c` | |
| 11 | Add `__mn_sqlite3_column_name(stmt, idx) -> MnString` — column name | `[ ]` | `mapanare_db.c` | For Row → Map<String, Value> conversion |

### PostgreSQL Bindings (libpq)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 12 | Add `__mn_pg_connect(conninfo: MnString) -> Int` — connect to PostgreSQL | `[ ]` | `mapanare_db.c` | Standard libpq connection string format |
| 13 | Add `__mn_pg_close(conn)` — close connection | `[ ]` | `mapanare_db.c` | |
| 14 | Add `__mn_pg_exec(conn, sql: MnString) -> Int` — execute query, return result handle | `[ ]` | `mapanare_db.c` | |
| 15 | Add `__mn_pg_exec_params(conn, sql, params: MnList) -> Int` — parameterized query | `[ ]` | `mapanare_db.c` | params is `List<String>` — libpq text format |
| 16 | Add `__mn_pg_ntuples(result)`, `nfields(result)` — result dimensions | `[ ]` | `mapanare_db.c` | |
| 17 | Add `__mn_pg_getvalue(result, row, col) -> MnString` — read cell | `[ ]` | `mapanare_db.c` | |
| 18 | Add `__mn_pg_fname(result, col) -> MnString` — column name | `[ ]` | `mapanare_db.c` | |
| 19 | Add `__mn_pg_status(result) -> Int` — result status code | `[ ]` | `mapanare_db.c` | PGRES_TUPLES_OK, PGRES_COMMAND_OK, etc. |
| 20 | Add `__mn_pg_errmsg(conn) -> MnString` — last error message | `[ ]` | `mapanare_db.c` | |
| 21 | Add `__mn_pg_clear(result)` — free result | `[ ]` | `mapanare_db.c` | |

### Redis Bindings (hiredis)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 22 | Add `__mn_redis_connect(host: MnString, port: Int) -> Int` — connect | `[ ]` | `mapanare_db.c` | Returns opaque context handle |
| 23 | Add `__mn_redis_command(ctx, cmd: MnString) -> MnString` — execute command | `[ ]` | `mapanare_db.c` | Returns reply as string (simple protocol) |
| 24 | Add `__mn_redis_command_status(ctx, cmd) -> Int` — execute, return status | `[ ]` | `mapanare_db.c` | For SET/DEL/etc. where reply is OK/integer |
| 25 | Add `__mn_redis_close(ctx)` — disconnect | `[ ]` | `mapanare_db.c` | |
| 26 | Add `__mn_redis_errmsg(ctx) -> MnString` — last error | `[ ]` | `mapanare_db.c` | |

### Extended Filesystem Primitives

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 27 | Add `__mn_file_exists(path) -> Int` — check file/dir existence | `[ ]` | `mapanare_io.c` | |
| 28 | Add `__mn_file_remove(path) -> Int` — delete file | `[ ]` | `mapanare_io.c` | |
| 29 | Add `__mn_dir_create(path, recursive) -> Int` — mkdir | `[ ]` | `mapanare_io.c` | |
| 30 | Add `__mn_dir_remove(path) -> Int` — rmdir (empty only) | `[ ]` | `mapanare_io.c` | |
| 31 | Add `__mn_file_rename(old, new) -> Int` — rename/move | `[ ]` | `mapanare_io.c` | |
| 32 | Add `__mn_file_copy(src, dst) -> Int` — copy file | `[ ]` | `mapanare_io.c` | Read + write, not sendfile (portability) |
| 33 | Add `__mn_tmpfile() -> MnString` — create temp file, return path | `[ ]` | `mapanare_io.c` | |
| 34 | Add `__mn_realpath(path) -> MnString` — resolve to absolute path | `[ ]` | `mapanare_io.c` | |
| 35 | Add `__mn_file_size(path) -> Int` — file size in bytes | `[ ]` | `mapanare_io.c` | Thin wrapper on `__mn_file_stat` |
| 36 | Add `__mn_file_mtime(path) -> Int` — modification time (epoch seconds) | `[ ]` | `mapanare_io.c` | |

### dlopen Loading Strategy

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 37 | Implement `dlopen("libsqlite3.so")` with graceful fallback | `[ ]` | `mapanare_db.c` | Same pattern as TLS/PCRE2: function pointers, NULL check, error message |
| 38 | Implement `dlopen("libpq.so")` with graceful fallback | `[ ]` | `mapanare_db.c` | |
| 39 | Implement `dlopen("libhiredis.so")` with graceful fallback | `[ ]` | `mapanare_db.c` | |
| 40 | Add `build_db.py` — compile `mapanare_db.c` into shared library | `[ ]` | `runtime/native/build_db.py` | Follows `build_io.py` pattern |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 41 | Test: SQLite3 open/close/exec/prepare/step/finalize cycle | `[ ]` | `tests/native/test_db_sqlite.py` | Uses in-memory `:memory:` DB |
| 42 | Test: SQLite3 parameterized queries prevent injection | `[ ]` | `tests/native/test_db_sqlite.py` | `'; DROP TABLE --` must not execute |
| 43 | Test: PostgreSQL connect/query/close (requires running PG) | `[ ]` | `tests/native/test_db_postgres.py` | Skip if libpq not found; CI needs PG service |
| 44 | Test: Redis connect/command/close (requires running Redis) | `[ ]` | `tests/native/test_db_redis.py` | Skip if hiredis not found |
| 45 | Test: Extended filesystem ops (exists, remove, mkdir, rename, copy) | `[ ]` | `tests/native/test_fs_extended.py` | Use temp directory for isolation |
| 46 | Test: dlopen graceful fallback when library not installed | `[ ]` | `tests/native/test_db_dlopen.py` | Verify error message, not crash |

**Done when:** All C runtime database and filesystem functions compile, link, and pass tests.
SQLite3 tests pass without external services. PostgreSQL and Redis tests pass when services are available.

---

## Phase 2 — `encoding/toml.mn` — TOML Parser/Serializer
**Status:** `Not Started`
**Priority:** HIGH — TOML is the config format for `mapanare.toml` project files and data pipeline configs
**Platform:** Windows (pure Mapanare, no C dependencies)
**Effort:** Medium (3-5 days)

Pure Mapanare TOML v1.0 parser/serializer. Follows the same patterns as `encoding/json.mn`:
recursive descent parser, typed value enum, encode/decode with `Result` error handling.

### Core Types & Parser

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `TomlValue` enum: `String`, `Int`, `Float`, `Bool`, `DateTime`, `Array`, `Table`, `InlineTable` | `[ ]` | `stdlib/encoding/toml.mn` | `DateTime` stored as string for v1.2 (full datetime type in v1.3) |
| 2 | Define `TomlError` struct with message, line, col | `[ ]` | `stdlib/encoding/toml.mn` | |
| 3 | Implement `decode(input: String) -> Result<TomlValue, TomlError>` — top-level parser entry | `[ ]` | `stdlib/encoding/toml.mn` | |
| 4 | Parse bare keys and quoted keys: `key = value`, `"key with spaces" = value` | `[ ]` | `stdlib/encoding/toml.mn` | |
| 5 | Parse dotted keys: `server.host = "localhost"` | `[ ]` | `stdlib/encoding/toml.mn` | |
| 6 | Parse basic strings (double-quoted, escape sequences) and literal strings (single-quoted) | `[ ]` | `stdlib/encoding/toml.mn` | `\n`, `\t`, `\\`, `\"`, `\uXXXX` |
| 7 | Parse multi-line basic strings (`"""..."""`) and multi-line literal strings (`'''...'''`) | `[ ]` | `stdlib/encoding/toml.mn` | |
| 8 | Parse integers: decimal, hex (`0x`), octal (`0o`), binary (`0b`), underscores | `[ ]` | `stdlib/encoding/toml.mn` | |
| 9 | Parse floats: fractional, exponent, special values (`inf`, `nan`) | `[ ]` | `stdlib/encoding/toml.mn` | |
| 10 | Parse booleans: `true`, `false` | `[ ]` | `stdlib/encoding/toml.mn` | |
| 11 | Parse datetime: offset date-time, local date-time, local date, local time | `[ ]` | `stdlib/encoding/toml.mn` | Stored as string, validated format |
| 12 | Parse arrays: `[1, 2, 3]`, heterogeneous disallowed per TOML spec | `[ ]` | `stdlib/encoding/toml.mn` | |
| 13 | Parse inline tables: `{name = "Tom", age = 30}` | `[ ]` | `stdlib/encoding/toml.mn` | |
| 14 | Parse standard tables: `[table]`, `[parent.child]` | `[ ]` | `stdlib/encoding/toml.mn` | Dotted table headers create nested structure |
| 15 | Parse array of tables: `[[products]]` | `[ ]` | `stdlib/encoding/toml.mn` | Each occurrence appends to array |
| 16 | Handle comments: `# comment to end of line` | `[ ]` | `stdlib/encoding/toml.mn` | |
| 17 | Validate: no key redefinition, no mixing inline/standard tables | `[ ]` | `stdlib/encoding/toml.mn` | |

### Serializer

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 18 | Implement `encode(value: TomlValue) -> String` — serialize to TOML string | `[ ]` | `stdlib/encoding/toml.mn` | Ordered output: simple values first, then sub-tables, then array-of-tables |
| 19 | Implement `encode_pretty(value: TomlValue) -> String` — with aligned `=` signs | `[ ]` | `stdlib/encoding/toml.mn` | Optional cosmetic alignment |

### Typed Decode

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 20 | Implement helper `get_string(table, key) -> Result<String, TomlError>` | `[ ]` | `stdlib/encoding/toml.mn` | Type-safe field access |
| 21 | Implement helper `get_int`, `get_float`, `get_bool`, `get_array`, `get_table` | `[ ]` | `stdlib/encoding/toml.mn` | |
| 22 | Implement helper `get_or(table, key, default) -> T` — with default fallback | `[ ]` | `stdlib/encoding/toml.mn` | |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 23 | Test: parse all TOML value types (string, int, float, bool, datetime, array, table) | `[ ]` | `tests/stdlib/test_toml.py` | |
| 24 | Test: parse dotted keys, nested tables, array of tables | `[ ]` | `tests/stdlib/test_toml.py` | |
| 25 | Test: parse multi-line strings (basic + literal) | `[ ]` | `tests/stdlib/test_toml.py` | |
| 26 | Test: encode → decode roundtrip preserves structure | `[ ]` | `tests/stdlib/test_toml.py` | |
| 27 | Test: error on invalid TOML (duplicate keys, mixed types in array, bad escapes) | `[ ]` | `tests/stdlib/test_toml.py` | |
| 28 | Test: parse `mapanare.toml` project file format | `[ ]` | `tests/stdlib/test_toml.py` | Validate our own config format |
| 29 | Test: compile `encoding/toml.mn` to LLVM IR and verify output | `[ ]` | `tests/e2e/test_toml_native.py` | End-to-end: .mn → IR → parse TOML |

**Done when:** `encoding/toml.mn` passes TOML v1.0 spec tests. Encode/decode roundtrip works.
Can parse `mapanare.toml` project files natively.

---

## Phase 3 — `encoding/yaml.mn` — YAML Parser/Serializer
**Status:** `Not Started`
**Priority:** HIGH — YAML is the config format for CI, Docker, Kubernetes, and scan templates (v1.3.0)
**Platform:** Windows (pure Mapanare, no C dependencies)
**Effort:** Large (1-2 weeks)

Pure Mapanare YAML 1.2 (Core Schema) parser/serializer. YAML is significantly more complex
than TOML or JSON — indentation-based structure, anchors/aliases, multi-document streams,
and ambiguous type coercion. We implement the Core Schema subset (no custom tags).

### Core Types & Parser

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `YamlValue` enum: `Null`, `Bool`, `Int`, `Float`, `Str`, `Seq`, `Map` | `[ ]` | `stdlib/encoding/yaml.mn` | `Seq` = `List<YamlValue>`, `Map` = ordered `List<(String, YamlValue)>` (not hash map — YAML maps preserve order) |
| 2 | Define `YamlError` struct with message, line, col | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 3 | Implement indentation tracker: track indent stack for block context | `[ ]` | `stdlib/encoding/yaml.mn` | The core complexity of YAML parsing |
| 4 | Implement `decode(input: String) -> Result<YamlValue, YamlError>` — single document | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 5 | Implement `decode_all(input: String) -> Result<List<YamlValue>, YamlError>` — multi-document | `[ ]` | `stdlib/encoding/yaml.mn` | `---` separators |
| 6 | Parse block mappings: `key: value` with indentation | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 7 | Parse block sequences: `- item` with indentation | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 8 | Parse flow mappings: `{key: value, key2: value2}` | `[ ]` | `stdlib/encoding/yaml.mn` | JSON-compatible flow syntax |
| 9 | Parse flow sequences: `[item1, item2, item3]` | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 10 | Parse scalars: plain (unquoted), single-quoted, double-quoted | `[ ]` | `stdlib/encoding/yaml.mn` | Plain scalars resolved by Core Schema |
| 11 | Implement Core Schema type resolution: `null`, `true/false`, int, float, string fallback | `[ ]` | `stdlib/encoding/yaml.mn` | `true/True/TRUE`, `null/Null/~`, `0x`, `0o`, `.inf`, `.nan` |
| 12 | Parse block literal scalars: `\|` (keep newlines) and `>` (fold newlines) | `[ ]` | `stdlib/encoding/yaml.mn` | With chomp indicators: `-` (strip), `+` (keep), default (clip) |
| 13 | Parse anchors (`&name`) and aliases (`*name`) | `[ ]` | `stdlib/encoding/yaml.mn` | Limited: no recursive anchors; expand on parse (no reference sharing) |
| 14 | Parse comments: `# comment to end of line` | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 15 | Parse document markers: `---` (start), `...` (end) | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 16 | Handle mixed block/flow nesting: block map with flow value, etc. | `[ ]` | `stdlib/encoding/yaml.mn` | |
| 17 | Handle edge cases: empty documents, empty mappings, empty sequences, trailing whitespace | `[ ]` | `stdlib/encoding/yaml.mn` | |

### Serializer

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 18 | Implement `encode(value: YamlValue) -> String` — serialize to block-style YAML | `[ ]` | `stdlib/encoding/yaml.mn` | Default: block style for readability |
| 19 | Implement `encode_flow(value: YamlValue) -> String` — serialize to flow (compact) style | `[ ]` | `stdlib/encoding/yaml.mn` | JSON-like output |
| 20 | Smart string quoting: plain for simple values, quoted when needed | `[ ]` | `stdlib/encoding/yaml.mn` | Quote strings that look like booleans/numbers/nulls |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 21 | Test: parse all YAML scalar types (null, bool, int, float, string) | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 22 | Test: parse block mappings and sequences (nested, mixed) | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 23 | Test: parse flow mappings and sequences | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 24 | Test: parse literal and folded block scalars with chomp indicators | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 25 | Test: parse anchors and aliases | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 26 | Test: parse multi-document streams | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 27 | Test: encode → decode roundtrip preserves structure | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 28 | Test: error on invalid YAML (bad indentation, duplicate anchors, tab indentation) | `[ ]` | `tests/stdlib/test_yaml.py` | |
| 29 | Test: parse real-world YAML (GitHub Actions workflow, Docker Compose, Kubernetes pod spec) | `[ ]` | `tests/stdlib/test_yaml.py` | Use sanitized snippets as test fixtures |
| 30 | Test: compile `encoding/yaml.mn` to LLVM IR and verify output | `[ ]` | `tests/e2e/test_yaml_native.py` | End-to-end: .mn → IR → parse YAML |

**Done when:** `encoding/yaml.mn` parses YAML 1.2 Core Schema correctly. Roundtrip encode/decode works.
Can parse common config files (CI, Docker Compose) without errors.

---

## Phase 4 — `fs.mn` — Filesystem Operations
**Status:** `Not Started`
**Priority:** HIGH — every data pipeline reads/writes files; Dato depends on this
**Platform:** WSL/Linux (FFI to C runtime) + Windows (cross-platform tests)
**Effort:** Medium (3-5 days)

High-level filesystem module built on top of C runtime primitives from Phase 1.
Provides `Path` type, directory operations, file metadata, and streaming file reads.

### Path Type

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `struct Path { raw: String }` — wrapper for path strings | `[ ]` | `stdlib/fs.mn` | |
| 2 | Implement `Path.join(other: String) -> Path` — platform-aware path joining | `[ ]` | `stdlib/fs.mn` | Use `/` separator (POSIX-first, works on Windows too) |
| 3 | Implement `Path.parent() -> Path` — parent directory | `[ ]` | `stdlib/fs.mn` | |
| 4 | Implement `Path.filename() -> String` — last component | `[ ]` | `stdlib/fs.mn` | |
| 5 | Implement `Path.extension() -> String` — file extension (without dot) | `[ ]` | `stdlib/fs.mn` | |
| 6 | Implement `Path.stem() -> String` — filename without extension | `[ ]` | `stdlib/fs.mn` | |
| 7 | Implement `Path.is_absolute() -> Bool` — starts with `/` or drive letter | `[ ]` | `stdlib/fs.mn` | |
| 8 | Implement `Path.resolve() -> Result<Path, FsError>` — absolute path via C runtime `__mn_realpath` | `[ ]` | `stdlib/fs.mn` | |

### File Operations

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 9 | Implement `read_file(path: String) -> Result<String, FsError>` | `[ ]` | `stdlib/fs.mn` | Wraps `__mn_file_read` with Result |
| 10 | Implement `write_file(path: String, content: String) -> Result<(), FsError>` | `[ ]` | `stdlib/fs.mn` | Wraps `__mn_file_write` |
| 11 | Implement `append_file(path: String, content: String) -> Result<(), FsError>` | `[ ]` | `stdlib/fs.mn` | Uses `__mn_file_open` with MN_FILE_APPEND |
| 12 | Implement `exists(path: String) -> Bool` | `[ ]` | `stdlib/fs.mn` | |
| 13 | Implement `remove(path: String) -> Result<(), FsError>` | `[ ]` | `stdlib/fs.mn` | |
| 14 | Implement `rename(old: String, new: String) -> Result<(), FsError>` | `[ ]` | `stdlib/fs.mn` | |
| 15 | Implement `copy(src: String, dst: String) -> Result<(), FsError>` | `[ ]` | `stdlib/fs.mn` | |
| 16 | Implement `file_size(path: String) -> Result<Int, FsError>` | `[ ]` | `stdlib/fs.mn` | |
| 17 | Implement `file_mtime(path: String) -> Result<Int, FsError>` | `[ ]` | `stdlib/fs.mn` | Epoch seconds |
| 18 | Implement `is_dir(path: String) -> Bool` | `[ ]` | `stdlib/fs.mn` | |
| 19 | Implement `is_file(path: String) -> Bool` | `[ ]` | `stdlib/fs.mn` | |

### Directory Operations

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 20 | Implement `mkdir(path: String) -> Result<(), FsError>` — create directory | `[ ]` | `stdlib/fs.mn` | |
| 21 | Implement `mkdir_all(path: String) -> Result<(), FsError>` — recursive create | `[ ]` | `stdlib/fs.mn` | |
| 22 | Implement `rmdir(path: String) -> Result<(), FsError>` — remove empty dir | `[ ]` | `stdlib/fs.mn` | |
| 23 | Implement `list_dir(path: String) -> Result<List<DirEntry>, FsError>` | `[ ]` | `stdlib/fs.mn` | `DirEntry { name: String, is_dir: Bool }` |
| 24 | Implement `walk(path: String) -> List<String>` — recursive directory listing | `[ ]` | `stdlib/fs.mn` | Returns flat list of all file paths |
| 25 | Implement `tmpfile() -> Result<String, FsError>` — create temp file | `[ ]` | `stdlib/fs.mn` | |

### Streaming File I/O

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 26 | Implement `read_lines(path: String) -> Result<Stream<String>, FsError>` | `[ ]` | `stdlib/fs.mn` | Stream-based, reads line by line without loading entire file |
| 27 | Implement `read_chunks(path: String, chunk_size: Int) -> Result<Stream<String>, FsError>` | `[ ]` | `stdlib/fs.mn` | For binary/large file processing |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 28 | Test: Path join, parent, filename, extension, stem, resolve | `[ ]` | `tests/stdlib/test_fs.py` | |
| 29 | Test: read/write/append file roundtrip | `[ ]` | `tests/stdlib/test_fs.py` | |
| 30 | Test: exists, remove, rename, copy | `[ ]` | `tests/stdlib/test_fs.py` | |
| 31 | Test: mkdir, mkdir_all, rmdir, list_dir, walk | `[ ]` | `tests/stdlib/test_fs.py` | |
| 32 | Test: read_lines streams lazily (doesn't OOM on large file) | `[ ]` | `tests/stdlib/test_fs.py` | Create 1M-line temp file, stream through |
| 33 | Test: error handling (file not found, permission denied, etc.) | `[ ]` | `tests/stdlib/test_fs.py` | |
| 34 | Test: compile `fs.mn` to LLVM IR and verify output | `[ ]` | `tests/e2e/test_fs_native.py` | |

**Done when:** `fs.mn` provides complete file/directory operations with Result-based error handling.
Streaming file reads work without loading entire files into memory.

---

## Phase 5 — `db/sql.mn` — SQL Database Drivers
**Status:** `Not Started`
**Priority:** CRITICAL — the central module of v1.2.0; Dato depends on it
**Platform:** WSL/Linux (requires C runtime from Phase 1)
**Effort:** X-Large (2+ weeks)

High-level SQL interface with driver trait, connection pooling via agents, parameterized queries,
transactions, and migration support. Built on Phase 1 C runtime bindings.

### Core Types

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `enum SqlValue { Null, Int(Int), Float(Float), Str(String), Bool(Bool), Blob(List<Int>) }` | `[ ]` | `stdlib/db/sql.mn` | Universal SQL value representation |
| 2 | Define `struct Row { columns: List<String>, values: List<SqlValue> }` | `[ ]` | `stdlib/db/sql.mn` | Named column access |
| 3 | Implement `Row.get(name: String) -> Option<SqlValue>` — column access by name | `[ ]` | `stdlib/db/sql.mn` | |
| 4 | Implement `Row.get_string(name) -> Option<String>`, `get_int`, `get_float`, `get_bool` | `[ ]` | `stdlib/db/sql.mn` | Type-safe accessors |
| 5 | Define `struct QueryResult { rows: List<Row>, affected: Int }` | `[ ]` | `stdlib/db/sql.mn` | |
| 6 | Define `enum SqlError { ConnectionFailed(String), QueryFailed(String), TypeMismatch(String), DriverNotFound(String) }` | `[ ]` | `stdlib/db/sql.mn` | |

### Driver Trait

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 7 | Define `trait SqlDriver` with connect, query, execute, close | `[ ]` | `stdlib/db/sql.mn` | `fn query(sql: String, params: List<SqlValue>) -> Result<QueryResult, SqlError>` |
| 8 | Implement `struct SqliteDriver` implementing `SqlDriver` | `[ ]` | `stdlib/db/sqlite.mn` | Wraps Phase 1 `__mn_sqlite3_*` functions |
| 9 | Implement `struct PostgresDriver` implementing `SqlDriver` | `[ ]` | `stdlib/db/postgres.mn` | Wraps Phase 1 `__mn_pg_*` functions |
| 10 | Implement `SqliteDriver.query` — prepare, bind params, step, collect rows | `[ ]` | `stdlib/db/sqlite.mn` | Central piece: SqlValue → sqlite3_bind_* dispatch |
| 11 | Implement `SqliteDriver.execute` — for INSERT/UPDATE/DELETE (no rows returned) | `[ ]` | `stdlib/db/sqlite.mn` | Returns affected row count |
| 12 | Implement `PostgresDriver.query` — exec_params, collect rows from result | `[ ]` | `stdlib/db/postgres.mn` | SqlValue → text format conversion for libpq |
| 13 | Implement `PostgresDriver.execute` — exec_params for non-query statements | `[ ]` | `stdlib/db/postgres.mn` | |

### Connection Management

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 14 | Define `struct Connection { driver: SqlDriver, url: String }` | `[ ]` | `stdlib/db/sql.mn` | |
| 15 | Implement `connect(url: String) -> Result<Connection, SqlError>` — URL-based dispatch | `[ ]` | `stdlib/db/sql.mn` | `sqlite:///path`, `postgres://user:pass@host/db` |
| 16 | Implement URL parsing: extract scheme, host, port, database, credentials | `[ ]` | `stdlib/db/sql.mn` | Simple parser — no need for full URI spec |

### Transactions

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 17 | Implement `begin(conn) -> Result<Transaction, SqlError>` | `[ ]` | `stdlib/db/sql.mn` | Sends `BEGIN` |
| 18 | Implement `Transaction.commit() -> Result<(), SqlError>` | `[ ]` | `stdlib/db/sql.mn` | |
| 19 | Implement `Transaction.rollback() -> Result<(), SqlError>` | `[ ]` | `stdlib/db/sql.mn` | |
| 20 | Implement `with_transaction(conn, fn) -> Result<T, SqlError>` — auto commit/rollback | `[ ]` | `stdlib/db/sql.mn` | Rollback on error, commit on success |

### Connection Pool (Agent-Based)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 21 | Define `agent PoolManager` — supervises N connection agents | `[ ]` | `stdlib/db/pool.mn` | |
| 22 | Implement pool checkout: request connection → receive from idle queue | `[ ]` | `stdlib/db/pool.mn` | Blocks if all connections busy (backpressure via channels) |
| 23 | Implement pool return: release connection back to idle queue | `[ ]` | `stdlib/db/pool.mn` | |
| 24 | Implement pool configuration: min/max connections, idle timeout | `[ ]` | `stdlib/db/pool.mn` | |
| 25 | Implement health check: periodic ping on idle connections | `[ ]` | `stdlib/db/pool.mn` | Agent sends `SELECT 1` on timer |

### Streaming Query Results

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 26 | Implement `query_stream(conn, sql, params) -> Result<Stream<Row>, SqlError>` | `[ ]` | `stdlib/db/sql.mn` | Returns lazy stream — rows fetched on demand |
| 27 | Implement cursor-based streaming for PostgreSQL (DECLARE CURSOR + FETCH) | `[ ]` | `stdlib/db/postgres.mn` | For large result sets |
| 28 | Implement step-based streaming for SQLite (sqlite3_step in a loop) | `[ ]` | `stdlib/db/sqlite.mn` | Natural streaming — step returns one row at a time |

### Migrations

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 29 | Define migration format: `struct Migration { version: Int, name: String, up: String, down: String }` | `[ ]` | `stdlib/db/migrate.mn` | |
| 30 | Implement `migrate_up(conn, migrations: List<Migration>) -> Result<(), SqlError>` | `[ ]` | `stdlib/db/migrate.mn` | Applies pending migrations in order |
| 31 | Implement `migrate_down(conn, target_version: Int) -> Result<(), SqlError>` | `[ ]` | `stdlib/db/migrate.mn` | Rolls back to target version |
| 32 | Implement migration tracking table: `__mn_migrations` with version, name, applied_at | `[ ]` | `stdlib/db/migrate.mn` | Auto-created on first migration |
| 33 | Implement `migration_status(conn) -> Result<List<MigrationInfo>, SqlError>` | `[ ]` | `stdlib/db/migrate.mn` | Shows applied/pending |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 34 | Test: SQLite CRUD — create table, insert, select, update, delete | `[ ]` | `tests/stdlib/test_sql_sqlite.py` | In-memory DB for speed |
| 35 | Test: SQLite parameterized queries — bind int, float, string, null, bool | `[ ]` | `tests/stdlib/test_sql_sqlite.py` | |
| 36 | Test: SQLite transactions — commit persists, rollback reverts | `[ ]` | `tests/stdlib/test_sql_sqlite.py` | |
| 37 | Test: SQLite streaming query — large result set, verify lazy evaluation | `[ ]` | `tests/stdlib/test_sql_sqlite.py` | Insert 10K rows, stream, verify no OOM |
| 38 | Test: PostgreSQL CRUD (skip if PG not available) | `[ ]` | `tests/stdlib/test_sql_postgres.py` | |
| 39 | Test: PostgreSQL parameterized queries | `[ ]` | `tests/stdlib/test_sql_postgres.py` | |
| 40 | Test: PostgreSQL transactions | `[ ]` | `tests/stdlib/test_sql_postgres.py` | |
| 41 | Test: Connection URL parsing (sqlite, postgres schemes) | `[ ]` | `tests/stdlib/test_sql_core.py` | |
| 42 | Test: Connection pool — checkout, return, max connections | `[ ]` | `tests/stdlib/test_sql_pool.py` | |
| 43 | Test: Migrations — up, down, status, idempotent re-apply | `[ ]` | `tests/stdlib/test_sql_migrate.py` | |
| 44 | Test: SQL injection attempt fails with parameterized queries | `[ ]` | `tests/stdlib/test_sql_security.py` | `Robert'; DROP TABLE students;--` |
| 45 | Test: compile `db/sql.mn` + `db/sqlite.mn` to LLVM IR | `[ ]` | `tests/e2e/test_sql_native.py` | |

**Done when:** SQLite driver fully functional end-to-end. PostgreSQL driver works when libpq is available.
Connection pooling works via agent supervision. Migrations can be applied and rolled back.
All parameterized query tests pass — zero SQL injection vectors.

---

## Phase 6 — `db/kv.mn` — Key-Value Store Interface
**Status:** `Not Started`
**Priority:** MEDIUM — useful for caching, sessions, and simple data persistence
**Platform:** WSL/Linux (Redis requires hiredis; embedded KV is pure Mapanare)
**Effort:** Medium (3-5 days)

Trait-based KV store interface with two implementations: Redis (FFI) and embedded (arena-backed).

### KVStore Trait

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `trait KVStore` | `[ ]` | `stdlib/db/kv.mn` | `fn get(key: String) -> Option<String>`, `fn set(key: String, value: String)`, `fn del(key: String) -> Bool`, `fn exists(key: String) -> Bool`, `fn keys() -> List<String>` |
| 2 | Define `struct KVError { message: String }` | `[ ]` | `stdlib/db/kv.mn` | |

### Redis Driver

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 3 | Implement `struct RedisKV` implementing `KVStore` | `[ ]` | `stdlib/db/redis.mn` | Wraps Phase 1 `__mn_redis_*` C functions |
| 4 | Implement `RedisKV.connect(host: String, port: Int) -> Result<RedisKV, KVError>` | `[ ]` | `stdlib/db/redis.mn` | |
| 5 | Implement `get` → `GET key`, `set` → `SET key value`, `del` → `DEL key`, `exists` → `EXISTS key` | `[ ]` | `stdlib/db/redis.mn` | Simple command mapping |
| 6 | Implement `set_ex(key, value, ttl_seconds)` — SET with expiry | `[ ]` | `stdlib/db/redis.mn` | `SET key value EX ttl` |
| 7 | Implement `keys(pattern)` → `KEYS pattern` | `[ ]` | `stdlib/db/redis.mn` | |
| 8 | Implement `incr(key)`, `decr(key)` — atomic counters | `[ ]` | `stdlib/db/redis.mn` | |
| 9 | Implement `close()` — disconnect | `[ ]` | `stdlib/db/redis.mn` | |

### Embedded KV (In-Process)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 10 | Implement `struct EmbeddedKV` implementing `KVStore` | `[ ]` | `stdlib/db/embedded_kv.mn` | Uses `Map<String, String>` internally |
| 11 | Implement `EmbeddedKV.new() -> EmbeddedKV` — create in-memory store | `[ ]` | `stdlib/db/embedded_kv.mn` | |
| 12 | Implement all `KVStore` trait methods on `EmbeddedKV` | `[ ]` | `stdlib/db/embedded_kv.mn` | Delegates to map operations |
| 13 | Implement `EmbeddedKV.save(path: String) -> Result<(), KVError>` — persist to disk | `[ ]` | `stdlib/db/embedded_kv.mn` | Serialize as JSON via `encoding/json.mn` |
| 14 | Implement `EmbeddedKV.load(path: String) -> Result<EmbeddedKV, KVError>` — load from disk | `[ ]` | `stdlib/db/embedded_kv.mn` | Deserialize from JSON |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 15 | Test: EmbeddedKV — set/get/del/exists/keys CRUD | `[ ]` | `tests/stdlib/test_kv.py` | No external deps |
| 16 | Test: EmbeddedKV — save to file, load from file, verify roundtrip | `[ ]` | `tests/stdlib/test_kv.py` | |
| 17 | Test: RedisKV — CRUD operations (skip if Redis not running) | `[ ]` | `tests/stdlib/test_kv_redis.py` | |
| 18 | Test: RedisKV — TTL expiry, atomic counters | `[ ]` | `tests/stdlib/test_kv_redis.py` | |
| 19 | Test: KVStore trait polymorphism — swap Redis for Embedded in same code | `[ ]` | `tests/stdlib/test_kv.py` | Proves trait abstraction works |
| 20 | Test: compile `db/kv.mn` to LLVM IR | `[ ]` | `tests/e2e/test_kv_native.py` | |

**Done when:** `KVStore` trait works with both Redis and embedded implementations.
Embedded KV can persist to/from disk. Trait polymorphism verified.

---

## Phase 7 — Dato v1.0 — Compiled Data Engine
**Status:** `Not Started`
**Priority:** CRITICAL — this is why Mapanare exists; the proof that a compiled language with agents and streams eats Python for breakfast
**Platform:** Both (separate repository: `github.com/Mapanare-Research/dato`)
**Effort:** X-Large (3+ weeks)

Dato is **not a DataFrame library**. It's a compiled data engine. No `DataFrame`. The
core type is `Table` — a typed, columnar, stream-native data structure that compiles to
native code and parallelizes across agents without you asking.

**What pandas can't do that Dato does natively:**

- **Compiled** — no Python GIL, no C extension bridge, no interpreter overhead. A `filter |> group |> mean` pipeline compiles to a tight LLVM IR loop.
- **Agent-parallel** — `table |> parallel(4, transform)` splits across 4 supervised agents. Natural Mapanare concurrency, not bolt-on multiprocessing.
- **Stream-native** — process 100GB with constant memory. `stream("huge.csv") |> filter(pred) |> fold(acc, reducer)` never loads the whole file.
- **Typed columns at compile time** — `sum("name_column")` is a compile error, not a runtime `TypeError` buried in a stack trace.
- **Zero-copy views** — `t.slice(0, 1000)` returns a view into the same column buffers, not a copy.
- **Reactive** — `Signal<Table>` auto-recomputes derived tables when source data changes. Live dashboards, not batch scripts.
- **SQL pushdown** — `from_sql(conn, query) |> filter(pred)` pushes the predicate into the SQL WHERE clause when possible, fetching less data.
- **Pipe-first** — no method chain soup creating 47 intermediate copies. `t |> select(cols) |> filter(pred) |> group("col") |> mean("val")` is one compiled pipeline.

Dato is an **external package** (`github.com/Mapanare-Research/dato`). This phase defines
the design, architecture, and acceptance criteria. Implementation lives in the Dato repo.

### Design Philosophy

```
# This is NOT pandas. This is what happens when data meets a compiled language
# with first-class agents, streams, and pipes.

// pandas: 47 intermediate copies, GIL-locked, pray the C extension handles it
// df = pd.read_csv("sales.csv")
// result = df[df["amount"] > 100].groupby("region")["amount"].mean()

// Dato: one compiled pipeline, zero copies, parallel if you want
let sales = csv("sales.csv")
let result = sales
    |> filter(fn(r) -> r.amount > 100)
    |> group("region")
    |> mean("amount")

// Dato: stream 100GB without blinking
stream("massive.csv", chunk: 50000)
    |> filter(fn(r) -> r.status == "active")
    |> parallel(8, fn(chunk) -> chunk |> group("region") |> sum("revenue"))
    |> merge()
    |> to_csv("output.csv")

// Dato: reactive — source changes, derived table auto-updates
let live_data: Signal<Table> = signal(from_sql(conn, "SELECT * FROM events"))
let dashboard = live_data |> computed(fn(t) -> t |> group("type") |> count())
// dashboard recomputes whenever live_data changes

// Dato: federated — query two databases, join natively
let users = from_sql(pg_conn, "SELECT * FROM users")
let orders = from_sql(sqlite_conn, "SELECT * FROM orders")
let report = join(users, orders, on: "user_id") |> group("name") |> sum("total")
```

### Core: `Table` Type

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | Define `struct Table { cols: List<Col>, nrows: Int, view: Bool }` | `[ ]` | `dato/src/table.mn` | `view: Bool` — true means this is a zero-copy view into another table's buffers |
| 2 | Define `enum Dtype { I64, F64, Str, Bool, Null }` | `[ ]` | `dato/src/col.mn` | 5 types. That's it. No object dtype, no category, no timedelta mess. |
| 3 | Define `struct Col { name: String, dtype: Dtype, ints: List<Int>, floats: List<Float>, strs: List<String>, bools: List<Bool>, mask: List<Bool> }` | `[ ]` | `dato/src/col.mn` | Only one data field active per dtype. `mask` = null bitmap (true = present, false = null). |
| 4 | Implement `col_i64(name: String, data: List<Int>) -> Col` — typed column constructor | `[ ]` | `dato/src/col.mn` | No nulls by default; use `col_i64_masked` for nullable |
| 5 | Implement `col_f64`, `col_str`, `col_bool` — same pattern | `[ ]` | `dato/src/col.mn` | |
| 6 | Implement `col_i64_masked(name, data, mask) -> Col` — nullable column | `[ ]` | `dato/src/col.mn` | |
| 7 | Implement `table(cols: List<Col>) -> Result<Table, DatoError>` — construct, validate equal lengths | `[ ]` | `dato/src/table.mn` | THE constructor. Not `Table.new()`. Just `table()`. |
| 8 | Implement `Table.ncols() -> Int`, `Table.nrows() -> Int` | `[ ]` | `dato/src/table.mn` | |
| 9 | Implement `Table.col(name: String) -> Option<Col>` — get column by name | `[ ]` | `dato/src/table.mn` | |
| 10 | Implement `Table.dtypes() -> List<(String, Dtype)>` — schema inspection | `[ ]` | `dato/src/table.mn` | |
| 11 | Implement `Table.row(i: Int) -> Option<Row>` — get single row as `Map<String, SqlValue>` | `[ ]` | `dato/src/table.mn` | For inspection, not iteration (use streams for that) |

### I/O: Sources & Sinks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 12 | Implement `csv(path: String) -> Result<Table, DatoError>` — load CSV | `[ ]` | `dato/src/io.mn` | Uses `encoding/csv.mn` + `fs.mn`. Auto-infers column types. |
| 13 | Implement `json(path: String) -> Result<Table, DatoError>` — load JSON (array of objects) | `[ ]` | `dato/src/io.mn` | Uses `encoding/json.mn` |
| 14 | Implement `from_sql(conn, query: String) -> Result<Table, DatoError>` — load from SQL query | `[ ]` | `dato/src/io.mn` | Uses `db/sql.mn` |
| 15 | Implement `from_sql_params(conn, query, params: List<SqlValue>) -> Result<Table, DatoError>` | `[ ]` | `dato/src/io.mn` | Parameterized — safe by default |
| 16 | Implement `from_rows(cols: List<String>, rows: List<List<SqlValue>>) -> Table` | `[ ]` | `dato/src/io.mn` | Manual construction from row data |
| 17 | Implement `to_csv(t: Table, path: String) -> Result<(), DatoError>` | `[ ]` | `dato/src/io.mn` | |
| 18 | Implement `to_json(t: Table, path: String) -> Result<(), DatoError>` | `[ ]` | `dato/src/io.mn` | |
| 19 | Implement `to_sql(t: Table, conn, table_name: String) -> Result<(), DatoError>` | `[ ]` | `dato/src/io.mn` | Batch INSERT with parameterized queries |
| 20 | Implement `show(t: Table, max_rows: Int)` — pretty-print to stdout | `[ ]` | `dato/src/display.mn` | Aligned columns, type header row, truncated strings, `...` for overflow |
| 21 | Implement `show(t: Table)` — default: show first 20 rows | `[ ]` | `dato/src/display.mn` | |

### Core Transforms (all pipe-friendly: `Table -> Table`)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 22 | Implement `select(t: Table, cols: List<String>) -> Table` — keep columns | `[ ]` | `dato/src/ops.mn` | Zero-copy: returns view into same column buffers |
| 23 | Implement `drop(t: Table, cols: List<String>) -> Table` — remove columns | `[ ]` | `dato/src/ops.mn` | Zero-copy view |
| 24 | Implement `rename(t: Table, old: String, new: String) -> Table` | `[ ]` | `dato/src/ops.mn` | |
| 25 | Implement `filter(t: Table, pred: fn(Row) -> Bool) -> Table` — predicate filtering | `[ ]` | `dato/src/ops.mn` | Compiles pred to native code — no interpreter dispatch per row |
| 26 | Implement `head(t: Table, n: Int) -> Table` — first N rows | `[ ]` | `dato/src/ops.mn` | Zero-copy view |
| 27 | Implement `tail(t: Table, n: Int) -> Table` — last N rows | `[ ]` | `dato/src/ops.mn` | Zero-copy view |
| 28 | Implement `slice(t: Table, start: Int, end: Int) -> Table` — row range | `[ ]` | `dato/src/ops.mn` | Zero-copy view |
| 29 | Implement `sort(t: Table, col: String, asc: Bool) -> Table` | `[ ]` | `dato/src/ops.mn` | Timsort on column, permute all columns by index array |
| 30 | Implement `unique(t: Table, col: String) -> Table` — deduplicate by column | `[ ]` | `dato/src/ops.mn` | Keep first occurrence |
| 31 | Implement `add_col(t: Table, c: Col) -> Table` — append column | `[ ]` | `dato/src/ops.mn` | |
| 32 | Implement `cast(t: Table, col: String, dtype: Dtype) -> Result<Table, DatoError>` — type conversion | `[ ]` | `dato/src/ops.mn` | Int→Float, Float→Int (truncate), *→Str, Str→Int/Float with validation |
| 33 | Implement `map_col(t: Table, col: String, f: fn(SqlValue) -> SqlValue) -> Table` — transform a column in-place | `[ ]` | `dato/src/ops.mn` | Like pandas `apply` but compiled |
| 34 | Implement `with_col(t: Table, name: String, f: fn(Row) -> SqlValue) -> Table` — derived column | `[ ]` | `dato/src/ops.mn` | `t \|> with_col("total", fn(r) -> r.price * r.qty)` |
| 35 | Implement `sample(t: Table, n: Int) -> Table` — random sample of N rows | `[ ]` | `dato/src/ops.mn` | |
| 36 | Implement `shuffle(t: Table) -> Table` — random row permutation | `[ ]` | `dato/src/ops.mn` | |

### Aggregation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 37 | Define `struct Grouped { key_col: String, groups: Map<SqlValue, Table> }` | `[ ]` | `dato/src/agg.mn` | Grouped tables — each group is a sub-Table (view) |
| 38 | Implement `group(t: Table, col: String) -> Grouped` | `[ ]` | `dato/src/agg.mn` | Hash-partition rows by column value |
| 39 | Implement `sum(g: Grouped, col: String) -> Table` | `[ ]` | `dato/src/agg.mn` | Result: `[key_col, col]` with one row per group |
| 40 | Implement `mean(g: Grouped, col: String) -> Table` | `[ ]` | `dato/src/agg.mn` | |
| 41 | Implement `count(g: Grouped) -> Table` | `[ ]` | `dato/src/agg.mn` | Result: `[key_col, "count"]` |
| 42 | Implement `min(g: Grouped, col: String) -> Table`, `max(g: Grouped, col: String) -> Table` | `[ ]` | `dato/src/agg.mn` | |
| 43 | Implement `agg(g: Grouped, specs: List<(String, String)>) -> Table` — multi-aggregation | `[ ]` | `dato/src/agg.mn` | `agg(g, [("amount", "sum"), ("count", "count"), ("price", "mean")])` — one pass |
| 44 | Implement `describe(t: Table) -> Table` — summary stats per numeric column | `[ ]` | `dato/src/agg.mn` | count, mean, std, min, 25%, 50%, 75%, max |
| 45 | Implement whole-table aggregates: `sum_col(t, col)`, `mean_col(t, col)`, `min_col`, `max_col`, `count_col` → `SqlValue` | `[ ]` | `dato/src/agg.mn` | No grouping — just the number. `sales \|> sum_col("revenue")` → `Int` |

### Joins

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 46 | Implement `join(left: Table, right: Table, on: String, how: String) -> Table` | `[ ]` | `dato/src/join.mn` | `how`: `"inner"`, `"left"`, `"right"`, `"outer"` |
| 47 | Implement hash-join strategy: build hash index on smaller table | `[ ]` | `dato/src/join.mn` | `Map<SqlValue, List<Int>>` for row indices |
| 48 | Implement `cross(left: Table, right: Table) -> Table` — cartesian product | `[ ]` | `dato/src/join.mn` | Useful for parameter sweeps |
| 49 | Implement `concat(tables: List<Table>) -> Result<Table, DatoError>` — vertical stack | `[ ]` | `dato/src/join.mn` | All tables must have same schema |

### Reshape

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 50 | Implement `pivot(t: Table, index: String, columns: String, values: String) -> Table` | `[ ]` | `dato/src/reshape.mn` | Wide format: one column per unique value in `columns` |
| 51 | Implement `melt(t: Table, id_vars: List<String>, value_vars: List<String>) -> Table` | `[ ]` | `dato/src/reshape.mn` | Long format: unpivot |
| 52 | Implement `transpose(t: Table) -> Table` — rows ↔ columns | `[ ]` | `dato/src/reshape.mn` | All columns must be same dtype (or coerce to Str) |

### Agent-Parallel Processing (THE differentiator)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 53 | Implement `parallel(t: Table, n: Int, f: fn(Table) -> Table) -> Table` | `[ ]` | `dato/src/parallel.mn` | Split table into N chunks, spawn N agents, each runs `f`, merge results. This is the killer feature. |
| 54 | Implement chunk splitting: `split(t: Table, n: Int) -> List<Table>` | `[ ]` | `dato/src/parallel.mn` | Split into N roughly equal sub-tables (zero-copy views) |
| 55 | Implement result merging: `merge(tables: List<Table>) -> Table` | `[ ]` | `dato/src/parallel.mn` | Vertical concat of agent results |
| 56 | Implement `parallel_map(t: Table, col: String, n: Int, f: fn(SqlValue) -> SqlValue) -> Table` | `[ ]` | `dato/src/parallel.mn` | Parallel column transform — split column across N agents |
| 57 | Implement agent supervision for parallel tasks — auto-restart failed workers | `[ ]` | `dato/src/parallel.mn` | Uses Mapanare's native agent supervision |
| 58 | Implement `parallel_reduce(t: Table, n: Int, map_fn: fn(Table) -> Table, reduce_fn: fn(Table, Table) -> Table) -> Table` | `[ ]` | `dato/src/parallel.mn` | MapReduce in 3 lines. Map across agents, reduce results. |

### Stream Processing (process files bigger than RAM)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 59 | Implement `stream(path: String, chunk: Int) -> Stream<Table>` — stream CSV in chunks | `[ ]` | `dato/src/stream.mn` | Each chunk is a `Table` with `chunk` rows. Backpressure-aware. |
| 60 | Implement `stream_sql(conn, query: String, batch: Int) -> Stream<Table>` | `[ ]` | `dato/src/stream.mn` | Cursor-based SQL streaming |
| 61 | Implement stream transforms: `stream \|> filter(pred)` applies filter per chunk | `[ ]` | `dato/src/stream.mn` | Reuse `filter`, `select`, etc. — they work on `Table`, stream maps over chunks |
| 62 | Implement `stream \|> fold(init, reducer) -> Table` — terminal: fold all chunks into one result | `[ ]` | `dato/src/stream.mn` | `stream("huge.csv", chunk: 50000) \|> fold(empty_table(), concat)` |
| 63 | Implement `stream \|> collect() -> Table` — terminal: materialize entire stream | `[ ]` | `dato/src/stream.mn` | For when you know it fits in memory |
| 64 | Implement `stream \|> sink_csv(path)` — terminal: stream results directly to file | `[ ]` | `dato/src/stream.mn` | Never holds full output in memory |
| 65 | Implement `stream \|> sink_sql(conn, table_name)` — terminal: stream into database | `[ ]` | `dato/src/stream.mn` | Batch INSERT per chunk |
| 66 | Implement `stream \|> parallel(n, transform)` — parallel stream processing | `[ ]` | `dato/src/stream.mn` | N agents process chunks concurrently from the stream. Bounded buffer between producer and consumer agents. |

### Reactive Tables (Signal integration)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 67 | Implement `reactive(source: fn() -> Table) -> Signal<Table>` — create reactive table source | `[ ]` | `dato/src/reactive.mn` | Wraps a table-producing function as a Signal |
| 68 | Implement `derived(source: Signal<Table>, transform: fn(Table) -> Table) -> Signal<Table>` | `[ ]` | `dato/src/reactive.mn` | Auto-recomputes when source changes. `let dashboard = derived(live_data, fn(t) -> t \|> group("type") \|> count())` |
| 69 | Implement `on_change(source: Signal<Table>, callback: fn(Table))` — subscribe to table changes | `[ ]` | `dato/src/reactive.mn` | For push notifications, live displays |
| 70 | Implement `refresh(source: Signal<Table>)` — manually trigger re-evaluation | `[ ]` | `dato/src/reactive.mn` | For poll-based sources (re-query SQL every N seconds) |

### SQL Pushdown (smart query optimization)

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 71 | Implement lazy `SqlQuery` builder: `from_sql_lazy(conn, table) -> SqlQuery` | `[ ]` | `dato/src/pushdown.mn` | Doesn't execute immediately — builds query plan |
| 72 | Implement `SqlQuery.filter(pred)` → appends WHERE clause | `[ ]` | `dato/src/pushdown.mn` | Translates simple predicates: `r.age > 18` → `WHERE age > 18` |
| 73 | Implement `SqlQuery.select(cols)` → set SELECT columns | `[ ]` | `dato/src/pushdown.mn` | Only fetch needed columns |
| 74 | Implement `SqlQuery.sort(col, asc)` → append ORDER BY | `[ ]` | `dato/src/pushdown.mn` | |
| 75 | Implement `SqlQuery.limit(n)` → append LIMIT | `[ ]` | `dato/src/pushdown.mn` | |
| 76 | Implement `SqlQuery.collect() -> Result<Table, DatoError>` — terminal: execute the built query | `[ ]` | `dato/src/pushdown.mn` | Sends one optimized SQL query, not "SELECT * then filter in Mapanare" |

### Null Handling

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 77 | Implement null propagation in arithmetic: `null + 5 = null` | `[ ]` | `dato/src/null.mn` | |
| 78 | Implement `drop_nulls(t: Table, col: String) -> Table` — remove rows where col is null | `[ ]` | `dato/src/null.mn` | |
| 79 | Implement `fill_null(t: Table, col: String, value: SqlValue) -> Table` — replace nulls | `[ ]` | `dato/src/null.mn` | |
| 80 | Implement `fill_forward(t: Table, col: String) -> Table` — forward-fill nulls | `[ ]` | `dato/src/null.mn` | Each null takes the value of the previous non-null row |
| 81 | Implement `null_count(t: Table, col: String) -> Int` — count nulls in column | `[ ]` | `dato/src/null.mn` | |
| 82 | Implement null-aware aggregations: `sum` skips nulls, `count` counts non-nulls | `[ ]` | `dato/src/agg.mn` | Default behavior — no `skipna=True` kwarg needed |

### Tests

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 83 | Test: `table()` construction — valid, mismatched lengths, empty | `[ ]` | `dato/tests/test_table.py` | |
| 84 | Test: `csv()` — load, inspect schema, verify column types auto-inferred | `[ ]` | `dato/tests/test_io.py` | |
| 85 | Test: `from_sql()` + `to_sql()` roundtrip | `[ ]` | `dato/tests/test_io.py` | |
| 86 | Test: `select`, `drop`, `rename`, `add_col`, `cast` | `[ ]` | `dato/tests/test_ops.py` | |
| 87 | Test: `filter`, `head`, `tail`, `slice`, `sort`, `unique` | `[ ]` | `dato/tests/test_ops.py` | |
| 88 | Test: `map_col`, `with_col` — derived column computation | `[ ]` | `dato/tests/test_ops.py` | |
| 89 | Test: `group \|> sum`, `group \|> mean`, `group \|> count`, `group \|> min/max` | `[ ]` | `dato/tests/test_agg.py` | |
| 90 | Test: `agg()` multi-aggregation in one pass | `[ ]` | `dato/tests/test_agg.py` | |
| 91 | Test: `describe()` — verify count, mean, std, min, quartiles, max | `[ ]` | `dato/tests/test_agg.py` | |
| 92 | Test: `join` — inner, left, right, outer; verify null handling in outer join | `[ ]` | `dato/tests/test_join.py` | |
| 93 | Test: `concat` — vertical stack, schema mismatch error | `[ ]` | `dato/tests/test_join.py` | |
| 94 | Test: `pivot` and `melt` roundtrip | `[ ]` | `dato/tests/test_reshape.py` | |
| 95 | Test: `parallel(4, transform)` — same result as sequential, but faster | `[ ]` | `dato/tests/test_parallel.py` | Verify correctness first, then benchmark |
| 96 | Test: `parallel_reduce` — MapReduce word count on 1M rows | `[ ]` | `dato/tests/test_parallel.py` | |
| 97 | Test: `stream("huge.csv") \|> filter \|> fold` — bounded memory on 1M-row file | `[ ]` | `dato/tests/test_stream.py` | RSS must stay below 2x chunk size |
| 98 | Test: `stream \|> parallel(4, transform) \|> sink_csv` — end-to-end streaming pipeline | `[ ]` | `dato/tests/test_stream.py` | |
| 99 | Test: `reactive` + `derived` — source change triggers derived recomputation | `[ ]` | `dato/tests/test_reactive.py` | |
| 100 | Test: SQL pushdown — verify generated SQL includes WHERE, SELECT, ORDER BY, LIMIT | `[ ]` | `dato/tests/test_pushdown.py` | Inspect query string, not just results |
| 101 | Test: null handling — `drop_nulls`, `fill_null`, `fill_forward`, null-aware aggregations | `[ ]` | `dato/tests/test_null.py` | |
| 102 | Test: zero-copy views — `slice` doesn't allocate new column buffers (memory check) | `[ ]` | `dato/tests/test_views.py` | |
| 103 | Test: pipe composition — `t \|> filter(pred) \|> group("col") \|> mean("val") \|> sort("val", false)` | `[ ]` | `dato/tests/test_pipe.py` | |
| 104 | Test: full pipeline — `csv("input.csv") \|> filter \|> parallel(4, group \|> sum) \|> merge \|> to_sql(conn, "results")` | `[ ]` | `dato/tests/test_pipeline.py` | The money test |

**Done when:** Dato v1.0 is a compiled data engine that loads from CSV/JSON/SQL, transforms
with typed columns and zero-copy views, parallelizes across agents, streams files larger than
RAM, reacts to source changes via signals, and pushes predicates down to SQL. The API is
pipe-first, minimalist, and compiles to native LLVM IR. No `DataFrame` anywhere.

---

## Phase 8 — Integration Testing & Release
**Status:** `Not Started`
**Priority:** GATE — nothing ships until all phases integrate
**Platform:** Both
**Effort:** Large (1-2 weeks)

### Cross-Module Integration

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 1 | End-to-end: read TOML config → connect to SQLite → query → write CSV | `[ ]` | `tests/e2e/test_data_pipeline.py` | |
| 2 | End-to-end: read YAML config → connect to PostgreSQL → query stream → DataFrame → JSON | `[ ]` | `tests/e2e/test_data_pipeline.py` | |
| 3 | End-to-end: `fs.walk()` → filter `.csv` → `stream_csv` → transform → `to_sql` | `[ ]` | `tests/e2e/test_data_pipeline.py` | File discovery → ETL pipeline |
| 4 | End-to-end: embedded KV as cache layer in front of SQL queries | `[ ]` | `tests/e2e/test_data_pipeline.py` | |
| 5 | End-to-end: connection pool with 10 concurrent query agents | `[ ]` | `tests/e2e/test_data_pipeline.py` | Verifies agent-based pooling under load |

### Performance Benchmarks

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 6 | Benchmark: TOML parse speed (100KB file) | `[ ]` | `benchmarks/bench_data.py` | Baseline for v1.2 |
| 7 | Benchmark: YAML parse speed (100KB file) | `[ ]` | `benchmarks/bench_data.py` | |
| 8 | Benchmark: SQLite insert 100K rows (parameterized) | `[ ]` | `benchmarks/bench_data.py` | |
| 9 | Benchmark: SQLite select 100K rows (streaming vs batch) | `[ ]` | `benchmarks/bench_data.py` | |
| 10 | Benchmark: DataFrame filter + group_by + mean on 1M rows | `[ ]` | `benchmarks/bench_dato.py` | |
| 11 | Benchmark: CSV → DataFrame → SQL roundtrip (100K rows) | `[ ]` | `benchmarks/bench_dato.py` | |

### Security Audit

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 12 | Audit: SQL injection tests — every driver, every bind type | `[ ]` | `tests/stdlib/test_sql_security.py` | |
| 13 | Audit: C runtime `mapanare_db.c` — buffer overflows, null derefs, integer overflows | `[ ]` | (manual review) | Same rigor as v1.0 security audit |
| 14 | Audit: TOML/YAML parsers — stack overflow on deeply nested input, billion-laughs attack | `[ ]` | `tests/stdlib/test_yaml_security.py` | Cap nesting depth + anchor expansion |
| 15 | Audit: filesystem operations — path traversal prevention in `fs.mn` | `[ ]` | `tests/stdlib/test_fs_security.py` | `../../etc/passwd` must not escape sandbox |

### Documentation

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 16 | Update `docs/stdlib.md` with all new modules: toml, yaml, fs, db/sql, db/kv | `[ ]` | `docs/stdlib.md` | |
| 17 | Update `docs/getting-started.md` with data tutorial (read CSV → query SQL → export) | `[ ]` | `docs/getting-started.md` | |
| 18 | Update `docs/SPEC.md` stdlib section with new module signatures | `[ ]` | `docs/SPEC.md` | |
| 19 | Write Dato v1.0 README with examples and API reference | `[ ]` | `dato/README.md` | |
| 20 | Update ROADMAP.md: v1.2.0 row in release history | `[ ]` | `docs/roadmap/ROADMAP.md` | |

### Pre-Release Checklist

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 21 | Full test suite green: `make test` — target 4,000+ tests | `[ ]` | | ~400 new tests from v1.2 modules |
| 22 | Lint clean: `make lint` | `[ ]` | | |
| 23 | All security audit findings resolved | `[ ]` | | |
| 24 | All benchmarks documented, no regressions from v1.1 | `[ ]` | | |
| 25 | CHANGELOG.md updated with all v1.2.0 changes | `[ ]` | | |
| 26 | VERSION file bumped to `1.2.0` | `[ ]` | | |

### Release

| # | Task | Status | Files | Notes |
|---|------|--------|-------|-------|
| 27 | Tag `v1.2.0` on `main` | `[ ]` | | |
| 28 | GitHub Release with release notes | `[ ]` | | Highlight: SQL drivers, TOML/YAML, filesystem, Dato v1.0 |
| 29 | PyPI release: `pip install mapanare==1.2.0` | `[ ]` | | |
| 30 | Dato v1.0 release: separate package, separate tag | `[ ]` | | `pip install dato-mn==1.0.0` or `mapanare pkg install dato` |

**Done when:** All modules integrate, security audit clean, benchmarks established,
documentation updated, and v1.2.0 tagged and released.

---

## Phase Dependencies

```
Phase 1 (C Runtime Primitives) ──┬──→ Phase 4 (fs.mn)
                                 ├──→ Phase 5 (db/sql.mn) ──→ Phase 7 (Dato v1.0)
                                 └──→ Phase 6 (db/kv.mn) ──→ Phase 7

Phase 2 (encoding/toml.mn) ──────────────────────────────→ Phase 7 (Dato reads TOML configs)
Phase 3 (encoding/yaml.mn) ──────────────────────────────→ Phase 8 (v1.3 scan templates need YAML)

Phase 4 (fs.mn) ─────────────────────────────────────────→ Phase 7 (Dato file I/O)

Phase 7 (Dato v1.0) ─────────────────────────────────────→ Phase 8 (Integration + Release)
```

### Priority Order

1. **Phase 1** — C Runtime Primitives (unblocks Phases 4, 5, 6)
2. **Phase 2** — TOML parser (independent, Windows, can parallel with Phase 1)
3. **Phase 4** — Filesystem (depends on Phase 1, small and foundational)
4. **Phase 5** — SQL drivers (depends on Phase 1, the biggest piece)
5. **Phase 3** — YAML parser (independent, Windows, can parallel with 4/5)
6. **Phase 6** — KV stores (depends on Phase 1, small)
7. **Phase 7** — Dato (depends on 4, 5, most work is external repo)
8. **Phase 8** — Integration + Release (depends on all)

### Parallelization Strategy

```
Week 1-2:  Phase 1 (WSL) + Phase 2 (Windows) — in parallel
Week 2-3:  Phase 4 (WSL) + Phase 3 (Windows) — in parallel
Week 3-5:  Phase 5 (WSL, main effort)
Week 4-5:  Phase 6 (WSL) + Phase 5 continued
Week 5-7:  Phase 7 (Both, external repo)
Week 7-8:  Phase 8 (Both, integration + release)
```

---

## New Files Created by v1.2.0

### C Runtime
- `runtime/native/mapanare_db.c` — SQLite3, PostgreSQL, Redis bindings
- `runtime/native/mapanare_db.h` — Header for database bindings
- `runtime/native/build_db.py` — Build script for database shared library

### Stdlib Modules (all `.mn`)
- `stdlib/encoding/toml.mn` — TOML v1.0 parser/serializer
- `stdlib/encoding/yaml.mn` — YAML 1.2 Core Schema parser/serializer
- `stdlib/fs.mn` — Filesystem operations, Path type
- `stdlib/db/sql.mn` — SQL driver trait, Connection, Transaction, URL dispatch
- `stdlib/db/sqlite.mn` — SQLite driver implementing SqlDriver
- `stdlib/db/postgres.mn` — PostgreSQL driver implementing SqlDriver
- `stdlib/db/pool.mn` — Agent-based connection pool
- `stdlib/db/migrate.mn` — Migration framework
- `stdlib/db/kv.mn` — KVStore trait
- `stdlib/db/redis.mn` — Redis driver implementing KVStore
- `stdlib/db/embedded_kv.mn` — In-process KV store implementing KVStore

### Dato (External Package)
- `dato/src/table.mn` — Table type, core constructors
- `dato/src/col.mn` — Column types, typed constructors
- `dato/src/ops.mn` — Core transforms (select, filter, sort, map_col, with_col, etc.)
- `dato/src/agg.mn` — Aggregation (group, sum, mean, count, describe, etc.)
- `dato/src/join.mn` — Join, cross, concat
- `dato/src/reshape.mn` — Pivot, melt, transpose
- `dato/src/io.mn` — All I/O: csv, json, from_sql, to_csv, to_json, to_sql
- `dato/src/display.mn` — Pretty-print tables
- `dato/src/parallel.mn` — Agent-parallel: parallel, split, merge, parallel_map, parallel_reduce
- `dato/src/stream.mn` — Stream processing: stream, stream_sql, sink_csv, sink_sql
- `dato/src/reactive.mn` — Reactive tables: reactive, derived, on_change, refresh
- `dato/src/pushdown.mn` — SQL pushdown: lazy query builder
- `dato/src/null.mn` — Null handling: drop_nulls, fill_null, fill_forward

### Tests
- `tests/native/test_db_sqlite.py`
- `tests/native/test_db_postgres.py`
- `tests/native/test_db_redis.py`
- `tests/native/test_db_dlopen.py`
- `tests/native/test_fs_extended.py`
- `tests/stdlib/test_toml.py`
- `tests/stdlib/test_yaml.py`
- `tests/stdlib/test_fs.py`
- `tests/stdlib/test_sql_sqlite.py`
- `tests/stdlib/test_sql_postgres.py`
- `tests/stdlib/test_sql_core.py`
- `tests/stdlib/test_sql_pool.py`
- `tests/stdlib/test_sql_migrate.py`
- `tests/stdlib/test_sql_security.py`
- `tests/stdlib/test_kv.py`
- `tests/stdlib/test_kv_redis.py`
- `tests/stdlib/test_yaml_security.py`
- `tests/stdlib/test_fs_security.py`
- `tests/e2e/test_toml_native.py`
- `tests/e2e/test_yaml_native.py`
- `tests/e2e/test_fs_native.py`
- `tests/e2e/test_sql_native.py`
- `tests/e2e/test_kv_native.py`
- `tests/e2e/test_data_pipeline.py`
- `dato/tests/test_table.py`
- `dato/tests/test_io.py`
- `dato/tests/test_ops.py`
- `dato/tests/test_agg.py`
- `dato/tests/test_join.py`
- `dato/tests/test_reshape.py`
- `dato/tests/test_parallel.py`
- `dato/tests/test_stream.py`
- `dato/tests/test_reactive.py`
- `dato/tests/test_pushdown.py`
- `dato/tests/test_null.py`
- `dato/tests/test_views.py`
- `dato/tests/test_pipe.py`
- `dato/tests/test_pipeline.py`

---

## Context Recovery

If context is interrupted mid-phase, add a handoff entry here:

| Date | Phase | Last Task | Next Task | Notes |
|------|-------|-----------|-----------|-------|
| | | | | |

---

## Estimated Total Task Count

| Phase | Tasks | Tests | Total |
|-------|-------|-------|-------|
| 1: C Runtime | 40 | 6 | 46 |
| 2: TOML | 22 | 7 | 29 |
| 3: YAML | 20 | 10 | 30 |
| 4: Filesystem | 27 | 7 | 34 |
| 5: SQL Drivers | 33 | 12 | 45 |
| 6: KV Stores | 14 | 6 | 20 |
| 7: Dato v1.0 | 82 | 22 | 104 |
| 8: Integration | 15 | 15 | 30 |
| **Total** | **253** | **85** | **338** |
