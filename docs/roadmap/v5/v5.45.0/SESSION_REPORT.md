# v5.45.0 — Session Report

**Tag:** v5.45.0 (lead-approved, not yet pushed)
**Branch:** dev
**Cut:** 2026-05-06
**Theme:** Ts.\* — tensor closeout arc CLOSED.

After v5.45.0 the "Not yet on LLVM" line in CLAUDE.md no longer
mentions tensor mutable views or stepped slices — the line is
removed entirely. The v5.41.0 option-B contract (Ts.2 + Ts.3)
ships 4 releases past slot.

---

## What shipped

| Item | Status |
|---|---|
| Ts.2.A — refcount on `mapanare_tensor_t` | ✅ append-only struct ext (40 → 64 B) |
| Ts.2.B — `t.view(shape)` + reshape semantic swap | ✅ |
| Ts.3.A — `[start..end:step]` grammar + AST + parser | ✅ |
| Ts.3.B — stepped slice runtime + lower + emit | ✅ |
| Ts.4 — test corpus (3 goldens + 3 pytest modules) | ✅ |
| Ts.5 — `docs/stdlib/tensor.md` cookbook | ✅ ~325 LOC |
| Ts.7 — self-host mirror | ✅ STRICT preserved |
| Ts.8 — binary-compat regression | ✅ 5/5 |
| UB-risk tier (TSan + ASan + valgrind + binary-compat) | ✅ |
| STRICT 3-stage fixed point | ✅ **243,749 lines / 0 diff** |
| Goldens 99/99 GREEN | ✅ |
| `make ci-gates` + `make lint` | ✅ |
| `check_doc_freshness.py` + `check_changelog_honesty.py` | ✅ |

---

## PROMPT/PLAN deviations (load-bearing)

Documented in detail at `docs/roadmap/v5/v5.45.0/PRE_PHASE_AUDIT.md`.
Five surfaced at Phase 0; one additional surfaced during execution.

### Deviation 1 — Golden 96 does NOT flip on the semantic swap

**PROMPT claim:** "the v5.41.0 source-unmodified-after-reshape test
in golden 96 EXPECTED to flip — that's the aliasing swap; document
explicitly."

**Reality:** Golden 96 lines 56-60 read both `f` and `f2` after
reshape but NEVER write between. Output is identical under copy
or alias semantics. The test as written does not exercise the
copy-vs-alias distinction.

**Resolution:** Golden 96 stays unchanged. The aliasing-write
contract lives in net-new golden 99 using `t[i, j] = val` writes.

### Deviation 2 — Bootstrap grammar update is optional, not lockstep

**PROMPT claim:** "Bootstrap copy of grammar in `bootstrap/`
updated in lockstep" + "Bootstrap grammar copy: yes (Ts.3.A)" in
checklist.

**Reality:** `bootstrap/parser.py` is frozen at v0.6.0 and not
involved in compiling v5.45.0 sources. The single test that
references it just asserts file existence.

**Resolution:** Updated `bootstrap/mapanare.lark` for snapshot
consistency, but did NOT update `bootstrap/parser.py` constructors.
Future test runs of v5.45.0+ source through bootstrap parser would
get a clear "unexpected token COLON in range_op" error.

### Deviation 3 — Three direct-malloc tensor sites need zero-init

**PROMPT focus:** solely on `mapanare_tensor_alloc` for refcount
initialization.

**Reality:** Three additional direct
`malloc(sizeof(mapanare_tensor_t))` sites exist in
`mapanare_gpu_builtins.c` (lines 56, 229, 230). These create
"borrow tensors" (data pointer aliases an MnList's buffer). They
do field-by-field init and bypass the alloc helper. Post-v5.45.0
the new fields would have been uninitialized memory.

**Resolution:** Added `memset(t, 0, sizeof(*t))` zero-init at each
site. Borrow tensors are freed via `tensor_borrow_free` which calls
`free(t->shape); free(t)` directly — they bypass the refcount
machinery (correct: borrow tensor data is owned by the caller's
MnList, not the tensor).

### Deviation 4 — Struct grows by +24 bytes, not +16

**PLAN claim:** "the `mapanare_tensor_t` struct grows by ~16
bytes (refcount + view flag + parent pointer)."

**Reality:** refcount (8) + is_view (1) + 7 padding bytes for
8-byte alignment of parent + parent (8) = **24 bytes**. The PLAN
underestimated by 8 bytes (alignment padding overlooked).

**Resolution:** Binary-compat regression test pins exact size
(40 → 64 bytes); CHANGELOG / SPEC sync note the actual delta.

### Deviation 5 — `IndexItem` has no `inclusive` field (pre-existing latent)

**Reality:** `IndexItem.kind = "range"` does not preserve the
`inclusive: bool` field of the source `RangeExpr`. Pre-existing
latent inconsistency since v4.45.0; not a v5.45.0 introduction.

**Resolution:** Out of scope. Documented in PRE_PHASE_AUDIT.

### Deviation 6 — `t.copy()` deferred to v5.47.0+

**Surfaced during Phase 1.** PROMPT-mentioned `t.copy()` for
explicit-copy opt-out from v5.41.0 copy semantics. No `.copy()`
API exists at HEAD. Adding it would be ~30 LOC across lower +
emit + self-host mirror + golden + cookbook entry.

**Lead-approved (Option A):** ship v5.45.0 without `.copy()`,
defer to v5.47.0+ as small ergonomic add. Phase 0 audit
established zero production callers rely on v5.41.0 copy
semantics so the missing opt-out is theoretical. Cookbook
documents the manual workaround (allocate fresh tensor + per-
element copy via `tensor[i, j] = val`).

---

## Two surprises captured

### Surprise 1 — `scripts/build_stage1.py` does NOT auto-regen `mnc_all.mn`

First STRICT check after Phase 5 self-host edits showed NEAR
(6 diff lines) because stage1 was still compiled from a stale
`mnc_all.mn` whose hardcoded
`" = call noalias ptr @__mn_tensor_reshape(ptr "` string predated
the Phase 5.4 emit_llvm.mn edit. The fix was to manually run
`scripts/concat_self.py` before `scripts/build_stage1.py`.

**Discipline captured:** future self-host edits must run
`scripts/concat_self.py` before `scripts/build_stage1.py`. Same
lesson as v5.31.0's stage1-rebuild discipline applied to a
different layer (concat → build → verify).

### Surprise 2 — Pre-existing v5.44.1 `Tensor<Int>` parser bug

During Phase 6 golden 98 testing, `Tensor<Int>` slice + tensor
builtin call (e.g., `tensor_size(int_slice_result)`) triggered a
parse error. Verified the same code fails on the v5.44.1 baseline
(stashed v5.45.0 changes, ran Python emitter, observed identical
parser error). Out-of-scope for v5.45.0.

**Resolution:** Golden 98 worked around by skipping the Int
section + note in the test source. Tracked as v5.46.0+ LOW carry.
Float-element tensors are unaffected.

---

## Phase-by-phase summary

### Phase 0 — Pre-flight + audit (~2h)

PRE_PHASE_AUDIT.md surfaced 5 deviations against v5.44.1 HEAD.
HEAD baseline: VERSION 5.44.1, goldens 96/96, STRICT preserved at
242,338 lines / 0 diff.

### Phase 1 — Ts.2.A C runtime: refcount (~3h)

Append-only `mapanare_tensor_t` extension; refcount-aware
`mapanare_tensor_free`. Three borrow-tensor zero-inits in
`mapanare_gpu_builtins.c`. C smoke `/tmp/ts2a_smoke.c` (8 cases
/ 22 assertions); ASan + valgrind clean.

### Phase 2 — Ts.2.B view + reshape swap (~4h)

`__mn_tensor_view` C export; reshape body delegates to view.
`noalias` attribute drops from Python emit attr table + call
literal. Python lower + emit handle both `.reshape()` and
`.view()` through unified branch. C smoke `/tmp/ts2b_smoke.c`
(4 cases / 22 assertions). pytest
`tests/llvm/test_tensor_views.py` (4 cases) GREEN. ASan +
valgrind clean.

### Phase 3 — Ts.3.A grammar + AST + parser (~3h)

Grammar productions in `mapanare/mapanare.lark` and
`bootstrap/mapanare.lark`. `RangeExpr.step` + `IndexItem.step`
fields with `None` defaults. Parser constructors. pytest
`tests/parser/test_range_step.py` (10 cases) + 256/256 parser
regression sweep GREEN.

### Phase 4 — Ts.3.B stepped slice runtime + lower + emit (~4h)

`__mn_tensor_step_slice` C export. `_lower_tensor_slice` extends
to detect any-stepped axes, route to `__mn_tensor_step_slice`
with steps array. Python emit packs starts/ends/steps into 3
stack-allocated arrays. Literal step ≤ 0 rejected at lower time
(catches both `IntLiteral(0)` and `UnaryExpr(-, IntLiteral(N))`).
pytest `tests/llvm/test_tensor_stepped_slice.py` (8 cases) +
C smoke `/tmp/ts3b_smoke.c` (4 cases / 19 assertions) GREEN.

### Phase 5 — Ts.7 self-host mirror (~6h)

Mirror order: ast.mn → parser.mn → lower.mn → emit_llvm.mn →
semantic.mn. Stage1 rebuild + goldens GREEN after each
milestone. **STRICT 3-stage fixed point preserved at 243,749
lines / 0 diff** (+1,411 lines vs v5.44.1).

### Phase 6 — Test corpus + binary-compat (~5h)

3 new goldens (97/98/99) all PASS. Pytest extensions
`test_tensor_views_sanitized.py` (14 ASan + valgrind cases) GREEN.
Binary-compat `test_tensor_struct_compat.py` (5 cases) GREEN.
Goldens 99/99.

### Phase 7 — Cookbook (~2h)

`docs/stdlib/tensor.md` (~325 LOC).

### Phase 8 — Closeout

VERSION 5.44.1 → 5.45.0; CHANGELOG `### Added` + `### Changed`
+ `### Fixed` + `### Notes`; CLAUDE.md release-notes entry +
"Not yet on LLVM" line removed; SPEC.md header sync; this
SESSION_REPORT.md; final stage1 rebuild + STRICT verify; all
gates GREEN.

---

## Source delta

- `runtime/native/mapanare_runtime.h` — ~14 LOC (struct ext)
- `runtime/native/mapanare_runtime.c` — ~30 LOC (alloc memset +
  refcount-aware free)
- `runtime/native/mapanare_gpu_builtins.c` — ~80 LOC
  (`__mn_tensor_view` + `__mn_tensor_step_slice` + 3 zero-init
  sites + reshape body delegation)
- `mapanare/lower.py` — ~70 LOC (view branch + step routing +
  literal-step-validation helper)
- `mapanare/emit_llvm_text.py` — ~75 LOC (view + step_slice
  handlers + reshape noalias drop + attr table entries)
- `mapanare/mapanare.lark` — +2 productions
- `bootstrap/mapanare.lark` — +2 productions (snapshot consistency)
- `mapanare/ast_nodes.py` — +5 LOC (step fields)
- `mapanare/parser.py` — +30 LOC (step constructors + index_expr
  propagation)
- `mapanare/semantic.py` — +9 LOC (TENSOR method-return-type rule)
- `mapanare/self/ast.mn` — +5 LOC
- `mapanare/self/parser.mn` — +12 LOC
- `mapanare/self/lower.mn` — +45 LOC
- `mapanare/self/emit_llvm.mn` — +75 LOC
- `mapanare/self/semantic.mn` — +8 LOC
- `mapanare/self/mnc_all.mn` — regenerated, ~+150 LOC
- 3 net-new goldens (`97`/`98`/`99`) — ~220 LOC total
- 3 net-new pytest modules — ~660 LOC total
  (`test_tensor_views.py` + `test_tensor_stepped_slice.py` +
  `test_tensor_views_sanitized.py`)
- 1 net-new binary-compat regression — ~195 LOC
  (`test_tensor_struct_compat.py`)
- 1 net-new parser pytest — ~135 LOC (`test_range_step.py`)
- `docs/stdlib/tensor.md` — ~325 LOC (cookbook)
- `docs/SPEC.md` — header bump + sync block
- `CHANGELOG.md` — full ## [5.45.0] section
- `CLAUDE.md` — release-notes entry; "Not yet on LLVM" line
  removed
- `docs/roadmap/v5/v5.45.0/PRE_PHASE_AUDIT.md` — net-new
- This `SESSION_REPORT.md` — net-new

**Total: ~3,200 LOC across 30 files** (vs v5.41.0
PRE_PHASE_AUDIT estimate of ~1,800 LOC; the overrun is mostly
in the test corpus, where the UB-risk tier added 14 ASan +
valgrind sweep cases that weren't in PROMPT and the binary-
compat regression test grew bigger than expected once we
needed both ctypes and a probe-compile path).

---

## Aggregate state entering v5.46.0

- **0 HIGH** (tensor closeout arc CLOSED)
- **2 MEDIUM** (three v5.43.0 lowerer bugs carry — v5.46.0's whole
  release; macOS notarization carry from v5.33.0 Nu.2)
- **~7 LOW**:
  - `.copy()` ergonomic for v5.47.0+
  - v5.44.1 `Tensor<Int>` parser bug (out-of-scope)
  - Strided / non-contiguous tensors carry to v6.0+
  - Reverse-step / negative-step carry to v6.0+
  - GPU tensor surface unification carry to v6.0+
  - Borrow checker on view aliasing — v6.0
  - Hard removal of `{}` (carry from v5.19.0)

**Tensor closeout arc CLOSED.** Manifesto arc CLOSED at v5.43.0.
Package-system runway CLOSED at v5.44.0. v5.46.0 picks up the
three lowerer bug closeouts; v5.47.0 closeout panel green-lights
v6.0.
