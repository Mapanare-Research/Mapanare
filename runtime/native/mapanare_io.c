/**
 * mapanare_io.c — I/O runtime implementation (Phase 6: C Runtime Expansion)
 *
 * Implements TCP networking, TLS (OpenSSL), extended file I/O, and
 * cross-platform event loop multiplexing.
 */

#include "mapanare_io.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

/* =======================================================================
 * Platform-specific includes and helpers
 * ======================================================================= */

#ifdef _WIN32
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  #include <io.h>
  #include <fcntl.h>
  #include <sys/stat.h>
  #pragma comment(lib, "ws2_32.lib")

  typedef SOCKET mn_socket_t;
  #define MN_INVALID_SOCKET INVALID_SOCKET
  #define MN_SOCKET_ERROR   SOCKET_ERROR
  #define mn_closesocket    closesocket
  #define mn_errno          WSAGetLastError()

#else /* POSIX */
  #include <unistd.h>
  #include <sys/socket.h>
  #include <sys/types.h>
  #include <sys/stat.h>
  #include <netinet/in.h>
  #include <netinet/tcp.h>
  #include <arpa/inet.h>
  #include <netdb.h>
  #include <fcntl.h>
  #include <dirent.h>
  #include <dlfcn.h>

  typedef int mn_socket_t;
  #define MN_INVALID_SOCKET (-1)
  #define MN_SOCKET_ERROR   (-1)
  #define mn_closesocket    close
  #define mn_errno          errno

  #if defined(__linux__)
    #include <sys/epoll.h>
    #define MN_USE_EPOLL 1
  #elif defined(__APPLE__) || defined(__FreeBSD__) || defined(__OpenBSD__)
    #include <sys/event.h>
    #define MN_USE_KQUEUE 1
  #else
    /* Fallback to select */
    #include <sys/select.h>
    #define MN_USE_SELECT 1
  #endif
#endif

/* =======================================================================
 * 1. TCP Networking
 * ======================================================================= */

static int s_net_initialized = 0;

MN_IO_EXPORT int64_t __mn_net_init(void) {
    if (s_net_initialized) return 0;
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        return -1;
    }
#endif
    s_net_initialized = 1;
    return 0;
}

MN_IO_EXPORT void __mn_net_cleanup(void) {
#ifdef _WIN32
    if (s_net_initialized) {
        WSACleanup();
        s_net_initialized = 0;
    }
#else
    s_net_initialized = 0;
#endif
}

MN_IO_EXPORT int64_t __mn_tcp_connect(const char *host, int64_t port) {
    if (!s_net_initialized) {
        if (__mn_net_init() < 0) return -1;
    }

    struct addrinfo hints, *res = NULL, *rp;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;      /* IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM;  /* TCP */

    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%d", (int)port);

    int gai_err = getaddrinfo(host, port_str, &hints, &res);
    if (gai_err != 0) {
        return -1;
    }

    mn_socket_t sock = MN_INVALID_SOCKET;
    for (rp = res; rp != NULL; rp = rp->ai_next) {
        sock = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sock == MN_INVALID_SOCKET) continue;

        if (connect(sock, rp->ai_addr, (int)rp->ai_addrlen) == 0) {
            break;  /* Success */
        }
        mn_closesocket(sock);
        sock = MN_INVALID_SOCKET;
    }

    freeaddrinfo(res);
    if (sock == MN_INVALID_SOCKET) return -1;
    return (int64_t)sock;
}

MN_IO_EXPORT int64_t __mn_tcp_listen(const char *host, int64_t port, int64_t backlog) {
    if (!s_net_initialized) {
        if (__mn_net_init() < 0) return -1;
    }

    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;        /* IPv4 */
    hints.ai_socktype = SOCK_STREAM;  /* TCP */
    hints.ai_flags = AI_PASSIVE;      /* For bind */

    char port_str[16];
    snprintf(port_str, sizeof(port_str), "%d", (int)port);

    if (getaddrinfo(host, port_str, &hints, &res) != 0) {
        return -1;
    }

    mn_socket_t sock = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sock == MN_INVALID_SOCKET) {
        freeaddrinfo(res);
        return -1;
    }

    /* Allow port reuse */
    int opt = 1;
#ifdef _WIN32
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, (const char *)&opt, sizeof(opt));
#else
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
#endif

    if (bind(sock, res->ai_addr, (int)res->ai_addrlen) != 0) {
        freeaddrinfo(res);
        mn_closesocket(sock);
        return -1;
    }
    freeaddrinfo(res);

    if (listen(sock, (int)backlog) != 0) {
        mn_closesocket(sock);
        return -1;
    }

    return (int64_t)sock;
}

MN_IO_EXPORT int64_t __mn_tcp_accept(int64_t listen_fd) {
    mn_socket_t lfd = (mn_socket_t)listen_fd;
    struct sockaddr_storage addr;
    socklen_t addr_len = sizeof(addr);

    mn_socket_t client = accept(lfd, (struct sockaddr *)&addr, &addr_len);
    if (client == MN_INVALID_SOCKET) return -1;
    return (int64_t)client;
}

MN_IO_EXPORT int64_t __mn_tcp_send(int64_t fd, const void *buf, int64_t len) {
    mn_socket_t sock = (mn_socket_t)fd;
#ifdef _WIN32
    int result = send(sock, (const char *)buf, (int)len, 0);
#else
    ssize_t result = send(sock, buf, (size_t)len, 0);
#endif
    if (result < 0) return -1;
    return (int64_t)result;
}

MN_IO_EXPORT int64_t __mn_tcp_recv(int64_t fd, void *buf, int64_t len) {
    mn_socket_t sock = (mn_socket_t)fd;
#ifdef _WIN32
    int result = recv(sock, (char *)buf, (int)len, 0);
#else
    ssize_t result = recv(sock, buf, (size_t)len, 0);
#endif
    if (result < 0) return -1;
    return (int64_t)result;
}

MN_IO_EXPORT void __mn_tcp_close(int64_t fd) {
    mn_socket_t sock = (mn_socket_t)fd;
    mn_closesocket(sock);
}

MN_IO_EXPORT int64_t __mn_tcp_set_timeout(int64_t fd, int64_t ms) {
    mn_socket_t sock = (mn_socket_t)fd;
#ifdef _WIN32
    DWORD timeout = (DWORD)ms;
    if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout,
                   sizeof(timeout)) != 0)
        return -1;
    if (setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char *)&timeout,
                   sizeof(timeout)) != 0)
        return -1;
#else
    struct timeval tv;
    tv.tv_sec = ms / 1000;
    tv.tv_usec = (ms % 1000) * 1000;
    if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) != 0)
        return -1;
    if (setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv)) != 0)
        return -1;
#endif
    return 0;
}

/* =======================================================================
 * 2. TLS (via OpenSSL)
 *
 * We dynamically load OpenSSL so the library can be built without
 * OpenSSL headers. If OpenSSL is not available, TLS functions return
 * errors gracefully.
 * ======================================================================= */

/*
 * OpenSSL type/function declarations (minimal subset we need).
 * We declare these ourselves to avoid requiring OpenSSL headers at
 * compile time. The actual symbols are resolved via dlopen/LoadLibrary.
 */

/* Opaque OpenSSL types */
typedef struct ssl_ctx_st MN_SSL_CTX;
typedef struct ssl_st MN_SSL;
typedef struct ssl_method_st MN_SSL_METHOD;

/* Function pointer types for OpenSSL API */
typedef MN_SSL_METHOD *(*fn_TLS_client_method)(void);
typedef MN_SSL_CTX *(*fn_SSL_CTX_new)(const MN_SSL_METHOD *);
typedef void (*fn_SSL_CTX_free)(MN_SSL_CTX *);
typedef MN_SSL *(*fn_SSL_new)(MN_SSL_CTX *);
typedef void (*fn_SSL_free)(MN_SSL *);
typedef int (*fn_SSL_set_fd)(MN_SSL *, int);
typedef int (*fn_SSL_connect)(MN_SSL *);
typedef int (*fn_SSL_read)(MN_SSL *, void *, int);
typedef int (*fn_SSL_write)(MN_SSL *, const void *, int);
typedef int (*fn_SSL_shutdown)(MN_SSL *);
typedef long (*fn_SSL_ctrl)(MN_SSL *, int, long, void *);
typedef int (*fn_SSL_CTX_set_default_verify_paths)(MN_SSL_CTX *);

/* OpenSSL constants */
#define MN_SSL_CTRL_SET_TLSEXT_HOSTNAME 55

/* Dynamic OpenSSL state */
static struct {
    int loaded;
    int available;
#ifdef _WIN32
    HMODULE libssl;
    HMODULE libcrypto;
#else
    void *libssl;
    void *libcrypto;
#endif
    fn_TLS_client_method    TLS_client_method;
    fn_SSL_CTX_new          SSL_CTX_new;
    fn_SSL_CTX_free         SSL_CTX_free;
    fn_SSL_new              SSL_new;
    fn_SSL_free             SSL_free;
    fn_SSL_set_fd           SSL_set_fd;
    fn_SSL_connect          SSL_connect;
    fn_SSL_read             SSL_read;
    fn_SSL_write            SSL_write;
    fn_SSL_shutdown         SSL_shutdown;
    fn_SSL_ctrl             SSL_ctrl;
    fn_SSL_CTX_set_default_verify_paths SSL_CTX_set_default_verify_paths;
} s_ssl = {0};

/* Internal: load OpenSSL dynamically */
static int ssl_load_library(void) {
    if (s_ssl.loaded) return s_ssl.available ? 0 : -1;
    s_ssl.loaded = 1;
    s_ssl.available = 0;

#ifdef _WIN32
    s_ssl.libssl = LoadLibraryA("libssl-3-x64.dll");
    if (!s_ssl.libssl) s_ssl.libssl = LoadLibraryA("libssl-1_1-x64.dll");
    if (!s_ssl.libssl) s_ssl.libssl = LoadLibraryA("ssleay32.dll");
    s_ssl.libcrypto = LoadLibraryA("libcrypto-3-x64.dll");
    if (!s_ssl.libcrypto) s_ssl.libcrypto = LoadLibraryA("libcrypto-1_1-x64.dll");
    if (!s_ssl.libcrypto) s_ssl.libcrypto = LoadLibraryA("libeay32.dll");
    if (!s_ssl.libssl || !s_ssl.libcrypto) return -1;

    #define SSL_SYM(name) s_ssl.name = (fn_##name)GetProcAddress(s_ssl.libssl, #name)
    #define CRYPTO_SYM(name) s_ssl.name = (fn_##name)GetProcAddress(s_ssl.libcrypto, #name)
#else
    /* Try common library names */
    s_ssl.libssl = dlopen("libssl.so.3", RTLD_NOW);
    if (!s_ssl.libssl) s_ssl.libssl = dlopen("libssl.so.1.1", RTLD_NOW);
    if (!s_ssl.libssl) s_ssl.libssl = dlopen("libssl.so", RTLD_NOW);
    #ifdef __APPLE__
    if (!s_ssl.libssl) s_ssl.libssl = dlopen("libssl.dylib", RTLD_NOW);
    #endif

    s_ssl.libcrypto = dlopen("libcrypto.so.3", RTLD_NOW);
    if (!s_ssl.libcrypto) s_ssl.libcrypto = dlopen("libcrypto.so.1.1", RTLD_NOW);
    if (!s_ssl.libcrypto) s_ssl.libcrypto = dlopen("libcrypto.so", RTLD_NOW);
    #ifdef __APPLE__
    if (!s_ssl.libcrypto) s_ssl.libcrypto = dlopen("libcrypto.dylib", RTLD_NOW);
    #endif

    if (!s_ssl.libssl || !s_ssl.libcrypto) return -1;

    #define SSL_SYM(name) s_ssl.name = (fn_##name)dlsym(s_ssl.libssl, #name)
    #define CRYPTO_SYM(name) s_ssl.name = (fn_##name)dlsym(s_ssl.libcrypto, #name)
#endif

    SSL_SYM(TLS_client_method);
    SSL_SYM(SSL_CTX_new);
    SSL_SYM(SSL_CTX_free);
    SSL_SYM(SSL_new);
    SSL_SYM(SSL_free);
    SSL_SYM(SSL_set_fd);
    SSL_SYM(SSL_connect);
    SSL_SYM(SSL_read);
    SSL_SYM(SSL_write);
    SSL_SYM(SSL_shutdown);
    SSL_SYM(SSL_ctrl);
    SSL_SYM(SSL_CTX_set_default_verify_paths);

    #undef SSL_SYM
    #undef CRYPTO_SYM

    /* Verify all required symbols loaded */
    if (!s_ssl.TLS_client_method || !s_ssl.SSL_CTX_new || !s_ssl.SSL_CTX_free ||
        !s_ssl.SSL_new || !s_ssl.SSL_free || !s_ssl.SSL_set_fd ||
        !s_ssl.SSL_connect || !s_ssl.SSL_read || !s_ssl.SSL_write ||
        !s_ssl.SSL_shutdown || !s_ssl.SSL_ctrl) {
        return -1;
    }

    s_ssl.available = 1;
    return 0;
}

/* TLS context wrapper — holds SSL* and SSL_CTX* together */
typedef struct {
    MN_SSL_CTX *ctx;
    MN_SSL     *ssl;
} MnTlsCtx;

MN_IO_EXPORT int64_t __mn_tls_init(void) {
    return ssl_load_library();
}

MN_IO_EXPORT void *__mn_tls_connect(int64_t fd, const char *hostname) {
    if (!s_ssl.available) {
        if (ssl_load_library() < 0) return NULL;
    }

    MN_SSL_CTX *ctx = s_ssl.SSL_CTX_new(s_ssl.TLS_client_method());
    if (!ctx) return NULL;

    /* Load default CA certificates */
    if (s_ssl.SSL_CTX_set_default_verify_paths) {
        s_ssl.SSL_CTX_set_default_verify_paths(ctx);
    }

    MN_SSL *ssl = s_ssl.SSL_new(ctx);
    if (!ssl) {
        s_ssl.SSL_CTX_free(ctx);
        return NULL;
    }

    s_ssl.SSL_set_fd(ssl, (int)fd);

    /* Set SNI hostname */
    if (hostname) {
        s_ssl.SSL_ctrl(ssl, MN_SSL_CTRL_SET_TLSEXT_HOSTNAME, 0, (void *)hostname);
    }

    if (s_ssl.SSL_connect(ssl) != 1) {
        s_ssl.SSL_free(ssl);
        s_ssl.SSL_CTX_free(ctx);
        return NULL;
    }

    MnTlsCtx *tctx = (MnTlsCtx *)calloc(1, sizeof(MnTlsCtx));
    if (!tctx) {
        s_ssl.SSL_shutdown(ssl);
        s_ssl.SSL_free(ssl);
        s_ssl.SSL_CTX_free(ctx);
        return NULL;
    }
    tctx->ctx = ctx;
    tctx->ssl = ssl;
    return tctx;
}

MN_IO_EXPORT int64_t __mn_tls_read(void *tls_ctx, void *buf, int64_t len) {
    if (!tls_ctx || !s_ssl.available) return -1;
    MnTlsCtx *tctx = (MnTlsCtx *)tls_ctx;
    int result = s_ssl.SSL_read(tctx->ssl, buf, (int)len);
    if (result <= 0) return (result == 0) ? 0 : -1;
    return (int64_t)result;
}

MN_IO_EXPORT int64_t __mn_tls_write(void *tls_ctx, const void *buf, int64_t len) {
    if (!tls_ctx || !s_ssl.available) return -1;
    MnTlsCtx *tctx = (MnTlsCtx *)tls_ctx;
    int result = s_ssl.SSL_write(tctx->ssl, buf, (int)len);
    if (result <= 0) return -1;
    return (int64_t)result;
}

MN_IO_EXPORT void __mn_tls_close(void *tls_ctx) {
    if (!tls_ctx || !s_ssl.available) return;
    MnTlsCtx *tctx = (MnTlsCtx *)tls_ctx;
    s_ssl.SSL_shutdown(tctx->ssl);
    s_ssl.SSL_free(tctx->ssl);
    s_ssl.SSL_CTX_free(tctx->ctx);
    free(tctx);
}

/* =======================================================================
 * 3. File I/O (extended)
 * ======================================================================= */

MN_IO_EXPORT int64_t __mn_file_open(const char *path, int64_t mode) {
#ifdef _WIN32
    int flags = _O_BINARY;
    int perm = _S_IREAD | _S_IWRITE;
    switch (mode) {
        case MN_FILE_READ:   flags |= _O_RDONLY; break;
        case MN_FILE_WRITE:  flags |= _O_WRONLY | _O_CREAT | _O_TRUNC; break;
        case MN_FILE_APPEND: flags |= _O_WRONLY | _O_CREAT | _O_APPEND; break;
        case MN_FILE_CREATE: flags |= _O_WRONLY | _O_CREAT | _O_EXCL; break;
        default: return -1;
    }
    int fd = _open(path, flags, perm);
    return (fd < 0) ? -1 : (int64_t)fd;
#else
    int flags = 0;
    mode_t perm = 0644;
    switch (mode) {
        case MN_FILE_READ:   flags = O_RDONLY; break;
        case MN_FILE_WRITE:  flags = O_WRONLY | O_CREAT | O_TRUNC; break;
        case MN_FILE_APPEND: flags = O_WRONLY | O_CREAT | O_APPEND; break;
        case MN_FILE_CREATE: flags = O_WRONLY | O_CREAT | O_EXCL; break;
        default: return -1;
    }
    int fd = open(path, flags, perm);
    return (fd < 0) ? -1 : (int64_t)fd;
#endif
}

MN_IO_EXPORT int64_t __mn_file_read_fd(int64_t fd, void *buf, int64_t len) {
#ifdef _WIN32
    int result = _read((int)fd, buf, (unsigned int)len);
#else
    ssize_t result = read((int)fd, buf, (size_t)len);
#endif
    if (result < 0) return -1;
    return (int64_t)result;
}

MN_IO_EXPORT int64_t __mn_file_write_fd(int64_t fd, const void *buf, int64_t len) {
#ifdef _WIN32
    int result = _write((int)fd, buf, (unsigned int)len);
#else
    ssize_t result = write((int)fd, buf, (size_t)len);
#endif
    if (result < 0) return -1;
    return (int64_t)result;
}

MN_IO_EXPORT void __mn_file_close(int64_t fd) {
#ifdef _WIN32
    _close((int)fd);
#else
    close((int)fd);
#endif
}

MN_IO_EXPORT int64_t __mn_file_stat(const char *path, MnFileStat *out) {
    if (!out) return -1;
#ifdef _WIN32
    struct _stat64 st;
    if (_stat64(path, &st) != 0) return -1;
    out->size = (int64_t)st.st_size;
    out->mtime = (int64_t)st.st_mtime;
    out->is_dir = (st.st_mode & _S_IFDIR) ? 1 : 0;
#else
    struct stat st;
    if (stat(path, &st) != 0) return -1;
    out->size = (int64_t)st.st_size;
    out->mtime = (int64_t)st.st_mtime;
    out->is_dir = S_ISDIR(st.st_mode) ? 1 : 0;
#endif
    return 0;
}

MN_IO_EXPORT int64_t __mn_dir_list(const char *path, MnDirEntry *out, int64_t max_entries) {
    if (!out || max_entries <= 0) return -1;
    int64_t count = 0;

#ifdef _WIN32
    char pattern[512];
    snprintf(pattern, sizeof(pattern), "%s\\*", path);

    WIN32_FIND_DATAA fd;
    HANDLE hFind = FindFirstFileA(pattern, &fd);
    if (hFind == INVALID_HANDLE_VALUE) return -1;

    do {
        /* Skip . and .. */
        if (strcmp(fd.cFileName, ".") == 0 || strcmp(fd.cFileName, "..") == 0)
            continue;
        if (count >= max_entries) break;

        strncpy(out[count].name, fd.cFileName, sizeof(out[count].name) - 1);
        out[count].name[sizeof(out[count].name) - 1] = '\0';
        out[count].is_dir = (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) ? 1 : 0;
        count++;
    } while (FindNextFileA(hFind, &fd));

    FindClose(hFind);
#else
    DIR *dir = opendir(path);
    if (!dir) return -1;

    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
        /* Skip . and .. */
        if (strcmp(ent->d_name, ".") == 0 || strcmp(ent->d_name, "..") == 0)
            continue;
        if (count >= max_entries) break;

        strncpy(out[count].name, ent->d_name, sizeof(out[count].name) - 1);
        out[count].name[sizeof(out[count].name) - 1] = '\0';
        out[count].is_dir = (ent->d_type == DT_DIR) ? 1 : 0;
        count++;
    }

    closedir(dir);
#endif

    return count;
}

/* =======================================================================
 * 4. Event Loop (I/O multiplexing)
 * ======================================================================= */

/* Maximum fds tracked per event loop */
#define MN_MAX_EVENTS 256

/* Per-fd registration entry */
typedef struct {
    int64_t         fd;
    int64_t         events;    /* MN_EVENT_READ | MN_EVENT_WRITE */
    MnEventCallback cb;
    void           *user_data;
    int             active;    /* 1 = registered, 0 = slot free */
} MnEventEntry;

struct MnEventLoop {
    MnEventEntry entries[MN_MAX_EVENTS];
    int          entry_count;
    int          running;

#if defined(MN_USE_EPOLL)
    int epoll_fd;
#elif defined(MN_USE_KQUEUE)
    int kq_fd;
#endif
    /* select fallback uses no extra state */
};

MN_IO_EXPORT MnEventLoop *__mn_event_loop_new(void) {
    MnEventLoop *loop = (MnEventLoop *)calloc(1, sizeof(MnEventLoop));
    if (!loop) return NULL;

    loop->entry_count = 0;
    loop->running = 0;

#if defined(MN_USE_EPOLL)
    loop->epoll_fd = epoll_create1(0);
    if (loop->epoll_fd < 0) {
        free(loop);
        return NULL;
    }
#elif defined(MN_USE_KQUEUE)
    loop->kq_fd = kqueue();
    if (loop->kq_fd < 0) {
        free(loop);
        return NULL;
    }
#endif

    return loop;
}

MN_IO_EXPORT mn_evloop_backend_t __mn_event_loop_backend(MnEventLoop *loop) {
    (void)loop;  /* backend is compile-time, not per-instance */
#if defined(MN_USE_EPOLL)
    return MN_EVLOOP_EPOLL;
#elif defined(MN_USE_KQUEUE)
    return MN_EVLOOP_KQUEUE;
#else
    return MN_EVLOOP_SELECT;
#endif
}

/* Find entry by fd */
static MnEventEntry *loop_find(MnEventLoop *loop, int64_t fd) {
    for (int i = 0; i < MN_MAX_EVENTS; i++) {
        if (loop->entries[i].active && loop->entries[i].fd == fd) {
            return &loop->entries[i];
        }
    }
    return NULL;
}

/* Find free slot */
static MnEventEntry *loop_alloc(MnEventLoop *loop) {
    for (int i = 0; i < MN_MAX_EVENTS; i++) {
        if (!loop->entries[i].active) {
            return &loop->entries[i];
        }
    }
    return NULL;
}

MN_IO_EXPORT int64_t __mn_event_loop_add_fd(MnEventLoop *loop, int64_t fd,
                                              int64_t events, MnEventCallback cb,
                                              void *user_data) {
    if (!loop || !cb) return -1;
    if (loop_find(loop, fd)) return -1;  /* Already registered */

    MnEventEntry *entry = loop_alloc(loop);
    if (!entry) return -1;  /* Full */

    entry->fd = fd;
    entry->events = events;
    entry->cb = cb;
    entry->user_data = user_data;
    entry->active = 1;
    loop->entry_count++;

#if defined(MN_USE_EPOLL)
    struct epoll_event ev;
    memset(&ev, 0, sizeof(ev));
    ev.data.fd = (int)fd;
    if (events & MN_EVENT_READ)  ev.events |= EPOLLIN;
    if (events & MN_EVENT_WRITE) ev.events |= EPOLLOUT;
    if (epoll_ctl(loop->epoll_fd, EPOLL_CTL_ADD, (int)fd, &ev) < 0) {
        entry->active = 0;
        loop->entry_count--;
        return -1;
    }
#elif defined(MN_USE_KQUEUE)
    struct kevent kev[2];
    int nev = 0;
    if (events & MN_EVENT_READ) {
        EV_SET(&kev[nev], (uintptr_t)fd, EVFILT_READ, EV_ADD | EV_ENABLE, 0, 0, NULL);
        nev++;
    }
    if (events & MN_EVENT_WRITE) {
        EV_SET(&kev[nev], (uintptr_t)fd, EVFILT_WRITE, EV_ADD | EV_ENABLE, 0, 0, NULL);
        nev++;
    }
    if (nev > 0 && kevent(loop->kq_fd, kev, nev, NULL, 0, NULL) < 0) {
        entry->active = 0;
        loop->entry_count--;
        return -1;
    }
#endif
    /* select: no pre-registration needed */

    return 0;
}

MN_IO_EXPORT int64_t __mn_event_loop_remove_fd(MnEventLoop *loop, int64_t fd) {
    if (!loop) return -1;
    MnEventEntry *entry = loop_find(loop, fd);
    if (!entry) return -1;

#if defined(MN_USE_EPOLL)
    epoll_ctl(loop->epoll_fd, EPOLL_CTL_DEL, (int)fd, NULL);
#elif defined(MN_USE_KQUEUE)
    struct kevent kev[2];
    int nev = 0;
    if (entry->events & MN_EVENT_READ) {
        EV_SET(&kev[nev], (uintptr_t)fd, EVFILT_READ, EV_DELETE, 0, 0, NULL);
        nev++;
    }
    if (entry->events & MN_EVENT_WRITE) {
        EV_SET(&kev[nev], (uintptr_t)fd, EVFILT_WRITE, EV_DELETE, 0, 0, NULL);
        nev++;
    }
    if (nev > 0) kevent(loop->kq_fd, kev, nev, NULL, 0, NULL);
#endif

    entry->active = 0;
    loop->entry_count--;
    return 0;
}

MN_IO_EXPORT int64_t __mn_event_loop_run_once(MnEventLoop *loop, int64_t timeout_ms) {
    if (!loop) return -1;
    int dispatched = 0;

#if defined(MN_USE_EPOLL)
    struct epoll_event events[64];
    int n = epoll_wait(loop->epoll_fd, events, 64, (int)timeout_ms);
    if (n < 0) return -1;
    for (int i = 0; i < n; i++) {
        int64_t fd = (int64_t)events[i].data.fd;
        MnEventEntry *entry = loop_find(loop, fd);
        if (!entry) continue;

        int64_t ev = 0;
        if (events[i].events & (EPOLLIN | EPOLLHUP | EPOLLERR)) ev |= MN_EVENT_READ;
        if (events[i].events & EPOLLOUT) ev |= MN_EVENT_WRITE;
        if (ev && entry->cb) {
            entry->cb(fd, ev, entry->user_data);
            dispatched++;
        }
    }

#elif defined(MN_USE_KQUEUE)
    struct kevent events[64];
    struct timespec ts, *tsp = NULL;
    if (timeout_ms >= 0) {
        ts.tv_sec = timeout_ms / 1000;
        ts.tv_nsec = (timeout_ms % 1000) * 1000000;
        tsp = &ts;
    }
    int n = kevent(loop->kq_fd, NULL, 0, events, 64, tsp);
    if (n < 0) return -1;
    for (int i = 0; i < n; i++) {
        int64_t fd = (int64_t)events[i].ident;
        MnEventEntry *entry = loop_find(loop, fd);
        if (!entry) continue;

        int64_t ev = 0;
        if (events[i].filter == EVFILT_READ)  ev |= MN_EVENT_READ;
        if (events[i].filter == EVFILT_WRITE) ev |= MN_EVENT_WRITE;
        if (ev && entry->cb) {
            entry->cb(fd, ev, entry->user_data);
            dispatched++;
        }
    }

#else /* select fallback */
    fd_set rfds, wfds;
    FD_ZERO(&rfds);
    FD_ZERO(&wfds);
    int maxfd = -1;

    for (int i = 0; i < MN_MAX_EVENTS; i++) {
        if (!loop->entries[i].active) continue;
        int fd = (int)loop->entries[i].fd;
        if (loop->entries[i].events & MN_EVENT_READ)  FD_SET(fd, &rfds);
        if (loop->entries[i].events & MN_EVENT_WRITE) FD_SET(fd, &wfds);
        if (fd > maxfd) maxfd = fd;
    }

    if (maxfd < 0) return 0;  /* No fds registered */

    struct timeval tv, *tvp = NULL;
    if (timeout_ms >= 0) {
        tv.tv_sec = (long)(timeout_ms / 1000);
        tv.tv_usec = (long)((timeout_ms % 1000) * 1000);
        tvp = &tv;
    }

    int n = select(maxfd + 1, &rfds, &wfds, NULL, tvp);
    if (n < 0) return -1;

    for (int i = 0; i < MN_MAX_EVENTS && dispatched < n; i++) {
        if (!loop->entries[i].active) continue;
        int fd = (int)loop->entries[i].fd;
        int64_t ev = 0;
        if ((loop->entries[i].events & MN_EVENT_READ) && FD_ISSET(fd, &rfds))
            ev |= MN_EVENT_READ;
        if ((loop->entries[i].events & MN_EVENT_WRITE) && FD_ISSET(fd, &wfds))
            ev |= MN_EVENT_WRITE;
        if (ev && loop->entries[i].cb) {
            loop->entries[i].cb(loop->entries[i].fd, ev, loop->entries[i].user_data);
            dispatched++;
        }
    }
#endif

    return (int64_t)dispatched;
}

MN_IO_EXPORT void __mn_event_loop_run(MnEventLoop *loop) {
    if (!loop) return;
    loop->running = 1;
    while (loop->running && loop->entry_count > 0) {
        int64_t n = __mn_event_loop_run_once(loop, 100);  /* 100ms poll */
        if (n < 0) break;
    }
}

MN_IO_EXPORT void __mn_event_loop_stop(MnEventLoop *loop) {
    if (loop) loop->running = 0;
}

MN_IO_EXPORT void __mn_event_loop_free(MnEventLoop *loop) {
    if (!loop) return;
#if defined(MN_USE_EPOLL)
    if (loop->epoll_fd >= 0) close(loop->epoll_fd);
#elif defined(MN_USE_KQUEUE)
    if (loop->kq_fd >= 0) close(loop->kq_fd);
#endif
    free(loop);
}

/* =======================================================================
 * 5. MnString-based TCP/TLS wrappers
 *
 * Bridge between Mapanare's { i8*, i64 } strings and the raw C
 * TCP/TLS API. Uses mn_untag() from mapanare_core.h for pointer safety.
 * ======================================================================= */

#include "mapanare_core.h"

/* Utility: extract a null-terminated C string from MnString.
 * Caller must free the result. */
static char *mnstr_to_cstr(MnString s) {
    const char *data = (const char *)((uintptr_t)s.data & ~(uintptr_t)1);
    char *cstr = (char *)malloc((size_t)s.len + 1);
    if (!cstr) return NULL;
    memcpy(cstr, data, (size_t)s.len);
    cstr[s.len] = '\0';
    return cstr;
}

MN_IO_EXPORT int64_t __mn_tcp_connect_str(MnString host, int64_t port) {
    char *chost = mnstr_to_cstr(host);
    if (!chost) return -1;
    int64_t fd = __mn_tcp_connect(chost, port);
    free(chost);
    return fd;
}

MN_IO_EXPORT int64_t __mn_tcp_send_str(int64_t fd, MnString data) {
    const char *buf = (const char *)((uintptr_t)data.data & ~(uintptr_t)1);
    return __mn_tcp_send(fd, buf, data.len);
}

MN_IO_EXPORT MnString __mn_tcp_recv_str(int64_t fd, int64_t max_len) {
    if (max_len <= 0) return __mn_str_empty();
    char *buf = (char *)malloc((size_t)max_len);
    if (!buf) return __mn_str_empty();

    int64_t n = __mn_tcp_recv(fd, buf, max_len);
    if (n <= 0) {
        free(buf);
        return __mn_str_empty();
    }

    MnString result = __mn_str_from_parts(buf, n);
    free(buf);
    return result;
}

MN_IO_EXPORT int64_t __mn_tcp_close_fd(int64_t fd) {
    __mn_tcp_close(fd);
    return 0;
}

MN_IO_EXPORT int64_t __mn_tls_connect_str(int64_t fd, MnString hostname) {
    char *chost = mnstr_to_cstr(hostname);
    if (!chost) return 0;
    void *ctx = __mn_tls_connect(fd, chost);
    free(chost);
    return (int64_t)(uintptr_t)ctx;
}

MN_IO_EXPORT int64_t __mn_tls_write_str(int64_t tls_ctx, MnString data) {
    void *ctx = (void *)(uintptr_t)tls_ctx;
    const char *buf = (const char *)((uintptr_t)data.data & ~(uintptr_t)1);
    return __mn_tls_write(ctx, buf, data.len);
}

MN_IO_EXPORT MnString __mn_tls_read_str(int64_t tls_ctx, int64_t max_len) {
    void *ctx = (void *)(uintptr_t)tls_ctx;
    if (max_len <= 0 || !ctx) return __mn_str_empty();
    char *buf = (char *)malloc((size_t)max_len);
    if (!buf) return __mn_str_empty();

    int64_t n = __mn_tls_read(ctx, buf, max_len);
    if (n <= 0) {
        free(buf);
        return __mn_str_empty();
    }

    MnString result = __mn_str_from_parts(buf, n);
    free(buf);
    return result;
}

MN_IO_EXPORT int64_t __mn_tls_close_fd(int64_t tls_ctx, int64_t fd) {
    void *ctx = (void *)(uintptr_t)tls_ctx;
    if (ctx) __mn_tls_close(ctx);
    __mn_tcp_close(fd);
    return 0;
}

MN_IO_EXPORT int64_t __mn_tcp_listen_str(MnString host, int64_t port, int64_t backlog) {
    char *chost = mnstr_to_cstr(host);
    if (!chost) return -1;
    int64_t fd = __mn_tcp_listen(chost, port, backlog);
    free(chost);
    return fd;
}

/* =======================================================================
 * 6. Crypto primitives (SHA-1, SHA-256, Base64, random bytes)
 *
 * SHA-1/SHA-256 use the already-loaded OpenSSL libcrypto (EVP API).
 * Base64 is pure C. Random uses /dev/urandom or CryptGenRandom.
 * ======================================================================= */

/* --- SHA-1 via OpenSSL EVP (dynamically loaded) --- */

/* EVP function pointer types */
typedef void* (*fn_EVP_MD_CTX_new)(void);
typedef void  (*fn_EVP_MD_CTX_free)(void *ctx);
typedef void* (*fn_EVP_sha1)(void);
typedef void* (*fn_EVP_sha256)(void);
typedef void* (*fn_EVP_sha512)(void);
typedef int   (*fn_EVP_DigestInit_ex)(void *ctx, const void *type, void *impl);
typedef int   (*fn_EVP_DigestUpdate)(void *ctx, const void *d, size_t cnt);
typedef int   (*fn_EVP_DigestFinal_ex)(void *ctx, unsigned char *md, unsigned int *s);

/* HMAC function pointers */
typedef void* (*fn_HMAC)(const void *evp_md, const void *key, int key_len,
                         const unsigned char *d, size_t n,
                         unsigned char *md, unsigned int *md_len);

static struct {
    int loaded;
    int available;
    fn_EVP_MD_CTX_new     EVP_MD_CTX_new;
    fn_EVP_MD_CTX_free    EVP_MD_CTX_free;
    fn_EVP_sha1           EVP_sha1;
    fn_EVP_sha256         EVP_sha256;
    fn_EVP_sha512         EVP_sha512;
    fn_EVP_DigestInit_ex  EVP_DigestInit_ex;
    fn_EVP_DigestUpdate   EVP_DigestUpdate;
    fn_EVP_DigestFinal_ex EVP_DigestFinal_ex;
    fn_HMAC               HMAC;
} s_evp = {0};

static int evp_load(void) {
    if (s_evp.loaded) return s_evp.available ? 0 : -1;
    s_evp.loaded = 1;
    s_evp.available = 0;

    /* Ensure libcrypto is loaded (reuse TLS loader) */
    if (!s_ssl.loaded) ssl_load_library();
    if (!s_ssl.libcrypto) return -1;

#ifdef _WIN32
    #define EVP_SYM(name) s_evp.name = (fn_##name)GetProcAddress(s_ssl.libcrypto, #name)
#else
    #define EVP_SYM(name) s_evp.name = (fn_##name)dlsym(s_ssl.libcrypto, #name)
#endif

    EVP_SYM(EVP_MD_CTX_new);
    EVP_SYM(EVP_MD_CTX_free);
    EVP_SYM(EVP_sha1);
    EVP_SYM(EVP_sha256);
    EVP_SYM(EVP_sha512);
    EVP_SYM(EVP_DigestInit_ex);
    EVP_SYM(EVP_DigestUpdate);
    EVP_SYM(EVP_DigestFinal_ex);
    EVP_SYM(HMAC);

    #undef EVP_SYM

    if (!s_evp.EVP_MD_CTX_new || !s_evp.EVP_MD_CTX_free ||
        !s_evp.EVP_sha1 || !s_evp.EVP_sha256 || !s_evp.EVP_sha512 ||
        !s_evp.EVP_DigestInit_ex || !s_evp.EVP_DigestUpdate ||
        !s_evp.EVP_DigestFinal_ex) {
        return -1;
    }

    s_evp.available = 1;
    return 0;
}

static MnString evp_hash(MnString data, void *(*md_fn)(void), int digest_len) {
    (void)digest_len;  /* used by non-EVP fallback path */
    if (evp_load() < 0) return __mn_str_empty();

    void *ctx = s_evp.EVP_MD_CTX_new();
    if (!ctx) return __mn_str_empty();

    unsigned char md[64]; /* big enough for SHA-512 */
    unsigned int md_len = 0;

    const char *buf = (const char *)((uintptr_t)data.data & ~(uintptr_t)1);

    if (s_evp.EVP_DigestInit_ex(ctx, md_fn(), NULL) != 1 ||
        s_evp.EVP_DigestUpdate(ctx, buf, (size_t)data.len) != 1 ||
        s_evp.EVP_DigestFinal_ex(ctx, md, &md_len) != 1) {
        s_evp.EVP_MD_CTX_free(ctx);
        return __mn_str_empty();
    }

    s_evp.EVP_MD_CTX_free(ctx);
    return __mn_str_from_parts((const char *)md, (int64_t)md_len);
}

MN_IO_EXPORT MnString __mn_sha1_str(MnString data) {
    return evp_hash(data, s_evp.EVP_sha1, 20);
}

MN_IO_EXPORT MnString __mn_sha256_str(MnString data) {
    return evp_hash(data, s_evp.EVP_sha256, 32);
}

MN_IO_EXPORT MnString __mn_sha512_str(MnString data) {
    return evp_hash(data, s_evp.EVP_sha512, 64);
}

/* --- HMAC-SHA256 via OpenSSL HMAC() --- */

MN_IO_EXPORT MnString __mn_hmac_sha256_str(MnString key, MnString data) {
    if (evp_load() < 0 || !s_evp.HMAC) return __mn_str_empty();

    const char *key_buf = (const char *)((uintptr_t)key.data & ~(uintptr_t)1);
    const char *data_buf = (const char *)((uintptr_t)data.data & ~(uintptr_t)1);

    unsigned char md[32];
    unsigned int md_len = 0;

    void *result = s_evp.HMAC(s_evp.EVP_sha256(), key_buf, (int)key.len,
                              (const unsigned char *)data_buf, (size_t)data.len,
                              md, &md_len);
    if (!result || md_len != 32) return __mn_str_empty();

    return __mn_str_from_parts((const char *)md, 32);
}

/* --- Hex encode/decode (pure C) --- */

MN_IO_EXPORT MnString __mn_hex_encode_str(MnString data) {
    const unsigned char *src = (const unsigned char *)((uintptr_t)data.data & ~(uintptr_t)1);
    int64_t slen = data.len;
    int64_t olen = slen * 2;
    char *out = (char *)malloc((size_t)olen + 1);
    if (!out) return __mn_str_empty();

    static const char hex[] = "0123456789abcdef";
    for (int64_t i = 0; i < slen; i++) {
        out[i * 2]     = hex[(src[i] >> 4) & 0x0F];
        out[i * 2 + 1] = hex[src[i]        & 0x0F];
    }
    out[olen] = '\0';

    MnString result = __mn_str_from_parts(out, olen);
    free(out);
    return result;
}

MN_IO_EXPORT MnString __mn_hex_decode_str(MnString data) {
    const char *src = (const char *)((uintptr_t)data.data & ~(uintptr_t)1);
    int64_t slen = data.len;
    if (slen % 2 != 0) return __mn_str_empty();

    int64_t olen = slen / 2;
    char *out = (char *)malloc((size_t)olen + 1);
    if (!out) return __mn_str_empty();

    for (int64_t i = 0; i < olen; i++) {
        int hi, lo;
        char ch = src[i * 2];
        char cl = src[i * 2 + 1];
        if (ch >= '0' && ch <= '9') hi = ch - '0';
        else if (ch >= 'a' && ch <= 'f') hi = ch - 'a' + 10;
        else if (ch >= 'A' && ch <= 'F') hi = ch - 'A' + 10;
        else { free(out); return __mn_str_empty(); }
        if (cl >= '0' && cl <= '9') lo = cl - '0';
        else if (cl >= 'a' && cl <= 'f') lo = cl - 'a' + 10;
        else if (cl >= 'A' && cl <= 'F') lo = cl - 'A' + 10;
        else { free(out); return __mn_str_empty(); }
        out[i] = (char)((hi << 4) | lo);
    }
    out[olen] = '\0';

    MnString result = __mn_str_from_parts(out, olen);
    free(out);
    return result;
}

/* --- Base64 (pure C) --- */

static const char b64_table[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

MN_IO_EXPORT MnString __mn_base64_encode_str(MnString data) {
    const unsigned char *src = (const unsigned char *)((uintptr_t)data.data & ~(uintptr_t)1);
    int64_t slen = data.len;
    int64_t olen = 4 * ((slen + 2) / 3);
    char *out = (char *)malloc((size_t)olen + 1);
    if (!out) return __mn_str_empty();

    int64_t i = 0, j = 0;
    while (i < slen) {
        uint32_t a = (i < slen) ? src[i++] : 0;
        uint32_t b = (i < slen) ? src[i++] : 0;
        uint32_t c = (i < slen) ? src[i++] : 0;
        uint32_t triple = (a << 16) | (b << 8) | c;

        out[j++] = b64_table[(triple >> 18) & 0x3F];
        out[j++] = b64_table[(triple >> 12) & 0x3F];
        out[j++] = b64_table[(triple >> 6)  & 0x3F];
        out[j++] = b64_table[triple         & 0x3F];
    }

    /* Padding */
    int64_t mod = slen % 3;
    if (mod == 1) { out[j - 1] = '='; out[j - 2] = '='; }
    else if (mod == 2) { out[j - 1] = '='; }
    out[j] = '\0';

    MnString result = __mn_str_from_parts(out, j);
    free(out);
    return result;
}

static int b64_decode_char(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}

MN_IO_EXPORT MnString __mn_base64_decode_str(MnString data) {
    const char *src = (const char *)((uintptr_t)data.data & ~(uintptr_t)1);
    int64_t slen = data.len;
    if (slen == 0 || slen % 4 != 0) return __mn_str_empty();

    int64_t olen = (slen / 4) * 3;
    if (slen >= 1 && src[slen - 1] == '=') olen--;
    if (slen >= 2 && src[slen - 2] == '=') olen--;

    char *out = (char *)malloc((size_t)olen + 1);
    if (!out) return __mn_str_empty();

    int64_t i = 0, j = 0;
    while (i < slen) {
        int a = (src[i] == '=') ? 0 : b64_decode_char(src[i]); i++;
        int b = (src[i] == '=') ? 0 : b64_decode_char(src[i]); i++;
        int c = (src[i] == '=') ? 0 : b64_decode_char(src[i]); i++;
        int d = (src[i] == '=') ? 0 : b64_decode_char(src[i]); i++;

        if (a < 0 || b < 0 || c < 0 || d < 0) { free(out); return __mn_str_empty(); }

        uint32_t triple = ((uint32_t)a << 18) | ((uint32_t)b << 12) | ((uint32_t)c << 6) | (uint32_t)d;
        if (j < olen) out[j++] = (char)((triple >> 16) & 0xFF);
        if (j < olen) out[j++] = (char)((triple >> 8) & 0xFF);
        if (j < olen) out[j++] = (char)(triple & 0xFF);
    }
    out[j] = '\0';

    MnString result = __mn_str_from_parts(out, olen);
    free(out);
    return result;
}

/* --- Random bytes --- */

MN_IO_EXPORT MnString __mn_random_bytes_str(int64_t n) {
    if (n <= 0) return __mn_str_empty();
    char *buf = (char *)malloc((size_t)n);
    if (!buf) return __mn_str_empty();

#ifdef _WIN32
    /* Use BCryptGenRandom (Vista+) or CryptGenRandom */
    typedef long (WINAPI *fn_BCryptGenRandom)(void*, unsigned char*, unsigned long, unsigned long);
    HMODULE bcrypt = LoadLibraryA("bcrypt.dll");
    if (bcrypt) {
        fn_BCryptGenRandom gen = (fn_BCryptGenRandom)GetProcAddress(bcrypt, "BCryptGenRandom");
        if (gen && gen(NULL, (unsigned char *)buf, (unsigned long)n, 2 /*BCRYPT_USE_SYSTEM_PREFERRED_RNG*/) == 0) {
            MnString result = __mn_str_from_parts(buf, n);
            free(buf);
            return result;
        }
    }
    /* Fallback: rand() seeded by time — NOT cryptographically secure */
    srand((unsigned int)GetTickCount());
    for (int64_t i = 0; i < n; i++) buf[i] = (char)(rand() & 0xFF);
#else
    FILE *f = fopen("/dev/urandom", "rb");
    if (f) {
        size_t read = fread(buf, 1, (size_t)n, f);
        fclose(f);
        if ((int64_t)read != n) {
            free(buf);
            return __mn_str_empty();
        }
    } else {
        free(buf);
        return __mn_str_empty();
    }
#endif

    MnString result = __mn_str_from_parts(buf, n);
    free(buf);
    return result;
}

/* =======================================================================
 * 7. Regular Expressions (PCRE2 via dlopen)
 *
 * Dynamically loads libpcre2-8 and wraps compile/match/replace.
 * Falls back gracefully (returns error) if PCRE2 is not available.
 * ======================================================================= */

/* PCRE2 constants (from pcre2.h) */
#define MN_PCRE2_UNSET          (~(size_t)0)
#define MN_PCRE2_UTF            0x00080000u
#define MN_PCRE2_SUBSTITUTE_GLOBAL     0x00000100u
#define MN_PCRE2_SUBSTITUTE_OVERFLOW_LENGTH 0x00001000u
#define MN_PCRE2_ERROR_NOMEMORY (-48)
#define MN_PCRE2_ERROR_NOMATCH  (-1)

/* PCRE2 function pointer types (pcre2_*_8 variants) */
typedef void* (*fn_pcre2_compile)(const unsigned char *pattern, size_t length,
                                  uint32_t options, int *errorcode,
                                  size_t *erroroffset, void *ccontext);
typedef void  (*fn_pcre2_code_free)(void *code);
typedef void* (*fn_pcre2_match_data_create_from_pattern)(const void *code, void *gcontext);
typedef int   (*fn_pcre2_match)(const void *code, const unsigned char *subject,
                                size_t length, size_t startoffset, uint32_t options,
                                void *match_data, void *mcontext);
typedef size_t* (*fn_pcre2_get_ovector_pointer)(void *match_data);
typedef uint32_t (*fn_pcre2_get_ovector_count)(void *match_data);
typedef void  (*fn_pcre2_match_data_free)(void *match_data);
typedef int   (*fn_pcre2_get_error_message)(int errorcode, unsigned char *buffer, size_t bufflen);
typedef int   (*fn_pcre2_substitute)(const void *code, const unsigned char *subject,
                                     size_t length, size_t startoffset, uint32_t options,
                                     void *match_data, void *mcontext,
                                     const unsigned char *replacement, size_t rlength,
                                     unsigned char *outputbuffer, size_t *outlengthptr);
typedef int   (*fn_pcre2_pattern_info)(const void *code, uint32_t what, void *where);

/* Cached PCRE2 function pointers */
static struct {
    int loaded;
    int available;
    fn_pcre2_compile              compile;
    fn_pcre2_code_free            code_free;
    fn_pcre2_match_data_create_from_pattern match_data_create;
    fn_pcre2_match                match;
    fn_pcre2_get_ovector_pointer  get_ovector_pointer;
    fn_pcre2_get_ovector_count    get_ovector_count;
    fn_pcre2_match_data_free      match_data_free;
    fn_pcre2_get_error_message    get_error_message;
    fn_pcre2_substitute           substitute;
    fn_pcre2_pattern_info         pattern_info;
} s_pcre2 = {0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL};

static int pcre2_load(void) {
    if (s_pcre2.loaded) return s_pcre2.available ? 0 : -1;
    s_pcre2.loaded = 1;
    s_pcre2.available = 0;

    void *lib = NULL;
#ifdef _WIN32
    lib = (void *)LoadLibraryA("pcre2-8.dll");
    if (!lib) lib = (void *)LoadLibraryA("pcre2-8d.dll");
    if (!lib) lib = (void *)LoadLibraryA("libpcre2-8.dll");
    if (!lib) lib = (void *)LoadLibraryA("libpcre2-8-0.dll");
    #define PCRE2_SYM(name) s_pcre2.name = (fn_pcre2_##name)GetProcAddress((HMODULE)lib, "pcre2_" #name "_8")
#else
    lib = dlopen("libpcre2-8.so", RTLD_NOW | RTLD_LOCAL);
    if (!lib) lib = dlopen("libpcre2-8.so.0", RTLD_NOW | RTLD_LOCAL);
    if (!lib) lib = dlopen("libpcre2-8.dylib", RTLD_NOW | RTLD_LOCAL);
    #define PCRE2_SYM(name) s_pcre2.name = (fn_pcre2_##name)dlsym(lib, "pcre2_" #name "_8")
#endif
    if (!lib) return -1;

    PCRE2_SYM(compile);
    PCRE2_SYM(code_free);
#ifdef _WIN32
    s_pcre2.match_data_create = (fn_pcre2_match_data_create_from_pattern)GetProcAddress((HMODULE)lib, "pcre2_match_data_create_from_pattern_8");
#else
    s_pcre2.match_data_create = (fn_pcre2_match_data_create_from_pattern)dlsym(lib, "pcre2_match_data_create_from_pattern_8");
#endif
    PCRE2_SYM(match);
    PCRE2_SYM(get_ovector_pointer);
    PCRE2_SYM(get_ovector_count);
    PCRE2_SYM(match_data_free);
    PCRE2_SYM(get_error_message);
    PCRE2_SYM(substitute);
    PCRE2_SYM(pattern_info);
    #undef PCRE2_SYM

    if (!s_pcre2.compile || !s_pcre2.match || !s_pcre2.code_free ||
        !s_pcre2.match_data_create || !s_pcre2.get_ovector_pointer ||
        !s_pcre2.match_data_free) {
        return -1;
    }

    s_pcre2.available = 1;
    return 0;
}

/* Per-handle state: compiled regex + last match data */
typedef struct {
    void   *code;        /* pcre2_code */
    void   *match_data;  /* pcre2_match_data (from last exec) */
    size_t *ovector;     /* ovector pointer from last exec */
    int     rc;          /* pcre2_match return code from last exec */
    int     errcode;     /* error code from failed compile */
    size_t  erroffset;   /* error offset from failed compile */
} MnRegexHandle;

MN_IO_EXPORT int64_t __mn_regex_compile_str(MnString pattern) {
    if (pcre2_load() < 0) return 0;

    const char *pat = (const char *)((uintptr_t)pattern.data & ~(uintptr_t)1);

    MnRegexHandle *h = (MnRegexHandle *)calloc(1, sizeof(MnRegexHandle));
    if (!h) return 0;

    h->code = s_pcre2.compile(
        (const unsigned char *)pat, (size_t)pattern.len,
        MN_PCRE2_UTF, &h->errcode, &h->erroffset, NULL
    );

    if (!h->code) {
        /* Keep h alive so __mn_regex_error_str can retrieve the message */
        return (int64_t)(uintptr_t)h;
    }

    h->match_data = s_pcre2.match_data_create(h->code, NULL);
    if (!h->match_data) {
        s_pcre2.code_free(h->code);
        free(h);
        return 0;
    }

    return (int64_t)(uintptr_t)h;
}

MN_IO_EXPORT int64_t __mn_regex_exec_str(int64_t handle, MnString subject, int64_t start_offset) {
    if (!handle) return -1;
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (!h->code) return -1;

    const char *subj = (const char *)((uintptr_t)subject.data & ~(uintptr_t)1);

    h->rc = s_pcre2.match(
        h->code,
        (const unsigned char *)subj, (size_t)subject.len,
        (size_t)start_offset, 0,
        h->match_data, NULL
    );

    if (h->rc == MN_PCRE2_ERROR_NOMATCH) {
        h->ovector = NULL;
        return 0;
    }
    if (h->rc < 0) {
        h->ovector = NULL;
        return -1;
    }

    h->ovector = s_pcre2.get_ovector_pointer(h->match_data);
    return 1;
}

MN_IO_EXPORT MnString __mn_regex_group_str(int64_t handle, MnString subject, int64_t group_idx) {
    if (!handle) return __mn_str_empty();
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (!h->ovector || h->rc <= 0) return __mn_str_empty();
    if (group_idx < 0 || group_idx >= h->rc) return __mn_str_empty();

    size_t start = h->ovector[2 * group_idx];
    size_t end   = h->ovector[2 * group_idx + 1];
    if (start == MN_PCRE2_UNSET || end == MN_PCRE2_UNSET) return __mn_str_empty();

    const char *subj = (const char *)((uintptr_t)subject.data & ~(uintptr_t)1);
    return __mn_str_from_parts(subj + start, (int64_t)(end - start));
}

MN_IO_EXPORT int64_t __mn_regex_group_start(int64_t handle, int64_t group_idx) {
    if (!handle) return -1;
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (!h->ovector || h->rc <= 0) return -1;
    if (group_idx < 0 || group_idx >= h->rc) return -1;

    size_t start = h->ovector[2 * group_idx];
    if (start == MN_PCRE2_UNSET) return -1;
    return (int64_t)start;
}

MN_IO_EXPORT int64_t __mn_regex_group_end(int64_t handle, int64_t group_idx) {
    if (!handle) return -1;
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (!h->ovector || h->rc <= 0) return -1;
    if (group_idx < 0 || group_idx >= h->rc) return -1;

    size_t end = h->ovector[2 * group_idx + 1];
    if (end == MN_PCRE2_UNSET) return -1;
    return (int64_t)end;
}

MN_IO_EXPORT int64_t __mn_regex_group_count(int64_t handle) {
    if (!handle) return 0;
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (!h->code || !s_pcre2.pattern_info) return 0;

    uint32_t capture_count = 0;
    /* PCRE2_INFO_CAPTURECOUNT = 4 */
    s_pcre2.pattern_info(h->code, 4, &capture_count);
    return (int64_t)capture_count;
}

MN_IO_EXPORT MnString __mn_regex_replace_str(int64_t handle, MnString subject,
                                              MnString replacement, int64_t replace_all) {
    if (!handle) return subject;
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (!h->code) return subject;

    /* If substitute function not available, return subject unchanged */
    if (!s_pcre2.substitute) return subject;

    const char *subj = (const char *)((uintptr_t)subject.data & ~(uintptr_t)1);
    const char *repl = (const char *)((uintptr_t)replacement.data & ~(uintptr_t)1);

    uint32_t opts = MN_PCRE2_SUBSTITUTE_OVERFLOW_LENGTH;
    if (replace_all) opts |= MN_PCRE2_SUBSTITUTE_GLOBAL;

    /* First call to get required output length */
    size_t outlen = 0;
    int rc = s_pcre2.substitute(
        h->code,
        (const unsigned char *)subj, (size_t)subject.len,
        0, opts, h->match_data, NULL,
        (const unsigned char *)repl, (size_t)replacement.len,
        NULL, &outlen
    );

    if (rc == MN_PCRE2_ERROR_NOMATCH) return subject;
    if (rc != MN_PCRE2_ERROR_NOMEMORY && rc < 0) return subject;

    /* Allocate buffer and do actual substitution */
    unsigned char *buf = (unsigned char *)malloc(outlen + 1);
    if (!buf) return subject;

    size_t actual_len = outlen + 1;
    rc = s_pcre2.substitute(
        h->code,
        (const unsigned char *)subj, (size_t)subject.len,
        0, opts & ~MN_PCRE2_SUBSTITUTE_OVERFLOW_LENGTH,
        h->match_data, NULL,
        (const unsigned char *)repl, (size_t)replacement.len,
        buf, &actual_len
    );

    if (rc < 0) {
        free(buf);
        return subject;
    }

    MnString result = __mn_str_from_parts((const char *)buf, (int64_t)actual_len);
    free(buf);
    return result;
}

MN_IO_EXPORT int64_t __mn_regex_free(int64_t handle) {
    if (!handle) return 0;
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;
    if (h->match_data && s_pcre2.match_data_free) s_pcre2.match_data_free(h->match_data);
    if (h->code && s_pcre2.code_free) s_pcre2.code_free(h->code);
    free(h);
    return 0;
}

MN_IO_EXPORT MnString __mn_regex_error_str(int64_t handle) {
    if (!handle) return __mn_str_from_cstr("PCRE2 not available");
    MnRegexHandle *h = (MnRegexHandle *)(uintptr_t)handle;

    if (h->code) return __mn_str_empty(); /* no error */

    if (s_pcre2.get_error_message) {
        unsigned char buf[256];
        int len = s_pcre2.get_error_message(h->errcode, buf, sizeof(buf));
        if (len > 0) return __mn_str_from_parts((const char *)buf, (int64_t)len);
    }

    return __mn_str_from_cstr("regex compilation failed");
}
