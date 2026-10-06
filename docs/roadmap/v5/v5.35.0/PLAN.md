# v5.35.0 — Sq.\* — sqlite3 driver

**Status:** PLANNING
**Type:** Stdlib expansion. New `stdlib/sql/sqlite/` module backed
by dlopen of `libsqlite3` (mirrors the OpenSSL dlopen pattern
already in the C runtime for TLS).
**Breaking:** No. Net-new module.
**Prerequisite:** v5.34.0 shipped (date/time stdlib — sqlite cells
that bind to `DATETIME` columns need it).
**Estimated effort:** 1–2 sessions. ~1200 LOC `.mn` + ~150 LOC C
shim for safe FFI.

---

## Why this exists

There is no first-class persistence story in Mapanare. Every real
application that's not a CLI filter needs *something* persistent.
SQLite is the right first target because:

- Single-file, no server, ubiquitous (every Linux + macOS box has
  `libsqlite3` already; Windows we bundle).
- Stable C API (one of the most stable in software — SQLite's
  binary compatibility commitment is famously strong).
- Works everywhere Mapanare runs (mobile included).
- Solves 80% of "I need a database" use cases without dragging in
  a Postgres dependency.

This is item #2 of the **stdlib gap-close arc**.

---

## Goals

1. **Sq.1** — `Database` type: open/close, prepare statement,
   execute, transaction.
2. **Sq.2** — `Statement` type: bind typed params, step, fetch
   typed columns.
3. **Sq.3** — Type bindings: `Int`, `Float`, `String`, `Bytes`,
   `Bool`, `Option<T>`, `Date`/`DateTime` (via Dt.\*),
   `Json` (via Js.\* preview).
4. **Sq.4** — Transaction semantics: `db.transaction(fn { ... })`
   with auto-commit on Ok return, auto-rollback on Err.
5. **Sq.5** — Prepared statement caching: `db.prepare(sql)` returns
   reusable handle; cache lifetime tied to `Database` lifetime.
6. **Sq.6** — Tests: full CRUD round-trip, transaction
   commit/rollback, prepared statement reuse, error handling.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Sq.1** | HIGH | **`Database` type in `stdlib/sql/sqlite/db.mn`.** `Database::open(path: String) -> Result<Database, SqlError>`. Methods: `execute(sql: String) -> Result<Unit, SqlError>`, `prepare(sql: String) -> Result<Statement, SqlError>`, `transaction<T>(f: fn() -> Result<T, SqlError>) -> Result<T, SqlError>`, `close()`. | 3h |
| **Sq.2** | HIGH | **`Statement` type in `stdlib/sql/sqlite/stmt.mn`.** Methods: `bind(idx: Int, val: Value) -> Result<Unit, SqlError>`, `bind_named(name: String, val: Value) -> Result<Unit, SqlError>`, `step() -> Result<StepResult, SqlError>` (variants `Row(Statement)`, `Done`), `column<T>(idx: Int) -> Result<T, SqlError>`, `reset()`, `finalize()`. | 3h |
| **Sq.3** | HIGH | **Value type union in `stdlib/sql/sqlite/value.mn`.** `enum Value { Null, Int(Int), Float(Float), Text(String), Blob(Bytes), Bool(Bool), DateTime(DateTime) }`. `column<T>` dispatches on the requested type and the actual SQLite column type, returning `Err` on mismatch. JSON support via Sq.3.B preview returns `Value::Text` containing JSON string for v5.35.0; first-class JSON column type ships with v5.36.0 (Js.\*) integration. | 2h |
| **Sq.4** | HIGH | **Transactions.** `db.transaction(\|\| -> Result<T, SqlError> { ... })` wraps the closure in `BEGIN` / `COMMIT` / `ROLLBACK` based on Ok/Err. Nested transactions emulated via SAVEPOINT + RELEASE SAVEPOINT (sqlite supports this natively). | 2h |
| **Sq.5** | MEDIUM | **Statement caching.** `Database` keeps a `Map<String, Statement>` of prepared statements; `db.prepare(sql)` returns cached handle if present, otherwise prepares and caches. Cache invalidates on `db.close()`; per-statement explicit `finalize()` removes from cache. | 2h |
| **Sq.6** | HIGH (gate) | **Tests in `stdlib/sql/sqlite/tests/`.** `test_open_close.mn`, `test_crud.mn` (CREATE TABLE / INSERT / SELECT / UPDATE / DELETE round-trip), `test_transaction.mn` (commit + rollback both paths), `test_prepared_reuse.mn`, `test_error_handling.mn` (bad SQL, type mismatches, constraint violations). All run against in-memory `:memory:` databases for speed + hermeticity. | 3h |
| **Sq.7** | MEDIUM | **C runtime shim** in `runtime/native/mapanare_sqlite.c`. Wraps dlopen of `libsqlite3.so` / `libsqlite3.dylib` / `sqlite3.dll`. Exports thin C functions that the .mn `extern` declarations call. ~150 LOC, follows the OpenSSL dlopen pattern in `runtime/native/mapanare_tls.c`. | 3h |
| **Sq.8** | LOW | **Bundle `sqlite3.dll` on Windows.** Linux + macOS have system `libsqlite3` available since the OS was installed; Windows users may not. Add `sqlite3.dll` to the Windows SDK ZIP at `bin\sqlite3.dll`. | 1h |
| **Sq.9** | LOW | **Doc page** at `docs/stdlib/sql.md`. Cookbook: open db, create table, insert N rows, query with WHERE, transaction-wrapped batch insert, error-handling patterns. | 1h |

---

## Phase plan

- **Phase 0** — Pre-flight; v5.34.0 HEAD clean; date/time stdlib
  available for Sq.3's DateTime binding.
- **Phase 1** — Sq.7 C shim first. `dlopen` plumbing identical to
  TLS shim; lift the pattern.
- **Phase 2** — Sq.1 + Sq.2 core types.
- **Phase 3** — Sq.3 typed values.
- **Phase 4** — Sq.4 transactions; Sq.5 caching.
- **Phase 5** — Sq.6 tests (the gate); Sq.8 Windows bundle;
  Sq.9 docs.
- **Phase 6** — Bump + tag.

---

## Out of scope

- **PostgreSQL driver.** v5.x carry; separate release. Same shape
  (libpq dlopen) but bigger surface.
- **MySQL/MariaDB driver.** Same as Postgres.
- **ORM / query builder.** Downstream package territory; stdlib
  ships the raw API only.
- **Schema migrations.** Downstream package; v5.x stdlib doesn't
  prescribe migration tooling.
- **Async sqlite.** SQLite's API is fundamentally sync. Apps that
  need async wrap calls in agents.
- **Tn.1, M.1, A.1, Ra.New1, Pv.8.B, named-tzdb** — carry forward.

---

## Risk

1. **dlopen path resolution on Windows.** `sqlite3.dll` next to
   the executable should resolve via default search order, but
   PATH ordering surprises happen. Mitigation: Sq.7 shim probes
   the executable's directory explicitly via `GetModuleFileNameW`
   before falling through to default search.
2. **SQLite version skew.** Linux distros ship a range from
   3.31 to 3.45+; macOS bundles 3.39+. Mapanare uses only the
   v3.7.0+ API surface (15 years stable). Mitigation: pin the
   minimum version in `Database::open` via `sqlite3_libversion`
   check; clear error if the system sqlite is too old.
3. **In-memory test parallelism.** Multiple tests opening
   `:memory:` are independent (each gets its own in-memory db),
   so parallelism is fine. Confirm via Phase 0 spike that pytest
   `-n auto` doesn't cause flakes.
4. **Statement-cache key collisions.** Two different SQL strings
   that hash the same — extremely unlikely with `String` keys
   (Mapanare's `Map<String, _>` uses Robin Hood hashing with
   real string equality on collision). No real risk.

---

## Success criteria

- ✅ `Database::open(":memory:")` works.
- ✅ Full CRUD round-trip in test passes.
- ✅ Transaction commit + rollback both paths work.
- ✅ Prepared statement reuse measured ~5-10× faster than
  re-preparing per call (basic benchmark).
- ✅ `sqlite3.dll` bundled in Windows SDK ZIP.
- ✅ Goldens 95/95.
- ✅ Strict 3-stage fixed point preserved.

---

## Carry-forward delta

**Closes:**
- "no first-class persistence" gap. Apps can ship.

**Inherits to v5.36.0:**
- Tn.1 — **DEADLINE was v5.35.0**. If not landed here, must be
  shipped as v5.35.1 hotfix before v5.36.0 starts. **No further
  carry forward acceptable.**
- macOS notarization, named-tzdb (LOW carry).
- PostgreSQL/MySQL drivers (new LOW; downstream-package
  candidates).
- Stdlib JSON-column integration with sqlite (Sq.3.B preview;
  proper integration at v5.36.0 Js.\* with Sq.\* compatibility test).
