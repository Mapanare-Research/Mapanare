/**
 * mapanare_io.h — I/O runtime for Mapanare (Phase 6: C Runtime Expansion)
 *
 * Provides low-level OS primitives for networking, TLS, file I/O, and
 * event loop multiplexing. These are the foundation that v0.9.0 stdlib
 * modules (net/http.mn, encoding/json.mn, etc.) will call into.
 *
 * All functions use the __mn_ prefix to avoid collisions.
 * Cross-platform: POSIX (Linux/macOS) + Winsock/IOCP (Windows).
 */

#ifndef MAPANARE_IO_H
#define MAPANARE_IO_H

#include <stdint.h>
#include <stddef.h>

#ifdef _WIN32
  #define MN_IO_EXPORT __declspec(dllexport)
#else
  #define MN_IO_EXPORT __attribute__((visibility("default")))
#endif

/* -----------------------------------------------------------------------
 * 1. TCP Networking
 *
 * File-descriptor-based TCP API. On Windows, fd is a SOCKET cast to int64_t.
 * On POSIX, fd is the native file descriptor.
 * Returns -1 on error for all functions (check errno / WSAGetLastError).
 * ----------------------------------------------------------------------- */

/** Initialize the networking subsystem (Winsock on Windows, no-op on POSIX). */
MN_IO_EXPORT int64_t __mn_net_init(void);

/** Cleanup the networking subsystem (Winsock on Windows, no-op on POSIX). */
MN_IO_EXPORT void __mn_net_cleanup(void);

/** Connect to host:port via TCP. Returns socket fd or -1 on error.
 *  host is a null-terminated C string (hostname or IP).
 *  Performs DNS resolution internally. */
MN_IO_EXPORT int64_t __mn_tcp_connect(const char *host, int64_t port);

/** Bind and listen on host:port. Returns listening socket fd or -1.
 *  host can be "0.0.0.0" or "127.0.0.1" or NULL for INADDR_ANY. */
MN_IO_EXPORT int64_t __mn_tcp_listen(const char *host, int64_t port, int64_t backlog);

/** Accept an incoming connection on a listening socket.
 *  Returns new connection fd or -1 on error. */
MN_IO_EXPORT int64_t __mn_tcp_accept(int64_t listen_fd);

/** Send data over a connected socket.
 *  Returns number of bytes sent, or -1 on error. */
MN_IO_EXPORT int64_t __mn_tcp_send(int64_t fd, const void *buf, int64_t len);

/** Receive data from a connected socket.
 *  Returns number of bytes received, 0 on peer close, or -1 on error. */
MN_IO_EXPORT int64_t __mn_tcp_recv(int64_t fd, void *buf, int64_t len);

/** Close a socket. */
MN_IO_EXPORT void __mn_tcp_close(int64_t fd);

/** Set send/receive timeout on a socket (in milliseconds).
 *  Applies to both SO_RCVTIMEO and SO_SNDTIMEO. */
MN_IO_EXPORT int64_t __mn_tcp_set_timeout(int64_t fd, int64_t ms);

/* -----------------------------------------------------------------------
 * 2. TLS (via OpenSSL)
 *
 * Wraps a TCP socket with TLS encryption. Requires OpenSSL/LibreSSL
 * to be installed on the system. Functions return -1 on error.
 *
 * TLS context is opaque — represented as void* externally.
 * ----------------------------------------------------------------------- */

/** Initialize the OpenSSL library (one-time global init).
 *  Returns 0 on success, -1 on failure. Safe to call multiple times. */
MN_IO_EXPORT int64_t __mn_tls_init(void);

/** Wrap an existing TCP socket fd with TLS (client mode).
 *  hostname is used for SNI and certificate verification.
 *  Returns opaque TLS context pointer, or NULL on failure. */
MN_IO_EXPORT void *__mn_tls_connect(int64_t fd, const char *hostname);

/** Read decrypted data from a TLS connection.
 *  Returns bytes read, 0 on clean shutdown, or -1 on error. */
MN_IO_EXPORT int64_t __mn_tls_read(void *tls_ctx, void *buf, int64_t len);

/** Write data to a TLS connection (encrypts before sending).
 *  Returns bytes written, or -1 on error. */
MN_IO_EXPORT int64_t __mn_tls_write(void *tls_ctx, const void *buf, int64_t len);

/** Close a TLS connection and free the TLS context.
 *  Does NOT close the underlying TCP socket — call __mn_tcp_close separately. */
MN_IO_EXPORT void __mn_tls_close(void *tls_ctx);

/* -----------------------------------------------------------------------
 * 3. File I/O (extended, fd-based)
 *
 * Low-level file operations using file descriptors. Complements the
 * high-level __mn_file_read/__mn_file_write in mapanare_core.h.
 *
 * Mode flags for __mn_file_open:
 *   MN_FILE_READ    = 0  (read-only)
 *   MN_FILE_WRITE   = 1  (write-only, create if missing, truncate)
 *   MN_FILE_APPEND  = 2  (write-only, create if missing, append)
 *   MN_FILE_CREATE  = 3  (write-only, create, fail if exists)
 * ----------------------------------------------------------------------- */

#define MN_FILE_READ   0
#define MN_FILE_WRITE  1
#define MN_FILE_APPEND 2
#define MN_FILE_CREATE 3

/** File stat result. */
typedef struct {
    int64_t size;       /* file size in bytes */
    int64_t mtime;      /* last modification time (Unix epoch seconds) */
    int64_t is_dir;     /* 1 if directory, 0 otherwise */
} MnFileStat;

/** Directory entry. */
typedef struct {
    char    name[256];  /* entry name (not full path) */
    int64_t is_dir;     /* 1 if directory, 0 if file */
} MnDirEntry;

/** Open a file. Returns fd or -1 on error.
 *  path is a null-terminated C string.
 *  mode is one of MN_FILE_READ/WRITE/APPEND/CREATE. */
MN_IO_EXPORT int64_t __mn_file_open(const char *path, int64_t mode);

/** Read from an open file descriptor.
 *  Returns bytes read, 0 at EOF, or -1 on error. */
MN_IO_EXPORT int64_t __mn_file_read_fd(int64_t fd, void *buf, int64_t len);

/** Write to an open file descriptor.
 *  Returns bytes written, or -1 on error. */
MN_IO_EXPORT int64_t __mn_file_write_fd(int64_t fd, const void *buf, int64_t len);

/** Close an open file descriptor. */
MN_IO_EXPORT void __mn_file_close(int64_t fd);

/** Get file status (size, mtime, is_dir).
 *  Returns 0 on success, -1 on error. */
MN_IO_EXPORT int64_t __mn_file_stat(const char *path, MnFileStat *out);

/** List directory entries.
 *  Returns number of entries written to `out`, or -1 on error.
 *  `max_entries` is the capacity of the `out` array.
 *  Caller allocates the MnDirEntry array. */
MN_IO_EXPORT int64_t __mn_dir_list(const char *path, MnDirEntry *out, int64_t max_entries);

/* -----------------------------------------------------------------------
 * 4. Event Loop (I/O multiplexing)
 *
 * Cross-platform event loop using epoll (Linux), kqueue (macOS),
 * or select (Windows fallback, IOCP in future).
 *
 * Event flags:
 *   MN_EVENT_READ  = 1
 *   MN_EVENT_WRITE = 2
 * ----------------------------------------------------------------------- */

/** Opaque event loop handle (forward declaration for use below). */
typedef struct MnEventLoop MnEventLoop;

/** Event loop backend selection.
 *  Detected automatically at creation time, or overridden manually. */
typedef enum {
    MN_EVLOOP_SELECT = 0,  /* Fallback: works everywhere              */
    MN_EVLOOP_EPOLL  = 1,  /* Linux / Android                         */
    MN_EVLOOP_KQUEUE = 2,  /* macOS / iOS                             */
} mn_evloop_backend_t;

/** Query which event loop backend is in use. */
MN_IO_EXPORT mn_evloop_backend_t __mn_event_loop_backend(MnEventLoop *loop);

#define MN_EVENT_READ  1
#define MN_EVENT_WRITE 2

/** Callback for event loop fd readiness.
 *  @param fd     The file descriptor that is ready
 *  @param events Bitmask of MN_EVENT_READ / MN_EVENT_WRITE
 *  @param user_data  Opaque pointer passed at registration time */
typedef void (*MnEventCallback)(int64_t fd, int64_t events, void *user_data);

/** Create a new event loop. Returns NULL on failure. */
MN_IO_EXPORT MnEventLoop *__mn_event_loop_new(void);

/** Register a file descriptor with the event loop.
 *  events is a bitmask of MN_EVENT_READ / MN_EVENT_WRITE.
 *  Returns 0 on success, -1 on error. */
MN_IO_EXPORT int64_t __mn_event_loop_add_fd(MnEventLoop *loop, int64_t fd,
                                              int64_t events, MnEventCallback cb,
                                              void *user_data);

/** Remove a file descriptor from the event loop.
 *  Returns 0 on success, -1 if fd not found. */
MN_IO_EXPORT int64_t __mn_event_loop_remove_fd(MnEventLoop *loop, int64_t fd);

/** Run the event loop until no more fds are registered or stop is called.
 *  Blocks the calling thread. */
MN_IO_EXPORT void __mn_event_loop_run(MnEventLoop *loop);

/** Run a single iteration of the event loop.
 *  timeout_ms: -1 = block forever, 0 = non-blocking, >0 = wait up to N ms.
 *  Returns number of events dispatched, or -1 on error. */
MN_IO_EXPORT int64_t __mn_event_loop_run_once(MnEventLoop *loop, int64_t timeout_ms);

/** Signal the event loop to stop (can be called from any thread).
 *  The loop will exit after the current iteration completes. */
MN_IO_EXPORT void __mn_event_loop_stop(MnEventLoop *loop);

/** Destroy the event loop and free resources. */
MN_IO_EXPORT void __mn_event_loop_free(MnEventLoop *loop);

/* -----------------------------------------------------------------------
 * 5. MnString-based TCP/TLS wrappers
 *
 * These wrappers accept and return MnString (the Mapanare { i8*, i64 }
 * struct) so that .mn stdlib modules can call TCP/TLS functions directly
 * without manual pointer extraction. Used by net/http.mn, etc.
 * ----------------------------------------------------------------------- */

#include "mapanare_core.h"

/** Connect to host:port via TCP. host is an MnString.
 *  Returns socket fd or -1 on error. */
MN_IO_EXPORT int64_t __mn_tcp_connect_str(MnString host, int64_t port);

/** Send data over a connected socket. data is an MnString.
 *  Returns number of bytes sent, or -1 on error. */
MN_IO_EXPORT int64_t __mn_tcp_send_str(int64_t fd, MnString data);

/** Receive data from a connected socket into an MnString.
 *  max_len is the maximum bytes to read.
 *  Returns an MnString with the received data (empty on error/close). */
MN_IO_EXPORT MnString __mn_tcp_recv_str(int64_t fd, int64_t max_len);

/** Close a socket. Returns 0 always (void wrapper). */
MN_IO_EXPORT int64_t __mn_tcp_close_fd(int64_t fd);

/** Wrap a TCP socket with TLS. hostname is an MnString.
 *  Returns opaque TLS context as int64_t, or 0 on failure. */
MN_IO_EXPORT int64_t __mn_tls_connect_str(int64_t fd, MnString hostname);

/** Write data to a TLS connection. data is an MnString.
 *  tls_ctx is the opaque context from __mn_tls_connect_str.
 *  Returns bytes written, or -1 on error. */
MN_IO_EXPORT int64_t __mn_tls_write_str(int64_t tls_ctx, MnString data);

/** Read decrypted data from a TLS connection into an MnString.
 *  max_len is the maximum bytes to read.
 *  Returns an MnString with the received data (empty on error/close). */
MN_IO_EXPORT MnString __mn_tls_read_str(int64_t tls_ctx, int64_t max_len);

/** Close a TLS connection and the underlying TCP socket.
 *  tls_ctx is the opaque context from __mn_tls_connect_str.
 *  Returns 0 always (void wrapper). */
MN_IO_EXPORT int64_t __mn_tls_close_fd(int64_t tls_ctx, int64_t fd);

/** Bind and listen on host:port. host is an MnString.
 *  Returns listening socket fd or -1 on error. */
MN_IO_EXPORT int64_t __mn_tcp_listen_str(MnString host, int64_t port, int64_t backlog);

/* -----------------------------------------------------------------------
 * 6. Crypto primitives (needed by WebSocket handshake, Phase 5/6)
 *
 * SHA-1 uses the already-loaded OpenSSL libcrypto (via dlopen).
 * Base64 is a pure C implementation.
 * Random bytes use /dev/urandom (POSIX) or CryptGenRandom (Windows).
 * ----------------------------------------------------------------------- */

/** SHA-1 hash of input data. Returns 20-byte raw hash as MnString.
 *  Uses OpenSSL EVP API via the already-loaded libcrypto. */
MN_IO_EXPORT MnString __mn_sha1_str(MnString data);

/** SHA-256 hash of input data. Returns 32-byte raw hash as MnString. */
MN_IO_EXPORT MnString __mn_sha256_str(MnString data);

/** SHA-512 hash of input data. Returns 64-byte raw hash as MnString. */
MN_IO_EXPORT MnString __mn_sha512_str(MnString data);

/** HMAC-SHA256. Returns 32-byte raw HMAC as MnString. */
MN_IO_EXPORT MnString __mn_hmac_sha256_str(MnString key, MnString data);

/** Hex-encode a binary string. Returns hex MnString (2x input length). */
MN_IO_EXPORT MnString __mn_hex_encode_str(MnString data);

/** Hex-decode a hex string. Returns binary MnString (empty on invalid input). */
MN_IO_EXPORT MnString __mn_hex_decode_str(MnString data);

/** Base64-encode a binary string. Returns base64-encoded MnString. */
MN_IO_EXPORT MnString __mn_base64_encode_str(MnString data);

/** Base64-decode a base64 string. Returns decoded MnString (empty on error). */
MN_IO_EXPORT MnString __mn_base64_decode_str(MnString data);

/** Generate n cryptographically random bytes as an MnString. */
MN_IO_EXPORT MnString __mn_random_bytes_str(int64_t n);

/* -----------------------------------------------------------------------
 * 7. Regular expressions (PCRE2 via dlopen)
 *
 * Handle-based API: compile a pattern, then execute matches, extract
 * groups, replace, or split. PCRE2 is loaded dynamically (like OpenSSL
 * for crypto). Returns 0/empty on failure if PCRE2 is not available.
 * ----------------------------------------------------------------------- */

/** Compile a regex pattern. Returns opaque handle (>0) or 0 on error. */
MN_IO_EXPORT int64_t __mn_regex_compile_str(MnString pattern);

/** Execute regex against subject starting at byte offset.
 *  Returns 1 if match found, 0 if no match, -1 on error.
 *  Match data is stored in the handle for group extraction. */
MN_IO_EXPORT int64_t __mn_regex_exec_str(int64_t handle, MnString subject, int64_t start_offset);

/** Get matched text for capture group (0 = full match).
 *  subject must be the same MnString passed to __mn_regex_exec_str.
 *  Returns empty string if group did not participate or index out of range. */
MN_IO_EXPORT MnString __mn_regex_group_str(int64_t handle, MnString subject, int64_t group_idx);

/** Get start byte offset of capture group in last match. Returns -1 if unset. */
MN_IO_EXPORT int64_t __mn_regex_group_start(int64_t handle, int64_t group_idx);

/** Get end byte offset (exclusive) of capture group. Returns -1 if unset. */
MN_IO_EXPORT int64_t __mn_regex_group_end(int64_t handle, int64_t group_idx);

/** Get number of capture groups (excluding group 0 = full match). */
MN_IO_EXPORT int64_t __mn_regex_group_count(int64_t handle);

/** Replace matches in subject. If replace_all != 0, replaces all occurrences.
 *  Returns new string with replacements applied. */
MN_IO_EXPORT MnString __mn_regex_replace_str(int64_t handle, MnString subject,
                                              MnString replacement, int64_t replace_all);

/** Free a compiled regex handle and its match data. Returns 0. */
MN_IO_EXPORT int64_t __mn_regex_free(int64_t handle);

/** Get error message from last failed compile. Returns empty if no error. */
MN_IO_EXPORT MnString __mn_regex_error_str(int64_t handle);

#endif /* MAPANARE_IO_H */
