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

int main(int argc, char *argv[]) {
    signal(SIGSEGV, crash_handler);
    signal(SIGABRT, crash_handler);
    __mn_argv_init(argc, argv);
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    const char *filepath = argv[1];

    /* Read the source file */
    MnString path_str = __mn_str_from_cstr(filepath);
    int64_t ok = 0;
    MnString source = __mn_file_read(path_str, &ok);

    if (!ok) {
        fprintf(stderr, "error: cannot read file '%s'\n", filepath);
        return 1;
    }

    /* Compile */
    MnString filename_str = __mn_str_from_cstr(filepath);

    CompileResult result = compile(source, filename_str);

    if (result.success) {
        /* Print LLVM IR to stdout — untag heap-allocated string pointer (bit 0) */
        if (result.ir_text.len > 0) {
            const char *ir_data = (const char *)((uintptr_t)result.ir_text.data & ~(uintptr_t)1);
            fwrite(ir_data, 1, (size_t)result.ir_text.len, stdout);
            /* Ensure trailing newline */
            if (ir_data[result.ir_text.len - 1] != '\n') {
                putchar('\n');
            }
        }
        return 0;
    } else {
        /* Print errors to stderr */
        int64_t n_errors = result.errors.len;
        for (int64_t i = 0; i < n_errors; i++) {
            SemanticError *err = (SemanticError *)(result.errors.data +
                                                    i * result.errors.elem_size);
            MnString msg = format_error(*err);
            if (msg.len > 0) {
                const char *msg_data = (const char *)((uintptr_t)msg.data & ~(uintptr_t)1);
                fwrite(msg_data, 1, (size_t)msg.len, stderr);
            }
            fputc('\n', stderr);
        }
        return 1;
    }
}
