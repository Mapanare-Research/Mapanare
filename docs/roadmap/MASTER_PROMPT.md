# Master Prompt — Execute Roadmap v3.37.0 → v3.39.0

> Fix memory safety, prove self-compilation, harden for production.
> Each version has its own prompt.md with full instructions.
> Execute one at a time, verify, commit, then move to next.
> Read CLAUDE.md for project context.

---

## Instructions

You are executing the Mapanare correctness roadmap from v3.37.0 through v3.39.0.
There are 3 versions to complete, each building on the previous one.

**For each version N:**

1. Read `docs/roadmap/vN/prompt.md` — it has the full instructions
2. Read `docs/roadmap/vN/PLAN.md` — it has the item breakdown
3. Execute all items in the prompt, following its phasing and priority order
4. Run the verification checklist from the prompt
5. Run `/bump-version` to bump to version N
6. Commit with the message format from the prompt
7. Update `docs/roadmap/vN/PLAN.md` status to DONE
8. Move to version N+1

**Execution order (strict — each depends on the previous):**

| # | Version | Codename | Theme | Proof |
|---|---------|----------|-------|-------|
| 1 | v3.37.0 | Araguato | Memory safety | `valgrind mnc hello.mn` = 0 errors, mnc compiles mnc_all.mn |
| 2 | v3.38.0 | Turpial | Fixed-point self-compilation | stage3 == stage2, 33/33 golden, seed updated |
| 3 | v3.39.0 | Caricare | Hardening + v4.0.0 gate | valgrind-clean everything, Culebra CI, <512MB peak |

**Dependencies:**

```
v3.37.0 (memory safety) ── struct copy clones lists, drop glue fixed, no_drop_glue removed
    │
    ▼
v3.38.0 (fixed point) ── compiler compiles itself identically, 33/33 golden
    │
    ▼
v3.39.0 (hardening) ── valgrind-clean, memory profiling, Culebra CI, docs
    │
    ▼
v4.0.0 (production) ── release tag after manual testing (NOT in this prompt)
```

**Rules:**

- Do NOT skip versions or reorder them
- Do NOT start version N+1 until version N is committed
- If a verification step fails, fix it before moving on
- Make decisions autonomously — do not ask for confirmation on implementation choices
- Commit at each milestone within a version (not just at the end)
- Use `/golden` after every compiler change
- Use `valgrind` after every memory-related change
- Use Culebra to verify IR quality after emitter changes
- Use ASan/TSan after C runtime changes
- The `no_drop_glue` hack MUST be removed in v3.37.0 — do not keep it

**What must be true after each version:**

| Check | v3.37.0 | v3.38.0 | v3.39.0 |
|-------|---------|---------|---------|
| `no_drop_glue` removed | YES | YES | YES |
| `valgrind mnc hello.mn` clean | YES | YES | YES |
| `mnc` compiles `mnc_all.mn` | YES | YES | YES |
| stage3 == stage2 (fixed point) | — | YES | YES |
| 33/33 golden | — | YES | YES |
| valgrind-clean all 33 golden | — | — | YES |
| valgrind-clean compiled programs | — | — | YES |
| Culebra CI gates | — | — | YES |
| Peak memory <512MB | — | — | YES |
| Seed binary updated | — | YES | YES |

**The root cause (understand this before writing code):**

The text emitter's `_do_copy` method (`emit_llvm_text.py` ~line 1501) does
a raw struct copy (insertvalue). When a struct contains a `List`, both the
original and the copy point to the same heap buffer, but the COW refcount
stays at 1. This causes:

1. Push on one copy → COW detach thinks it's sole owner → doesn't copy buffer
2. Drop glue on the other copy → frees the shared buffer
3. Any access through the first copy → use-after-free
4. After enough of these on a large file → glibc heap corruption → crash

The fix: `_do_copy` must call `__mn_list_clone(ptr)` for each list field
in the struct. This increments the refcount so COW detach and drop glue
work correctly. ~15 lines of code in the emitter.

The SECOND fix: drop glue must not free list/string fields that are part
of the return value when the return type is a struct. The existing code
only skips bare `List` returns — extend it to check struct fields.

**Culebra commands to use throughout:**

```bash
# After every emitter change — check for IR regressions
culebra scan mapanare/self/main.ll --tags abi
culebra health mapanare/self/main.ll
culebra triage mapanare/self/main.ll --brief

# After fixing drop glue — verify the fix
culebra verify mapanare/self/main.ll return-type-divergence
culebra verify mapanare/self/main.ll option-type-pun-zeroinit

# When debugging crashes — map offsets to fields
culebra crashmap mapanare/self/main.ll --offset <addr>
culebra trace mapanare/self/main.ll --function <fn> --var '%state'

# When comparing stage2 vs stage3
culebra diff /tmp/stage2.ll /tmp/stage3.ll
culebra bisect /tmp/stage2.ll /tmp/stage3.ll --top 10

# Track progress across fixes
culebra baseline save mapanare/self/main.ll
culebra baseline diff mapanare/self/main.ll

# Wrap valgrind runs for pattern learning
culebra wrap -- valgrind ./mapanare/self/mnc-stage1 tests/golden/01_hello.mn
culebra learn
```

**Current state:**
- Version: 3.36.0
- Branch: dev
- 29/33 golden tests pass (4 generic/impl type errors)
- `no_drop_glue=True` hack active — ALL memory cleanup disabled
- mnc-stage1 crashes on mnc_all.mn (760KB) with `corrupted double-linked list`
- Self-compilation DOES NOT WORK
- IR: 185K lines, binary: 3.4MB stripped
- Precompiled C runtime (`libmapanare_rt.a`) available
- Incremental build system (`mnc build <dir>`) available
- Startup benchmarks and compile-time benchmarks in CI

**After all 3 versions are done:**
- The compiler compiles itself correctly (fixed-point proven)
- Zero memory errors (valgrind-clean)
- Zero hacks (`no_drop_glue` gone)
- 33/33 golden tests
- Culebra regression gates in CI
- Seed binary updated
- Ready for manual testing before v4.0.0 release tag
