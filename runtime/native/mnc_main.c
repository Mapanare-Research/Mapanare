/* mnc_main.c — Entry point wrapper for the self-hosted Mapanare compiler.
 * Links with the compiler IR (stage2+) to produce an mnc binary.
 * The self-hosted compiler exposes compile_and_print(sret, source, filename).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mapanare_runtime.h"

/* Forward-declare the self-hosted compiler entry point.
 * Signature: void compile_and_print(CompileResult *sret, MnString source, MnString filename)
 * We don't need the CompileResult definition — just allocate enough space. */
typedef struct { char _pad[256]; } CompileResult;
extern void compile_and_print(CompileResult *__sret__, MnString source, MnString filename);

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: mnc <file.mn>\n"); return 1; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { fprintf(stderr, "error: cannot open %s\n", argv[1]); return 1; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = (char *)malloc(sz + 1);
    fread(buf, 1, sz, f);
    buf[sz] = 0;
    fclose(f);
    MnString source = __mn_str_from_cstr(buf);
    MnString filename = __mn_str_from_cstr(argv[1]);
    CompileResult cr = {0};
    compile_and_print(&cr, source, filename);
    free(buf);
    return 0;
}
