# Mapanare v3.35.0 — "Báquiro" (Incremental Compilation)

> Make rebuilds fast. Only recompile what changed. Hash-based module caching,
> parallel module compilation, precompiled imports. Target: <2s rebuild on
> 20K-line codebase after single-file change.

**Status:** DONE
**Estimated scope:** Large (3-4 sessions)
**Breaking:** No
**Prerequisite:** v3.34.0

---

## Motivation

v3.34.0 made single-file compilation fast (<100ms). But building a project with
20+ modules still recompiles everything from scratch. Changing one line in
`lexer.mn` triggers a full 5-15s rebuild of all 11 modules. That's the difference
between "snappy" and "I'll go make coffee."

This version adds incremental compilation: hash each module's source, cache its
MIR/IR output, only recompile modules whose source (or dependencies) changed.

---

## Items

### 1. Module Dependency Graph [HIGH]

**File:** `mapanare/self/main.mn` (or new `mapanare/self/deps.mn`)

Build a dependency graph from `import` statements:
```
main.mn → emit_llvm.mn → mir.mn → ast.mn
        → parser.mn → lexer.mn → ast.mn
        → semantic.mn → ast.mn
        → lower.mn → mir.mn, ast.mn
```

When `lexer.mn` changes, only recompile: lexer → parser → main.
Don't touch: mir, lower, emit_llvm, semantic (unless they import lexer).

### 2. Source Hashing + Cache [HIGH]

**Files:** `mapanare/self/main.mn`, new cache directory `.mnc_cache/`

For each module:
1. Hash the source file (SHA-256)
2. Check `.mnc_cache/<module>.<hash>.ll` exists
3. If yes and all dependencies unchanged → skip compilation, use cached IR
4. If no → compile, write IR to cache

Cache layout:
```
.mnc_cache/
    lexer.a1b2c3.ll       # cached LLVM IR for lexer.mn
    parser.d4e5f6.ll       # cached LLVM IR for parser.mn
    manifest.json          # source hashes + dependency edges
```

### 3. Parallel Module Compilation [HIGH]

**File:** `mapanare/self/main.mn`

Modules without dependencies on each other can compile in parallel.
From the dependency graph:
```
Level 0 (parallel): ast.mn, lexer.mn
Level 1 (parallel): parser.mn, mir.mn, semantic.mn
Level 2 (parallel): lower.mn, lower_state.mn
Level 3: emit_llvm.mn, emit_llvm_ir.mn
Level 4: main.mn
```

Use the C runtime thread pool (`__mn_thread_pool_*`) for parallel compilation.
Each thread: parse → lower → emit IR for one module.

### 4. Precompiled Module Headers [MEDIUM]

**File:** `mapanare/self/main.mn`

When module A imports module B, A needs B's type signatures (function types,
struct layouts, trait definitions) but not B's function bodies.

Generate `.mni` (Mapanare Interface) files — just the public signatures:
```
// lexer.mni — auto-generated
struct Token { kind: Int, value: String, line: Int, col: Int }
fn tokenize(source: String) -> List<Token>
fn token_kind_name(kind: Int) -> String
```

Reading a `.mni` is instant vs re-parsing the full module.

### 5. Incremental Linking [MEDIUM]

**Files:** `mapanare/self/main.mn`, build scripts

Compile each module to a separate `.o` file, then link once:
```
mnc build myproject/ →
    .mnc_cache/lexer.o    (cached, skip)
    .mnc_cache/parser.o   (changed, recompile)
    .mnc_cache/semantic.o (cached, skip)
    ...
    → link all .o → binary
```

Only the changed module gets recompiled. The link step is fast (<100ms).

### 6. `--watch` Mode [LOW]

**File:** `mapanare/self/main.mn`

```
mnc build --watch myproject/
```

Watch for file changes, incrementally rebuild on save. Using OS file
watchers (inotify on Linux, ReadDirectoryChangesW on Windows).

### 7. Build Timing Report [LOW]

**File:** `mapanare/self/main.mn`

```
mnc build myproject/ --timing

  lexer.mn      [cached]     0ms
  parser.mn     [compiled]  45ms
  semantic.mn   [cached]     0ms
  lower.mn      [cached]     0ms
  emit_llvm.mn  [cached]     0ms
  link                      38ms
  ─────────────────────────────
  total                     83ms  (4/5 modules cached)
```

### 8. Cache Management [LOW]

```
mnc cache stats              # show cache size, hit rate
mnc cache clean              # clear all cached artifacts
mnc cache clean --older 7d   # clear artifacts older than 7 days
```

---

## Verification

- [ ] Change one line in `lexer.mn`, rebuild: only lexer + dependents recompile
- [ ] Full clean build of 11-module compiler: <15s
- [ ] Incremental rebuild after single-file change: <2s
- [ ] Parallel compilation uses multiple cores (verify with `--timing`)
- [ ] `.mni` files generated and used correctly
- [ ] Cache invalidation works: change a struct in `ast.mn`, all dependents rebuild
- [ ] `--watch` mode detects changes and rebuilds
- [ ] `/golden` — all pass
- [ ] No correctness regressions from caching (hash collision = rebuild, not stale)
