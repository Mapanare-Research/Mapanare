# Mapanare v4.0.0 — Production Release

> This is "other people can use it."
> Not "the compiler compiles itself" — that's done.
> This is "you can build a CLI tool, a file processor, an HTTP client."

**Status:** PLANNED
**Breaking:** No (API stable from v3.x)
**Prerequisite versions:** v3.41.0 → v3.45.0

---

## What v4.0.0 ACTUALLY Means

v4.0.0 is when someone who isn't the compiler author can:

1. **Write a CLI program** that reads stdin, processes files, and writes output
2. **Fetch data over HTTP** from a native binary
3. **Transpile a .py or .php file** to Mapanare and run it natively
4. **Install a package** and use it in their project
5. **Get useful error messages** when something goes wrong

If you can't do ALL of these things, it's not v4.0.0.

---

## The Real Gap (audited v3.40.0)

The compiler engineering is 9.76/10. The usability is 3/10. Here's why:

| Layer | Status | Problem |
|-------|--------|---------|
| **mapanare_core.c** | Linked, works | Strings, lists, maps, file read/write, signals, streams all functional |
| **mapanare_io.c** | Written, NOT linked | TCP, TLS, regex, crypto, extended file I/O — all exist but never compiled into native binaries |
| **mapanare_runtime.c** | Written, NOT linked | Agent scheduler, thread pool, backpressure — all exist but not available natively |
| **mapanare_gpu.c** | Written, NOT linked | CUDA/Vulkan loading — exists but GPU annotations don't codegen |
| **stdin / read_line** | MISSING | No function to read user input — can't build interactive programs |
| **append_file / list_dir** | Disabled | Raw pointer ABI issues prevent these from working natively |
| **LLVM emitter** | Partial declarations | Only declares mapanare_core.c functions; IO/runtime functions not declared |
| **Package manager** | Scaffolding only | `install` command parses manifests but does nothing |
| **Examples** | Mostly fake | GPU/mobile/HTTP examples don't compile or run |

---

## Path to v4.0.0

### v3.41.0 — "Culebrita" (IO Foundation)

> Wire the existing C runtime into native binaries. Most of this code is ALREADY
> WRITTEN — it just needs to be linked and declared in the LLVM emitter.

**Build system:**
- [ ] Link `mapanare_io.c` into native builds (`scripts/build_stage1.py`)
- [ ] Add `mapanare_io.o` to the linker step alongside `mapanare_core.o`
- [ ] Verify with `nm` that all `__mn_tcp_*`, `__mn_tls_*`, `__mn_file_*` symbols are available
- [ ] Update CI native job to compile `mapanare_io.c` with ASan + TSan

**Stdin / read_line:**
- [ ] Add `__mn_read_line()` to `mapanare_core.c` — returns `MnString` from stdin via `fgets`
- [ ] Add `__mn_read_line` to `mapanare_core.h` exports
- [ ] Register `read_line` as a builtin in `types.py` and `semantic.py`
- [ ] Emit `read_line()` calls in `emit_llvm_text.py`
- [ ] Self-hosted: add `read_line` to `emit_llvm.mn` runtime declarations

**Fix disabled file I/O:**
- [ ] Fix `append_file` in `stdlib/fs.mn` — use `__mn_file_write` with append flag or add `__mn_file_append` to C runtime
- [ ] Fix `list_dir` — add `__mn_dir_list_strings` returning `MnList` of `MnString` (no raw pointer ABI needed)
- [ ] Enable `walk` built on top of working `list_dir`

**LLVM emitter declarations:**
- [ ] Declare all `__mn_tcp_*` functions in `_RUNTIME_FN_ATTRS` and `_declare_runtime_fns`
- [ ] Declare all `__mn_tls_*` functions
- [ ] Declare all `__mn_file_open`, `__mn_file_close`, `__mn_dir_list_strings`
- [ ] Declare all `__mn_sha*`, `__mn_hmac*`, `__mn_hex*`, `__mn_base64*`
- [ ] Declare all `__mn_regex_*` functions

**Golden tests (add 3):**
- [ ] `34_file_io.mn` — read file, write file, append file, list directory, check exists
- [ ] `35_stdin.mn` — read_line from stdin, process input, print output
- [ ] `36_string_advanced.mn` — split, join, replace, trim, upper/lower on real data

**Culebra validation:**
- [ ] `culebra scan` on new IR — zero critical findings
- [ ] `culebra abi` check — verify IO function signatures match C headers

**Exit criteria:** `mnc run` compiles and runs a program that reads a file, processes it, writes output. `read_line()` works.

---

### v3.42.0 — "Cascabel" (Network Native)

> HTTP client works from a native binary. You can fetch a URL and parse the response.

**Network in native:**
- [ ] TCP connect + send + recv work from native binary (already in mapanare_io.c)
- [ ] TLS handshake works (OpenSSL via dlopen — already in mapanare_io.c)
- [ ] Add `__mn_http_get_str(url)` convenience function to C runtime — wraps TCP connect + TLS + HTTP/1.1 GET + response parsing
- [ ] Register `http_get` as a builtin or stdlib function

**stdlib/net verified:**
- [ ] `stdlib/net/http.mn` — `get(url)`, `post(url, body)` work natively via extern C calls
- [ ] `stdlib/net/tcp.mn` — `connect(host, port)`, `send(data)`, `recv()` work natively
- [ ] At least `http_get("https://httpbin.org/get")` returns a response string

**Crypto in native:**
- [ ] SHA-256, HMAC-SHA256, base64 encode/decode all callable from `.mn` code
- [ ] `stdlib/crypto.mn` verified with golden test

**Regex in native:**
- [ ] `regex_match`, `regex_replace` work from `.mn` code via PCRE2 dlopen
- [ ] Graceful fallback when PCRE2 not available

**Golden tests (add 3):**
- [ ] `37_tcp_echo.mn` — connect to a local echo server, send message, receive response
- [ ] `38_crypto.mn` — SHA-256 hash a string, base64 encode/decode, HMAC
- [ ] `39_regex.mn` — match patterns, extract groups, replace

**Culebra validation:**
- [ ] `culebra scan` — zero critical on all new IR
- [ ] `culebra abi` — verify all IO function signatures

**Exit criteria:** A native binary can fetch data from the internet.

---

### v3.43.0 — "Mapanare" (Agent Runtime Native)

> Agents work from native binaries. spawn, send, sync with real threads.

**Link agent runtime:**
- [ ] Link `mapanare_runtime.c` into native builds
- [ ] Declare all `__mn_agent_*`, `__mn_ring_*`, `__mn_threadpool_*` in LLVM emitter
- [ ] Agent spawn/send/sync generates correct IR that links against C runtime

**Agent golden tests (add 3):**
- [ ] `40_agent_basic.mn` — spawn agent, send message, sync response
- [ ] `41_agent_pipeline.mn` — 3-stage pipeline: parse → validate → transform
- [ ] `42_agent_concurrent.mn` — spawn multiple agents, fan-out/fan-in pattern

**Culebra validation:**
- [ ] Full `culebra scan` on agent IR — check for race conditions, use-after-free patterns
- [ ] `culebra triage` — zero critical findings

**Exit criteria:** `spawn`, `<-`, `sync` work in a native binary with real OS threads.

---

### v3.44.0 — "Cunaguaro" (Real Examples)

> Every example in the repo compiles and runs. Transpilation works end-to-end.

**Fix ALL examples:**
- [ ] `examples/` — every `.mn` file compiles with `mnc emit-llvm` without errors
- [ ] Remove or fix examples that depend on unimplemented features (GPU tensor dispatch)
- [ ] Add `examples/cli/` — at least 3 real CLI programs:
  - [ ] `calculator.mn` — read expressions from stdin, evaluate, print result
  - [ ] `file_search.mn` — recursively search files for a pattern (like mini-grep)
  - [ ] `word_count.mn` — read file, count words/lines/chars (like wc)
- [ ] Add `examples/network/` — at least 2 real network programs:
  - [ ] `http_fetch.mn` — fetch a URL and print the response body
  - [ ] `url_checker.mn` — read URLs from file, check each one is alive

**Transpilation end-to-end:**
- [ ] `mapanare transpile examples/transpile/fibonacci.py` → produces valid `.mn`
- [ ] `mnc run` on the transpiled `.mn` → prints correct Fibonacci output
- [ ] `mapanare transpile examples/transpile/hello.php` → valid `.mn` → runs
- [ ] Add `examples/transpile/` directory with:
  - [ ] `fibonacci.py` — simple recursive Fibonacci in Python
  - [ ] `hello.php` — PHP hello world with basic control flow
  - [ ] `data_transform.py` — list processing with map/filter
  - [ ] `README.md` — instructions: "run `mapanare transpile file.py` then `mnc run file.mn`"

**Self-hosted transpiler testing:**
- [ ] Verify `from_python.mn`, `from_php.mn` produce same output as Python-side transpilers
- [ ] Add golden test that transpiles + compiles + validates IR

**Culebra validation:**
- [ ] `culebra scan` on ALL example IR outputs
- [ ] `culebra summary` — all examples score "healthy"

**Exit criteria:** A new user can clone the repo, look at examples, and run them ALL.

---

### v3.45.0 — "Turpial" (Package Manager + Polish)

> `mapanare install` works. Error messages are helpful. Documentation is current.

**Package manager:**
- [ ] `mapanare install <path>` — install a local package (copy to `.mapanare/packages/`)
- [ ] `mapanare install <git-url>` — clone and install a package from git
- [ ] `import pkg_name` resolves installed packages
- [ ] `mapanare.toml` manifest: `[dependencies]` section with local path and git URL support
- [ ] At least 3 example packages that install and work:
  - [ ] `mn_collections` — extra data structures (stack, queue, deque)
  - [ ] `mn_json` — JSON parser (pure Mapanare)
  - [ ] `mn_text` — text processing utilities

**Error recovery:**
- [ ] Compiler reports multiple errors instead of crashing on first error
- [ ] Missing import gives "did you mean?" suggestion
- [ ] Type mismatch shows expected vs actual with source location
- [ ] Audit all `panic()` / `abort()` in the compiler — replace with diagnostic errors

**Documentation:**
- [ ] `docs/getting-started.md` works end-to-end: install → write → compile → run
- [ ] README reflects reality (updated stats, working examples, honest feature matrix)
- [ ] Website updated with v4.0.0 content
- [ ] All SPEC disclaimers current (tensor §3.10, batch §10.5, GPU §23)

**Culebra full audit:**
- [ ] `culebra scan` on all golden tests, examples, and stdlib — zero critical
- [ ] `culebra triage --brief` — clean report
- [ ] `culebra summary` on main.ll — healthy

**Exit criteria:** Someone reads the docs, installs Mapanare, writes a program, and it works.

---

## v4.0.0 — Production Release

**Precondition:** v3.41.0 through v3.45.0 ALL complete.

### Release checklist:

- [ ] ALL examples compile and run
- [ ] ALL golden tests pass (target: 42+)
- [ ] Fixed point maintained (stage4 == stage3)
- [ ] Valgrind-clean on golden tests (target: 35+/42)
- [ ] 7-reviewer code review: target 9.5+/10
- [ ] `culebra scan` clean on all targets
- [ ] `read_line()`, file I/O, HTTP client, agents all work natively
- [ ] Transpile Python/PHP → Mapanare → native binary works end-to-end
- [ ] `mapanare install` installs packages
- [ ] Getting Started guide works end-to-end
- [ ] Version badge: 4.0.0
- [ ] Website updated
- [ ] Blog post: "Mapanare v4.0.0 — Build Real Programs"
- [ ] Git tag: v4.0.0

### The bar:

**A developer who has never seen Mapanare can:**
1. Install it (`curl -fsSL https://mapanare.dev/install | bash`)
2. Write a program that reads input, processes data, writes output
3. Fetch data from the internet
4. Use agents for concurrency
5. Install a package
6. Get helpful error messages when something breaks
7. Transpile an existing Python script and run it natively

**If ANY of these don't work, it's not v4.0.0.**

---

## Non-Goals for v4.0.0

Deferred to v4.1+:
- GPU tensor dispatch (codegen not connected — SPEC disclaimed)
- Database drivers (need real implementation, not type stubs)
- Full async/await
- LSP improvements
- Mobile deployment
- WASM runtime in browser playground
- TypeScript/Go transpilers in Python CLI (self-hosted only)
- Trait objects / dynamic dispatch
- Higher-kinded types / const generics
- Associated types

---

## Version History → v4.0.0

| Version | Theme | Key Deliverables |
|---------|-------|------------------|
| v3.38.0 | Fixed Point | stage4 == stage3 proven, seed updated |
| v3.39.0 | Valgrind Clean | 30/33 golden, 160 MB peak, memory profiling |
| v3.40.0 | Review Cleanup | SPEC disclaimers, typed pointers, trim fix, version auto-read |
| v3.41.0 | IO Foundation | Link mapanare_io.c, stdin, fix file I/O, declare IO functions |
| v3.42.0 | Network Native | TCP/TLS/HTTP/crypto/regex work from native binaries |
| v3.43.0 | Agent Runtime | spawn/send/sync with real threads in native |
| v3.44.0 | Real Examples | ALL examples run, transpile .py/.php end-to-end, CLI demos |
| v3.45.0 | Package Manager | install works, error recovery, docs updated |
| **v4.0.0** | **Production** | **Build real programs. Not fake. Not scaffolding. Real.** |
