# Mapanare v0.2.0 — "Self-Hosting"

> v0.1.0 proved the language works. v0.2.0 begins writing the compiler in Mapanare itself.
>
> Core theme: **Self-hosted compiler modules, LLVM codegen improvements, C runtime.**

---

## Scope

1. **LLVM string/list codegen** — native string operations and list manipulation
2. **C runtime foundation** — lock-free ring buffers, thread pool with work stealing
3. **Self-hosted compiler** — write lexer, parser, semantic checker, and emitter in `.mn`
4. **Builtin functions** — `str`, `int`, `float` conversion builtins on LLVM backend
5. **While loops and maps** — grammar + AST + Python emitter for remaining constructs
6. **REPL** — interactive mode for quick experimentation

---

## What Shipped

### LLVM Backend Improvements

- String codegen: `__mn_str_concat`, `__mn_str_eq`, `__mn_str_len`, `__mn_str_slice`, `__mn_str_index`
- List codegen: `__mn_list_new`, `__mn_list_push`, `__mn_list_get`, `__mn_list_set`, `__mn_list_len`
- `str()`, `int()`, `float()` builtin functions on LLVM backend
- Implicit top-level statements (no `fn main()` required for scripts)

### C Runtime (`runtime/native/`)

- Lock-free SPSC ring buffers for agent message passing
- Thread pool with work stealing for parallel agent execution
- Core header: `mapanare_core.h` with memory, string, list, agent primitives

### Self-Hosted Compiler (`mapanare/self/`)

- `lexer.mn` (~500 lines) — character-by-character tokenizer
- `parser.mn` (~850 lines) — recursive descent, 13-level precedence climbing
- `semantic.mn` (~800 lines) — two-pass type checker with scope resolution
- `emit_llvm.mn` (~600 lines) — LLVM IR string emitter
- Total: ~5,800 lines of Mapanare compiler in Mapanare

### Grammar & Language

- `while` loops added to grammar, AST, and Python emitter
- Map/Dict literal syntax (`#{key: value}`) in grammar and AST

---

## Success Criteria (met)

1. Self-hosted lexer tokenizes all valid `.mn` files correctly
2. Self-hosted parser produces matching AST for test programs
3. LLVM backend handles string and list operations natively
4. C runtime ring buffers pass stress tests
5. `str()`, `int()`, `float()` work on LLVM backend

---

*"A language that can describe its own compiler is no longer just an experiment."*
