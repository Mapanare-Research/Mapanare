/**
 * mnc_main.c — Entry point for the Mapanare self-hosted compiler (mnc).
 *
 * Reads a .mn source file from argv[1], calls the self-hosted compiler's
 * compile() function, and prints the resulting LLVM IR or error messages.
 *
 * This file is linked with:
 *   - main.o (self-hosted compiler, compiled from main.ll)
 *   - mapanare_core.o (C runtime: strings, lists, file I/O)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifndef _WIN32
#include <pthread.h>
#endif

/* v4.105.0 Phase 4 — crash breadcrumbs.
 * The legacy handler (pre-v4.105.0) called fprintf() and backtrace() from
 * inside a signal handler, both async-signal-unsafe. Phase 3's TSan run
 * flagged this across 29 crashing tests. The replacement lives in the
 * runtime (runtime/native/mapanare_runtime.c) and is installed via
 * __mn_install_crash_handler(). It uses only write(2) and hand-rolled
 * formatters, then hands off to backtrace_symbols_fd (explicitly AS-safe
 * per signal-safety(7)). */
extern void __mn_install_crash_handler(void);
extern void __mn_set_current_source(const char *filename, int32_t line);
extern void __mn_set_current_phase(const char *phase);

/* -----------------------------------------------------------------------
 * ABI types — must match the LLVM IR layout exactly
 * ----------------------------------------------------------------------- */

typedef struct {
    const char *data;
    int64_t     len;
} MnString;

typedef struct {
    char   *data;
    int64_t len;
    int64_t cap;
    int64_t elem_size;
    int64_t managed;
} MnList;

/* SemanticError: { filename: String, line: Int, column: Int, message: String } */
typedef struct {
    MnString filename;
    int64_t  line;
    int64_t  column;
    MnString message;
} SemanticError;

/* CompileResult: { success: Bool, ir_text: String, errors: List<SemanticError> } */
typedef struct {
    int8_t   success;    /* i1 in LLVM — passed as i8 in C ABI */
    MnString ir_text;
    MnList   errors;
} CompileResult;

/* -----------------------------------------------------------------------
 * External: self-hosted compiler functions (from main.o)
 * ----------------------------------------------------------------------- */

extern CompileResult compile(MnString source, MnString filename);
extern MnString format_error(SemanticError err);

/* -----------------------------------------------------------------------
 * External: C runtime functions (from mapanare_core.o)
 * ----------------------------------------------------------------------- */

extern MnString __mn_file_read(MnString path, int64_t *ok);
extern MnString __mn_str_from_cstr(const char *cstr);
extern MnString __mn_str_concat(MnString a, MnString b);

/* Debug: call compile_and_print to see println output */
extern CompileResult compile_and_print(MnString source, MnString filename);

/* -----------------------------------------------------------------------
 * main
 * ----------------------------------------------------------------------- */

extern void __mn_argv_init(int argc, char **argv);
extern void mn_main(void);

/* Stack size for compiler thread: 32 MB (self-compilation needs ~16 MB) */
#define MNC_STACK_SIZE (32 * 1024 * 1024)

#ifndef _WIN32
/* Passed to compiler_thread so the breadcrumb lives on the same thread
 * as the crash. Thread-locals in main() do not cross to the worker. */
typedef struct {
    const char *source_path;
} compiler_thread_arg;

static void *compiler_thread(void *arg) {
    compiler_thread_arg *ca = (compiler_thread_arg *)arg;
    if (ca && ca->source_path) {
        __mn_set_current_source(ca->source_path, 0);
    }
    __mn_set_current_phase("compile");
    mn_main();
    __mn_set_current_phase("shutdown");
    return NULL;
}
#endif

int main(int argc, char *argv[]) {
    __mn_install_crash_handler();
    __mn_set_current_phase("startup");
    if (argc > 1) {
        /* argv[1] lives for the duration of the process, safe to stash. */
        __mn_set_current_source(argv[1], 0);
    }
    __mn_argv_init(argc, argv);
    __mn_set_current_phase("pre-compile");

    /* Run mn_main() on a thread with a larger stack so the compiler
     * can handle self-compilation (13K+ lines) without ulimit. */
#ifndef _WIN32
    compiler_thread_arg ca = { .source_path = (argc > 1) ? argv[1] : NULL };
    pthread_t tid;
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setstacksize(&attr, MNC_STACK_SIZE);
    if (pthread_create(&tid, &attr, compiler_thread, &ca) == 0) {
        pthread_attr_destroy(&attr);
        pthread_join(tid, NULL);
    } else {
        /* Fallback: run on main thread if thread creation fails.
         * Breadcrumb is already set on this thread from main() above. */
        pthread_attr_destroy(&attr);
        __mn_set_current_phase("compile");
        mn_main();
    }
#else
    mn_main();
#endif
    return 0;
}
