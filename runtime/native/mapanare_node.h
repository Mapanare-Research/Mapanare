/**
 * mapanare_node.h — distributed-agents transport runtime (v5.43.0 Da.8)
 *
 * Per-connection state machine for the agent-to-agent network protocol.
 * Sits on top of the existing TCP + TLS exports in mapanare_io.{c,h}.
 *
 * The C layer here is intentionally narrow: it handles raw byte
 * transport plus the 4-byte big-endian length-prefix framing on the
 * wire. Everything security-critical (HMAC compute + verify, sequence
 * tracking, replay rejection, payload deserialization) lives in the
 * .mn layer where v5.39.0 crypto stdlib (`hmac_sha256_raw`,
 * `constant_time_eq`) is available.
 *
 * Wire format (v1, locked at v5.43.0 PRE_PHASE_AUDIT):
 *   [u32 length BE][frame body]
 *   length = sizeof(frame body), capped at 100 MB.
 *
 * The C layer reads/writes the body only; .mn unpacks the structured
 * fields (version, msg_type, sequence, hmac, payload).
 */

#ifndef MAPANARE_NODE_H
#define MAPANARE_NODE_H

#include <stdint.h>
#include "mapanare_core.h"  /* for MnString */

#ifdef _WIN32
  #define MN_NODE_EXPORT __declspec(dllexport)
#else
  #define MN_NODE_EXPORT __attribute__((visibility("default")))
#endif

/* Maximum frame body size in bytes (100 MB). Per v5.43.0 wire-format
 * invariant locked in PRE_PHASE_AUDIT. Exposed so the .mn side can
 * mirror the constant for diagnostic messages. */
#define MAPANARE_NODE_MAX_FRAME_BYTES (100LL * 1024LL * 1024LL)

/* Opaque per-connection state. Cast to int64_t for Mapanare ABI. */
typedef struct mn_node_conn mn_node_conn_t;

/* Listen on host:port. Wraps __mn_tcp_listen. Returns listening fd
 * (>= 0) or -1 on error. The fd is a plain socket; TLS is layered on
 * at accept time via the is_tls + server_ctx params of __mn_node_accept. */
MN_NODE_EXPORT int64_t __mn_node_listen_str(MnString host, int64_t port,
                                              int64_t backlog);

/* Accept an incoming connection on a listening socket.
 * If is_tls != 0, server_ctx must be a non-null TLS server context
 * (from __mn_tls_server_ctx_new in mapanare_io.h). For plain TCP,
 * pass is_tls=0, server_ctx=0.
 * Returns mn_node_conn_t * cast to int64_t, or 0 on error. */
MN_NODE_EXPORT int64_t __mn_node_accept(int64_t listen_fd,
                                          int64_t is_tls,
                                          int64_t server_ctx);

/* Connect to host:port as a client. is_tls != 0 wraps the connection
 * with TLS using the system trust store; sni_hostname is used for SNI
 * and certificate verification when is_tls != 0 (ignored otherwise).
 * Returns mn_node_conn_t * cast to int64_t, or 0 on error. */
MN_NODE_EXPORT int64_t __mn_node_connect_str(MnString host, int64_t port,
                                               int64_t is_tls,
                                               MnString sni_hostname);

/* Write one length-prefixed frame. The frame_body MnString contains
 * everything AFTER the 4-byte length prefix (the .mn layer's encoded
 * version + msg_type + sequence + hmac + payload). The C layer
 * prepends the u32 BE length and writes the whole record.
 *
 * Returns 0 on success, -1 on error/close, -2 on oversize
 * (body length > MAPANARE_NODE_MAX_FRAME_BYTES). */
MN_NODE_EXPORT int64_t __mn_node_write_str(int64_t conn,
                                             MnString frame_body);

/* Read one length-prefixed frame. Reads 4-byte u32 BE length,
 * validates 0 < length <= MAPANARE_NODE_MAX_FRAME_BYTES, allocates,
 * reads length bytes.
 *
 * On success: returns the body as a heap MnString (caller-owned).
 * On error/close/oversize: returns an empty MnString with a NULL
 *   data pointer. v5.43.0 wire-format invariant: every legitimate
 *   frame body is at least 26 bytes (1 version + 1 msg_type + 8
 *   sequence + 16 hmac + 0 payload), so a returned empty MnString
 *   unambiguously signals error. */
MN_NODE_EXPORT MnString __mn_node_read_frame_str(int64_t conn);

/* Close the connection: TLS shutdown if applicable, fd close,
 * heap-buffer free, mn_node_conn_t free. Idempotent. */
MN_NODE_EXPORT void __mn_node_close(int64_t conn);

/* Diagnostic: returns the underlying TCP fd for a connection, or -1.
 * Useful for wiring connections into __mn_event_loop_add_fd. */
MN_NODE_EXPORT int64_t __mn_node_get_fd(int64_t conn);

/* MnString-form wrapper for __mn_tls_server_ctx_new. Mapanare extern
 * declarations cannot pass `const char *` directly; this materialises
 * cert + key path strings and delegates. Returns the opaque server
 * context cast to int64_t, or 0 on failure (missing OpenSSL, bad
 * cert/key, mismatch, etc.). */
MN_NODE_EXPORT int64_t __mn_tls_server_ctx_new_str(MnString cert_path,
                                                     MnString key_path);

/* MnString-form alias for __mn_tls_server_ctx_free (same address
 * spec — int64_t-cast pointer). */
MN_NODE_EXPORT void __mn_tls_server_ctx_free_handle(int64_t server_ctx);

#endif /* MAPANARE_NODE_H */
