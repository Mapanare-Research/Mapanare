# Master Prompt — Execute Roadmap v3.41.0 → v4.0.0

> Bridge the gap from "compiler works" to "language is usable."
> The compiler engineering is 9.76/10. The usability is 3/10. Fix that.
> Each version has its own PLAN.md with full instructions.
> Execute one at a time, verify, commit, then move to next.
> Read CLAUDE.md for project context.

---

## Instructions

You are executing the Mapanare usability roadmap from v3.41.0 through v4.0.0.
There are 5 versions to complete before the production release, each building
on the previous one.

**For each version N:**

1. Read `docs/roadmap/vN/PLAN.md` — it has the item breakdown and exit criteria
2. Execute all items in the plan, following its priority order
3. Run the verification/exit criteria from the plan
4. Run Culebra validation: `culebra scan` on new IR, `culebra abi` on ABI changes
5. Run `/bump-version` to bump to version N
6. Commit with message: `vN: <theme> — <one-line summary>`
7. Update `docs/roadmap/vN/PLAN.md` status to DONE
8. Move to version N+1

**Execution order (strict — each depends on the previous):**

| # | Version | Codename | Theme | Proof |
|---|---------|----------|-------|-------|
| 1 | v3.41.0 | Culebrita | IO Foundation | `read_line()` works, file I/O complete, `mapanare_io.c` linked |
| 2 | v3.42.0 | Cascabel | Network Native | HTTP GET fetches a URL from native binary, crypto/regex work |
| 3 | v3.43.0 | Mapanare | Agent Runtime | `spawn`/`send`/`sync` work with real OS threads in native |
| 4 | v3.44.0 | Cunaguaro | Real Examples | ALL examples compile+run, transpile .py/.php → native end-to-end |
| 5 | v3.45.0 | Turpial | Package Manager | `mapanare install` works, error recovery, docs match reality |

After all 5: tag v4.0.0.

**Dependencies:**

```
v3.40.0 (review cleanup) ── compiler engineering 9.76/10, zero CRITICAL/HIGH
    │
    ▼
v3.41.0 (IO foundation) ── link mapanare_io.c, add read_line(), fix file I/O
    │                       UNLOCKS: all IO functions available in native binaries
    ▼
v3.42.0 (network native) ── HTTP client, TCP/TLS, crypto, regex from native
    │                        UNLOCKS: programs that talk to the internet
    ▼
v3.43.0 (agent runtime) ── link mapanare_runtime.c, spawn/send/sync with threads
    │                       UNLOCKS: concurrent programs
    ▼
v3.44.0 (real examples) ── fix all examples, CLI demos, transpile end-to-end
    │                       UNLOCKS: someone can look at examples and learn
    ▼
v3.45.0 (package manager) ── install works, error recovery, docs updated
    │                         UNLOCKS: ecosystem, discoverability
    ▼
v4.0.0 (production) ── release tag, website update, blog post
                        THE BAR: a new user can install → write → compile → run
```

---

## Rules

- Do NOT skip versions or reorder them
- Do NOT start version N+1 until version N is committed and verified
- If an exit criteria fails, fix it before moving on
- Make decisions autonomously — do not ask for confirmation on implementation choices
- Commit at each milestone within a version (not just at the end)
- Use `/golden` after every compiler change
- Use `/rebuild` after every emitter change
- Use Culebra to verify IR quality after emitter changes
- Use ASan/TSan after C runtime changes
- Use `valgrind` after memory-related changes
- Every new golden test must also pass through mnc-stage1

---

## What must be true after each version

| Check | v3.41.0 | v3.42.0 | v3.43.0 | v3.44.0 | v3.45.0 |
|-------|---------|---------|---------|---------|---------|
| `mapanare_io.c` linked | YES | YES | YES | YES | YES |
| `read_line()` works | YES | YES | YES | YES | YES |
| File I/O complete (append, list_dir) | YES | YES | YES | YES | YES |
| IO functions declared in LLVM emitter | YES | YES | YES | YES | YES |
| HTTP GET works from native binary | — | YES | YES | YES | YES |
| Crypto (SHA-256, base64) works | — | YES | YES | YES | YES |
| Regex works (with PCRE2 fallback) | — | YES | YES | YES | YES |
| `mapanare_runtime.c` linked | — | — | YES | YES | YES |
| Agent spawn/send/sync native | — | — | YES | YES | YES |
| ALL examples compile and run | — | — | — | YES | YES |
| Transpile .py → .mn → native works | — | — | — | YES | YES |
| `mapanare install` works | — | — | — | — | YES |
| Multiple errors reported (not crash) | — | — | — | — | YES |
| Getting Started guide works e2e | — | — | — | — | YES |
| Fixed point maintained (stage4==stage3) | YES | YES | YES | YES | YES |
| Valgrind-clean 30+/N golden | YES | YES | YES | YES | YES |
| Culebra scan clean (zero critical) | YES | YES | YES | YES | YES |

---

## The real gap (audited at v3.40.0)

The compiler is 9.76/10. Here's why the language is 3/10 for usability:

| Layer | What exists | What's broken |
|-------|------------|---------------|
| `mapanare_core.c` (linked) | Strings, lists, maps, basic file I/O, signals, streams | `append_file` disabled, `list_dir` disabled (ABI issues) |
| `mapanare_io.c` (NOT linked) | TCP, TLS, crypto, regex, extended file I/O, event loop | Never compiled into native binaries |
| `mapanare_runtime.c` (NOT linked) | Agent scheduler, thread pool, ring buffers, backpressure | Agents only work in Python interpreter |
| `mapanare_gpu.c` (NOT linked) | CUDA/Vulkan loading | GPU annotations don't codegen (SPEC disclaimed) |
| Stdin | — | `read_line()` doesn't exist — can't build interactive programs |
| LLVM emitter | Declares ~80 mapanare_core.c functions | Doesn't declare ANY mapanare_io.c or runtime functions |
| Package manager | Parses mapanare.toml manifests | `install` is a no-op |
| Examples | 14 .mn files in examples/ | Most don't compile (depend on unlinked features) |
| Transpilers | Python + PHP → .mn works | Nobody tested transpile → compile → run end-to-end |

**The good news:** mapanare_io.c is 49KB of working C code. mapanare_runtime.c
is 1,343 lines of working C code. The code EXISTS — it needs to be linked,
declared in the emitter, and tested. v3.41.0 is the biggest unlock.

---

## Culebra commands to use throughout

```bash
# After every emitter change — check for IR regressions
culebra scan mapanare/self/main.ll
culebra triage mapanare/self/main.ll --brief
culebra health mapanare/self/main.ll

# After ABI changes — verify function signatures match C headers
culebra abi mapanare/self/main.ll --header runtime/native/mapanare_core.h

# After adding new runtime declarations
culebra scan mapanare/self/main.ll --tags abi
culebra verify mapanare/self/main.ll return-type-divergence

# When debugging crashes
culebra crashmap mapanare/self/main.ll --offset <addr>
culebra trace mapanare/self/main.ll --function <fn> --var '%state'
culebra wrap -- valgrind ./mapanare/self/mnc-stage1 tests/golden/34_file_io.mn

# Track progress across fixes
culebra baseline save mapanare/self/main.ll
culebra baseline diff mapanare/self/main.ll

# After each version — full summary
culebra summary mapanare/self/main.ll
```

---

## Current state (v3.40.0)

- Version: 3.40.0
- Branch: dev
- 33/33 golden tests pass, 30/33 valgrind-clean
- Fixed point: stage4 == stage3 (proven v3.38.0)
- Self-hosted compiler: 15,500+ lines across 11 modules
- 4,465+ pytest tests, 181 native C assertions
- 7 CI jobs: ci, self-hosted, bootstrap, native, wasm, android, macos
- Peak memory: 160 MB, binary: 2.7 MB, self-compile: 0.74s
- LLVM 17+ compliant: zero typed pointer sites
- Code review: 9.76/10 aggregate (7 reviewers, unanimous PASS)
- `mapanare_io.c`: 49KB, NOT linked — TCP, TLS, crypto, regex, extended file I/O
- `mapanare_runtime.c`: 1,343 lines, NOT linked — agents, thread pool, ring buffers
- `read_line()`: does not exist
- Package manager: scaffolding only
- Examples: mostly non-functional

## After all 5 versions are done

- Native binaries can read stdin, process files, fetch URLs, run agents
- ALL examples compile and run
- Transpile .py/.php → .mn → native binary works end-to-end
- `mapanare install` installs packages
- Error messages are helpful (multiple errors, suggestions)
- Getting Started guide works from install to running program
- Documentation matches reality
- Ready for v4.0.0 production release tag
- **A new user can build a real program.**
