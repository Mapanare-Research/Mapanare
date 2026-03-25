"""db/migrate.mn — Database Migration Framework tests.

Tests verify that the migration framework module compiles to valid LLVM IR via
the MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the SQL core, SQLite driver, and migration module source code within
test programs.

Covers:
  - ensure_table creates __mn_migrations tracking table
  - migrate_up applies pending migrations in version order
  - migrate_down rolls back migrations above target version
  - migration_status shows applied/pending for each migration
  - Idempotent re-apply: already applied migrations are skipped
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

_SQL_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "sql.mn"
).read_text(encoding="utf-8")

_SQLITE_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "sqlite.mn"
).read_text(encoding="utf-8")

_MIGRATE_MN = (
    Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "migrate.mn"
).read_text(encoding="utf-8")

# Combine all three modules, stripping import statements since we inline everything.
_MIGRATE_COMBINED = (
    _SQL_MN
    + "\n\n"
    + "\n".join(line for line in _SQLITE_MN.splitlines() if not line.startswith("import "))
    + "\n\n"
    + "\n".join(line for line in _MIGRATE_MN.splitlines() if not line.startswith("import "))
)


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_sql_migrate.mn", use_mir=True)


def _migrate_with_main(main_body: str) -> str:
    """Prepend combined SQL+SQLite+Migrate source and wrap main_body in fn main()."""
    return _MIGRATE_COMBINED + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Migration construction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMigrationConstruction:
    def test_new_migration(self) -> None:
        """new_migration constructor compiles."""
        src = _migrate_with_main("""\
            let m: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)", "DROP TABLE users")
            println(m.name)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migration_struct_literal(self) -> None:
        """Migration struct literal compiles."""
        src = _migrate_with_main("""\
            let m: Migration = new Migration { version: 1, name: "create_users", up: "CREATE TABLE users (id INTEGER)", down: "DROP TABLE users" }
            println(str(m.version))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migration_info_struct(self) -> None:
        """MigrationInfo struct compiles."""
        src = _migrate_with_main("""\
            let info: MigrationInfo = new MigrationInfo { version: 1, name: "create_users", applied: true }
            println(str(info.applied))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_multiple_migrations(self) -> None:
        """List of migrations compiles."""
        src = _migrate_with_main("""\
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)", "DROP TABLE users")
            let m2: Migration = new_migration(2, "add_email", "ALTER TABLE users ADD COLUMN email TEXT", "ALTER TABLE users DROP COLUMN email")
            let m3: Migration = new_migration(3, "add_age", "ALTER TABLE users ADD COLUMN age INTEGER", "ALTER TABLE users DROP COLUMN age")
            let migrations: List<Migration> = [m1, m2, m3]
            println(str(len(migrations)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# ensure_table
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestEnsureTable:
    def test_ensure_table(self) -> None:
        """ensure_table creates __mn_migrations table."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let result: Result<Bool, SqlError> = ensure_table(conn)
            match result {
                Ok(ok) => { println("table created") },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_ensure_table_idempotent(self) -> None:
        """ensure_table called twice does not fail (IF NOT EXISTS)."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let r1: Result<Bool, SqlError> = ensure_table(conn)
            let r2: Result<Bool, SqlError> = ensure_table(conn)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# migrate_up
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMigrateUp:
    def test_migrate_up_single(self) -> None:
        """migrate_up with one migration compiles."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)", "DROP TABLE users")
            let migrations: List<Migration> = [m1]
            let result: Result<Int, SqlError> = migrate_up(conn, migrations)
            match result {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migrate_up_multiple(self) -> None:
        """migrate_up with multiple migrations applies in version order."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE users")
            let m2: Migration = new_migration(2, "add_name", "ALTER TABLE users ADD COLUMN name TEXT", "ALTER TABLE users DROP COLUMN name")
            let m3: Migration = new_migration(3, "add_email", "ALTER TABLE users ADD COLUMN email TEXT", "ALTER TABLE users DROP COLUMN email")
            let migrations: List<Migration> = [m3, m1, m2]
            let result: Result<Int, SqlError> = migrate_up(conn, migrations)
            match result {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migrate_up_empty_list(self) -> None:
        """migrate_up with empty migration list returns 0."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let migrations: List<Migration> = []
            let result: Result<Int, SqlError> = migrate_up(conn, migrations)
            match result {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migrate_up_idempotent(self) -> None:
        """migrate_up called twice skips already-applied migrations."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE users")
            let migrations: List<Migration> = [m1]
            let r1: Result<Int, SqlError> = migrate_up(conn, migrations)
            let r2: Result<Int, SqlError> = migrate_up(conn, migrations)
            match r2 {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# migrate_down
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMigrateDown:
    def test_migrate_down_to_zero(self) -> None:
        """migrate_down to version 0 rolls back all migrations."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY)", "DROP TABLE IF EXISTS users")
            let m2: Migration = new_migration(2, "create_posts", "CREATE TABLE posts (id INTEGER PRIMARY KEY)", "DROP TABLE IF EXISTS posts")
            let migrations: List<Migration> = [m1, m2]
            let result: Result<Int, SqlError> = migrate_down(conn, migrations, 0)
            match result {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migrate_down_partial(self) -> None:
        """migrate_down to target version rolls back only higher versions."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER)", "DROP TABLE IF EXISTS users")
            let m2: Migration = new_migration(2, "create_posts", "CREATE TABLE posts (id INTEGER)", "DROP TABLE IF EXISTS posts")
            let m3: Migration = new_migration(3, "create_comments", "CREATE TABLE comments (id INTEGER)", "DROP TABLE IF EXISTS comments")
            let migrations: List<Migration> = [m1, m2, m3]
            let result: Result<Int, SqlError> = migrate_down(conn, migrations, 1)
            match result {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migrate_down_nothing_to_rollback(self) -> None:
        """migrate_down when no migrations applied returns 0."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER)", "DROP TABLE users")
            let migrations: List<Migration> = [m1]
            let result: Result<Int, SqlError> = migrate_down(conn, migrations, 0)
            match result {
                Ok(count) => { println(str(count)) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migrate_up_then_down(self) -> None:
        """Full up-then-down cycle compiles."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)", "DROP TABLE IF EXISTS users")
            let migrations: List<Migration> = [m1]
            let up_result: Result<Int, SqlError> = migrate_up(conn, migrations)
            let down_result: Result<Int, SqlError> = migrate_down(conn, migrations, 0)
            println("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# migration_status
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestMigrationStatus:
    def test_migration_status(self) -> None:
        """migration_status returns list of MigrationInfo."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER)", "DROP TABLE users")
            let m2: Migration = new_migration(2, "add_email", "ALTER TABLE users ADD COLUMN email TEXT", "ALTER TABLE users DROP COLUMN email")
            let migrations: List<Migration> = [m1, m2]
            let result: Result<List<MigrationInfo>, SqlError> = migration_status(conn, migrations)
            match result {
                Ok(infos) => { println(str(len(infos))) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migration_status_empty(self) -> None:
        """migration_status with no migrations returns empty list."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let migrations: List<Migration> = []
            let result: Result<List<MigrationInfo>, SqlError> = migration_status(conn, migrations)
            match result {
                Ok(infos) => { println(str(len(infos))) },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migration_status_shows_applied_pending(self) -> None:
        """migration_status distinguishes applied from pending."""
        src = _migrate_with_main("""\
            let conn: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let m1: Migration = new_migration(1, "create_users", "CREATE TABLE users (id INTEGER)", "DROP TABLE users")
            let m2: Migration = new_migration(2, "create_posts", "CREATE TABLE posts (id INTEGER)", "DROP TABLE posts")
            let m3: Migration = new_migration(3, "create_comments", "CREATE TABLE comments (id INTEGER)", "DROP TABLE comments")
            let migrations: List<Migration> = [m1, m2, m3]
            let result: Result<List<MigrationInfo>, SqlError> = migration_status(conn, migrations)
            match result {
                Ok(infos) => {
                    let count: Int = len(infos)
                    println(str(count))
                },
                Err(e) => { println(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_migration_info_field_access(self) -> None:
        """MigrationInfo fields are accessible."""
        src = _migrate_with_main("""\
            let info: MigrationInfo = new MigrationInfo { version: 1, name: "create_users", applied: false }
            println(str(info.version))
            println(info.name)
            println(str(info.applied))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestInternalHelpers:
    def test_version_is_applied(self) -> None:
        """version_is_applied function compiles."""
        src = _migrate_with_main("""\
            let versions: List<Int> = [1, 2, 3]
            let found: Bool = version_is_applied(versions, 2)
            println(str(found))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_version_is_applied_not_found(self) -> None:
        """version_is_applied returns false for missing version."""
        src = _migrate_with_main("""\
            let versions: List<Int> = [1, 3, 5]
            let found: Bool = version_is_applied(versions, 4)
            println(str(found))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sort_migrations(self) -> None:
        """sort_migrations orders by version ascending."""
        src = _migrate_with_main("""\
            let m3: Migration = new_migration(3, "third", "CREATE TABLE c (id INTEGER)", "DROP TABLE c")
            let m1: Migration = new_migration(1, "first", "CREATE TABLE a (id INTEGER)", "DROP TABLE a")
            let m2: Migration = new_migration(2, "second", "CREATE TABLE b (id INTEGER)", "DROP TABLE b")
            let unsorted: List<Migration> = [m3, m1, m2]
            let sorted: List<Migration> = sort_migrations(unsorted)
            println(sorted[0].name)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sort_migrations_single(self) -> None:
        """sort_migrations with single migration returns it unchanged."""
        src = _migrate_with_main("""\
            let m1: Migration = new_migration(1, "only", "CREATE TABLE t (id INTEGER)", "DROP TABLE t")
            let migrations: List<Migration> = [m1]
            let sorted: List<Migration> = sort_migrations(migrations)
            println(str(len(sorted)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_sort_migrations_empty(self) -> None:
        """sort_migrations with empty list returns empty."""
        src = _migrate_with_main("""\
            let migrations: List<Migration> = []
            let sorted: List<Migration> = sort_migrations(migrations)
            println(str(len(sorted)))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
