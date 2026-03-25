/**
 * mapanare_html.c --- HTML parsing, timing, environment, and URL runtime
 *                     implementation for Mapanare v1.3.0
 *
 * Implements HTML parsing via lexbor (dlopen), timing primitives,
 * environment variable access, and pure-C URL parsing.
 */

#include "mapanare_html.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* =======================================================================
 * Platform-specific includes
 * ======================================================================= */

#ifdef _WIN32
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #include <windows.h>

  #define mn_dlopen(name)       LoadLibraryA(name)
  #define mn_dlsym(lib, name)   GetProcAddress((HMODULE)(lib), name)
  #define mn_dlclose(lib)       FreeLibrary((HMODULE)(lib))
  typedef HMODULE mn_lib_t;

#else /* POSIX */
  #include <unistd.h>
  #include <time.h>
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

/** Extract a null-terminated C string from MnString. Caller must free. */
static char *mnstr_to_cstr(MnString s) {
    const char *data = (const char *)((uintptr_t)s.data & ~(uintptr_t)1);
    char *cstr = (char *)malloc((size_t)s.len + 1);
    if (!cstr) return NULL;
    if (s.len > 0) memcpy(cstr, data, (size_t)s.len);
    cstr[s.len] = '\0';
    return cstr;
}

/** Get untagged pointer to MnString data (no copy, no null terminator guarantee). */
static const char *mnstr_data(MnString s) {
    return (const char *)((uintptr_t)s.data & ~(uintptr_t)1);
}

/* =======================================================================
 * Handle table infrastructure
 *
 * Each resource type gets a fixed-size table of opaque pointers.
 * Handle = array index + 1 (so 0 means "invalid/error").
 * ======================================================================= */

#define MN_MAX_HANDLES 256

typedef struct {
    void *ptrs[MN_MAX_HANDLES];
} MnHandleTable;

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
 * 1. HTML Parsing (via dlopen of lexbor)
 *
 * lexbor is a fast, standards-compliant HTML5 parser written in C.
 * We load it dynamically and call into its DOM + CSS selector APIs.
 *
 * If lexbor is not found, all parse/query functions return 0/empty.
 * ======================================================================= */

/*
 * Opaque lexbor types — we only use pointers, so forward declarations suffice.
 * The actual struct layouts are internal to lexbor.
 */
typedef struct lxb_html_document     lxb_html_document_t;
typedef struct lxb_html_parser       lxb_html_parser_t;
typedef struct lxb_dom_element       lxb_dom_element_t;
typedef struct lxb_dom_node          lxb_dom_node_t;
typedef struct lxb_dom_collection    lxb_dom_collection_t;
typedef struct lxb_css_selector_list lxb_css_selector_list_t;
typedef struct lxb_selectors         lxb_selectors_t;
typedef struct lxb_css_parser        lxb_css_parser_t;

/* lexbor status type */
typedef unsigned int lxb_status_t;
#define LXB_STATUS_OK 0x0000

/* lexbor serialization callback type */
typedef lxb_status_t (*lxb_html_serialize_cb_f)(const char *data, size_t len, void *ctx);

/* Function pointer types for lexbor API */
typedef lxb_html_parser_t *(*fn_lxb_html_parser_create)(void);
typedef lxb_status_t        (*fn_lxb_html_parser_init)(lxb_html_parser_t *);
typedef lxb_html_document_t *(*fn_lxb_html_parse)(lxb_html_parser_t *, const unsigned char *, size_t);
typedef void                (*fn_lxb_html_parser_destroy)(lxb_html_parser_t *);
typedef void                (*fn_lxb_html_document_destroy)(lxb_html_document_t *);

typedef lxb_dom_collection_t *(*fn_lxb_dom_collection_create)(void *);  /* actually lxb_dom_document_t* */
typedef lxb_status_t          (*fn_lxb_dom_collection_init)(lxb_dom_collection_t *, size_t);
typedef void                  (*fn_lxb_dom_collection_destroy)(lxb_dom_collection_t *, int);
typedef size_t                (*fn_lxb_dom_collection_length)(lxb_dom_collection_t *);
typedef lxb_dom_element_t    *(*fn_lxb_dom_collection_element)(lxb_dom_collection_t *, size_t);

typedef const unsigned char  *(*fn_lxb_dom_element_local_name)(lxb_dom_element_t *, size_t *);
typedef const unsigned char  *(*fn_lxb_dom_element_get_attribute)(lxb_dom_element_t *, const unsigned char *, size_t, size_t *);
typedef lxb_status_t          (*fn_lxb_html_serialize_tree_cb)(lxb_dom_node_t *, lxb_html_serialize_cb_f, void *);

/* CSS selector API */
typedef lxb_css_parser_t     *(*fn_lxb_css_parser_create)(void);
typedef lxb_status_t          (*fn_lxb_css_parser_init)(lxb_css_parser_t *, void *);  /* lxb_css_memory_t* */
typedef void                  (*fn_lxb_css_parser_destroy)(lxb_css_parser_t *, int);
typedef lxb_css_selector_list_t *(*fn_lxb_css_selectors_parse)(lxb_css_parser_t *, const unsigned char *, size_t);

typedef lxb_selectors_t      *(*fn_lxb_selectors_create)(void);
typedef lxb_status_t          (*fn_lxb_selectors_init)(lxb_selectors_t *);
typedef void                  (*fn_lxb_selectors_destroy)(lxb_selectors_t *, int);
typedef lxb_status_t          (*fn_lxb_selectors_find)(lxb_selectors_t *, lxb_dom_node_t *,
                                                        lxb_css_selector_list_t *,
                                                        void * /* callback */, void * /* ctx */);

typedef lxb_dom_node_t       *(*fn_lxb_dom_node_first_child)(lxb_dom_node_t *);
typedef lxb_dom_node_t       *(*fn_lxb_dom_node_next)(lxb_dom_node_t *);

/* Text content extraction callback type for selectors_find */
typedef lxb_status_t (*lxb_selectors_cb_f)(lxb_dom_node_t *node, void *spec, void *ctx);

/* Dynamic lexbor state */
static struct {
    int loaded;
    int available;
    mn_lib_t lib;

    fn_lxb_html_parser_create       p_parser_create;
    fn_lxb_html_parser_init         p_parser_init;
    fn_lxb_html_parse               p_parse;
    fn_lxb_html_parser_destroy      p_parser_destroy;
    fn_lxb_html_document_destroy    p_doc_destroy;

    fn_lxb_dom_collection_create    p_coll_create;
    fn_lxb_dom_collection_init      p_coll_init;
    fn_lxb_dom_collection_destroy   p_coll_destroy;
    fn_lxb_dom_collection_length    p_coll_length;
    fn_lxb_dom_collection_element   p_coll_element;

    fn_lxb_dom_element_local_name       p_elem_local_name;
    fn_lxb_dom_element_get_attribute    p_elem_get_attr;
    fn_lxb_html_serialize_tree_cb       p_serialize_tree;

    fn_lxb_css_parser_create        p_css_parser_create;
    fn_lxb_css_parser_init          p_css_parser_init;
    fn_lxb_css_parser_destroy       p_css_parser_destroy;
    fn_lxb_css_selectors_parse      p_css_selectors_parse;

    fn_lxb_selectors_create         p_selectors_create;
    fn_lxb_selectors_init           p_selectors_init;
    fn_lxb_selectors_destroy        p_selectors_destroy;
    fn_lxb_selectors_find           p_selectors_find;

    fn_lxb_dom_node_first_child     p_node_first_child;
    fn_lxb_dom_node_next            p_node_next;
} s_lexbor = {0};

/* Handle tables for docs, collections, and elements */
static MnHandleTable s_html_docs  = {{0}};
static MnHandleTable s_html_colls = {{0}};
static MnHandleTable s_html_elems = {{0}};

/* Document wrapper: stores the document + the parser used to create it */
typedef struct {
    lxb_html_document_t *doc;
    lxb_html_parser_t   *parser;
} MnHtmlDoc;

static int lexbor_load(void) {
    if (s_lexbor.loaded) return s_lexbor.available ? 0 : -1;
    s_lexbor.loaded = 1;
    s_lexbor.available = 0;

#ifdef _WIN32
    s_lexbor.lib = mn_dlopen("lexbor.dll");
    if (!s_lexbor.lib) s_lexbor.lib = mn_dlopen("liblexbor.dll");
#else
    s_lexbor.lib = mn_dlopen("liblexbor.so");
    if (!s_lexbor.lib) s_lexbor.lib = mn_dlopen("liblexbor.so.2");
    if (!s_lexbor.lib) s_lexbor.lib = mn_dlopen("liblexbor.so.1");
    #ifdef __APPLE__
    if (!s_lexbor.lib) s_lexbor.lib = mn_dlopen("liblexbor.dylib");
    #endif
#endif

    if (!s_lexbor.lib) return -1;

    #define LXB_SYM(field, name) \
        s_lexbor.field = (__typeof__(s_lexbor.field))mn_dlsym(s_lexbor.lib, #name)

    LXB_SYM(p_parser_create,    lxb_html_parser_create);
    LXB_SYM(p_parser_init,      lxb_html_parser_init);
    LXB_SYM(p_parse,            lxb_html_parse);
    LXB_SYM(p_parser_destroy,   lxb_html_parser_destroy);
    LXB_SYM(p_doc_destroy,      lxb_html_document_destroy);

    LXB_SYM(p_coll_create,      lxb_dom_collection_create);
    LXB_SYM(p_coll_init,        lxb_dom_collection_init);
    LXB_SYM(p_coll_destroy,     lxb_dom_collection_destroy);
    LXB_SYM(p_coll_length,      lxb_dom_collection_length);
    LXB_SYM(p_coll_element,     lxb_dom_collection_element);

    LXB_SYM(p_elem_local_name,  lxb_dom_element_local_name);
    LXB_SYM(p_elem_get_attr,    lxb_dom_element_get_attribute);
    LXB_SYM(p_serialize_tree,   lxb_html_serialize_tree_cb);

    LXB_SYM(p_css_parser_create,    lxb_css_parser_create);
    LXB_SYM(p_css_parser_init,      lxb_css_parser_init);
    LXB_SYM(p_css_parser_destroy,   lxb_css_parser_destroy);
    LXB_SYM(p_css_selectors_parse,  lxb_css_selectors_parse);

    LXB_SYM(p_selectors_create, lxb_selectors_create);
    LXB_SYM(p_selectors_init,   lxb_selectors_init);
    LXB_SYM(p_selectors_destroy,lxb_selectors_destroy);
    LXB_SYM(p_selectors_find,   lxb_selectors_find);

    LXB_SYM(p_node_first_child, lxb_dom_node_first_child);
    LXB_SYM(p_node_next,        lxb_dom_node_next);

    #undef LXB_SYM

    /* Verify minimum required symbols for parse/query */
    if (!s_lexbor.p_parser_create || !s_lexbor.p_parser_init ||
        !s_lexbor.p_parse || !s_lexbor.p_doc_destroy ||
        !s_lexbor.p_parser_destroy) {
        return -1;
    }

    s_lexbor.available = 1;
    return 0;
}

MN_HTML_EXPORT int64_t __mn_html_parse(MnString html) {
    if (!s_lexbor.available) {
        if (lexbor_load() < 0) return 0;
    }

    lxb_html_parser_t *parser = s_lexbor.p_parser_create();
    if (!parser) return 0;

    lxb_status_t status = s_lexbor.p_parser_init(parser);
    if (status != LXB_STATUS_OK) {
        s_lexbor.p_parser_destroy(parser);
        return 0;
    }

    const char *data = mnstr_data(html);
    lxb_html_document_t *doc = s_lexbor.p_parse(
        parser, (const unsigned char *)data, (size_t)html.len
    );
    if (!doc) {
        s_lexbor.p_parser_destroy(parser);
        return 0;
    }

    MnHtmlDoc *wrap = (MnHtmlDoc *)calloc(1, sizeof(MnHtmlDoc));
    if (!wrap) {
        s_lexbor.p_doc_destroy(doc);
        s_lexbor.p_parser_destroy(parser);
        return 0;
    }
    wrap->doc = doc;
    wrap->parser = parser;

    int64_t handle = handle_alloc(&s_html_docs, wrap);
    if (handle == 0) {
        s_lexbor.p_doc_destroy(doc);
        s_lexbor.p_parser_destroy(parser);
        free(wrap);
        return 0;
    }
    return handle;
}

/* Selector find callback: appends matched nodes to a collection */
static lxb_status_t selector_cb(lxb_dom_node_t *node, void *spec, void *ctx) {
    (void)spec;
    /* ctx is a pointer to a MnHandleTable-style collector — we store elements */
    MnHandleTable *elems = (MnHandleTable *)ctx;
    /* Find first empty slot */
    for (int i = 0; i < MN_MAX_HANDLES; i++) {
        if (elems->ptrs[i] == NULL) {
            elems->ptrs[i] = node;
            break;
        }
    }
    return LXB_STATUS_OK;
}

/* Collection wrapper: stores matched elements inline */
typedef struct {
    void  *elems[MN_MAX_HANDLES];
    int64_t count;
    /* Resources to free */
    lxb_selectors_t         *selectors;
    lxb_css_parser_t        *css_parser;
    lxb_css_selector_list_t *sel_list;
} MnHtmlColl;

MN_HTML_EXPORT int64_t __mn_html_query(int64_t doc_handle, MnString selector) {
    if (!s_lexbor.available) return 0;

    MnHtmlDoc *wrap = (MnHtmlDoc *)handle_get(&s_html_docs, doc_handle);
    if (!wrap) return 0;

    /* Need CSS selector + selectors engine APIs */
    if (!s_lexbor.p_css_parser_create || !s_lexbor.p_css_selectors_parse ||
        !s_lexbor.p_selectors_create || !s_lexbor.p_selectors_find) {
        return 0;
    }

    /* Create CSS parser */
    lxb_css_parser_t *css_parser = s_lexbor.p_css_parser_create();
    if (!css_parser) return 0;

    lxb_status_t status = s_lexbor.p_css_parser_init(css_parser, NULL);
    if (status != LXB_STATUS_OK) {
        s_lexbor.p_css_parser_destroy(css_parser, 1);
        return 0;
    }

    /* Parse the CSS selector */
    const char *sel_data = mnstr_data(selector);
    lxb_css_selector_list_t *sel_list = s_lexbor.p_css_selectors_parse(
        css_parser, (const unsigned char *)sel_data, (size_t)selector.len
    );
    if (!sel_list) {
        s_lexbor.p_css_parser_destroy(css_parser, 1);
        return 0;
    }

    /* Create selectors engine */
    lxb_selectors_t *selectors = s_lexbor.p_selectors_create();
    if (!selectors) {
        s_lexbor.p_css_parser_destroy(css_parser, 1);
        return 0;
    }
    status = s_lexbor.p_selectors_init(selectors);
    if (status != LXB_STATUS_OK) {
        s_lexbor.p_selectors_destroy(selectors, 1);
        s_lexbor.p_css_parser_destroy(css_parser, 1);
        return 0;
    }

    /* Collect matching elements */
    MnHtmlColl *coll = (MnHtmlColl *)calloc(1, sizeof(MnHtmlColl));
    if (!coll) {
        s_lexbor.p_selectors_destroy(selectors, 1);
        s_lexbor.p_css_parser_destroy(css_parser, 1);
        return 0;
    }

    /* Use a temporary handle table for the callback to store elements */
    MnHandleTable tmp_elems = {{0}};

    /* Run the selector against the document root */
    status = s_lexbor.p_selectors_find(
        selectors,
        (lxb_dom_node_t *)wrap->doc,  /* document as root node */
        sel_list,
        (void *)selector_cb,
        &tmp_elems
    );

    /* Count collected elements and store them in the collection */
    coll->count = 0;
    for (int i = 0; i < MN_MAX_HANDLES && tmp_elems.ptrs[i] != NULL; i++) {
        coll->elems[i] = tmp_elems.ptrs[i];
        coll->count++;
    }

    /* Store resources for cleanup */
    coll->selectors = selectors;
    coll->css_parser = css_parser;
    coll->sel_list = sel_list;

    int64_t handle = handle_alloc(&s_html_colls, coll);
    if (handle == 0) {
        s_lexbor.p_selectors_destroy(selectors, 1);
        s_lexbor.p_css_parser_destroy(css_parser, 1);
        free(coll);
        return 0;
    }
    return handle;
}

MN_HTML_EXPORT int64_t __mn_html_collection_len(int64_t coll_handle) {
    MnHtmlColl *coll = (MnHtmlColl *)handle_get(&s_html_colls, coll_handle);
    if (!coll) return 0;
    return coll->count;
}

MN_HTML_EXPORT int64_t __mn_html_collection_get(int64_t coll_handle, int64_t idx) {
    MnHtmlColl *coll = (MnHtmlColl *)handle_get(&s_html_colls, coll_handle);
    if (!coll || idx < 0 || idx >= coll->count) return 0;

    void *elem = coll->elems[idx];
    if (!elem) return 0;

    int64_t handle = handle_alloc(&s_html_elems, elem);
    return handle;
}

MN_HTML_EXPORT MnString __mn_html_element_tag(int64_t elem_handle) {
    if (!s_lexbor.available || !s_lexbor.p_elem_local_name) {
        return __mn_str_empty();
    }

    lxb_dom_element_t *elem = (lxb_dom_element_t *)handle_get(&s_html_elems, elem_handle);
    if (!elem) return __mn_str_empty();

    size_t name_len = 0;
    const unsigned char *name = s_lexbor.p_elem_local_name(elem, &name_len);
    if (!name || name_len == 0) return __mn_str_empty();

    return __mn_str_from_parts((const char *)name, (int64_t)name_len);
}

MN_HTML_EXPORT MnString __mn_html_element_attr(int64_t elem_handle, MnString attr_name) {
    if (!s_lexbor.available || !s_lexbor.p_elem_get_attr) {
        return __mn_str_empty();
    }

    lxb_dom_element_t *elem = (lxb_dom_element_t *)handle_get(&s_html_elems, elem_handle);
    if (!elem) return __mn_str_empty();

    const char *name_data = mnstr_data(attr_name);
    size_t val_len = 0;
    const unsigned char *val = s_lexbor.p_elem_get_attr(
        elem,
        (const unsigned char *)name_data,
        (size_t)attr_name.len,
        &val_len
    );
    if (!val) return __mn_str_empty();

    return __mn_str_from_parts((const char *)val, (int64_t)val_len);
}

/* Serialization callback context for building a string buffer */
typedef struct {
    char   *buf;
    size_t  len;
    size_t  cap;
} MnSerBuf;

static lxb_status_t serialize_cb(const char *data, size_t len, void *ctx) {
    MnSerBuf *sb = (MnSerBuf *)ctx;
    size_t need = sb->len + len;
    if (need > sb->cap) {
        size_t new_cap = sb->cap * 2;
        if (new_cap < need) new_cap = need;
        if (new_cap < 256) new_cap = 256;
        char *nb = (char *)realloc(sb->buf, new_cap);
        if (!nb) return 1;  /* error status */
        sb->buf = nb;
        sb->cap = new_cap;
    }
    memcpy(sb->buf + sb->len, data, len);
    sb->len += len;
    return LXB_STATUS_OK;
}

MN_HTML_EXPORT MnString __mn_html_element_text(int64_t elem_handle) {
    if (!s_lexbor.available) return __mn_str_empty();

    lxb_dom_node_t *node = (lxb_dom_node_t *)handle_get(&s_html_elems, elem_handle);
    if (!node) return __mn_str_empty();

    /*
     * Walk child nodes to concatenate text. lexbor represents text content
     * as child text nodes (node type 3). We walk the immediate children
     * and collect their text data. For a proper deep extraction we would
     * need recursive traversal, but for typical use (title, link text)
     * immediate children suffice.
     *
     * If the node_first_child/node_next APIs are available, use them.
     * Otherwise fall back to serialization and strip tags.
     */
    if (s_lexbor.p_node_first_child && s_lexbor.p_node_next) {
        MnSerBuf sb = {NULL, 0, 0};
        lxb_dom_node_t *child = s_lexbor.p_node_first_child(node);
        while (child) {
            /*
             * In lexbor's DOM, the node struct has: type at a known offset.
             * Text node type is 3 (LXB_DOM_NODE_TYPE_TEXT).
             * The text content is stored in a lxb_dom_character_data_t whose
             * layout starts with the node, followed by a lexbor_str_t.
             *
             * Since we are using an opaque API, we use serialization for
             * individual text nodes. This is safe and correct.
             */
            if (s_lexbor.p_serialize_tree) {
                s_lexbor.p_serialize_tree(child, serialize_cb, &sb);
            }
            child = s_lexbor.p_node_next(child);
        }
        if (sb.buf && sb.len > 0) {
            /* Strip HTML tags from serialized output to get plain text */
            char *plain = (char *)malloc(sb.len + 1);
            if (plain) {
                size_t j = 0;
                int in_tag = 0;
                for (size_t i = 0; i < sb.len; i++) {
                    if (sb.buf[i] == '<') { in_tag = 1; continue; }
                    if (sb.buf[i] == '>') { in_tag = 0; continue; }
                    if (!in_tag) plain[j++] = sb.buf[i];
                }
                plain[j] = '\0';
                free(sb.buf);
                MnString result = __mn_str_from_parts(plain, (int64_t)j);
                free(plain);
                return result;
            }
        }
        free(sb.buf);
        return __mn_str_empty();
    }

    /* Fallback: serialize subtree and strip tags */
    if (s_lexbor.p_serialize_tree) {
        MnSerBuf sb = {NULL, 0, 0};
        s_lexbor.p_serialize_tree(node, serialize_cb, &sb);
        if (sb.buf && sb.len > 0) {
            char *plain = (char *)malloc(sb.len + 1);
            if (plain) {
                size_t j = 0;
                int in_tag = 0;
                for (size_t i = 0; i < sb.len; i++) {
                    if (sb.buf[i] == '<') { in_tag = 1; continue; }
                    if (sb.buf[i] == '>') { in_tag = 0; continue; }
                    if (!in_tag) plain[j++] = sb.buf[i];
                }
                plain[j] = '\0';
                free(sb.buf);
                MnString result = __mn_str_from_parts(plain, (int64_t)j);
                free(plain);
                return result;
            }
        }
        free(sb.buf);
    }

    return __mn_str_empty();
}

MN_HTML_EXPORT MnString __mn_html_element_html(int64_t elem_handle) {
    if (!s_lexbor.available || !s_lexbor.p_serialize_tree) {
        return __mn_str_empty();
    }

    lxb_dom_node_t *node = (lxb_dom_node_t *)handle_get(&s_html_elems, elem_handle);
    if (!node) return __mn_str_empty();

    MnSerBuf sb = {NULL, 0, 0};
    lxb_status_t status = s_lexbor.p_serialize_tree(node, serialize_cb, &sb);
    if (status != LXB_STATUS_OK || !sb.buf) {
        free(sb.buf);
        return __mn_str_empty();
    }

    MnString result = __mn_str_from_parts(sb.buf, (int64_t)sb.len);
    free(sb.buf);
    return result;
}

MN_HTML_EXPORT void __mn_html_free(int64_t doc_handle) {
    MnHtmlDoc *wrap = (MnHtmlDoc *)handle_get(&s_html_docs, doc_handle);
    if (!wrap) return;

    if (s_lexbor.available) {
        if (wrap->doc) s_lexbor.p_doc_destroy(wrap->doc);
        if (wrap->parser) s_lexbor.p_parser_destroy(wrap->parser);
    }
    free(wrap);
    handle_free(&s_html_docs, doc_handle);
}

MN_HTML_EXPORT void __mn_html_collection_free(int64_t coll_handle) {
    MnHtmlColl *coll = (MnHtmlColl *)handle_get(&s_html_colls, coll_handle);
    if (!coll) return;

    /* Free element handles that were allocated from this collection */
    for (int64_t i = 0; i < coll->count; i++) {
        /* Find and clear any element handle pointing to this element */
        for (int j = 0; j < MN_MAX_HANDLES; j++) {
            if (s_html_elems.ptrs[j] == coll->elems[i]) {
                s_html_elems.ptrs[j] = NULL;
            }
        }
    }

    /* Free CSS selector resources */
    if (s_lexbor.available) {
        if (coll->selectors) s_lexbor.p_selectors_destroy(coll->selectors, 1);
        if (coll->css_parser) s_lexbor.p_css_parser_destroy(coll->css_parser, 1);
        /* sel_list is owned by css_parser, freed above */
    }

    free(coll);
    handle_free(&s_html_colls, coll_handle);
}

/* =======================================================================
 * 2. Timing Primitives
 * ======================================================================= */

MN_HTML_EXPORT int64_t __mn_time_now_ms(void) {
#ifdef _WIN32
    return (int64_t)GetTickCount64();
#else
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) return 0;
    return (int64_t)ts.tv_sec * 1000 + (int64_t)(ts.tv_nsec / 1000000);
#endif
}

MN_HTML_EXPORT int64_t __mn_time_now_unix(void) {
    return (int64_t)time(NULL);
}

MN_HTML_EXPORT void __mn_sleep_ms(int64_t ms) {
    if (ms <= 0) return;
#ifdef _WIN32
    Sleep((DWORD)ms);
#else
    usleep((useconds_t)(ms * 1000));
#endif
}

/* =======================================================================
 * 3. Environment Variables
 * ======================================================================= */

MN_HTML_EXPORT MnString __mn_env_get(MnString name) {
    char *cname = mnstr_to_cstr(name);
    if (!cname) return __mn_str_empty();

    const char *val = getenv(cname);
    free(cname);

    if (!val) return __mn_str_empty();
    return __mn_str_from_cstr(val);
}

/* =======================================================================
 * 4. URL Parsing (pure C string scanning)
 *
 * Handles URLs of the form: scheme://host:port/path?query#fragment
 * Each function extracts one component. Missing components return
 * empty string or 0.
 * ======================================================================= */

/**
 * Find the position of "://" in the URL data.
 * Returns the index of ':', or -1 if not found.
 */
static int64_t find_scheme_sep(const char *data, int64_t len) {
    for (int64_t i = 0; i + 2 < len; i++) {
        if (data[i] == ':' && data[i + 1] == '/' && data[i + 2] == '/') {
            return i;
        }
    }
    return -1;
}

MN_HTML_EXPORT MnString __mn_url_parse_scheme(MnString url) {
    const char *data = mnstr_data(url);
    int64_t sep = find_scheme_sep(data, url.len);
    if (sep <= 0) return __mn_str_empty();
    return __mn_str_from_parts(data, sep);
}

MN_HTML_EXPORT MnString __mn_url_parse_host(MnString url) {
    const char *data = mnstr_data(url);
    int64_t sep = find_scheme_sep(data, url.len);

    int64_t host_start;
    if (sep >= 0) {
        host_start = sep + 3;  /* skip "://" */
    } else {
        host_start = 0;
    }

    if (host_start >= url.len) return __mn_str_empty();

    /* Find end of host: first of ':', '/', '?', '#', or end of string */
    int64_t host_end = host_start;
    while (host_end < url.len) {
        char c = data[host_end];
        if (c == ':' || c == '/' || c == '?' || c == '#') break;
        host_end++;
    }

    if (host_end <= host_start) return __mn_str_empty();
    return __mn_str_from_parts(data + host_start, host_end - host_start);
}

MN_HTML_EXPORT int64_t __mn_url_parse_port(MnString url) {
    const char *data = mnstr_data(url);
    int64_t sep = find_scheme_sep(data, url.len);

    int64_t host_start;
    if (sep >= 0) {
        host_start = sep + 3;
    } else {
        host_start = 0;
    }

    /* Find the ':' that separates host from port */
    int64_t colon = -1;
    for (int64_t i = host_start; i < url.len; i++) {
        char c = data[i];
        if (c == '/' || c == '?' || c == '#') break;
        if (c == ':') {
            colon = i;
            break;
        }
    }

    if (colon < 0) return 0;  /* no port specified */

    /* Parse digits after the colon */
    int64_t port = 0;
    for (int64_t i = colon + 1; i < url.len; i++) {
        char c = data[i];
        if (c < '0' || c > '9') break;
        port = port * 10 + (c - '0');
    }

    return port;
}

MN_HTML_EXPORT MnString __mn_url_parse_path(MnString url) {
    const char *data = mnstr_data(url);
    int64_t sep = find_scheme_sep(data, url.len);

    int64_t after_scheme;
    if (sep >= 0) {
        after_scheme = sep + 3;
    } else {
        after_scheme = 0;
    }

    /* Skip past the host (and optional port) to find the first '/' */
    int64_t path_start = -1;
    for (int64_t i = after_scheme; i < url.len; i++) {
        if (data[i] == '/') {
            path_start = i;
            break;
        }
        if (data[i] == '?' || data[i] == '#') break;
    }

    if (path_start < 0) {
        return __mn_str_from_cstr("/");
    }

    /* Find end of path: first of '?', '#', or end */
    int64_t path_end = path_start;
    while (path_end < url.len) {
        char c = data[path_end];
        if (c == '?' || c == '#') break;
        path_end++;
    }

    if (path_end <= path_start) {
        return __mn_str_from_cstr("/");
    }

    return __mn_str_from_parts(data + path_start, path_end - path_start);
}
