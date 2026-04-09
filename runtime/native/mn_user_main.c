/**
 * mn_user_main.c — Entry shim for compiled Mapanare programs.
 *
 * The self-hosted compiler generates `define i32 @mn_main() { ... }`.
 * This wrapper provides the real main() that initializes the runtime
 * (argc/argv) before calling the user's mn_main.
 */

#include <stdint.h>

extern void __mn_argv_init(int argc, char **argv);
extern int32_t mn_main(void);

int main(int argc, char *argv[]) {
    __mn_argv_init(argc, argv);
    return mn_main();
}
