/**
 * mapanare_html.h --- HTML parsing, timing, environment, and URL runtime
 *                     for Mapanare v1.3.0
 *
 * Provides HTML parsing via lexbor (loaded dynamically via dlopen), monotonic
 * and wall-clock timing primitives, environment variable access, and pure-C
 * URL parsing. These are the foundation that v1.3.0 stdlib modules
 * (net/crawl.mn, net/http.mn, etc.) call into.
 *
 * If lexbor is not installed, a simple tag-scanning fallback is provided
 * that can extract <a href="..."> links and <title> content — enough for
 * basic web crawling without a full DOM parser.
 *
 * All functions use the __mn_ prefix to avoid collisions.
 * Strings use the Mapanare { i8*, i64 } MnString struct passed by value.
 */

#ifndef MAPANARE_HTML_H
#define MAPANARE_HTML_H

#include <stdint.h>
#include <stddef.h>
#include "mapanare_core.h"

#ifdef _WIN32
  #define MN_HTML_EXPORT __declspec(dllexport)
#else
  #define MN_HTML_EXPORT __attribute__((visibility("default")))
#endif

/* =======================================================================
 * 1. HTML Parsing (lexbor via dlopen)
 *
 * Handle-based API: parse an HTML document, run CSS selector queries,
 * iterate over collections of matching elements, and extract tag names,
 * attributes, inner text, and outer HTML.
 *
 * lexbor is loaded dynamically (liblexbor.so / .dylib / .dll). If not
 * available, __mn_html_parse returns 0 and the fallback functions
 * (__mn_html_links / __mn_html_title) remain usable.
 *
 * Handles are opaque int64_t values (array index + 1). A handle of 0
 * indicates an error (library not loaded, parse failure, etc.).
 * ======================================================================= */

/** Parse an HTML string into a document. Returns doc handle (>0) or 0 on error. */
MN_HTML_EXPORT int64_t __mn_html_parse(MnString html);

/** Run a CSS selector query against a document.
 *  Returns collection handle (>0) or 0 on error. */
MN_HTML_EXPORT int64_t __mn_html_query(int64_t doc, MnString selector);

/** Get the number of elements in a collection. */
MN_HTML_EXPORT int64_t __mn_html_collection_len(int64_t coll);

/** Get the element at index `idx` from a collection.
 *  Returns element handle (>0) or 0 if out of bounds. */
MN_HTML_EXPORT int64_t __mn_html_collection_get(int64_t coll, int64_t idx);

/** Get the tag name of an element (e.g. "a", "div", "title"). */
MN_HTML_EXPORT MnString __mn_html_element_tag(int64_t elem);

/** Get the value of an attribute on an element.
 *  Returns empty string if the attribute does not exist. */
MN_HTML_EXPORT MnString __mn_html_element_attr(int64_t elem, MnString name);

/** Get the inner text content of an element (text nodes concatenated). */
MN_HTML_EXPORT MnString __mn_html_element_text(int64_t elem);

/** Get the outer HTML of an element (serialized subtree). */
MN_HTML_EXPORT MnString __mn_html_element_html(int64_t elem);

/** Free a parsed document and all its resources. */
MN_HTML_EXPORT void __mn_html_free(int64_t doc);

/** Free a CSS selector collection. */
MN_HTML_EXPORT void __mn_html_collection_free(int64_t coll);

/* =======================================================================
 * 2. Timing Primitives
 *
 * Monotonic clock (for measuring elapsed time), Unix epoch time, and
 * sleep. Cross-platform: POSIX clock_gettime / Windows GetTickCount64.
 * ======================================================================= */

/** Get current monotonic time in milliseconds. */
MN_HTML_EXPORT int64_t __mn_time_now_ms(void);

/** Get current Unix epoch time in seconds. */
MN_HTML_EXPORT int64_t __mn_time_now_unix(void);

/** Sleep for the given number of milliseconds. */
MN_HTML_EXPORT void __mn_sleep_ms(int64_t ms);

/* =======================================================================
 * 3. Environment Variables
 * ======================================================================= */

/** Get the value of an environment variable.
 *  Returns empty string if the variable is not set. */
MN_HTML_EXPORT MnString __mn_env_get(MnString name);

/* =======================================================================
 * 4. URL Parsing (pure C)
 *
 * Lightweight URL component extraction via string scanning.
 * Handles scheme://host:port/path format.
 * Returns empty string / 0 for missing components.
 * ======================================================================= */

/** Extract the scheme from a URL (e.g. "https" from "https://example.com"). */
MN_HTML_EXPORT MnString __mn_url_parse_scheme(MnString url);

/** Extract the host from a URL (e.g. "example.com" from "https://example.com:443/path"). */
MN_HTML_EXPORT MnString __mn_url_parse_host(MnString url);

/** Extract the port from a URL. Returns 0 if no explicit port is present. */
MN_HTML_EXPORT int64_t __mn_url_parse_port(MnString url);

/** Extract the path from a URL (e.g. "/path/to/page" from "https://example.com/path/to/page").
 *  Returns "/" if no path is present. */
MN_HTML_EXPORT MnString __mn_url_parse_path(MnString url);

#endif /* MAPANARE_HTML_H */
