/*
 * mnc_driver.c — Entry point for the LLVM-compiled self-hosted compiler.
 * Links with stage2.o + mapanare_core.c to create mnc-stage2.
 *
 * Reads a .mn file from argv[1], creates MnString values, and calls
 * compile_and_print() which is defined in the compiler's LLVM IR.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* MnString = { ptr, i64 } = 16 bytes */
typedef struct { const char *ptr; int64_t len; } MnString;

/* CompileResult struct — must match the LLVM IR layout.
 * We don't inspect it; we just need stack space for the sret. */
typedef struct { char _opaque[256]; } CompileResult;

/* The self-hosted compiler's entry point (sret calling convention). */
extern void compile_and_print(CompileResult *__sret__,
                              MnString source, MnString filename);

/* Runtime helper to create MnString from C string. */
extern MnString __mn_str_from_cstr(const char *s);

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: mnc <file.mn>\n");
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        fprintf(stderr, "error: cannot open %s\n", argv[1]);
        return 1;
    }

    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);

    char *buf = malloc(sz + 1);
    fread(buf, 1, sz, f);
    buf[sz] = '\0';
    fclose(f);

    MnString source = __mn_str_from_cstr(buf);
    MnString filename = __mn_str_from_cstr(argv[1]);

    CompileResult result;
    compile_and_print(&result, source, filename);

    free(buf);
    return 0;
}
