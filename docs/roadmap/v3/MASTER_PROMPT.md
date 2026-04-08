# Master Prompt — Execute Roadmap v3.46.0 → v4.0.0

> Bridge the gap from "language is usable" to "GPU works and it ships."
> The usability arc (v3.41–v3.45) scored 9.69/10. The GPU runtime is built but not linked.
> The 4090 is sitting right there. Wire it up, fix the review items, ship v4.0.0.
> Each version has its own PLAN.md with full instructions.
> Execute one at a time, verify, commit, then move to next.
> Read CLAUDE.md for project context.

---

## Instructions

You are executing the Mapanare GPU + production roadmap from v3.46.0 through v4.0.0.
There are 2 versions to complete before the production release tag, each building
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
| 1 | v3.46.0 | Caimán | GPU Foundation | `gpu_available()` returns true, `gpu_tensor_add()` runs on 4090 |
| 2 | v3.47.0 | Guacamaya | GPU Examples + v4.0.0 Gate | Real GPU examples, SPEC S23 honest, all review items fixed |

After both: tag v4.0.0.

**Dependencies:**

```
v3.45.0 (package manager) ── 9.69/10 review, 5 hard blockers, GPU runtime unlinked
    │
    ▼
v3.46.0 (GPU foundation) ── link mapanare_gpu.c, add gpu_* builtins, fix review blockers
    │                        UNLOCKS: GPU tensor math from Mapanare code on the 4090
    │                        FIXES: SPEC S23, random_bytes, HMODULE leak, tar filter,
    │                               test_examples, -Werror all C files, version strings
    ▼
v3.47.0 (GPU examples + gate) ── real GPU programs, SPEC rewrite, ABI fixes, polish
    │                              UNLOCKS: SPEC Section 23 shows code that compiles
    │                              FIXES: self-hosted emitter ABI (regex, file_exists,
    │                                     str(false)), thread-safe dlopen, intern lock,
    │                                     concat early return, dedup, golden refs
    ▼
v4.0.0 (production) ── release tag
                        THE BAR: GPU works, every review item addressed,
                        a new user can install → write → compile → run
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
- GPU golden tests must handle no-GPU gracefully (CI has no GPU)
- Test GPU builtins on the 4090 in WSL before committing

---

## What must be true after each version

| Check | v3.46.0 | v3.47.0 |
|-------|---------|---------|
| Everything from v3.45.0 (IO, network, agents, examples, pkg mgr) | YES | YES |
| `mapanare_gpu.c` linked into mnc-stage1 | YES | YES |
| `gpu_available()` returns true on 4090 | YES | YES |
| `gpu_device_name()` returns "NVIDIA GeForce RTX 4090" | YES | YES |
| `gpu_tensor_add/sub/mul/div` produce correct results on GPU | YES | YES |
| `gpu_tensor_matmul` produces correct results on GPU | YES | YES |
| GPU builtins degrade to CPU when no GPU available | YES | YES |
| Golden tests 39-40 pass (bootstrap + stage1) | YES | YES |
| CI passes (GPU tests skip gracefully) | YES | YES |
| SPEC S23 has honest status note | YES | YES |
| `random_bytes` no longer falls back to `rand()` | YES | YES |
| HMODULE leak fixed (bcrypt.dll cached) | YES | YES |
| `tar.extractall(filter='data')` in pkg manager | YES | YES |
| `test_examples.py` includes all example dirs | YES | YES |
| `-Werror` on ALL C files in build_stage1.py | YES | YES |
| Real GPU examples in `examples/gpu/` | — | YES |
| SPEC S23 code example actually compiles | — | YES |
| Self-hosted emitter: regex ABI fixed | — | YES |
| Self-hosted emitter: `file_exists` i64 return | — | YES |
| Self-hosted emitter: `str(false)` zext fixed | — | YES |
| Self-hosted emitter: GPU builtins wired | — | YES |
| Thread-safe dlopen loaders (pthread_once) | — | YES |
| `intern_ensure_table()` inside lock | — | YES |
| `__mn_str_concat` early return for empty operands | — | YES |
| `mnstr_to_cstr` / `MnHandleTable` deduplicated | — | YES |
| `__mn_http_get` 64 MB response limit | — | YES |
| All version strings updated (main.mn, refs, docs) | — | YES |
| Golden refs re-blessed | — | YES |
| mnc-stage1 rebuilt with current version | — | YES |
| Fixed point maintained (stage4==stage3) | YES | YES |
| Valgrind-clean 30+/N golden | YES | YES |
| Culebra scan clean (zero critical) | YES | YES |

---

## The GPU gap (audited at v3.45.0)

The v3.41–v3.45 usability arc crossed the chasm — real programs compile and run.
The v3.45.0 review (9.69/10, 7 reviewers, all PASS) identified:

| Layer | What exists | What's not wired |
|-------|------------|------------------|
| `mapanare_gpu.c` (NOT linked) | 1,938 lines: CUDA Driver API via dlopen, PTX kernels for tensor add/sub/mul/div/matmul, Vulkan compute pipeline, GPU memory management | Never compiled into native binaries |
| `mapanare_gpu.h` (complete) | 28 exported functions, mn_gpu_ctx_t, buffer/kernel/pipeline structs | Not declared in LLVM emitter |
| CUDA driver in WSL | `libcuda.so` at `/usr/lib/wsl/lib/`, NVIDIA 591.86, CUDA 13.1 | `mapanare_gpu.c` does `dlopen("libcuda.so")` — just needs linking |
| `emit_llvm_mir.py` (deprecated) | Full GPU dispatch: @gpu/@cuda/@vulkan detection, PTX embedding, kernel launch | This is the DEPRECATED emitter — not the shipping one |
| `emit_llvm_text.py` (shipping) | Zero GPU code | Needs gpu_* builtin dispatch (same pattern as http_get, sha256, etc.) |
| `lower.py:959` | `raise NotImplementedError` on @gpu decorators | Blocks @gpu syntax — but builtins bypass this entirely |
| SPEC Section 23 | "Mapanare supports GPU-accelerated computation as a first-class feature" with non-functional code examples | The ONLY remaining P0 from v3.40.0 review — 3 cycles unfixed |
| GPU tests | 1,600+ lines across 3 test files | Test the infrastructure, not actual GPU execution |
| GPU examples | 3 examples in `examples/experimental/gpu/` using @gpu decorators | Don't compile (decorators raise NotImplementedError) |

**The approach:** Same as v3.41.0. The code EXISTS — link it, add builtins,
wire the emitter, add golden tests. Builtins (`gpu_tensor_add()`) bypass the
`@gpu` decorator path entirely — no changes to `lower.py` needed.

**Hardware available:** NVIDIA GeForce RTX 4090, 24GB VRAM, visible in WSL2.

---

## v3.45.0 Review — All action items mapped to versions

The v3.45.0 code review (9.69/10 aggregate, 7 reviewers) produced 28 action items.
Every item is assigned to either v3.46.0 or v3.47.0:

### Hard Blockers → v3.46.0

| # | Item | Effort | Reviewer |
|---|------|--------|----------|
| 1 | SPEC S23 GPU disclaimer (add honest status note) | 30 sec | Coral, Cobra, Boa |
| 2 | `random_bytes` — return empty when BCrypt unavailable | 2 lines | Viper |
| 3 | `__mn_random_bytes_str` — cache bcrypt.dll HMODULE | 15 lines | Mamba, Viper |
| 4 | `tar.extractall(filter='data')` | 1 line | Boa |
| 5 | `test_examples.py` — add cli/network/transpile dirs | 1 line | Boa |

### Build Hygiene → v3.46.0

| # | Item | Effort | Reviewer |
|---|------|--------|----------|
| 6 | `-Werror` on all C files in build_stage1.py | 1 line | Cobra, Anaconda |
| 7 | Dead conditional build_stage1.py:76 | 1 line | Anaconda |
| 8 | `obj_path` in cleanup loop | 1 word | Anaconda |
| 9 | `main.mn:31` version string | 1 line | Anaconda, Rattler, Coral |
| 10 | `emit_c.py:1` docstring version | 1 line | Cobra |

### Self-Hosted Emitter ABI → v3.47.0

| # | Item | Effort | Reviewer |
|---|------|--------|----------|
| 11 | `str(false)` i1→i64 zext | 5 lines .mn | Rattler |
| 12 | `file_exists` i1→i64 return type | 5 lines .mn | Viper, Rattler |
| 13 | Regex phantom symbols → compile+exec+free | ~30 lines .mn | Viper, Rattler |
| 14 | 9 missing I/O builtin declarations | 9 lines .mn | Rattler |

### Runtime Fixes → v3.47.0

| # | Item | Effort | Reviewer |
|---|------|--------|----------|
| 15 | Thread-safe dlopen (pthread_once) | 30 lines | Cobra, Viper |
| 16 | `__mn_http_get` 64 MB response limit | 3 lines | Viper |
| 17 | `intern_ensure_table()` inside lock | 2 lines | Mamba |
| 18 | `__mn_str_concat` early return empty | 2 lines | Mamba |
| 19 | `mnstr_to_cstr` dedup to shared header | 1 header | Mamba |
| 20 | `MnHandleTable` dedup to shared header | same header | Mamba |

### Version/Doc Cleanup → v3.47.0

| # | Item | Effort | Reviewer |
|---|------|--------|----------|
| 21 | `reference.md` version 0.5.0 → current | 1 line | Coral |
| 22 | `cookbook.md` example version 3.20.0 | 1 line | Coral |
| 23 | Re-bless golden refs (still at v3.14.0) | 30 sec | Rattler |
| 24 | Rebuild main.ll + mnc-stage1 | 1 min | Rattler |
| 25 | SPEC S1 "ML-ready" caveat | 1 word | Coral |

### Deferred to v4.1 (not blocking v4.0.0)

| # | Item | Reviewer |
|---|------|----------|
| 26 | Drop glue for struct-returning functions | Viper |
| 27 | Self-hosted typed pointers, nsw, noalias/willreturn | Rattler, Cobra |
| 28 | Dead arena code, _mn_iters leak, _Indent duplication | Cobra, Boa |

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
culebra wrap -- valgrind ./mapanare/self/mnc-stage1 tests/golden/39_gpu_detect.mn

# Track progress across fixes
culebra baseline save mapanare/self/main.ll
culebra baseline diff mapanare/self/main.ll

# After each version — full summary
culebra summary mapanare/self/main.ll
```

---

## Current state (v3.45.0)

- Version: 3.45.0
- Branch: dev
- 38/38 golden tests pass, 30/33 valgrind-clean
- Fixed point: stage4 == stage3 (proven v3.38.0)
- Self-hosted compiler: 14,764 lines core (mnc_all.mn), 35,868 total across 17 modules
- 4,845+ pytest tests, 74 native C assertions, 4,004 lines of native tests
- 7 CI jobs: ci, self-hosted, bootstrap, native, wasm, android, macos
- Peak memory: 160 MB, binary: 2.94 MB, self-compile: 0.74s
- LLVM 17+ compliant: zero typed pointer sites in Python emitter output
- Code review: 9.69/10 aggregate (7 reviewers, all PASS, 28 action items)
- `mapanare_io.c`: 1,655 lines, LINKED — TCP, TLS, crypto, regex, HTTP
- `mapanare_runtime.c`: 1,343 lines, LINKED — agents, thread pool, ring buffers
- `mapanare_gpu.c`: 1,938 lines, NOT LINKED — CUDA/Vulkan via dlopen, PTX kernels
- Package manager: functional (`mapanare install` works)
- Examples: 3 working CLI/network examples + transpile demo
- GPU: `nvidia-smi` shows RTX 4090, `libcuda.so` present in WSL
- SPEC Section 23: still claims GPU works (it doesn't) — P0 carry-forward, 3 cycles

## After both versions are done

- GPU tensor operations run on the 4090 from Mapanare code
- SPEC Section 23 shows code that actually compiles and runs
- All 25 review action items addressed (3 deferred to v4.1 by panel consensus)
- Self-hosted emitter ABI matches C runtime for all builtins
- Thread-safe initialization for all dlopen loaders
- All version strings current, golden refs re-blessed
- CI green across all 7 jobs
- Ready for v4.0.0 production release tag
- **A new user can build a GPU-accelerated program.**
