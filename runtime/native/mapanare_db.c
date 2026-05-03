/**
 * mapanare_db.c --- Database & extended filesystem runtime implementation
 *
 * Implements SQLite3, PostgreSQL, and Redis bindings via dlopen, plus
 * extended POSIX filesystem operations with Windows fallbacks.
 */

#include "mapanare_db.h"
#include "mapanare_internal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

/* =======================================================================
 * Platform-specific includes
 * ======================================================================= */

#ifdef _WIN32
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #include <windows.h>
  #include <io.h>
  #include <direct.h>
  #include <sys/stat.h>
  #include <sys/types.h>

  #define mn_dlopen(name)       LoadLibraryA(name)
  #define mn_dlsym(lib, name)   GetProcAddress((HMODULE)(lib), name)
  #define mn_dlclose(lib)       FreeLibrary((HMODULE)(lib))
  typedef HMODULE mn_lib_t;

#else /* POSIX */
  #include <unistd.h>
  #include <sys/stat.h>
  #include <sys/types.h>
  #include <limits.h>
  #include <dlfcn.h>

  #define mn_dlopen(name)       dlopen(name, RTLD_LAZY)
  #define mn_dlsym(lib, name)   dlsym(lib, name)
  #define mn_dlclose(lib)       dlclose(lib)
  typedef void *mn_lib_t;
#endif

/* =======================================================================
 * Utility: MnString <-> C string conversion
 *
 * MnString uses a tag bit (LSB of data pointer) to distinguish heap
 * from constant strings. We must untag before reading.
 * ======================================================================= */

/* v4.32.0 Phase 2.3: mnstr_to_cstr is now in mapanare_internal.h */

/* =======================================================================
 * Handle table infrastructure
 *
 * Each database library gets a fixed-size table of opaque pointers.
 * Handle = array index + 1 (so 0 means "invalid/error").
 * ======================================================================= */

/* v4.32.0: MnHandleTable and MN_MAX_HANDLES are now in
 * mapanare_internal.h. The local handle_alloc/get/free functions
 * below use 1-based handles (return index+1, access h-1) and are NOT
 * equivalent to the header's mn_handle_alloc/get/free (0-based). */

static int64_t handle_alloc(MnHandleTable *t, void *ptr) {
    for (int i = 0; i < MN_MAX_HANDLES; i++) {
        if (t->ptrs[i] == NULL) {
            t->ptrs[i] = ptr;
            return (int64_t)(i + 1);
        }
    }
    return 0;  /* table full */
}

static void *handle_get(MnHandleTable *t, int64_t h) {
    if (h <= 0 || h > MN_MAX_HANDLES) return NULL;
    return t->ptrs[h - 1];
}

static void handle_free(MnHandleTable *t, int64_t h) {
    if (h > 0 && h <= MN_MAX_HANDLES) {
        t->ptrs[h - 1] = NULL;
    }
}

/* =======================================================================
 * 1. SQLite3 Bindings (via dlopen)
 * ======================================================================= */

/* SQLite3 constants */
#define MN_SQLITE_OK     0
#define MN_SQLITE_ROW    100
#define MN_SQLITE_DONE   101
#define MN_SQLITE_TRANSIENT ((void *)(intptr_t)-1)

/* SQLite3 column type constants */
#define MN_SQLITE_INTEGER 1
#define MN_SQLITE_FLOAT   2
#define MN_SQLITE_TEXT    3
#define MN_SQLITE_BLOB    4
#define MN_SQLITE_NULL    5

/* Opaque SQLite3 types */
typedef struct sqlite3       mn_sqlite3;
typedef struct sqlite3_stmt  mn_sqlite3_stmt;

/* Function pointer types */
typedef int    (*fn_sqlite3_open)(const char *, mn_sqlite3 **);
typedef int    (*fn_sqlite3_close)(mn_sqlite3 *);
typedef int    (*fn_sqlite3_exec)(mn_sqlite3 *, const char *, void *, void *, char **);
typedef int    (*fn_sqlite3_prepare_v2)(mn_sqlite3 *, const char *, int, mn_sqlite3_stmt **, const char **);
typedef int    (*fn_sqlite3_bind_int64)(mn_sqlite3_stmt *, int, int64_t);
typedef int    (*fn_sqlite3_bind_double)(mn_sqlite3_stmt *, int, double);
typedef int    (*fn_sqlite3_bind_text)(mn_sqlite3_stmt *, int, const char *, int, void *);
typedef int    (*fn_sqlite3_bind_null)(mn_sqlite3_stmt *, int);
typedef int    (*fn_sqlite3_step)(mn_sqlite3_stmt *);
typedef int64_t (*fn_sqlite3_column_int64)(mn_sqlite3_stmt *, int);
typedef double (*fn_sqlite3_column_double)(mn_sqlite3_stmt *, int);
typedef const unsigned char *(*fn_sqlite3_column_text)(mn_sqlite3_stmt *, int);
typedef int    (*fn_sqlite3_column_type)(mn_sqlite3_stmt *, int);
typedef int    (*fn_sqlite3_column_count)(mn_sqlite3_stmt *);
typedef const char *(*fn_sqlite3_column_name)(mn_sqlite3_stmt *, int);
typedef int    (*fn_sqlite3_finalize)(mn_sqlite3_stmt *);
typedef const char *(*fn_sqlite3_errmsg)(mn_sqlite3 *);
typedef void   (*fn_sqlite3_free)(void *);

/* v5.35.0 Sq.7 additions — version check, blob support, statement
 * cache reuse (reset), named-parameter binding, change tracking.
 * All present in the sqlite3 v3.7.0+ API surface (15 years stable). */
typedef const char *(*fn_sqlite3_libversion)(void);
typedef int    (*fn_sqlite3_bind_blob)(mn_sqlite3_stmt *, int, const void *, int, void *);
typedef const void *(*fn_sqlite3_column_blob)(mn_sqlite3_stmt *, int);
typedef int    (*fn_sqlite3_column_bytes)(mn_sqlite3_stmt *, int);
typedef int    (*fn_sqlite3_reset)(mn_sqlite3_stmt *);
typedef int    (*fn_sqlite3_bind_parameter_index)(mn_sqlite3_stmt *, const char *);
typedef int    (*fn_sqlite3_changes)(mn_sqlite3 *);
typedef int64_t (*fn_sqlite3_last_insert_rowid)(mn_sqlite3 *);
typedef int    (*fn_sqlite3_extended_errcode)(mn_sqlite3 *);

/* Dynamic SQLite3 state */
static struct {
    int loaded;
    int available;
    mn_lib_t lib;
    fn_sqlite3_open           p_open;
    fn_sqlite3_close          p_close;
    fn_sqlite3_exec           p_exec;
    fn_sqlite3_prepare_v2     p_prepare_v2;
    fn_sqlite3_bind_int64     p_bind_int64;
    fn_sqlite3_bind_double    p_bind_double;
    fn_sqlite3_bind_text      p_bind_text;
    fn_sqlite3_bind_null      p_bind_null;
    fn_sqlite3_step           p_step;
    fn_sqlite3_column_int64   p_column_int64;
    fn_sqlite3_column_double  p_column_double;
    fn_sqlite3_column_text    p_column_text;
    fn_sqlite3_column_type    p_column_type;
    fn_sqlite3_column_count   p_column_count;
    fn_sqlite3_column_name    p_column_name;
    fn_sqlite3_finalize       p_finalize;
    fn_sqlite3_errmsg         p_errmsg;
    fn_sqlite3_free           p_free;
    /* v5.35.0 Sq.7 additions */
    fn_sqlite3_libversion           p_libversion;
    fn_sqlite3_bind_blob            p_bind_blob;
    fn_sqlite3_column_blob          p_column_blob;
    fn_sqlite3_column_bytes         p_column_bytes;
    fn_sqlite3_reset                p_reset;
    fn_sqlite3_bind_parameter_index p_bind_parameter_index;
    fn_sqlite3_changes              p_changes;
    fn_sqlite3_last_insert_rowid    p_last_insert_rowid;
    fn_sqlite3_extended_errcode     p_extended_errcode;
} s_sqlite = {0};

static MnHandleTable s_sqlite_dbs  = {{0}};
static MnHandleTable s_sqlite_stmts = {{0}};

static int sqlite3_load(void) {
    if (s_sqlite.loaded) return s_sqlite.available ? 0 : -1;
    s_sqlite.loaded = 1;
    s_sqlite.available = 0;

#ifdef _WIN32
    s_sqlite.lib = mn_dlopen("sqlite3.dll");
    if (!s_sqlite.lib) s_sqlite.lib = mn_dlopen("libsqlite3.dll");
#else
    s_sqlite.lib = mn_dlopen("libsqlite3.so");
    if (!s_sqlite.lib) s_sqlite.lib = mn_dlopen("libsqlite3.so.0");
    #ifdef __APPLE__
    if (!s_sqlite.lib) s_sqlite.lib = mn_dlopen("libsqlite3.dylib");
    #endif
#endif

    if (!s_sqlite.lib) return -1;

    #define SQLITE_SYM(field, name) \
        s_sqlite.field = (fn_##name)mn_dlsym(s_sqlite.lib, #name)

    SQLITE_SYM(p_open,           sqlite3_open);
    SQLITE_SYM(p_close,          sqlite3_close);
    SQLITE_SYM(p_exec,           sqlite3_exec);
    SQLITE_SYM(p_prepare_v2,     sqlite3_prepare_v2);
    SQLITE_SYM(p_bind_int64,     sqlite3_bind_int64);
    SQLITE_SYM(p_bind_double,    sqlite3_bind_double);
    SQLITE_SYM(p_bind_text,      sqlite3_bind_text);
    SQLITE_SYM(p_bind_null,      sqlite3_bind_null);
    SQLITE_SYM(p_step,           sqlite3_step);
    SQLITE_SYM(p_column_int64,   sqlite3_column_int64);
    SQLITE_SYM(p_column_double,  sqlite3_column_double);
    SQLITE_SYM(p_column_text,    sqlite3_column_text);
    SQLITE_SYM(p_column_type,    sqlite3_column_type);
    SQLITE_SYM(p_column_count,   sqlite3_column_count);
    SQLITE_SYM(p_column_name,    sqlite3_column_name);
    SQLITE_SYM(p_finalize,       sqlite3_finalize);
    SQLITE_SYM(p_errmsg,         sqlite3_errmsg);
    SQLITE_SYM(p_free,           sqlite3_free);

    /* v5.35.0 Sq.7 — these are optional at load time. The Sq.7
     * fast-path checks each pointer at call time and returns a
     * distinct error code if the symbol was missing (library too
     * old / stripped). The "required" symbols list below is
     * unchanged so existing v5.34.x callers see no behavior
     * change. */
    SQLITE_SYM(p_libversion,           sqlite3_libversion);
    SQLITE_SYM(p_bind_blob,            sqlite3_bind_blob);
    SQLITE_SYM(p_column_blob,          sqlite3_column_blob);
    SQLITE_SYM(p_column_bytes,         sqlite3_column_bytes);
    SQLITE_SYM(p_reset,                sqlite3_reset);
    SQLITE_SYM(p_bind_parameter_index, sqlite3_bind_parameter_index);
    SQLITE_SYM(p_changes,              sqlite3_changes);
    SQLITE_SYM(p_last_insert_rowid,    sqlite3_last_insert_rowid);
    SQLITE_SYM(p_extended_errcode,     sqlite3_extended_errcode);

    #undef SQLITE_SYM

    /* Verify required symbols */
    if (!s_sqlite.p_open || !s_sqlite.p_close || !s_sqlite.p_exec ||
        !s_sqlite.p_prepare_v2 || !s_sqlite.p_step || !s_sqlite.p_finalize ||
        !s_sqlite.p_errmsg) {
        return -1;
    }

    s_sqlite.available = 1;
    return 0;
}

MN_DB_EXPORT int64_t __mn_sqlite3_open(MnString path) {
    if (!s_sqlite.available) {
        if (sqlite3_load() < 0) return 0;
    }

    char *cpath = mnstr_to_cstr(path);
    if (!cpath) return 0;

    mn_sqlite3 *db = NULL;
    int rc = s_sqlite.p_open(cpath, &db);
    free(cpath);

    if (rc != MN_SQLITE_OK || !db) {
        if (db) s_sqlite.p_close(db);
        return 0;
    }

    int64_t handle = handle_alloc(&s_sqlite_dbs, db);
    if (handle == 0) {
        s_sqlite.p_close(db);
        return 0;
    }
    return handle;
}

MN_DB_EXPORT void __mn_sqlite3_close(int64_t handle) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available) return;
    s_sqlite.p_close(db);
    handle_free(&s_sqlite_dbs, handle);
}

MN_DB_EXPORT int64_t __mn_sqlite3_exec(int64_t handle, MnString sql) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available) return -1;

    char *csql = mnstr_to_cstr(sql);
    if (!csql) return -1;

    char *errmsg = NULL;
    int rc = s_sqlite.p_exec(db, csql, NULL, NULL, &errmsg);
    free(csql);
    if (errmsg && s_sqlite.p_free) s_sqlite.p_free(errmsg);

    return (int64_t)rc;
}

MN_DB_EXPORT int64_t __mn_sqlite3_prepare(int64_t handle, MnString sql) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available) return 0;

    char *csql = mnstr_to_cstr(sql);
    if (!csql) return 0;

    mn_sqlite3_stmt *stmt = NULL;
    int rc = s_sqlite.p_prepare_v2(db, csql, (int)sql.len, &stmt, NULL);
    free(csql);

    if (rc != MN_SQLITE_OK || !stmt) {
        if (stmt) s_sqlite.p_finalize(stmt);
        return 0;
    }

    int64_t shandle = handle_alloc(&s_sqlite_stmts, stmt);
    if (shandle == 0) {
        s_sqlite.p_finalize(stmt);
        return 0;
    }
    return shandle;
}

MN_DB_EXPORT int64_t __mn_sqlite3_bind_int(int64_t stmt, int64_t idx, int64_t val) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_bind_int64) return -1;
    return (int64_t)s_sqlite.p_bind_int64(s, (int)idx, val);
}

MN_DB_EXPORT int64_t __mn_sqlite3_bind_float(int64_t stmt, int64_t idx, double val) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_bind_double) return -1;
    return (int64_t)s_sqlite.p_bind_double(s, (int)idx, val);
}

MN_DB_EXPORT int64_t __mn_sqlite3_bind_str(int64_t stmt, int64_t idx, MnString val) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_bind_text) return -1;

    char *cval = mnstr_to_cstr(val);
    if (!cval) return -1;

    int rc = s_sqlite.p_bind_text(s, (int)idx, cval, (int)val.len, MN_SQLITE_TRANSIENT);
    free(cval);
    return (int64_t)rc;
}

MN_DB_EXPORT int64_t __mn_sqlite3_bind_null(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_bind_null) return -1;
    return (int64_t)s_sqlite.p_bind_null(s, (int)idx);
}

MN_DB_EXPORT int64_t __mn_sqlite3_step(int64_t stmt) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available) return -1;
    return (int64_t)s_sqlite.p_step(s);
}

MN_DB_EXPORT int64_t __mn_sqlite3_column_int(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_int64) return 0;
    return s_sqlite.p_column_int64(s, (int)idx);
}

MN_DB_EXPORT double __mn_sqlite3_column_float(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_double) return 0.0;
    return s_sqlite.p_column_double(s, (int)idx);
}

MN_DB_EXPORT MnString __mn_sqlite3_column_str(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_text) return __mn_str_empty();

    const unsigned char *text = s_sqlite.p_column_text(s, (int)idx);
    if (!text) return __mn_str_empty();
    return __mn_str_from_cstr((const char *)text);
}

MN_DB_EXPORT int64_t __mn_sqlite3_column_type(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_type) return MN_SQLITE_NULL;
    return (int64_t)s_sqlite.p_column_type(s, (int)idx);
}

MN_DB_EXPORT int64_t __mn_sqlite3_column_count(int64_t stmt) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_count) return 0;
    return (int64_t)s_sqlite.p_column_count(s);
}

MN_DB_EXPORT MnString __mn_sqlite3_column_name(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_name) return __mn_str_empty();

    const char *name = s_sqlite.p_column_name(s, (int)idx);
    if (!name) return __mn_str_empty();
    return __mn_str_from_cstr(name);
}

MN_DB_EXPORT int64_t __mn_sqlite3_finalize(int64_t stmt) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available) return -1;
    int rc = s_sqlite.p_finalize(s);
    handle_free(&s_sqlite_stmts, stmt);
    return (int64_t)rc;
}

MN_DB_EXPORT MnString __mn_sqlite3_errmsg(int64_t handle) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available || !s_sqlite.p_errmsg) {
        return __mn_str_from_cstr("sqlite3 not available");
    }
    const char *msg = s_sqlite.p_errmsg(db);
    if (!msg) return __mn_str_empty();
    return __mn_str_from_cstr(msg);
}

/* v5.35.0 Sq.7 — additions for the new stdlib/sql/sqlite/ surface.
 * Each wrapper guards on s_sqlite.available AND on the specific
 * function pointer being non-NULL (the Sq.* surface treats a
 * missing optional symbol as load-fail rather than masking it). */

/* Get the runtime-loaded sqlite3 library version string (e.g.
 * "3.31.1"). Empty string if the library wasn't loaded or is
 * too old to expose sqlite3_libversion (pre-3.0). The Sq.1
 * Database.open path parses this and rejects libraries below
 * 3.7.0 with SqlError::VersionTooOld. */
MN_DB_EXPORT MnString __mn_sqlite3_libversion(void) {
    if (!s_sqlite.available) {
        if (sqlite3_load() < 0) return __mn_str_empty();
    }
    if (!s_sqlite.p_libversion) return __mn_str_empty();
    const char *v = s_sqlite.p_libversion();
    if (!v) return __mn_str_empty();
    return __mn_str_from_cstr(v);
}

/* Bind a blob to a prepared statement. The Mapanare surface carries
 * blobs as MnString since both share the {ptr, len} layout and
 * sqlite treats them as opaque byte buffers. SQLITE_TRANSIENT tells
 * sqlite to copy the bytes immediately so the caller can free or
 * reuse the source buffer. Returns 0 on success, sqlite rc on
 * failure, -1 if the symbol wasn't resolved. */
MN_DB_EXPORT int64_t __mn_sqlite3_bind_blob(int64_t stmt, int64_t idx, MnString val) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_bind_blob) return -1;
    return (int64_t)s_sqlite.p_bind_blob(s, (int)idx, val.data, (int)val.len, MN_SQLITE_TRANSIENT);
}

/* Read a blob column. Returns the bytes as an MnString (length-
 * prefixed; raw bytes, no encoding). Empty string if the column
 * is NULL or the symbol wasn't resolved. The Sq.3 Value::Blob
 * variant carries this through to the caller. */
MN_DB_EXPORT MnString __mn_sqlite3_column_blob(int64_t stmt, int64_t idx) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_column_blob || !s_sqlite.p_column_bytes) {
        return __mn_str_empty();
    }
    /* sqlite3 docs: call sqlite3_column_bytes BEFORE sqlite3_column_blob
     * is most efficient when the column is a TEXT (forces conversion
     * once); for actual BLOBs the order doesn't matter, but we follow
     * the docs' pattern to keep behavior consistent across types. */
    int n = s_sqlite.p_column_bytes(s, (int)idx);
    if (n <= 0) return __mn_str_empty();
    const void *data = s_sqlite.p_column_blob(s, (int)idx);
    if (!data) return __mn_str_empty();
    return __mn_str_from_parts((const char *)data, (int64_t)n);
}

/* Reset a prepared statement back to its initial state so it can
 * be re-bound and re-executed. Used by the Sq.5 statement cache
 * when handing out a previously-prepared statement on a cache hit.
 * Does NOT clear bound parameters (sqlite3_reset preserves them);
 * the Sq.5 cache caller invokes reset followed by re-binding all
 * params. Returns 0 on success, sqlite rc on failure, -1 if not
 * resolved. */
MN_DB_EXPORT int64_t __mn_sqlite3_reset(int64_t stmt) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_reset) return -1;
    return (int64_t)s_sqlite.p_reset(s);
}

/* Resolve a named parameter (e.g. ":id", "@name", "$value") to its
 * 1-based index in the prepared statement. Returns 0 if the name
 * is not bound — sqlite uses 0 as the not-found sentinel. The Sq.2
 * bind_named method maps this 0 to SqlError::BadSql with a clear
 * "no such parameter: NAME" message. */
MN_DB_EXPORT int64_t __mn_sqlite3_bind_parameter_index(int64_t stmt, MnString name) {
    mn_sqlite3_stmt *s = (mn_sqlite3_stmt *)handle_get(&s_sqlite_stmts, stmt);
    if (!s || !s_sqlite.available || !s_sqlite.p_bind_parameter_index) return 0;
    char *cname = mnstr_to_cstr(name);
    if (!cname) return 0;
    int idx = s_sqlite.p_bind_parameter_index(s, cname);
    free(cname);
    return (int64_t)idx;
}

/* Number of rows modified by the most recent INSERT, UPDATE, or
 * DELETE on this connection. For SELECT, returns the value as of
 * the previous data-modifying statement. Used by Database.execute
 * to return rows-affected from the .mn surface. */
MN_DB_EXPORT int64_t __mn_sqlite3_changes(int64_t handle) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available || !s_sqlite.p_changes) return 0;
    return (int64_t)s_sqlite.p_changes(db);
}

/* ROWID of the most recent successful INSERT into a rowid table
 * on this connection. 0 if no INSERT has occurred. */
MN_DB_EXPORT int64_t __mn_sqlite3_last_insert_rowid(int64_t handle) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available || !s_sqlite.p_last_insert_rowid) return 0;
    return s_sqlite.p_last_insert_rowid(db);
}

/* Extended error code for the most recent error on this connection.
 * Sqlite's primary rc is coarse (e.g. SQLITE_CONSTRAINT = 19); the
 * extended code distinguishes specific constraint classes
 * (SQLITE_CONSTRAINT_UNIQUE = 2067, SQLITE_CONSTRAINT_NOTNULL = 1299,
 * SQLITE_BUSY = 5, etc.). The Sq.1 from_sqlite_rc helper uses this
 * to map sqlite errors to specific SqlError variants. */
MN_DB_EXPORT int64_t __mn_sqlite3_extended_errcode(int64_t handle) {
    mn_sqlite3 *db = (mn_sqlite3 *)handle_get(&s_sqlite_dbs, handle);
    if (!db || !s_sqlite.available || !s_sqlite.p_extended_errcode) return 0;
    return (int64_t)s_sqlite.p_extended_errcode(db);
}

/* =======================================================================
 * 2. PostgreSQL Bindings (via dlopen of libpq)
 * ======================================================================= */

/* libpq status constants */
#define MN_PGRES_EMPTY_QUERY  0
#define MN_PGRES_COMMAND_OK   1
#define MN_PGRES_TUPLES_OK    2
#define MN_PGRES_FATAL_ERROR  7

/* Connection status */
#define MN_PG_CONNECTION_OK   0
#define MN_PG_CONNECTION_BAD  1

/* Opaque libpq types */
typedef struct pg_conn    mn_PGconn;
typedef struct pg_result  mn_PGresult;

/* Function pointer types */
typedef mn_PGconn *(*fn_PQconnectdb)(const char *);
typedef int        (*fn_PQstatus)(const mn_PGconn *);
typedef void       (*fn_PQfinish)(mn_PGconn *);
typedef mn_PGresult *(*fn_PQexec)(mn_PGconn *, const char *);
typedef mn_PGresult *(*fn_PQexecParams)(mn_PGconn *, const char *, int,
                                         const void *, const char *const *,
                                         const int *, const int *, int);
typedef int        (*fn_PQntuples)(const mn_PGresult *);
typedef int        (*fn_PQnfields)(const mn_PGresult *);
typedef char      *(*fn_PQgetvalue)(const mn_PGresult *, int, int);
typedef char      *(*fn_PQfname)(const mn_PGresult *, int);
typedef int        (*fn_PQresultStatus)(const mn_PGresult *);
typedef char      *(*fn_PQerrorMessage)(const mn_PGconn *);
typedef void       (*fn_PQclear)(mn_PGresult *);

/* Dynamic libpq state */
static struct {
    int loaded;
    int available;
    mn_lib_t lib;
    fn_PQconnectdb    p_connectdb;
    fn_PQstatus       p_status;
    fn_PQfinish       p_finish;
    fn_PQexec         p_exec;
    fn_PQexecParams   p_execParams;
    fn_PQntuples      p_ntuples;
    fn_PQnfields      p_nfields;
    fn_PQgetvalue     p_getvalue;
    fn_PQfname        p_fname;
    fn_PQresultStatus p_resultStatus;
    fn_PQerrorMessage p_errorMessage;
    fn_PQclear        p_clear;
} s_pg = {0};

static MnHandleTable s_pg_conns   = {{0}};
static MnHandleTable s_pg_results = {{0}};

static int pg_load(void) {
    if (s_pg.loaded) return s_pg.available ? 0 : -1;
    s_pg.loaded = 1;
    s_pg.available = 0;

#ifdef _WIN32
    s_pg.lib = mn_dlopen("libpq.dll");
    if (!s_pg.lib) s_pg.lib = mn_dlopen("pq.dll");
#else
    s_pg.lib = mn_dlopen("libpq.so");
    if (!s_pg.lib) s_pg.lib = mn_dlopen("libpq.so.5");
    #ifdef __APPLE__
    if (!s_pg.lib) s_pg.lib = mn_dlopen("libpq.dylib");
    #endif
#endif

    if (!s_pg.lib) return -1;

    #define PG_SYM(field, name) \
        s_pg.field = (fn_##name)mn_dlsym(s_pg.lib, #name)

    PG_SYM(p_connectdb,    PQconnectdb);
    PG_SYM(p_status,       PQstatus);
    PG_SYM(p_finish,       PQfinish);
    PG_SYM(p_exec,         PQexec);
    PG_SYM(p_execParams,   PQexecParams);
    PG_SYM(p_ntuples,      PQntuples);
    PG_SYM(p_nfields,      PQnfields);
    PG_SYM(p_getvalue,     PQgetvalue);
    PG_SYM(p_fname,        PQfname);
    PG_SYM(p_resultStatus, PQresultStatus);
    PG_SYM(p_errorMessage, PQerrorMessage);
    PG_SYM(p_clear,        PQclear);

    #undef PG_SYM

    /* Verify required symbols */
    if (!s_pg.p_connectdb || !s_pg.p_finish || !s_pg.p_exec ||
        !s_pg.p_ntuples || !s_pg.p_nfields || !s_pg.p_getvalue ||
        !s_pg.p_resultStatus || !s_pg.p_clear) {
        return -1;
    }

    s_pg.available = 1;
    return 0;
}

MN_DB_EXPORT int64_t __mn_pg_connect(MnString conninfo) {
    if (!s_pg.available) {
        if (pg_load() < 0) return 0;
    }

    char *cinfo = mnstr_to_cstr(conninfo);
    if (!cinfo) return 0;

    mn_PGconn *conn = s_pg.p_connectdb(cinfo);
    free(cinfo);

    if (!conn) return 0;

    /* Check connection status */
    if (s_pg.p_status && s_pg.p_status(conn) != MN_PG_CONNECTION_OK) {
        s_pg.p_finish(conn);
        return 0;
    }

    int64_t handle = handle_alloc(&s_pg_conns, conn);
    if (handle == 0) {
        s_pg.p_finish(conn);
        return 0;
    }
    return handle;
}

MN_DB_EXPORT void __mn_pg_close(int64_t conn) {
    mn_PGconn *c = (mn_PGconn *)handle_get(&s_pg_conns, conn);
    if (!c || !s_pg.available) return;
    s_pg.p_finish(c);
    handle_free(&s_pg_conns, conn);
}

MN_DB_EXPORT int64_t __mn_pg_exec(int64_t conn, MnString sql) {
    mn_PGconn *c = (mn_PGconn *)handle_get(&s_pg_conns, conn);
    if (!c || !s_pg.available) return 0;

    char *csql = mnstr_to_cstr(sql);
    if (!csql) return 0;

    mn_PGresult *res = s_pg.p_exec(c, csql);
    free(csql);

    if (!res) return 0;

    int64_t handle = handle_alloc(&s_pg_results, res);
    if (handle == 0) {
        s_pg.p_clear(res);
        return 0;
    }
    return handle;
}

MN_DB_EXPORT int64_t __mn_pg_exec_params(int64_t conn, MnString sql,
                                          int64_t nparams, MnString *params) {
    mn_PGconn *c = (mn_PGconn *)handle_get(&s_pg_conns, conn);
    if (!c || !s_pg.available || !s_pg.p_execParams) return 0;

    char *csql = mnstr_to_cstr(sql);
    if (!csql) return 0;

    /* Convert MnString params to C string array */
    const char **cparams = NULL;
    if (nparams > 0 && params) {
        cparams = (const char **)malloc((size_t)nparams * sizeof(char *));
        if (!cparams) {
            free(csql);
            return 0;
        }
        for (int64_t i = 0; i < nparams; i++) {
            cparams[i] = mnstr_to_cstr(params[i]);
            if (!cparams[i]) {
                /* Cleanup already-converted params */
                for (int64_t j = 0; j < i; j++) free((void *)cparams[j]);
                free(cparams);
                free(csql);
                return 0;
            }
        }
    }

    mn_PGresult *res = s_pg.p_execParams(
        c, csql, (int)nparams,
        NULL,          /* paramTypes: let server infer */
        cparams,       /* paramValues */
        NULL,          /* paramLengths: text format, null-terminated */
        NULL,          /* paramFormats: all text (0) */
        0              /* resultFormat: text */
    );

    /* Cleanup C strings */
    if (cparams) {
        for (int64_t i = 0; i < nparams; i++) free((void *)cparams[i]);
        free(cparams);
    }
    free(csql);

    if (!res) return 0;

    int64_t handle = handle_alloc(&s_pg_results, res);
    if (handle == 0) {
        s_pg.p_clear(res);
        return 0;
    }
    return handle;
}

MN_DB_EXPORT int64_t __mn_pg_ntuples(int64_t result) {
    mn_PGresult *r = (mn_PGresult *)handle_get(&s_pg_results, result);
    if (!r || !s_pg.available) return 0;
    return (int64_t)s_pg.p_ntuples(r);
}

MN_DB_EXPORT int64_t __mn_pg_nfields(int64_t result) {
    mn_PGresult *r = (mn_PGresult *)handle_get(&s_pg_results, result);
    if (!r || !s_pg.available) return 0;
    return (int64_t)s_pg.p_nfields(r);
}

MN_DB_EXPORT MnString __mn_pg_getvalue(int64_t result, int64_t row, int64_t col) {
    mn_PGresult *r = (mn_PGresult *)handle_get(&s_pg_results, result);
    if (!r || !s_pg.available) return __mn_str_empty();

    char *val = s_pg.p_getvalue(r, (int)row, (int)col);
    if (!val) return __mn_str_empty();
    return __mn_str_from_cstr(val);
}

MN_DB_EXPORT MnString __mn_pg_fname(int64_t result, int64_t col) {
    mn_PGresult *r = (mn_PGresult *)handle_get(&s_pg_results, result);
    if (!r || !s_pg.available || !s_pg.p_fname) return __mn_str_empty();

    char *name = s_pg.p_fname(r, (int)col);
    if (!name) return __mn_str_empty();
    return __mn_str_from_cstr(name);
}

MN_DB_EXPORT int64_t __mn_pg_status(int64_t result) {
    mn_PGresult *r = (mn_PGresult *)handle_get(&s_pg_results, result);
    if (!r || !s_pg.available) return MN_PGRES_FATAL_ERROR;
    return (int64_t)s_pg.p_resultStatus(r);
}

MN_DB_EXPORT MnString __mn_pg_errmsg(int64_t conn) {
    mn_PGconn *c = (mn_PGconn *)handle_get(&s_pg_conns, conn);
    if (!c || !s_pg.available || !s_pg.p_errorMessage) {
        return __mn_str_from_cstr("libpq not available");
    }
    char *msg = s_pg.p_errorMessage(c);
    if (!msg) return __mn_str_empty();
    return __mn_str_from_cstr(msg);
}

MN_DB_EXPORT void __mn_pg_clear(int64_t result) {
    mn_PGresult *r = (mn_PGresult *)handle_get(&s_pg_results, result);
    if (!r || !s_pg.available) return;
    s_pg.p_clear(r);
    handle_free(&s_pg_results, result);
}

/* =======================================================================
 * 3. Redis Bindings (via dlopen of libhiredis)
 * ======================================================================= */

/* hiredis reply types */
#define MN_REDIS_REPLY_STRING  1
#define MN_REDIS_REPLY_ARRAY   2
#define MN_REDIS_REPLY_INTEGER 3
#define MN_REDIS_REPLY_NIL     4
#define MN_REDIS_REPLY_STATUS  5
#define MN_REDIS_REPLY_ERROR   6

/* Opaque hiredis types */
typedef struct mn_redisContext mn_redisContext;

/* Minimal redisReply struct layout (matches hiredis ABI) */
typedef struct mn_redisReply {
    int type;
    long long integer;
    double dval;           /* hiredis 1.0+ */
    size_t len;
    char *str;
    size_t elements;       /* array length */
    struct mn_redisReply **element;  /* array elements */
} mn_redisReply;

/* Function pointer types */
typedef mn_redisContext *(*fn_redisConnect)(const char *, int);
typedef void            *(*fn_redisCommand)(mn_redisContext *, const char *, ...);
typedef void             (*fn_freeReplyObject)(void *);
typedef void             (*fn_redisFree)(mn_redisContext *);

/* Dynamic hiredis state */
static struct {
    int loaded;
    int available;
    mn_lib_t lib;
    fn_redisConnect    p_connect;
    fn_redisCommand    p_command;
    fn_freeReplyObject p_freeReply;
    fn_redisFree       p_free;
} s_redis = {0};

/* Redis context wrapper: stores the context and last error message */
typedef struct {
    mn_redisContext *ctx;
    char errmsg[256];
} MnRedisHandle;

static MnHandleTable s_redis_ctxs = {{0}};

static int redis_load(void) {
    if (s_redis.loaded) return s_redis.available ? 0 : -1;
    s_redis.loaded = 1;
    s_redis.available = 0;

#ifdef _WIN32
    s_redis.lib = mn_dlopen("hiredis.dll");
    if (!s_redis.lib) s_redis.lib = mn_dlopen("libhiredis.dll");
#else
    s_redis.lib = mn_dlopen("libhiredis.so");
    if (!s_redis.lib) s_redis.lib = mn_dlopen("libhiredis.so.1.1.0");
    if (!s_redis.lib) s_redis.lib = mn_dlopen("libhiredis.so.1.0.0");
    if (!s_redis.lib) s_redis.lib = mn_dlopen("libhiredis.so.0.14");
    #ifdef __APPLE__
    if (!s_redis.lib) s_redis.lib = mn_dlopen("libhiredis.dylib");
    #endif
#endif

    if (!s_redis.lib) return -1;

    #define REDIS_SYM(field, name) \
        s_redis.field = (fn_##name)mn_dlsym(s_redis.lib, #name)

    REDIS_SYM(p_connect,   redisConnect);
    REDIS_SYM(p_command,   redisCommand);
    REDIS_SYM(p_freeReply, freeReplyObject);
    REDIS_SYM(p_free,      redisFree);

    #undef REDIS_SYM

    if (!s_redis.p_connect || !s_redis.p_command ||
        !s_redis.p_freeReply || !s_redis.p_free) {
        return -1;
    }

    s_redis.available = 1;
    return 0;
}

MN_DB_EXPORT int64_t __mn_redis_connect(MnString host, int64_t port) {
    if (!s_redis.available) {
        if (redis_load() < 0) return 0;
    }

    char *chost = mnstr_to_cstr(host);
    if (!chost) return 0;

    mn_redisContext *ctx = s_redis.p_connect(chost, (int)port);
    free(chost);

    if (!ctx) return 0;

    /* Check for connection error — hiredis stores err field at offset 0 */
    /* We access the err field which is an int at the start of redisContext */
    int *err_ptr = (int *)ctx;
    if (*err_ptr != 0) {
        s_redis.p_free(ctx);
        return 0;
    }

    MnRedisHandle *rh = (MnRedisHandle *)calloc(1, sizeof(MnRedisHandle));
    if (!rh) {
        s_redis.p_free(ctx);
        return 0;
    }
    rh->ctx = ctx;
    rh->errmsg[0] = '\0';

    int64_t handle = handle_alloc(&s_redis_ctxs, rh);
    if (handle == 0) {
        s_redis.p_free(ctx);
        free(rh);
        return 0;
    }
    return handle;
}

MN_DB_EXPORT MnString __mn_redis_command(int64_t ctx, MnString cmd) {
    MnRedisHandle *rh = (MnRedisHandle *)handle_get(&s_redis_ctxs, ctx);
    if (!rh || !s_redis.available) return __mn_str_empty();

    char *ccmd = mnstr_to_cstr(cmd);
    if (!ccmd) return __mn_str_empty();

    mn_redisReply *reply = (mn_redisReply *)s_redis.p_command(rh->ctx, ccmd);
    free(ccmd);

    if (!reply) {
        snprintf(rh->errmsg, sizeof(rh->errmsg), "command returned NULL reply");
        return __mn_str_empty();
    }

    MnString result;
    switch (reply->type) {
        case MN_REDIS_REPLY_STRING:
        case MN_REDIS_REPLY_STATUS:
            result = __mn_str_from_parts(reply->str, (int64_t)reply->len);
            break;
        case MN_REDIS_REPLY_ERROR:
            snprintf(rh->errmsg, sizeof(rh->errmsg), "%.*s",
                     (int)reply->len, reply->str);
            result = __mn_str_from_parts(reply->str, (int64_t)reply->len);
            break;
        case MN_REDIS_REPLY_INTEGER: {
            char buf[32];
            int n = snprintf(buf, sizeof(buf), "%lld", (long long)reply->integer);
            result = __mn_str_from_parts(buf, (int64_t)n);
            break;
        }
        case MN_REDIS_REPLY_NIL:
            result = __mn_str_empty();
            break;
        default:
            result = __mn_str_from_cstr("(unsupported reply type)");
            break;
    }

    s_redis.p_freeReply(reply);
    return result;
}

MN_DB_EXPORT int64_t __mn_redis_command_status(int64_t ctx, MnString cmd) {
    MnRedisHandle *rh = (MnRedisHandle *)handle_get(&s_redis_ctxs, ctx);
    if (!rh || !s_redis.available) return -1;

    char *ccmd = mnstr_to_cstr(cmd);
    if (!ccmd) return -1;

    mn_redisReply *reply = (mn_redisReply *)s_redis.p_command(rh->ctx, ccmd);
    free(ccmd);

    if (!reply) {
        snprintf(rh->errmsg, sizeof(rh->errmsg), "command returned NULL reply");
        return -1;
    }

    int64_t status;
    if (reply->type == MN_REDIS_REPLY_ERROR) {
        snprintf(rh->errmsg, sizeof(rh->errmsg), "%.*s",
                 (int)reply->len, reply->str);
        status = -1;
    } else {
        status = 0;
    }

    s_redis.p_freeReply(reply);
    return status;
}

MN_DB_EXPORT void __mn_redis_close(int64_t ctx) {
    MnRedisHandle *rh = (MnRedisHandle *)handle_get(&s_redis_ctxs, ctx);
    if (!rh || !s_redis.available) return;
    s_redis.p_free(rh->ctx);
    free(rh);
    handle_free(&s_redis_ctxs, ctx);
}

MN_DB_EXPORT MnString __mn_redis_errmsg(int64_t ctx) {
    MnRedisHandle *rh = (MnRedisHandle *)handle_get(&s_redis_ctxs, ctx);
    if (!rh) return __mn_str_from_cstr("hiredis not available");
    if (rh->errmsg[0] == '\0') return __mn_str_empty();
    return __mn_str_from_cstr(rh->errmsg);
}

/* =======================================================================
 * 4. Extended Filesystem Operations
 *
 * v4.29.0: these were originally defined here in v1.2.0, but during
 * the v4.x orphan period the canonical implementations migrated to
 * ``runtime/native/mapanare_core.c`` (where they are tested and wired
 * into every build). When v4.29.0 re-linked ``mapanare_db.c``, the
 * duplicate definitions produced a linker error. The db.c copies have
 * been removed in favour of the core.c implementations; this file now
 * owns SQLite/Postgres/Redis only, and the "extended filesystem"
 * surface lives in core.c alone. Header stubs are retained below for
 * build-time checks that nothing here shadows the core symbols.
 * ======================================================================= */

/* All extended filesystem operations now live in mapanare_core.c:
 *   __mn_file_exists, __mn_file_remove, __mn_dir_create, __mn_dir_remove,
 *   __mn_file_rename, __mn_file_copy, __mn_tmpfile_path, __mn_realpath,
 *   __mn_file_size, __mn_file_mtime.
 */

