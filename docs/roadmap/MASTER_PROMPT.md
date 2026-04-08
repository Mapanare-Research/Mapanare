# Master Prompt — Execute Roadmap v3.34.0 → v3.36.0

> Kill the Python dependency, make compilation snappy, prepare for v4.0.0.
> Each version has its own prompt.md with full instructions.
> Execute one at a time, verify, commit, then move to next.
> Read CLAUDE.md for project context.

---

## Instructions

You are executing the Mapanare performance roadmap from v3.34.0 through v3.36.0.
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

| # | Version | Codename | Theme | User-Facing Result |
|---|---------|----------|-------|--------------------|
| 1 | v3.34.0 | Cachicamo | Zero-Python driver | `mnc run hello.mn` in <100ms, no Python needed |
| 2 | v3.35.0 | Baquiro | Incremental compilation | <2s rebuild after single-file change |
| 3 | v3.36.0 | Cunaguaro II | Performance + release prep | <10MB binary, <200K IR, benchmarks in CI |

**Dependencies:**

```
v3.34.0 (native driver) ── mnc becomes the default binary
    │
    ▼
v3.35.0 (incremental) ── caching and parallel compilation on top of mnc
    │
    ▼
v3.36.0 (performance) ── optimize compiler output, establish CI gates
    │
    ▼
v4.0.0 (production) ── pure quality gate, no new features
```

**Rules:**

- Do NOT skip versions or reorder them
- Do NOT start version N+1 until version N is committed
- If a verification step fails, fix it before moving on
- Make decisions autonomously — do not ask for confirmation on implementation choices
- Commit at each milestone within a version (not just at the end)
- Use `/golden` after every compiler change
- Measure startup time (`time mnc run hello.mn`) after every phase
- Use Culebra to verify IR quality after emitter changes
- Use ASan/TSan after C runtime changes
- Run `.\dev.ps1` (full validate) before every version bump

**Performance targets (cumulative):**

| Metric | v3.34.0 | v3.35.0 | v3.36.0 |
|--------|---------|---------|---------|
| `mnc run hello.mn` | <100ms | <100ms | <100ms |
| Clean build (11 modules) | — | <15s | <15s |
| Incremental rebuild (1 file) | — | <2s | <2s |
| IR blowup ratio | — | — | <10x |
| Binary size (stripped) | — | — | <10MB |
| Peak memory (self-compile) | — | — | <512MB |

**Current state:**
- Version: 3.35.0
- Branch: dev
- Self-hosted compiler works (20K+ lines, 16 modules, compiles itself)
- Python/PHP/TypeScript/Go transpilers working (all self-hosted in .mn)
- `any` type implemented
- All 20 v3.33.0 review items addressed, break-in-for confirmed fixed
- Text emitter codegen bug fixed, main.ll regenerated (275K lines, current ABI)
- Seed binary updated, all CI jobs re-enabled
- User-facing CLI still goes through Python (~437ms for hello.mn)
- All golden tests pass (33/33)
- 843+ tests passing, mypy/ruff/black clean

**After all 3 versions are done:**
- `mnc` is the default compiler — no Python required for end users
- Single-file compilation: <100ms
- Multi-module incremental rebuild: <2s
- Compiler binary: <10MB
- Compile-time benchmarks enforced in CI
- v4.0.0 is next — docs, demos, quality gate
