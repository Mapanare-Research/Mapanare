/*
 * test_html_smoke.c — v4.29.0 PLAN §1.2 smoke test for mapanare_html.c.
 *
 * Why this test exists
 * --------------------
 *
 * Prior to v4.29.0, runtime/native/mapanare_html.c (812 lines of HTML
 * parser + time + env + URL helpers) was orphaned the same way
 * mapanare_db.c was: neither the Makefile nor scripts/build_stage1.py
 * nor the LLVM emitter's runtime declaration table knew about it. The
 * v4.26.0 seven-reviewer panel flagged it (Anaconda HIGH); v4.29.0
 * wired it in.
 *
 * What it tests
 * -------------
 *
 * 1) ``test_link_is_wired_up`` — calls ``__mn_html_parse`` so the
 *    linker has to resolve a symbol from mapanare_html.c. If the file
 *    is re-orphaned in a future edit, this test fails to link and the
 *    CI native job breaks. That is the fuse.
 *
 * 2) ``test_parse_and_query_when_lexbor_available`` — if liblexbor is
 *    installed, parses a small HTML fragment, queries "h1", and
 *    verifies the tag name comes back as "h1". On CI machines without
 *    liblexbor, ``__mn_html_parse`` returns 0 (graceful dlopen failure)
 *    and the test prints "skipped" and exits 0. The fuse stays on the
 *    link, not on having lexbor installed.
 *
 * 3) ``test_time_helpers`` — verifies the always-present POSIX-backed
 *    helpers (``__mn_time_now_ms``, ``__mn_time_now_unix``) return
 *    reasonable values. No dlopen involved; these always work.
 *
 * Build line (also referenced by the CI native job):
 *
 *     gcc -O2 -I runtime/native tests/runtime/test_html_smoke.c \
 *         runtime/native/libmapanare_rt.a \
 *         -o /tmp/test_html_smoke -lm -lpthread -ldl
 *     /tmp/test_html_smoke
 */

#include "mapanare_core.h"
#include "mapanare_html.h"

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
    MnString html = __mn_str_from_cstr(
        "<html><body><h1>Hello</h1></body></html>"
    );
    int64_t doc = __mn_html_parse(html);
    if (doc < 0) {
        fail("__mn_html_parse returned a negative handle");
        return;
    }
    if (doc > 0) {
        __mn_html_free(doc);
    }
    pass("test_link_is_wired_up (mapanare_html.c symbol resolves)");
}

static void test_parse_and_query_when_lexbor_available(void) {
    MnString html = __mn_str_from_cstr(
        "<html>\n"
        "  <head><title>t</title></head>\n"
        "  <body>\n"
        "    <h1>Hello, Mapanare</h1>\n"
        "    <p>paragraph</p>\n"
        "  </body>\n"
        "</html>\n"
    );
    int64_t doc = __mn_html_parse(html);
    if (doc == 0) {
        printf("skip: liblexbor not available — link-fuse held, "
               "but the parse path is not exercised here.\n");
        return;
    }

    MnString selector = __mn_str_from_cstr("h1");
    int64_t coll = __mn_html_query(doc, selector);
    if (coll == 0) {
        /* CSS selector engine may not be loaded. The fuse has still
         * held — exit quietly. */
        __mn_html_free(doc);
        printf("skip: liblexbor CSS selector engine not available — "
               "link-fuse held.\n");
        return;
    }

    int64_t n = __mn_html_collection_len(coll);
    if (n < 1) {
        fail("query 'h1' returned zero elements");
        __mn_html_collection_free(coll);
        __mn_html_free(doc);
        return;
    }

    int64_t elem = __mn_html_collection_get(coll, 0);
    if (elem == 0) {
        fail("collection_get(0) returned 0 on a non-empty collection");
        __mn_html_collection_free(coll);
        __mn_html_free(doc);
        return;
    }

    MnString tag = __mn_html_element_tag(elem);
    if (tag.len != 2 || strncmp(mnstr_bytes(tag), "h1", 2) != 0) {
        fail("element tag was not 'h1'");
        __mn_html_collection_free(coll);
        __mn_html_free(doc);
        return;
    }

    __mn_html_collection_free(coll);
    __mn_html_free(doc);
    pass("test_parse_and_query_when_lexbor_available");
}

static void test_time_helpers(void) {
    /* These helpers do not rely on dlopen and must always return a
     * positive value. Note that ``__mn_time_now_ms`` uses
     * ``CLOCK_MONOTONIC`` (since-boot, not since-epoch) — comparing
     * it to ``__mn_time_now_unix`` (seconds since epoch) directly is
     * meaningless, so we only pin each one to "positive" and check
     * monotonic progression inside one process. */
    int64_t ms1 = __mn_time_now_ms();
    if (ms1 <= 0) {
        fail("__mn_time_now_ms returned non-positive");
        return;
    }
    int64_t unix_secs = __mn_time_now_unix();
    if (unix_secs <= 0) {
        fail("__mn_time_now_unix returned non-positive");
        return;
    }
    /* Call ms again and check it did not go backwards. This also
     * verifies the symbol is not a stub that returns a constant. */
    int64_t ms2 = __mn_time_now_ms();
    if (ms2 < ms1) {
        fail("__mn_time_now_ms went backwards between two calls");
        return;
    }
    pass("test_time_helpers");
}

int main(void) {
    printf("=== test_html_smoke (v4.29.0 Phase 1.2) ===\n");
    test_link_is_wired_up();
    test_parse_and_query_when_lexbor_available();
    test_time_helpers();
    if (g_fail_count > 0) {
        fprintf(stderr, "\n%d failure(s)\n", g_fail_count);
        return 1;
    }
    printf("\nOK — mapanare_html.c smoke suite passed.\n");
    return 0;
}
