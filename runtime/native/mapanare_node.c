/**
 * mapanare_node.c — distributed-agents transport runtime (v5.43.0 Da.8)
 *
 * Per-connection state machine for agent-to-agent network messaging.
 * Wraps existing TCP/TLS exports in mapanare_io.{c,h}; adds 4-byte
 * big-endian length-prefix framing on top.
 *
 * The C layer is deliberately thin. Security-critical operations
 * (HMAC compute/verify, sequence tracking, replay rejection,
 * payload (de)serialization) all live at the .mn layer where the
 * v5.39.0 crypto stdlib provides timing-safe primitives. C just
 * does I/O.
 */

#include "mapanare_node.h"
#include "mapanare_io.h"
#include "mapanare_core.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Per-connection state. */
struct mn_node_conn {
    int64_t  fd;        /* underlying TCP socket fd */
    void    *tls;       /* nullable; non-NULL if TLS-wrapped */
};

/* ---------------------------------------------------------------------
 * Internal helpers
 * --------------------------------------------------------------------- */

/* Read exactly n bytes from a connection. Returns 0 on success, -1 on
 * error or peer close. Loops over short reads. */
static int read_exact(mn_node_conn_t *c, void *buf, size_t n) {
    char *p = (char *)buf;
    size_t rem = n;
    while (rem > 0) {
        int64_t r;
        if (c->tls) {
            r = __mn_tls_read(c->tls, p, (int64_t)rem);
        } else {
            r = __mn_tcp_recv(c->fd, p, (int64_t)rem);
        }
        if (r <= 0) return -1;  /* error or peer close */
        p += r;
        rem -= (size_t)r;
    }
    return 0;
}

/* Write exactly n bytes. Returns 0 on success, -1 on error. */
static int write_exact(mn_node_conn_t *c, const void *buf, size_t n) {
    const char *p = (const char *)buf;
    size_t rem = n;
    while (rem > 0) {
        int64_t w;
        if (c->tls) {
            w = __mn_tls_write(c->tls, p, (int64_t)rem);
        } else {
            w = __mn_tcp_send(c->fd, p, (int64_t)rem);
        }
        if (w <= 0) return -1;
        p += w;
        rem -= (size_t)w;
    }
    return 0;
}

/* Encode a u32 in big-endian byte order. */
static void put_u32_be(uint8_t out[4], uint32_t v) {
    out[0] = (uint8_t)((v >> 24) & 0xFF);
    out[1] = (uint8_t)((v >> 16) & 0xFF);
    out[2] = (uint8_t)((v >>  8) & 0xFF);
    out[3] = (uint8_t)( v        & 0xFF);
}

static uint32_t get_u32_be(const uint8_t in[4]) {
    return ((uint32_t)in[0] << 24) |
           ((uint32_t)in[1] << 16) |
           ((uint32_t)in[2] <<  8) |
           ((uint32_t)in[3]);
}

/* Convert MnString (not null-terminated) to a heap-allocated C string.
 * Returns NULL on allocation failure. Caller frees. Used for host /
 * cert path arguments that need to be passed to existing const char *
 * APIs in mapanare_io. */
static char *mnstring_to_cstr(MnString s) {
    int64_t len = (int64_t)(s.len & MN_STR_LEN_MASK);
    if (len < 0) return NULL;
    char *cs = (char *)malloc((size_t)len + 1);
    if (!cs) return NULL;
    if (len > 0 && s.data) memcpy(cs, s.data, (size_t)len);
    cs[len] = '\0';
    return cs;
}

/* ---------------------------------------------------------------------
 * Public surface
 * --------------------------------------------------------------------- */

MN_NODE_EXPORT int64_t __mn_node_listen_str(MnString host, int64_t port,
                                              int64_t backlog) {
    char *host_cstr = mnstring_to_cstr(host);
    if (!host_cstr) return -1;
    int64_t fd = __mn_tcp_listen(host_cstr, port, backlog > 0 ? backlog : 32);
    free(host_cstr);
    return fd;
}

MN_NODE_EXPORT int64_t __mn_node_accept(int64_t listen_fd,
                                          int64_t is_tls,
                                          int64_t server_ctx) {
    int64_t client_fd = __mn_tcp_accept(listen_fd);
    if (client_fd < 0) return 0;

    void *tls = NULL;
    if (is_tls) {
        if (!server_ctx) {
            __mn_tcp_close(client_fd);
            return 0;
        }
        tls = __mn_tls_accept(client_fd, (void *)(uintptr_t)server_ctx);
        if (!tls) {
            __mn_tcp_close(client_fd);
            return 0;
        }
    }

    mn_node_conn_t *c = (mn_node_conn_t *)calloc(1, sizeof(mn_node_conn_t));
    if (!c) {
        if (tls) __mn_tls_close(tls);
        __mn_tcp_close(client_fd);
        return 0;
    }
    c->fd = client_fd;
    c->tls = tls;
    return (int64_t)(uintptr_t)c;
}

MN_NODE_EXPORT int64_t __mn_node_connect_str(MnString host, int64_t port,
                                               int64_t is_tls,
                                               MnString sni_hostname) {
    char *host_cstr = mnstring_to_cstr(host);
    if (!host_cstr) return 0;
    int64_t fd = __mn_tcp_connect(host_cstr, port);
    if (fd < 0) {
        free(host_cstr);
        return 0;
    }

    void *tls = NULL;
    if (is_tls) {
        char *sni_cstr = mnstring_to_cstr(sni_hostname);
        const char *sni = sni_cstr ? sni_cstr : host_cstr;
        tls = __mn_tls_connect(fd, sni);
        if (sni_cstr) free(sni_cstr);
        if (!tls) {
            __mn_tcp_close(fd);
            free(host_cstr);
            return 0;
        }
    }
    free(host_cstr);

    mn_node_conn_t *c = (mn_node_conn_t *)calloc(1, sizeof(mn_node_conn_t));
    if (!c) {
        if (tls) __mn_tls_close(tls);
        __mn_tcp_close(fd);
        return 0;
    }
    c->fd = fd;
    c->tls = tls;
    return (int64_t)(uintptr_t)c;
}

MN_NODE_EXPORT int64_t __mn_node_write_str(int64_t conn_handle,
                                             MnString frame_body) {
    if (!conn_handle) return -1;
    mn_node_conn_t *c = (mn_node_conn_t *)(uintptr_t)conn_handle;

    int64_t body_len = (int64_t)(frame_body.len & MN_STR_LEN_MASK);
    if (body_len < 0) return -1;
    if (body_len > MAPANARE_NODE_MAX_FRAME_BYTES) return -2;

    uint8_t lenbuf[4];
    put_u32_be(lenbuf, (uint32_t)body_len);
    if (write_exact(c, lenbuf, 4) != 0) return -1;
    if (body_len > 0) {
        if (write_exact(c, frame_body.data, (size_t)body_len) != 0) return -1;
    }
    return 0;
}

MN_NODE_EXPORT MnString __mn_node_read_frame_str(int64_t conn_handle) {
    MnString empty = { NULL, 0, 0 };
    if (!conn_handle) return empty;
    mn_node_conn_t *c = (mn_node_conn_t *)(uintptr_t)conn_handle;

    uint8_t lenbuf[4];
    if (read_exact(c, lenbuf, 4) != 0) return empty;
    uint32_t body_len = get_u32_be(lenbuf);

    /* DoS guard: reject oversized frames before allocating. */
    if (body_len == 0 || (int64_t)body_len > MAPANARE_NODE_MAX_FRAME_BYTES) {
        return empty;
    }

    char *buf = (char *)malloc((size_t)body_len);
    if (!buf) return empty;
    if (read_exact(c, buf, (size_t)body_len) != 0) {
        free(buf);
        return empty;
    }

    /* __mn_str_from_parts copies the buffer into its own heap allocation
     * tagged is_heap=1, so Mapanare's drop glue will free that copy.
     * We free our temporary read buffer here. */
    MnString out = __mn_str_from_parts(buf, (int64_t)body_len);
    free(buf);
    return out;
}

MN_NODE_EXPORT void __mn_node_close(int64_t conn_handle) {
    if (!conn_handle) return;
    mn_node_conn_t *c = (mn_node_conn_t *)(uintptr_t)conn_handle;
    if (c->tls) {
        __mn_tls_close(c->tls);
        c->tls = NULL;
    }
    if (c->fd >= 0) {
        __mn_tcp_close(c->fd);
        c->fd = -1;
    }
    free(c);
}

MN_NODE_EXPORT int64_t __mn_node_get_fd(int64_t conn_handle) {
    if (!conn_handle) return -1;
    mn_node_conn_t *c = (mn_node_conn_t *)(uintptr_t)conn_handle;
    return c->fd;
}

MN_NODE_EXPORT int64_t __mn_tls_server_ctx_new_str(MnString cert_path,
                                                     MnString key_path) {
    char *cert_cstr = mnstring_to_cstr(cert_path);
    char *key_cstr = mnstring_to_cstr(key_path);
    if (!cert_cstr || !key_cstr) {
        if (cert_cstr) free(cert_cstr);
        if (key_cstr) free(key_cstr);
        return 0;
    }
    void *ctx = __mn_tls_server_ctx_new(cert_cstr, key_cstr);
    free(cert_cstr);
    free(key_cstr);
    return (int64_t)(uintptr_t)ctx;
}

MN_NODE_EXPORT void __mn_tls_server_ctx_free_handle(int64_t server_ctx) {
    if (!server_ctx) return;
    __mn_tls_server_ctx_free((void *)(uintptr_t)server_ctx);
}
