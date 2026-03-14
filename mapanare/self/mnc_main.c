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

int main(int argc, char *argv[]) {
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

    /* Debug: check struct sizes and layout */
    fprintf(stderr, "[DEBUG] sizeof(MnString)=%zu sizeof(MnList)=%zu sizeof(CompileResult)=%zu\n",
            sizeof(MnString), sizeof(MnList), sizeof(CompileResult));
    fprintf(stderr, "[DEBUG] offsetof(success)=%zu offsetof(ir_text)=%zu offsetof(errors)=%zu\n",
            __builtin_offsetof(CompileResult, success),
            __builtin_offsetof(CompileResult, ir_text),
            __builtin_offsetof(CompileResult, errors));

    CompileResult result = compile(source, filename_str);

    /* Debug: dump raw bytes of CompileResult */
    {
        unsigned char *raw = (unsigned char *)&result;
        fprintf(stderr, "[DEBUG] CompileResult raw bytes (%zu bytes):\n", sizeof(result));
        for (size_t i = 0; i < sizeof(result); i++) {
            if (i % 16 == 0) fprintf(stderr, "  %04zx: ", i);
            fprintf(stderr, "%02x ", raw[i]);
            if (i % 16 == 15) fprintf(stderr, "\n");
        }
        fprintf(stderr, "\n");
    }
    /* Debug: dump CompileResult struct layout */
    fprintf(stderr, "[DEBUG] success=%d ir_text.data=%p ir_text.len=%ld\n",
            (int)result.success, (void*)result.ir_text.data, (long)result.ir_text.len);
    fprintf(stderr, "[DEBUG] errors.data=%p errors.len=%ld errors.cap=%ld errors.elem_size=%ld\n",
            (void*)result.errors.data, (long)result.errors.len,
            (long)result.errors.cap, (long)result.errors.elem_size);
    if (result.ir_text.len > 0 && result.ir_text.data) {
        fprintf(stderr, "[DEBUG] ir_text first 64 bytes (hex):");
        int64_t show = result.ir_text.len < 64 ? result.ir_text.len : 64;
        for (int64_t i = 0; i < show; i++) {
            if (i % 16 == 0) fprintf(stderr, "\n  ");
            fprintf(stderr, "%02x ", (unsigned char)result.ir_text.data[i]);
        }
        fprintf(stderr, "\n");
    }

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
