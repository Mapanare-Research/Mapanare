# Mapanare v3.4.0 — Native Stdlib & Module System

> The compiler works. Now make the language useful.

**Status:** IN PROGRESS — Phase 1+2 complete
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## The Goal

v3.3.0 proved the compiler can compile itself. v3.4.0 makes it
compile **real programs** — programs that import stdlib modules,
do file I/O, parse JSON, make HTTP requests.

37 stdlib `.mn` modules already exist (AI, databases, encoding,
HTTP, filesystem, crypto, etc.). They were written for the Python
compiler. This release makes them work with the self-hosted compiler.

---

## What Exists

| Category | Modules | Lines |
|----------|---------|-------|
| AI | llm, embedding, rag | ~3,500 |
| Database | sql, sqlite, postgres, redis, kv, embedded_kv, pool, migrate | ~4,000 |
| Encoding | json, csv, toml, yaml | ~3,500 |
| Network | http, http/server, http/auth, websocket, + 6 http sub-modules | ~5,000 |
| Core | fs, time, log, math, crypto, text, regex | ~3,000 |
| GPU | device, kernel, tensor | ~1,500 |
| WASM | bridge, runtime | ~500 |
| Packages | crawl (web crawler), scan (vuln scanner) | ~2,000 |

**Total: ~23,000 lines of `.mn` stdlib already written.**

---

## Attack Order

### Phase 1: Native Module Imports

The self-hosted compiler currently compiles a single concatenated
file (`mnc_all.mn`). Add `import` resolution so it can compile
multi-file programs.

**What to implement:**
- Parse `import` statements (parser already handles the syntax)
- File-based module resolution (`import stdlib::fs` → `stdlib/fs.mn`)
- Concatenate imported modules before lowering
- Symbol visibility (`pub` vs private)

**Note:** The Python compiler already does this via `multi_module.py`.
Port the logic to the self-hosted compiler's `main.mn`.

### Phase 2: Compile Stdlib Modules

Take the existing 37 stdlib modules and compile them through the
self-hosted compiler. Fix any issues:
- Missing builtins or C runtime functions
- Type inference gaps
- Syntax the self-hosted parser doesn't handle

Start with the simplest modules and work outward:
1. `stdlib/math.mn` (pure computation, no I/O)
2. `stdlib/fs.mn` (C runtime FFI for file I/O)
3. `stdlib/encoding/json.mn` (string processing)
4. `stdlib/net/http.mn` (TCP + TLS via C runtime)
5. `stdlib/ai/llm.mn` (HTTP + JSON composition)

### Phase 3: End-to-End Programs

Build and run real programs that use the stdlib:

```mapanare
import stdlib::fs
import stdlib::encoding::json

fn main() {
    let data: String = fs::read_file("config.json")
    let config: JsonValue = json::parse(data)
    print(json::get_string(config, "name"))
}
```

Verify: compile with `./mnc`, link with gcc, run the binary.

### Phase 4: Package Compilation

Compile the `crawl/` and `scan/` packages through the self-hosted
compiler. These are multi-module packages with cross-file imports.

---

## Success Criteria

- [x] Self-hosted compiler resolves `import` statements
- [x] `stdlib/math.mn` compiles through `./mnc` (42 functions, 16 extern C, llvm-as VALID)
- [x] `stdlib/fs.mn` compiles + links + runs (write, read, exists, remove, extension, stem)
- [ ] `stdlib/encoding/json.mn` — 33/28 functions compile, blocked by Map type (no map literals)
- [x] An end-to-end program using stdlib compiles and runs
- [ ] Build script compiles stdlib into a linkable library

---

## Non-Goals

- Replacing pytest/ruff/mypy with .mn equivalents (dev tools stay Python)
- WASM backend for stdlib (WASM still uses Python emitter)
- Package registry or dependency resolution (future)
