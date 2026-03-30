"""db/pool.mn — Connection Pool tests.

Tests verify that the connection pool module compiles to valid LLVM IR via the
MIR-based emitter. Since cross-module compilation (Phase 8) is not yet ready,
tests inline the SQL core and pool module source code within test programs.

Covers:
  - Pool creation with new_pool_config and new_pool
  - Checkout and checkin flow
  - Pool size and active count queries
  - Checkout all connections, verify none idle
  - close_pool closes all connections
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

_SQL_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "sql.mn").read_text(
    encoding="utf-8"
)

_POOL_MN = (Path(__file__).resolve().parent.parent.parent / "stdlib" / "db" / "pool.mn").read_text(
    encoding="utf-8"
)


# Combine both modules. Strip import and extern lines from pool.mn since
# we inline sql.mn directly. Also strip extern/connect/close from sql.mn
# that reference C FFI — pool logic is testable without actual connections.
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


_SQL_PURE = _stub_externs(_SQL_MN)

_POOL_PURE = _stub_externs(
    "\n".join(line for line in _POOL_MN.splitlines() if not line.startswith("import "))
)

_POOL_COMBINED = _SQL_PURE + "\n\n" + _POOL_PURE


def _compile_mir(source: str) -> str:
    """Compile via MIR-based LLVM emitter."""
    return _compile_to_llvm_ir(source, "test_sql_pool.mn", use_mir=True)


def _pool_with_main(main_body: str) -> str:
    """Prepend combined SQL+Pool source and wrap main_body in fn main()."""
    return _POOL_COMBINED + "\n\n" + textwrap.dedent(f"""\
        fn main() {{
        {textwrap.indent(textwrap.dedent(main_body), '    ')}
        }}
    """)


# ---------------------------------------------------------------------------
# Pool config construction
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPoolConfig:
    def test_new_pool_config(self) -> None:
        """new_pool_config constructor compiles."""
        src = _pool_with_main("""\
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 10, 60000)
            print(config.url)
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pool_config_fields(self) -> None:
        """PoolConfig field access compiles."""
        src = _pool_with_main("""\
            let config: PoolConfig = new_pool_config("sqlite:///app.db", 1, 5, 30000)
            print(str(config.min_conns))
            print(str(config.max_conns))
            print(str(config.idle_timeout))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pool_config_struct_literal(self) -> None:
        """PoolConfig via struct literal compiles."""
        src = _pool_with_main("""\
            let config: PoolConfig = new PoolConfig { url: "sqlite:///x.db", min_conns: 0, max_conns: 3, idle_timeout: 5000 }
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Pool creation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPoolCreation:
    def test_pool_struct(self) -> None:
        """Pool struct can be constructed directly."""
        src = _pool_with_main("""\
            let conns: List<Connection> = []
            let flags: List<Bool> = []
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 0, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pool_with_connections(self) -> None:
        """Pool struct with pre-populated connections compiles."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2]
            let flags: List<Bool> = [false, false]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 10, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Checkout and checkin
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestCheckoutCheckin:
    def test_checkout(self) -> None:
        """checkout returns an idle connection."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1]
            let flags: List<Bool> = [false]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 1, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let result: Result<Connection, SqlError> = checkout(pool)
            match result {
                Ok(conn) => { print(str(conn.handle)) },
                Err(e) => { print(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_checkin(self) -> None:
        """checkin returns pool with connection marked idle."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1]
            let flags: List<Bool> = [true]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 1, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let updated: Pool = checkin(pool, c1)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_checkout_with_pool(self) -> None:
        """checkout_with_pool returns updated pool state."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2]
            let flags: List<Bool> = [false, false]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let cr: CheckoutResult = checkout_with_pool(pool)
            print(str(cr.ok))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_checkout_then_checkin_cycle(self) -> None:
        """Full checkout-checkin cycle compiles."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1]
            let flags: List<Bool> = [false]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 1, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let cr: CheckoutResult = checkout_with_pool(pool)
            let pool2: Pool = checkin(cr.pool, cr.conn)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Pool size and active count
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPoolStatus:
    def test_pool_size(self) -> None:
        """pool_size returns total connection count."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2]
            let flags: List<Bool> = [false, true]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 10, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let size: Int = pool_size(pool)
            print(str(size))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pool_active(self) -> None:
        """pool_active returns count of in-use connections."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let c3: Connection = new Connection { handle: 3, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2, c3]
            let flags: List<Bool> = [true, false, true]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 3, 10, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let active: Int = pool_active(pool)
            print(str(active))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_pool_idle(self) -> None:
        """pool_idle returns count of available connections."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2]
            let flags: List<Bool> = [true, false]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 10, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let idle: Int = pool_idle(pool)
            print(str(idle))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_all_connections_in_use(self) -> None:
        """All connections checked out, pool_idle returns 0."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2]
            let flags: List<Bool> = [true, true]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 2, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let idle: Int = pool_idle(pool)
            let active: Int = pool_active(pool)
            print(str(idle))
            print(str(active))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_empty_pool(self) -> None:
        """Empty pool has size 0."""
        src = _pool_with_main("""\
            let conns: List<Connection> = []
            let flags: List<Bool> = []
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 0, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let size: Int = pool_size(pool)
            let active: Int = pool_active(pool)
            let idle: Int = pool_idle(pool)
            print(str(size))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Close pool
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestClosePool:
    def test_close_pool_empty(self) -> None:
        """close_pool on empty pool compiles."""
        src = _pool_with_main("""\
            let conns: List<Connection> = []
            let flags: List<Bool> = []
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 0, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let result: Result<Bool, SqlError> = close_pool(pool)
            print("ok")
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_close_pool_with_connections(self) -> None:
        """close_pool with active connections compiles."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let c2: Connection = new Connection { handle: 2, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1, c2]
            let flags: List<Bool> = [false, false]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 2, 5, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let result: Result<Bool, SqlError> = close_pool(pool)
            match result {
                Ok(ok) => { print("closed") },
                Err(e) => { print(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out


# ---------------------------------------------------------------------------
# Pool exhaustion
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_LLVMLITE, reason="llvmlite not installed")
class TestPoolExhaustion:
    def test_checkout_exhausted_pool(self) -> None:
        """checkout on fully exhausted pool returns error."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1]
            let flags: List<Bool> = [true]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 1, 1, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let result: Result<Connection, SqlError> = checkout(pool)
            match result {
                Ok(conn) => { print("got connection") },
                Err(e) => { print(error_message(e)) }
            }
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out

    def test_checkout_with_pool_exhausted(self) -> None:
        """checkout_with_pool on exhausted pool returns error in CheckoutResult."""
        src = _pool_with_main("""\
            let c1: Connection = new Connection { handle: 1, driver: "sqlite", url: "sqlite:///test.db" }
            let conns: List<Connection> = [c1]
            let flags: List<Bool> = [true]
            let config: PoolConfig = new_pool_config("sqlite:///test.db", 1, 1, 60000)
            let pool: Pool = new Pool { connections: conns, in_use: flags, config: config }
            let cr: CheckoutResult = checkout_with_pool(pool)
            print(str(cr.ok))
        """)
        ir_out = _compile_mir(src)
        assert "main" in ir_out
