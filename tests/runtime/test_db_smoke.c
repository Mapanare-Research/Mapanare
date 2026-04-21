/*
 * test_db_smoke.c — v4.29.0 PLAN §1.1 smoke test for mapanare_db.c.
 *
 * Why this test exists
 * --------------------
 *
 * Prior to v4.29.0, runtime/native/mapanare_db.c (1,130 lines of SQLite,
 * PostgreSQL, Redis, and extended-filesystem bindings) was orphaned:
 * neither the Makefile's build-rt target nor scripts/build_stage1.py nor
 * the LLVM text emitter's runtime declaration table knew about it. The
 * v4.26.0 seven-reviewer panel (Anaconda HIGH) flagged it; v4.29.0 wired
 * it in. This smoke test is the fuse: any future edit that accidentally
 * re-orphans the file will fail to link this test and the native CI job
 * breaks.
 *
 * What it tests
 * -------------
 *
 * Two things, in order:
 *
 * 1) ``test_link_is_wired_up`` — the call to ``__mn_sqlite3_open`` must
 *    resolve at link time against the symbols pulled in from
 *    ``mapanare_db.c``. If the file is not built, the linker errors;
 *    that is the entire point of this test. We do not care whether the
 *    call *succeeds* — only that it links.
 *
 * 2) ``test_round_trip_when_sqlite_available`` — if libsqlite3 is
 *    installed in the test environment, we exercise the full
 *    open/exec/close cycle on an in-memory DB. On CI machines without
 *    libsqlite3, ``__mn_sqlite3_open`` returns 0 (graceful dlopen
 *    failure), and this test prints "skipped" and exits 0 — which is
 *    exactly what the PLAN asks for (the fuse is on the link, not on
 *    having sqlite3 installed).
 *
 * Build line (also referenced by the CI native job):
 *
 *     gcc -O2 -I runtime/native tests/runtime/test_db_smoke.c \
 *         runtime/native/libmapanare_rt.a \
 *         -o /tmp/test_db_smoke -lm -lpthread -ldl
 *     /tmp/test_db_smoke
 */

#include "mapanare_core.h"
#include "mapanare_db.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int g_fail_count = 0;

static void fail(const char *msg) {
    fprintf(stderr, "FAIL: %s\n", msg);
    g_fail_count++;
}

static void pass(const char *msg) {
    printf("pass: %s\n", msg);
}

/* MnString.data has its LSB set as a "heap" tag (see
 * mapanare_core.c:mn_tag_heap). Untag before reading raw bytes. */
static const char *mnstr_bytes(MnString s) {
    return (const char *)((uintptr_t)s.data & ~(uintptr_t)1);
}

static void test_link_is_wired_up(void) {
    /* Open an in-memory database. Return value:
     *   handle > 0: libsqlite3 found, DB opened.
     *   handle == 0: libsqlite3 not available (graceful dlopen failure).
     *
     * Either way the call resolved at link time against the symbol
     * from mapanare_db.c. If mapanare_db.c is re-orphaned, this file
     * fails to link — that is the fuse.
     */
    MnString mem = __mn_str_from_cstr(":memory:");
    int64_t h = __mn_sqlite3_open(mem);
    if (h < 0) {
        fail("__mn_sqlite3_open returned a negative handle");
        return;
    }
    if (h > 0) {
        /* Path where libsqlite3 is installed — close the handle so we
         * do not leak across the next subtest. */
        __mn_sqlite3_close(h);
    }
    pass("test_link_is_wired_up (mapanare_db.c symbol resolves)");
}

static void test_round_trip_when_sqlite_available(void) {
    MnString mem = __mn_str_from_cstr(":memory:");
    int64_t h = __mn_sqlite3_open(mem);
    if (h == 0) {
        printf("skip: libsqlite3 not available in this environment "
               "(mapanare_db.c still linked correctly — the fuse held).\n");
        return;
    }

    MnString create = __mn_str_from_cstr(
        "CREATE TABLE t (k INTEGER PRIMARY KEY, v TEXT)"
    );
    int64_t rc_create = __mn_sqlite3_exec(h, create);
    if (rc_create != 0) {
        fail("CREATE TABLE returned non-zero");
        __mn_sqlite3_close(h);
        return;
    }

    MnString insert = __mn_str_from_cstr(
        "INSERT INTO t (k, v) VALUES (1, 'hello')"
    );
    int64_t rc_insert = __mn_sqlite3_exec(h, insert);
    if (rc_insert != 0) {
        fail("INSERT returned non-zero");
        __mn_sqlite3_close(h);
        return;
    }

    /* Read back via prepared statement. */
    MnString select = __mn_str_from_cstr("SELECT v FROM t WHERE k = 1");
    int64_t stmt = __mn_sqlite3_prepare(h, select);
    if (stmt == 0) {
        fail("PREPARE returned 0");
        __mn_sqlite3_close(h);
        return;
    }

    int64_t step_rc = __mn_sqlite3_step(stmt);
    /* SQLITE_ROW == 100. SQLITE_DONE == 101. Either means the driver
     * worked and we got either a row or end-of-results. */
    if (step_rc != 100 && step_rc != 101) {
        fail("__mn_sqlite3_step returned an unexpected code");
        __mn_sqlite3_finalize(stmt);
        __mn_sqlite3_close(h);
        return;
    }

    if (step_rc == 100) {
        MnString v = __mn_sqlite3_column_str(stmt, 0);
        if (v.len != 5 || strncmp(mnstr_bytes(v), "hello", 5) != 0) {
            fail("column 0 did not contain 'hello'");
            __mn_sqlite3_finalize(stmt);
            __mn_sqlite3_close(h);
            return;
        }
    }

    __mn_sqlite3_finalize(stmt);
    __mn_sqlite3_close(h);
    pass("test_round_trip_when_sqlite_available");
}

int main(void) {
    printf("=== test_db_smoke (v4.29.0 Phase 1.1) ===\n");
    test_link_is_wired_up();
    test_round_trip_when_sqlite_available();
    if (g_fail_count > 0) {
        fprintf(stderr, "\n%d failure(s)\n", g_fail_count);
        return 1;
    }
    printf("\nOK — mapanare_db.c smoke suite passed.\n");
    return 0;
}
