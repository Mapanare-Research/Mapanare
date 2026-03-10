/**
 * mapanare_core.h — Core runtime for the Mapanare self-hosted compiler.
 *
 * Provides fundamental data type operations that native-compiled Mapanare
 * programs link against:
 *   - MnString: heap-allocated, length-prefixed strings
 *   - MnList:   type-erased growable arrays
 *   - File I/O: read source files
 *   - Memory:   alloc/free wrappers
 *
 * All functions use the __mn_ prefix to avoid collisions.
 * Strings are the Mapanare { i8*, i64 } struct passed by value.
 */

#ifndef MAPANARE_CORE_H
#define MAPANARE_CORE_H

#include <stdint.h>
#include <stddef.h>

#ifdef _WIN32
  #define MN_EXPORT __declspec(dllexport)
#else
  #define MN_EXPORT __attribute__((visibility("default")))
#endif

/* -----------------------------------------------------------------------
 * MnString — matches LLVM layout { i8*, i64 }
 *
 * The data pointer is heap-allocated (or points to a global constant).
 * Length does NOT include a null terminator, but we always allocate
 * one extra byte and null-terminate for C interop convenience.
 * ----------------------------------------------------------------------- */

typedef struct {
    const char *data;
    int64_t     len;
} MnString;

/** Create a string from a C string (copies the data). */
MN_EXPORT MnString __mn_str_from_cstr(const char *cstr);

/** Create a string from data + length (copies the data). */
MN_EXPORT MnString __mn_str_from_parts(const char *data, int64_t len);

/** Create an empty string. */
MN_EXPORT MnString __mn_str_empty(void);

/** Concatenate two strings. Returns a new heap-allocated string. */
MN_EXPORT MnString __mn_str_concat(MnString a, MnString b);

/** Get the character at index `i` as a single-character string.
 *  Returns empty string if out of bounds. */
MN_EXPORT MnString __mn_str_char_at(MnString s, int64_t i);

/** Get the raw byte value at index `i`. Returns -1 if out of bounds. */
MN_EXPORT int64_t __mn_str_byte_at(MnString s, int64_t i);

/** String length. */
MN_EXPORT int64_t __mn_str_len(MnString s);

/** String equality. Returns 1 if equal, 0 otherwise. */
MN_EXPORT int64_t __mn_str_eq(MnString a, MnString b);

/** String comparison (lexicographic). Returns <0, 0, or >0. */
MN_EXPORT int64_t __mn_str_cmp(MnString a, MnString b);

/** Substring from `start` (inclusive) to `end` (exclusive).
 *  Clamps to valid range. */
MN_EXPORT MnString __mn_str_substr(MnString s, int64_t start, int64_t end);

/** Returns 1 if `s` starts with `prefix`. */
MN_EXPORT int64_t __mn_str_starts_with(MnString s, MnString prefix);

/** Returns 1 if `s` ends with `suffix`. */
MN_EXPORT int64_t __mn_str_ends_with(MnString s, MnString suffix);

/** Find first occurrence of `needle` in `haystack`. Returns index or -1. */
MN_EXPORT int64_t __mn_str_find(MnString haystack, MnString needle);

/** Convert an i64 to its decimal string representation. */
MN_EXPORT MnString __mn_str_from_int(int64_t value);

/** Convert a double to its string representation. */
MN_EXPORT MnString __mn_str_from_float(double value);

/** Free a heap-allocated string. No-op for constant strings.
 *  Uses tag bit (LSB of data pointer) to distinguish heap from constant. */
MN_EXPORT void __mn_str_free(MnString s);

/** Print a string to stdout (no newline). */
MN_EXPORT void __mn_str_print(MnString s);

/** Print a string to stdout with newline. */
MN_EXPORT void __mn_str_println(MnString s);

/** Print a string to stderr with newline (for diagnostics). */
MN_EXPORT void __mn_str_eprintln(MnString s);

/* -----------------------------------------------------------------------
 * MnList — type-erased growable array
 *
 * LLVM layout: { i8*, i64, i64, i64 }
 *   - data:      pointer to heap-allocated element buffer
 *   - len:       number of elements
 *   - cap:       allocated capacity
 *   - elem_size: size of each element in bytes
 *
 * Elements are stored inline (memcpy'd). For pointer-sized elements
 * (strings, other lists), this stores them by value.
 * ----------------------------------------------------------------------- */

typedef struct {
    char   *data;
    int64_t len;
    int64_t cap;
    int64_t elem_size;
} MnList;

/** Create an empty list for elements of `elem_size` bytes. */
MN_EXPORT MnList __mn_list_new(int64_t elem_size);

/** Push an element (copied from `elem_ptr`) onto the end of the list. */
MN_EXPORT void __mn_list_push(MnList *list, const void *elem_ptr);

/** Get pointer to element at index `i`. Returns NULL if out of bounds. */
MN_EXPORT void *__mn_list_get(MnList *list, int64_t i);

/** Set element at index `i` (copied from `elem_ptr`). No-op if OOB. */
MN_EXPORT void __mn_list_set(MnList *list, int64_t i, const void *elem_ptr);

/** Number of elements. */
MN_EXPORT int64_t __mn_list_len(MnList *list);

/** Remove and return the last element. Caller provides buffer `out_ptr`.
 *  Returns 0 on success, -1 if empty. */
MN_EXPORT int64_t __mn_list_pop(MnList *list, void *out_ptr);

/** Clear the list (set len to 0, keep capacity). */
MN_EXPORT void __mn_list_clear(MnList *list);

/** Free the list's data buffer (does NOT free contained elements). */
MN_EXPORT void __mn_list_free(MnList *list);

/** Free a list of strings: frees each contained string, then the buffer. */
MN_EXPORT void __mn_list_free_strings(MnList *list);

/* -----------------------------------------------------------------------
 * Convenience: MnList of MnString
 * ----------------------------------------------------------------------- */

/** Create a new list of strings. */
MN_EXPORT MnList __mn_list_str_new(void);

/** Push a string onto a string list. */
MN_EXPORT void __mn_list_str_push(MnList *list, MnString s);

/** Get string at index `i`. Returns empty string if OOB. */
MN_EXPORT MnString __mn_list_str_get(MnList *list, int64_t i);

/* -----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------- */

/** Read an entire file into a string. Returns empty string on error.
 *  The `ok` flag is set to 1 on success, 0 on failure. */
MN_EXPORT MnString __mn_file_read(MnString path, int64_t *ok);

/** Write a string to a file. Returns 0 on success, -1 on error. */
MN_EXPORT int64_t __mn_file_write(MnString path, MnString content);

/* -----------------------------------------------------------------------
 * Memory
 * ----------------------------------------------------------------------- */

/** Allocate `size` bytes, zero-initialized. Aborts on failure. */
MN_EXPORT void *__mn_alloc(int64_t size);

/** Reallocate to `new_size` bytes. Aborts on failure. */
MN_EXPORT void *__mn_realloc(void *ptr, int64_t new_size);

/** Free memory. */
MN_EXPORT void __mn_free(void *ptr);

/* -----------------------------------------------------------------------
 * Arena Allocator
 *
 * Bump allocator for scope-local temporaries. All allocations are freed
 * in one shot when the arena is destroyed. Blocks are linked together
 * and grow as needed.
 * ----------------------------------------------------------------------- */

typedef struct MnArenaBlock {
    struct MnArenaBlock *next;
    int64_t size;
    int64_t used;
    /* Flexible array member: data follows the header. */
    char data[];
} MnArenaBlock;

typedef struct {
    MnArenaBlock *head;
    int64_t default_block_size;
} MnArena;

/** Create a new arena with the given default block size. */
MN_EXPORT MnArena *mn_arena_create(int64_t block_size);

/** Allocate `size` bytes from the arena (zero-initialized). */
MN_EXPORT void *mn_arena_alloc(MnArena *arena, int64_t size);

/** Destroy the arena, freeing all blocks. */
MN_EXPORT void mn_arena_destroy(MnArena *arena);

/* -----------------------------------------------------------------------
 * Agent-Scoped Arenas (Phase 2.1 integration point)
 *
 * Each agent owns an arena tied to its lifetime. When the agent is
 * stopped or destroyed, its arena is freed in one shot. The actual
 * wiring happens in Phase 2.1 (Native Agents).
 * ----------------------------------------------------------------------- */

/** Create an arena for an agent's lifetime. */
MN_EXPORT MnArena *mn_agent_arena_create(void);

/** Destroy an agent's arena (called on agent stop/destroy). */
MN_EXPORT void mn_agent_arena_destroy(MnArena *arena);

/* -----------------------------------------------------------------------
 * Process
 * ----------------------------------------------------------------------- */

/** Exit with status code. */
MN_EXPORT void __mn_exit(int64_t code);

/** Print an error and exit with code 1. */
MN_EXPORT void __mn_panic(MnString message);

#endif /* MAPANARE_CORE_H */
