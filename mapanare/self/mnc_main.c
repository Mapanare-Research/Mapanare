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
#include <signal.h>
#ifndef _WIN32
#include <execinfo.h>
#include <unistd.h>
#include <pthread.h>
#endif

static void crash_handler(int sig) {
    fflush(stdout);
#ifndef _WIN32
    void *frames[64];
    int n = backtrace(frames, 64);
    fprintf(stderr, "\n[CRASH] Signal %d at:\n", sig);
    backtrace_symbols_fd(frames, n, 2);
    _exit(128 + sig);
#else
    fprintf(stderr, "\n[CRASH] Signal %d\n", sig);
    exit(128 + sig);
#endif
}

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

static void print_usage(const char *prog) {
    fprintf(stderr, "Usage: %s <file.mn>\n", prog);
    fprintf(stderr, "  Compiles a Mapanare source file and prints LLVM IR to stdout.\n");
}

extern void __mn_argv_init(int argc, char **argv);
extern void mn_main(void);

/* Stack size for compiler thread: 32 MB (self-compilation needs ~16 MB) */
#define MNC_STACK_SIZE (32 * 1024 * 1024)

#ifndef _WIN32
static void *compiler_thread(void *arg) {
    (void)arg;
    mn_main();
    return NULL;
}
#endif

int main(int argc, char *argv[]) {
    signal(SIGSEGV, crash_handler);
    signal(SIGABRT, crash_handler);
    __mn_argv_init(argc, argv);

    /* Run mn_main() on a thread with a larger stack so the compiler
     * can handle self-compilation (13K+ lines) without ulimit. */
#ifndef _WIN32
    pthread_t tid;
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setstacksize(&attr, MNC_STACK_SIZE);
    if (pthread_create(&tid, &attr, compiler_thread, NULL) == 0) {
        pthread_attr_destroy(&attr);
        pthread_join(tid, NULL);
    } else {
        /* Fallback: run on main thread if thread creation fails */
        pthread_attr_destroy(&attr);
        mn_main();
    }
#else
    mn_main();
#endif
    return 0;
}
