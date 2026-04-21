# Mapanare v4.30.0 — Codegen + Optimizer + Emitter Carry-Forwards

> **Recovery release #4.** v4.27.0 fixed CRITICALs, v4.28.0 fixed
> concurrency, v4.29.0 fixed CI gates. v4.30.0 fixes the codegen and
> optimizer items the panel marked HIGH, plus the emitter carry-forwards
> that are on their 7th review cycle. Still **zero new features.**

**Status:** PLANNED
**Breaking:** Possibly — `await` may be deleted from grammar
**Prerequisite:** v4.29.0
**Estimated work:** 1-2 days
**Theme:** The optimizer and emitter must do what they claim. The carry-forward queue must drain.

---

## The Problem

Three classes of HIGH-severity items in codegen and optimization:

### Class A: Hollow runtime features

| Feature | Site | Issue | Reporter |
|---------|------|-------|----------|
| `await` | `lower.py` | Lowers to `return self._lower_expr(expr.expr)` — pure identity, no coroutine | Viper H2, Rattler #5 |
| Agent dispatch | `_emit_agent_wrap` | No-op stub returning 0 | Rattler #3 |

These are paired with v4.27.0's `@gpu` and v4.27.0's `const` decisions —
features that look like they exist but don't run. The decision protocol is
the same: implement or strike.

### Class B: Optimizer claims that don't hold

| Site | File:Line | Issue | Reporter |
|------|-----------|-------|----------|
| Optimizer non-convergence | `mir_opt.py:1128-1135` | `logging.warning` instead of ICE | Anaconda HIGH |
| `stream_fusion` outside fixpoint | `mir_opt.py:1138-1143` | Contradicts v4.7.0 "unified fixpoint loop" claim | Anaconda HIGH |
| Self-hosted DCE bounded loops | self-hosted dead block elim | Bounded iteration; `clean_phis_in_block` defined but never invoked | Rattler #6 |

### Class C: Emitter carry-forwards (7th cycle)

The panel called this "the worst carry-forward performance in project
history." Six emitter items have survived seven review cycles each:

| # | Item | Reporter |
|---|------|----------|
| 1 | `i64*` opaque pointer migration (LLVM 17+ compat) | Rattler |
| 2 | `void ()*` opaque pointer migration | Rattler |
| 3 | List `bitcast` cleanup | Rattler |
| 4 | Missing `nsw` flags on int arithmetic | Rattler |
| 5 | `__mn_map_new` 3-param signature mismatch | Rattler |
| 6 | Missing `noalias`/`willreturn` attrs on runtime decls | Rattler |

Plus the parser issue prerequisite to a real `const` (if v4.27.0 took Path B):

| # | Item | File:Line | Reporter |
|---|------|-----------|----------|
| 7 | `const_def` parser collapses `TypeExpr` to `.name` string | `parser.py:1444-1459` | Anaconda HIGH |

---

## Phase 1: `await` decision

### Path A: Real coroutine lowering

- [ ] Lower `await expr` to LLVM coroutine intrinsics: `llvm.coro.id`,
      `llvm.coro.suspend`, `llvm.coro.resume`
- [ ] `async fn` becomes a coroutine, returns a `Future<T>`-like handle
- [ ] Cooperative scheduler integration via the existing C runtime
- [ ] Add a golden test that demonstrates async behavior: a function that
      yields and resumes, with observable concurrency
- [ ] Estimated 2-3 days. **Beyond the v4.30.0 time budget for a recovery
      release.**

### Path B: Strike

- [ ] Remove `async` and `await` keywords from `mapanare/mapanare.lark`
- [ ] Remove from self-hosted lexer/parser
- [ ] Delete `46_async_stream.mn` golden test (it tests a non-feature)
- [ ] Strike the v4.19.0 and v4.24.0 "async/await wired" CHANGELOG claims;
      add a new CHANGELOG entry under "Removed"
- [ ] Document in `docs/SPEC.md` that async is a v5.x feature

**Default: Path B.** The panel's preference. Path A becomes the v5.0.0
roadmap.

---

## Phase 2: Agent dispatch decision

### Path A: Wire `_emit_agent_wrap`

- [ ] `_emit_agent_wrap` is currently a no-op stub returning 0
- [ ] Wire it to the existing `mapanare_agent_*` runtime functions
      (the scheduler exists; the emitter binding doesn't)
- [ ] Spawn lowering: `agent fn foo()` → `mapanare_agent_create(...)`
- [ ] Send lowering: `foo.send(msg)` → `mapanare_agent_send(...)`
- [ ] Receive lowering: `agent fn foo() { receive m -> ... }` → ring buffer poll
- [ ] Add a golden test: spawn an agent, send 3 messages, receive them in
      order, terminate
- [ ] Estimated 4-6 hours

### Path B: Strike

- [ ] Remove agent syntax from grammar (huge surface; this is a feature
      the language is built around)
- [ ] **Not recommended.** Agents are a first-class primitive in the
      project's identity. Striking them is a v5.x rewrite, not a v4.30.0
      recovery item.

**Default: Path A.** Agents are central to Mapanare's identity. The panel
flagged the no-op stub specifically because the language *promises* agents
work; the stub is the smallest gap to close to make that promise honest.

---

## Phase 3: Optimizer correctness

### Phase 3.1: Non-convergence ICE

- [ ] `mir_opt.py:1128-1135` — currently `logging.warning(...)` when the
      optimizer hits its 10-iteration cap. Suboptimal code ships silently.
- [ ] Replace with `raise ICE(...)` so a non-convergent optimizer pass is a
      compiler bug, not a quiet warning
- [ ] Add a test: synthesize a MIR module that doesn't converge under the
      current passes; assert ICE
- [ ] If the test reveals a real non-convergence on the golden corpus, fix
      the underlying pass — do not raise the iteration cap

### Phase 3.2: `stream_fusion` in fixpoint loop

- [ ] `mir_opt.py:1138-1143` — `stream_fusion` runs as a single pass
      *outside* the unified O1+O2 fixpoint loop. The v4.7.0 CHANGELOG
      claimed "unified fixpoint loop merges O1 and O2." Adding a third pass
      that runs once outside the loop contradicts that claim.
- [ ] Move `stream_fusion` inside the fixpoint loop, or document
      explicitly why it's exempt (e.g., "stream fusion is structural and
      idempotent; running it once is sufficient")
- [ ] Update the v4.7.0 CHANGELOG entry if `stream_fusion` is being kept
      outside the loop with documentation

### Phase 3.3: Self-hosted dead block elim

- [ ] The self-hosted dead block elimination pass has bounded iteration
      loops (where the Python equivalent uses BFS with fixed-point
      termination)
- [ ] Replace bounded loops with BFS + fixed-point termination
- [ ] `clean_phis_in_block` is defined but never invoked — wire it at the
      right step (after a block is removed, before the BFS continues)
- [ ] Add a self-hosted golden test that exercises a dead-block-with-PHI
      pattern; verify both bootstrap and stage1 produce identical output

---

## Phase 4: Emitter carry-forwards (7th cycle)

This phase pays back the carry-forward debt the panel called the worst in
project history. Each item is small individually; the discipline is
finishing all six in one version.

### Phase 4.1: Opaque pointers (LLVM 17+)

- [ ] Find the 2 remaining typed pointers in the emitter:
      - `i64*` for tensor allocations
      - `void ()*` for function constants
- [ ] Replace each with `ptr` (LLVM's opaque pointer type)
- [ ] Verify with `llvm-as` on the resulting IR — should accept on LLVM 17+
- [ ] If the change reveals downstream issues (e.g., mismatched arg types),
      fix them in the same version

### Phase 4.2: List bitcast cleanup

- [ ] Find every `bitcast` involving list pointers in `emit_llvm_text.py`
- [ ] Most should be unnecessary after the opaque pointer migration —
      delete them
- [ ] Any that remain must have a comment explaining why

### Phase 4.3: Missing `nsw` flags

- [ ] Integer arithmetic in MIR that's known not to overflow should emit
      `add nsw`, `sub nsw`, `mul nsw` (no signed wrap)
- [ ] This is a small optimizer hint; LLVM uses it to enable folds
- [ ] Apply uniformly to: integer literals, loop counters, array indices,
      arithmetic on type-tagged `Int`

### Phase 4.4: `__mn_map_new` signature

- [ ] `__mn_map_new` is currently called with 3 parameters from the emitter
      but declared with a different arity in the runtime (or vice versa)
- [ ] Find the mismatch; align the call site and the declaration
- [ ] Add the function to `_RUNTIME_FN_ATTRS` if missing

### Phase 4.5: Missing `noalias`/`willreturn` attrs

- [ ] Audit every runtime function declaration in `_RUNTIME_FN_ATTRS`
- [ ] `noalias` on pointer-returning allocators (`__mn_string_new`, etc.)
- [ ] `willreturn` on pure functions that always terminate
- [ ] Add `nounwind` where appropriate
- [ ] Verify with `llvm-as` and confirm no warnings

### Phase 4.6: `const_def` parser fix (if v4.27.0 took Path B)

- [ ] If v4.27.0 took Path A and `const` is a real feature, this is
      already done — skip
- [ ] If v4.27.0 took Path B and `const` was deleted, this is moot — skip
- [ ] Otherwise (a third state where `const` exists but the parser is
      broken), `parser.py:1444-1459` collapses the full `TypeExpr` to
      `.name` — preserve the full TypeExpr for downstream consumers

---

## Exit Criteria

| # | Check | Required |
|---|-------|----------|
| 1 | `await` decision executed (Path A or Path B); if Path B, syntax removed | YES |
| 2 | Agent dispatch wired; golden test spawn/send/receive passes | YES |
| 3 | Optimizer non-convergence raises ICE, not warning | YES |
| 4 | `stream_fusion` either inside fixpoint loop or documented as exempt | YES |
| 5 | Self-hosted DCE uses BFS + fixed-point; calls `clean_phis_in_block` | YES |
| 6 | Zero `i64*` typed pointers in `emit_llvm_text.py` | YES |
| 7 | Zero `void ()*` typed pointers | YES |
| 8 | Zero unnecessary list bitcasts | YES |
| 9 | `nsw` flags on integer arithmetic | YES |
| 10 | `__mn_map_new` signature mismatch resolved | YES |
| 11 | `noalias`/`willreturn` attrs on runtime decls | YES |
| 12 | 46/46+ golden, 11/11 stage2 | YES |
| 13 | LLVM 17+ accepts the emitted IR (`llvm-as` clean) | YES |
| 14 | black/ruff/mypy clean | YES |
| 15 | `docs/roadmap/v4/v4.30.0/SESSION_REPORT.md` written | YES |

---

## What v4.30.0 explicitly does NOT do

- SPEC update, Spanish README sync (→ v4.31.0)
- User-Agent string bump (→ v4.31.0)
- Dead code removal (`__mn_list_oob_buf`) (→ v4.31.0)
- DWARF debug info — already decided in v4.29.0
- New language features (none until next major)

---

## Verification commands

```bash
# Phase 1 await
grep -r "async\|await" mapanare/mapanare.lark mapanare/self/lexer.mn  # depends on path

# Phase 2 agents
python3 scripts/test_native.py --filter agent_spawn -v

# Phase 3 optimizer
python3 -m pytest tests/optimizer/test_non_convergence.py -v
python3 -m pytest tests/optimizer/test_fixpoint_loop.py -v

# Phase 4 emitter
git grep -E "i64\*|void \(\)\*" mapanare/emit_llvm_text.py
# Both should return 0 hits
llvm-as mapanare/self/main.ll -o /dev/null && echo "LLVM 17+ clean"

# Full validation
.\dev.ps1
```
