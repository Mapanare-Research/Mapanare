# `stdlib/sql/sqlite` — SQLite3 driver

**Available since:** v5.35.0 (Sq.\*)
**Status:** stable surface; Sq.5 statement cache + Sq.3 native Bytes
type tracked as v5.36.0 candidates (see "Deviations" below).

First-class persistence story for Mapanare. SQLite is the right first
target — single-file, no server, ubiquitous, famously stable C API.
Solves 80% of "I need a database" use cases without dragging in a
Postgres dependency.

Backed by `dlopen(libsqlite3)` wrappers in
`runtime/native/mapanare_db.c`. The pre-existing v5.34.x sqlite3
exports were extended at v5.35.0 Sq.7 with version detection, blob
support, statement reset, named-parameter index resolution, change
tracking, and extended error codes — the surface needed for typed
columns and rich `SqlError` mapping.

> **Compiler limitation note (v5.35.0).** Cross-module function calls
> have a known limitation in the current Mapanare LLVM toolchain (same
> root cause as v5.34.0 `stdlib/time.mn` — see that module's preamble
> for details). v5.35.0 ships `stdlib/sql/sqlite.mn` as a single file;
> tests under `stdlib/sql/sqlite/tests/` are run via concatenation
> harness at `tests/stdlib/test_sq_sqlite.py`. Until the cross-module
> emitter fix lands, prepend `stdlib/sql/sqlite.mn` to your own
> `.mn` source rather than `import sql.sqlite as db`. The surface API
> will not change once that fix lands.

## Quick reference

```mn
// Open / close
let db_r: Result<Database, SqlError> = database_open(":memory:")
let mem:  Result<Database, SqlError> = database_open_memory()
let f_r:  Result<Database, SqlError> = database_open("/var/data/app.db")
let dropped: Database = database_close(db)

// Execute (no rows back) — returns rows affected
let n_r: Result<Int, SqlError> = database_execute(db, "INSERT INTO t VALUES(1, 2)")
let last: Int = database_last_insert_rowid(db)
let chg:  Int = database_changes(db)

// Prepare / step / column-typed reads
let stmt_r: Result<Statement, SqlError> = database_prepare(db, "SELECT v FROM t WHERE k = ?")
let bind_r: Result<Bool, SqlError> = statement_bind_string(stmt, 1, "alice")
let s_r:    Result<Int, SqlError>  = statement_step(stmt)        // 100=ROW, 101=DONE
let v_r:    Result<Int, SqlError>  = statement_column_int(stmt, 0)
let reset:  Result<Bool, SqlError> = statement_reset(stmt)
let fin:    Statement              = statement_finalize(stmt)

// Named parameters — :name, @name, $name
let stmt2_r: Result<Statement, SqlError> = database_prepare(db, "SELECT v FROM t WHERE k = :name")
let nb_r:    Result<Bool, SqlError> = statement_bind_named(stmt2, ":name", value_text("alice"))

// Transactions — explicit begin/commit/rollback
let _: Result<Bool, SqlError> = database_begin(db)
//   ... database_execute / prepare / step ...
let _: Result<Bool, SqlError> = database_commit(db)      // or database_rollback(db)

// Nested via SAVEPOINTs
let sph_r: Result<SavepointHandle, SqlError> = database_savepoint_begin(db)
match sph_r {
    Ok(sph) => {
        //   ... work using sph.db ...
        let _: Result<Bool, SqlError> = database_savepoint_release(sph)
        // or: database_savepoint_rollback(sph) to revert just this nesting
    },
    Err(e) => { /* ... */ }
}
```

## Types

```mn
pub tipo Database { handle: Int, closed: Bool, sp_counter: Int }

pub tipo Statement { handle: Int, db_handle: Int, finalized: Bool }

pub tipo SavepointHandle { db: Database, name: String }

// Polymorphic value carrier — use for generic row dumpers / iterators.
// Blob carries raw bytes as a String (length-prefixed buffer; sqlite
// treats BLOB and TEXT identically at the storage layer).
// DateTime is an ISO 8601 string (sqlite has no native datetime type).
pub tipo Value {
    | Null
    | Int(Int)
    | Float(Float)
    | Text(String)
    | Blob(String)
    | Bool(Bool)
    | DateTime(String)
}

pub tipo SqlError {
    | LoadFail              // libsqlite3 not loaded
    | VersionTooOld(String) // libsqlite3 < 3.7.0; carries detected version
    | BadSql(String)        // syntax / unbound param / table-not-found
    | TypeMismatch(String)  // column<T> requested wrong type for column
    | Constraint(String)    // UNIQUE / NOT NULL / FOREIGN KEY violation
    | Busy                  // SQLITE_BUSY — soft, retry with backoff
    | Misuse                // SQLITE_MISUSE — programmer error, not retryable
    | Closed                // operation on closed Database / finalized Statement
}
```

## Recipes

### Open + create + insert + read (`:memory:`)

```mn
let db_r: Result<Database, SqlError> = database_open_memory()
match db_r {
    Ok(db) => {
        let _r1: Result<Int, SqlError> = database_execute(db, "CREATE TABLE u(id INTEGER PRIMARY KEY, name TEXT)")
        let _r2: Result<Int, SqlError> = database_execute(db, "INSERT INTO u(name) VALUES('alice')")
        let q_r: Result<Statement, SqlError> = database_prepare(db, "SELECT name FROM u WHERE id = 1")
        match q_r {
            Ok(stmt) => {
                let _ : Result<Int, SqlError> = statement_step(stmt)
                let n_r: Result<String, SqlError> = statement_column_string(stmt, 0)
                match n_r {
                    Ok(name) => { print("got: " + name) },
                    Err(e)   => { print("read err") }
                }
                let dropped: Statement = statement_finalize(stmt)
            },
            Err(e) => { print("prepare err") }
        }
        let dropped_db: Database = database_close(db)
    },
    Err(e) => { print("open err") }
}
```

### On-disk database with a real path

```mn
let db_r: Result<Database, SqlError> = database_open("/var/data/app.db")
// SQLite auto-creates the file if it doesn't exist; the directory
// must already exist + be writable. Returns LoadFail on permission /
// path errors.
```

### Transaction-wrapped batch insert (the perf win)

```mn
let _b: Result<Bool, SqlError> = database_begin(db)
let p_r: Result<Statement, SqlError> = database_prepare(db, "INSERT INTO t(v) VALUES(?)")
match p_r {
    Ok(stmt) => {
        let mut i: Int = 0
        while i < 1000 {
            let _: Result<Bool, SqlError> = statement_reset(stmt)
            let _: Result<Bool, SqlError> = statement_bind_int(stmt, 1, i * 7)
            let _: Result<Int, SqlError>  = statement_step(stmt)
            i = i + 1
        }
        let dropped: Statement = statement_finalize(stmt)
    },
    Err(e) => { /* ... */ }
}
let _c: Result<Bool, SqlError> = database_commit(db)
```

Wrapping the loop in a single transaction is the difference between
sqlite's implicit per-INSERT commit (one disk fsync per row) and a
single batch commit at the end. Speed-up is typically 100×+ on
spinning disks, 5-10× on SSDs.

### Prepared-statement reuse (manual; v5.35.0 has no automatic cache)

```mn
// Prepare ONCE outside the loop. Reuse via reset+bind+step inside.
// This is the Sq.5-deferred path — the v5.35.0 surface does not
// auto-cache prepared statements; users get the speedup manually.
let p_r: Result<Statement, SqlError> = database_prepare(db, "SELECT v FROM t WHERE k = ?")
match p_r {
    Ok(stmt) => {
        let mut i: Int = 0
        while i < 100 {
            let _: Result<Bool, SqlError> = statement_reset(stmt)
            let _: Result<Bool, SqlError> = statement_bind_int(stmt, 1, i)
            let s_r: Result<Int, SqlError> = statement_step(stmt)
            // ... read columns, etc. ...
            i = i + 1
        }
        let dropped: Statement = statement_finalize(stmt)
    },
    Err(e) => { /* ... */ }
}
```

### Match on `SqlError` for retry / recovery

```mn
let r: Result<Int, SqlError> = database_execute(db, "INSERT INTO t VALUES(1, 'x')")
match r {
    Ok(n)  => { /* changed n rows */ },
    Err(e) => match e {
        Busy           => { /* retry with backoff */ },
        Constraint(s)  => { /* duplicate / NULL violation — surface to user */ },
        BadSql(s)      => { /* programmer error in SQL string */ },
        TypeMismatch(s) => { /* programmer error in column<T> call */ },
        Misuse         => { /* programmer error in API usage */ },
        Closed         => { /* operation on closed db / finalized stmt */ },
        LoadFail       => { /* libsqlite3 missing — install sqlite3 */ },
        VersionTooOld(v) => { /* libsqlite3 too old — need >= 3.7.0 */ }
    }
}
```

The `Busy` variant is the only soft-retryable one. The others all
indicate either programmer error or a recoverable user-visible
condition (constraint violation, missing library).

### Working with blobs

```mn
// Bind raw bytes (a String acts as the carrier — no separate Bytes type yet).
let raw: String = "..."  // bytes
let _b: Result<Bool, SqlError> = statement_bind_blob(stmt, 1, raw)

// Read a blob column.
let b_r: Result<String, SqlError> = statement_column_blob(stmt, 0)
match b_r {
    Ok(bytes) => { /* len(bytes) is the byte count */ },
    Err(e) => { /* ... */ }
}
```

### JSON (Sq.3.B preview — full integration at v5.36.0 Js.\*)

For v5.35.0, JSON columns are stored and retrieved as `Value::Text`
containing a JSON string:

```mn
// Store a JSON document
let _i: Result<Int, SqlError> = database_execute(db,
    "INSERT INTO docs(payload) VALUES('{\"k\": 42}')")

// Read it back
let q_r: Result<Statement, SqlError> = database_prepare(db, "SELECT payload FROM docs LIMIT 1")
match q_r {
    Ok(stmt) => {
        let _: Result<Int, SqlError> = statement_step(stmt)
        let json_r: Result<String, SqlError> = statement_column_string(stmt, 0)
        // ... parse the JSON string with whatever JSON tooling is available
        let dropped: Statement = statement_finalize(stmt)
    },
    Err(e) => { /* ... */ }
}
```

The v5.36.0 **Js.\*** arc adds first-class `Value::Json(JsonValue)` with
typed parse/access and a sqlite-compatibility test that round-trips
the same column both ways (string ↔ JsonValue). The v5.35.0 surface is
forward-compatible: a `Value::Text` containing JSON keeps working
verbatim once Js.\* lands.

## Deviations from PROMPT/PLAN

The v5.35.0 PROMPT specified a richer surface than v5.35.0 actually
ships. Each deviation is structurally driven by current Mapanare
toolchain limitations and is documented in
`docs/roadmap/v5/v5.35.0/SESSION_REPORT.md`:

1. **Single-file module, not directory.** Same lesson as v5.34.0
   `stdlib/time.mn`. The `import sql.sqlite` shape is correct; the
   single-file path is the workaround until cross-module emitter
   support lands.

2. **`Value::Blob` carries `String`, not `Bytes`.** Mapanare has no
   native `Bytes` type yet. `MnString = { ptr, i64 }` is the
   length-prefixed-byte-buffer carrier; treat `Blob` payloads as raw
   bytes with no encoding assumption.

3. **No `transaction(\|\| ...)` closure wrapper.** Mapanare's stdlib has
   no precedent for generic functions taking closures. v5.35.0 ships
   explicit `database_begin / database_commit / database_rollback`
   plus `SavepointHandle`-based nesting, matching the existing
   `stdlib/db/sqlite.mn` convention. Closure wrapper is a v5.36.0+
   candidate.

4. **No automatic statement cache.** Caller-managed reuse via
   `prepare-once + statement_reset + bind + step` produces the same
   ~5-10× speedup as the proposed cache. The cache layer's API
   ergonomics deteriorate badly without first-class state mutation
   across function calls + a `Map<K,V>` ergonomic surface; deferred
   to v5.36.0 with proper map operations.

## Compatibility with existing `stdlib/db/sqlite.mn`

The v5.34.x driver at `stdlib/db/sqlite.mn` (URL-routed `Connection`
type, `SqlValue` enum, simpler error variants) is **untouched** by
v5.35.0. Both drivers coexist:

- **Pick `stdlib/db/sqlite.mn`** for compatibility with the unified
  SQL routing layer (`sqlite://`, `postgres://` URLs through the
  same `Connection` type) and for code that uses the old `SqlError`
  variants.
- **Pick `stdlib/sql/sqlite.mn`** (v5.35.0+) for the typed
  `column<T>`, named parameter binding, blob support, rich
  `SqlError` variants with retry/recovery semantics, and explicit
  transaction primitives + nested SAVEPOINTs.

A migration tool from the old driver to the new one is not yet
provided; both surfaces are stable and supported.

## Windows binary distribution (Sq.8)

The v5.35.0 Windows SDK + minimal ZIPs ship `sqlite3.dll` at
`bin/sqlite3.dll` (alongside the v5.32.0 native `mnc.exe` at the
bundle root). The pinned version is **3.46.1** (sourced from
`https://www.sqlite.org/2024/sqlite-dll-win-x64-3460100.zip`); future
releases bump the pin in CHANGELOG and `publish.yml` together.

Linux + macOS users: the system libsqlite3 (Ubuntu 20.04+ ships
3.31+; macOS 13+ ships 3.39+) is used directly — no bundled DLL
needed. v5.35.0's Sq.7 shim does a `>= 3.7.0` version check at
`Database::open` and returns `SqlError::VersionTooOld` cleanly if
the system sqlite is too old (15 years stable, so this is a safety
net, not a load-bearing path).
