# v3.2.0 — Real Programs — Continuation Prompt

> Make the compiler handle real-world code. Read CLAUDE.md for project context.
> Track progress in `docs/roadmap/v3.2.0/PLAN.md`.
> Commit at each milestone. Make decisions autonomously.

## MANDATORY: Use Culebra for ALL debugging

```bash
~/.cargo/bin/culebra wrap -- gcc ...
~/.cargo/bin/culebra journal add "description" --action fix --tags "stdlib"
~/.cargo/bin/culebra journal show
```

---

## Goal

Expand from 15 toy tests to real programs: native file I/O, string escapes,
stderr errors, 25+ tests, and stdlib in .mn.

---

## Attack Order

### Phase 1: Native File I/O (CRITICAL PATH)

The compiler should read files itself, not through a C driver.

1. Add `__mn_file_read(MnString path) -> MnString` to mapanare_core.c
2. Add `__mn_argv(i64) -> MnString` and `__mn_argc() -> i64` to mapanare_core.c
3. Add extern declarations to main.mn
4. Implement `fn main()` in main.mn that reads file from argv and compiles
5. Remove mnc_driver.c dependency from the build chain

### Phase 2: String Escapes

1. Update `scan_string` in lexer.mn to process `\n`, `\t`, `\\`, `\"`
2. Update string constant emission in emit_llvm.mn to emit LLVM escape bytes
3. Add golden test `16_string_escape.mn`

### Phase 3: Stderr + Exit Codes

1. Add `__mn_eprint` / `__mn_eprintln` to C runtime
2. Update compiler to print errors to stderr
3. Return exit code 1 on compilation failure

### Phase 4: Expand Test Suite

Add golden tests 16-25 covering:
- String escapes, Option, method chains, modules
- Agents, signals, pipes, error propagation
- Lambdas, maps

### Phase 5: Stdlib in .mn

Port `string_utils.mn`, `io.mn` from Python to Mapanare.
Compile through stage1 and link with user programs.

---

## Key Files

| File | Role | Changes |
|------|------|---------|
| `runtime/native/mapanare_core.c` | C runtime | Add file_read, argv, eprint |
| `mapanare/self/main.mn` | Compiler driver | Add main() with file I/O |
| `mapanare/self/lexer.mn` | Lexer | String escape processing |
| `mapanare/self/emit_llvm.mn` | LLVM emitter | Escape bytes in string constants |
| `tests/golden/16_*.mn` — `25_*.mn` | New tests | 10 new golden programs |
| `stdlib/string_utils.mn` | Stdlib | Port from Python |

---

## Verification

```bash
bash scripts/rebuild.sh quick           # rebuild stage1
bash scripts/verify_fixed_point.sh      # fixed point
bash scripts/test_runtime.sh            # runtime (should handle 25+ tests)

# Test native file I/O
./mnc tests/golden/01_hello.mn > /tmp/test.ll  # no driver needed
llvm-as /tmp/test.ll -o /dev/null
```
