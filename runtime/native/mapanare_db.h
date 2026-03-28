/**
 * mapanare_db.h --- Database & extended filesystem runtime for Mapanare v1.2.0
 *
 * Provides database driver bindings and extended filesystem operations that
 * native-compiled Mapanare programs link against:
 *   - SQLite3:    embedded SQL database (via dlopen of libsqlite3)
 *   - PostgreSQL: client library (via dlopen of libpq)
 *   - Redis:      in-memory store (via dlopen of libhiredis)
 *   - Filesystem: extended POSIX file/directory operations
 *
 * All database libraries are loaded dynamically at runtime via dlopen/LoadLibrary.
 * If a library is not installed, the corresponding functions return graceful errors
 * (0 handles, empty strings) without crashing.
 *
 * All functions use the __mn_ prefix to avoid collisions.
 * Strings use the Mapanare { i8*, i64 } MnString struct passed by value.
 */

#ifndef MAPANARE_DB_H
#define MAPANARE_DB_H

#include <stdint.h>
#include <stddef.h>
#include "mapanare_core.h"

#ifdef _WIN32
  #define MN_DB_EXPORT __declspec(dllexport)
#else
  #define MN_DB_EXPORT __attribute__((visibility("default")))
#endif

/* =======================================================================
 * 1. SQLite3 Bindings
 *
 * Handle-based API: open a database, execute SQL, prepare statements,
 * bind parameters, step through results, and read column values.
 * SQLite3 is loaded dynamically via dlopen (libsqlite3.so / .dylib / .dll).
 *
 * Handles are opaque int64_t values (array index + 1). A handle of 0
 * indicates an error (database not opened, statement not prepared, etc.).
 *
 * Step return codes: 100 = SQLITE_ROW, 101 = SQLITE_DONE.
 * Column type codes: 1 = INTEGER, 2 = FLOAT, 3 = TEXT, 4 = BLOB, 5 = NULL.
 * ======================================================================= */

/** Open or create a SQLite3 database. Returns handle (>0) or 0 on error. */
MN_DB_EXPORT int64_t __mn_sqlite3_open(MnString path);

/** Close a SQLite3 database handle. */
MN_DB_EXPORT void __mn_sqlite3_close(int64_t handle);

/** Execute a non-query SQL statement. Returns 0 on success, or SQLite error code. */
MN_DB_EXPORT int64_t __mn_sqlite3_exec(int64_t handle, MnString sql);

/** Prepare a SQL statement. Returns statement handle (>0) or 0 on error. */
MN_DB_EXPORT int64_t __mn_sqlite3_prepare(int64_t handle, MnString sql);

/** Bind an integer value to parameter at index (1-based). Returns 0 on success. */
MN_DB_EXPORT int64_t __mn_sqlite3_bind_int(int64_t stmt, int64_t idx, int64_t val);

/** Bind a float value to parameter at index (1-based). Returns 0 on success. */
MN_DB_EXPORT int64_t __mn_sqlite3_bind_float(int64_t stmt, int64_t idx, double val);

/** Bind a string value to parameter at index (1-based). Returns 0 on success. */
MN_DB_EXPORT int64_t __mn_sqlite3_bind_str(int64_t stmt, int64_t idx, MnString val);

/** Bind NULL to parameter at index (1-based). Returns 0 on success. */
MN_DB_EXPORT int64_t __mn_sqlite3_bind_null(int64_t stmt, int64_t idx);

/** Step a prepared statement. Returns 100 (ROW), 101 (DONE), or error code. */
MN_DB_EXPORT int64_t __mn_sqlite3_step(int64_t stmt);

/** Read an integer value from column at index (0-based). */
MN_DB_EXPORT int64_t __mn_sqlite3_column_int(int64_t stmt, int64_t idx);

/** Read a float value from column at index (0-based). */
MN_DB_EXPORT double __mn_sqlite3_column_float(int64_t stmt, int64_t idx);

/** Read a string value from column at index (0-based). */
MN_DB_EXPORT MnString __mn_sqlite3_column_str(int64_t stmt, int64_t idx);

/** Get the type of column at index (0-based). 1=INT, 2=FLOAT, 3=TEXT, 4=BLOB, 5=NULL. */
MN_DB_EXPORT int64_t __mn_sqlite3_column_type(int64_t stmt, int64_t idx);

/** Get the number of columns in the result set. */
MN_DB_EXPORT int64_t __mn_sqlite3_column_count(int64_t stmt);

/** Get the name of column at index (0-based). */
MN_DB_EXPORT MnString __mn_sqlite3_column_name(int64_t stmt, int64_t idx);

/** Finalize (free) a prepared statement. Returns 0 on success. */
MN_DB_EXPORT int64_t __mn_sqlite3_finalize(int64_t stmt);

/** Get the last error message for a database handle. */
MN_DB_EXPORT MnString __mn_sqlite3_errmsg(int64_t handle);

/* =======================================================================
 * 2. PostgreSQL Bindings (libpq)
 *
 * Connection-based API: connect to a PostgreSQL server, execute queries,
 * read results. libpq is loaded dynamically via dlopen.
 *
 * Handles are opaque int64_t values (array index + 1).
 * Result status codes mirror PGresult status:
 *   0 = PGRES_EMPTY_QUERY, 1 = PGRES_COMMAND_OK, 2 = PGRES_TUPLES_OK,
 *   7 = PGRES_FATAL_ERROR.
 * ======================================================================= */

/** Connect to PostgreSQL using a connection string.
 *  Returns connection handle (>0) or 0 on error. */
MN_DB_EXPORT int64_t __mn_pg_connect(MnString conninfo);

/** Close a PostgreSQL connection. */
MN_DB_EXPORT void __mn_pg_close(int64_t conn);

/** Execute a SQL query. Returns result handle (>0) or 0 on error. */
MN_DB_EXPORT int64_t __mn_pg_exec(int64_t conn, MnString sql);

/** Execute a parameterized SQL query. params is an array of MnString values.
 *  Returns result handle (>0) or 0 on error. */
MN_DB_EXPORT int64_t __mn_pg_exec_params(int64_t conn, MnString sql,
                                          int64_t nparams, MnString *params);

/** Get the number of rows in a result set. */
MN_DB_EXPORT int64_t __mn_pg_ntuples(int64_t result);

/** Get the number of columns in a result set. */
MN_DB_EXPORT int64_t __mn_pg_nfields(int64_t result);

/** Get the value at (row, col) as a string. */
MN_DB_EXPORT MnString __mn_pg_getvalue(int64_t result, int64_t row, int64_t col);

/** Get the column name at index. */
MN_DB_EXPORT MnString __mn_pg_fname(int64_t result, int64_t col);

/** Get the status code of a result. */
MN_DB_EXPORT int64_t __mn_pg_status(int64_t result);

/** Get the last error message for a connection. */
MN_DB_EXPORT MnString __mn_pg_errmsg(int64_t conn);

/** Clear (free) a result set. */
MN_DB_EXPORT void __mn_pg_clear(int64_t result);

/* =======================================================================
 * 3. Redis Bindings (hiredis)
 *
 * Simple command-based API: connect to a Redis server, execute commands,
 * read replies. hiredis is loaded dynamically via dlopen.
 *
 * Handles are opaque int64_t values (array index + 1).
 * ======================================================================= */

/** Connect to a Redis server. Returns context handle (>0) or 0 on error. */
MN_DB_EXPORT int64_t __mn_redis_connect(MnString host, int64_t port);

/** Execute a Redis command and return the reply as a string.
 *  For non-string replies, returns a string representation. */
MN_DB_EXPORT MnString __mn_redis_command(int64_t ctx, MnString cmd);

/** Execute a Redis command and return the status code.
 *  Returns 0 on success, -1 on error. */
MN_DB_EXPORT int64_t __mn_redis_command_status(int64_t ctx, MnString cmd);

/** Close a Redis connection. */
MN_DB_EXPORT void __mn_redis_close(int64_t ctx);

/** Get the last error message for a Redis connection. */
MN_DB_EXPORT MnString __mn_redis_errmsg(int64_t ctx);

/* =======================================================================
 * 4. Extended Filesystem Operations
 *
 * Higher-level file and directory operations using POSIX APIs with
 * Windows fallbacks. All paths are MnString values.
 * Returns 0 on success, -1 on error (unless otherwise noted).
 * ======================================================================= */

/** Check if a file or directory exists. Returns 1 if exists, 0 otherwise. */
MN_DB_EXPORT int64_t __mn_file_exists(MnString path);

/** Remove (delete) a file. Returns 0 on success, -1 on error. */
MN_DB_EXPORT int64_t __mn_file_remove(MnString path);

/** Create a directory. If recursive != 0, creates parent directories.
 *  Returns 0 on success, -1 on error. */
MN_DB_EXPORT int64_t __mn_dir_create(MnString path, int64_t recursive);

/** Remove an empty directory. Returns 0 on success, -1 on error. */
MN_DB_EXPORT int64_t __mn_dir_remove(MnString path);

/** Rename (move) a file or directory. Returns 0 on success, -1 on error. */
MN_DB_EXPORT int64_t __mn_file_rename(MnString old_path, MnString new_path);

/** Copy a file from src to dst. Returns 0 on success, -1 on error. */
MN_DB_EXPORT int64_t __mn_file_copy(MnString src, MnString dst);

/** Get a unique temporary file path. Returns the path as MnString. */
MN_DB_EXPORT MnString __mn_tmpfile_path(void);

/** Resolve a path to its canonical absolute form. Returns empty on error. */
MN_DB_EXPORT MnString __mn_realpath(MnString path);

/** Get the size of a file in bytes. Returns -1 on error. */
MN_DB_EXPORT int64_t __mn_file_size(MnString path);

/** Get the last modification time of a file (Unix epoch seconds). Returns -1 on error. */
MN_DB_EXPORT int64_t __mn_file_mtime(MnString path);

#endif /* MAPANARE_DB_H */
