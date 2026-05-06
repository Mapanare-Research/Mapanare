# v5.46.0 — Phase 0 audit

**Status:** complete.
**Author:** Phase 0 (Lf.0).
**Outcome:** PLAN/PROMPT premise confirmed for the bug repros.
**Major load-bearing finding:** all three bugs (Lf.1 + Lf.2 + Lf.3)
share **one** root cause, and the root cause lives **only in the
Python bootstrap lowerer** (`mapanare/lower.py`). The self-host
mirror (`mapanare/self/lower.mn`) **already has the fix** —
v5.26.1 Eu.2 introduced the `current_fn.return_type` consultation
on the self-host side at lines 2259-2306; the same fix was never
backported to the Python bootstrap. Self-host stage1
(`mapanare/self/mnc-stage1`) produces correct output for all
three repros at v5.45.0 HEAD. Therefore Lf.5 self-host mirror is a
**no-op gate** — STRICT 3-stage fixed point preserved by
construction with zero `mapanare/self/*.mn` source touches.

---

## Pre-flight

- VERSION at HEAD: `5.45.0` ✓
- `bash scripts/verify_fixed_point.sh` STRICT GREEN at 243,749
  lines / 0 diff ✓
- `python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
  → 99/99 ✓
- Working tree: only routine GitNexus index updates pending
  (AGENTS.md + CLAUDE.md gitnexus blocks).

---

## Repro reconstruction

The original v5.43.0 `/tmp/diag_*.mn` repro suite is still on disk
(node_listen, match, propagate, full, fe, etc.). Used these as the
ground truth and synthesized minimal repros at
`/tmp/diag_lf{1,2,3,4}{_*,}.mn`.

### Lf.1 — Result<COMPLEX_OK, COMPLEX_ERR> destructure tag corruption

**Triggering shape:** `Result<NodeHandle, NetworkError>` where
`NodeHandle` is a 6-field 64-byte struct.
**Repro:** `/tmp/diag_lf1_real.mn` — wraps the v5.43.0
`fake_node_listen2` shape inline.
**Expected:** `kind=3` (NoKey).
**Pre-fix observed (Python bootstrap):** `kind=1` (BadUrl).
**Falsifiability:** `Result<Int, NetworkError>` (`/tmp/diag_lf1_minOk.mn`)
prints `kind=3` correctly — bug **only fires** when the Ok side is
non-trivial (struct ≥ 16 bytes triggers it; trivial Int does not).

### Lf.2 — Variant rewrap corruption through match propagation

**Triggering shape:** Result<NonTrivialOk, E> where the inner
function rewraps via `match Err(e) { da Err(e) }` and returns the
same Result type.
**Repro:** `/tmp/diag_lf2_complex.mn`.
**Expected:** `kind=3` (NoKey).
**Pre-fix observed (Python bootstrap):** **link error** —
`'%ok.37' defined with type 'i64' but expected '{ i64, { ptr, i64 },
i64, { ptr, i64 }, i1, i64 }'` at IR-validation time. The receiving
binding `pon r: Result<NodeHandle, NetworkError> = first()` allocates
`r` as `{i1, {i64, {i64, ptr}}}` (small Result<Int, ?> shape) instead
of the full type, because `first()`'s body lowers `da Err(NoKey(..))`
with default Ok=Int — and the call site's alloca shape inherits from
the call return type, which inherited from the buggy WrapErr.

### Lf.3 — Nested 15+-arm match silent no-fire

**Triggering shape:** `Result<NonTrivialOk, NetworkError>` returned
from a function with `da Err(VARIANT(...))`, then destructured at
caller via outer `match r { Err(e) => match e { 15 arms } }`.
**Repro:** `/tmp/diag_lf3_min.mn`, `/tmp/diag_full.mn` (v5.43.0
original).
**Expected:** prints "got NoKey".
**Pre-fix observed (Python bootstrap):** **silent no-fire** — empty
output. Outer `Err(e)` arm does fire, but `e`'s tag is corrupt
(reads from wrong byte offset), so none of the 15 inner arms match
and control flow falls through.
**Falsifiability:** standalone 15-arm match on a directly-bound
`NetworkError` (`/tmp/diag_lf3.mn`) prints `kind=12` correctly. Bug
**only fires** when the enum value is destructured through a
mismatched-shape Result wrapper — same root cause as Lf.1.

### Lf.4 — Variant-name collision in match patterns

**Triggering shape:** two enums `NetworkError` and `ExitReason` both
declaring a `TransportLost(String)` variant.
**Repro:** `/tmp/diag_lf4.mn`.
**Pre-fix observed (Python bootstrap):** **semantic-checker error** —
`Type mismatch: declared type NetworkError but initial value is
ExitReason` on the line `pon n: NetworkError = TransportLost("net")`.
Variant-name resolution in
`mapanare/semantic.py:2069` registers each variant in `global_scope`
by unqualified name; the second `define()` shadows the first. The
constructor's inferred return type is whichever enum was registered
last.

---

## IR-level diagnosis

### Root cause (Lf.1 + Lf.2 + Lf.3)

The `Err(...)` and `Ok(...)` constructor lowering at
`mapanare/lower.py:2398-2429` defaults the wrapper's untyped side
to `Int`/`String` regardless of context. From the source:

```python
if fn_name == "Ok" and len(args) == 1:
    ...
    res_ty = MIRType(
        TypeInfo(kind=TypeKind.RESULT, args=[ok_ti, TypeInfo(kind=TypeKind.STRING)])
    )

if fn_name == "Err" and len(args) == 1:
    ...
    res_ty = MIRType(
        TypeInfo(kind=TypeKind.RESULT, args=[TypeInfo(kind=TypeKind.INT), err_ti])
    )
```

When the enclosing function returns `Result<NodeHandle, NetworkError>`
the literal `Err(NoKey(...))` is lowered with shape
`Result<Int, NetworkError>` = 32 bytes; the body then stores that
into the function's `__sret__` slot which is sized for the real
`Result<NodeHandle, NetworkError>` = 88 bytes. The store writes 32
bytes; bytes 32..87 stay zero. The receiver's match-arm extracts
the Err `NetworkError` from offset 72 (per the big layout), reads
zero, gets variant tag = 0 = BadUrl + null payload.

### Captured IR (Lf.3 `validate_key`, /tmp/diag_lf3_min.ll lines 81-89)

```llvm
  %we.21 = insertvalue {i1, {i64, {i64, ptr}}} undef, i1 0, 0
  %we.22 = insertvalue {i1, {i64, {i64, ptr}}} %we.21, {i64, ptr} %l.20, 1, 1
  store {i1, {i64, {i64, ptr}}} %we.22, ptr %t7.a.23  ; SMALL 32-byte shape
  ...
  %l.24 = load {i1, {i64, {i64, ptr}}}, ptr %t7.a.23
  store {i1, {{ptr, i64}, {i64, ptr}}} zeroinitializer, ptr %rc.25  ; clear 40 bytes
  store {i1, {i64, {i64, ptr}}} %l.24, ptr %rc.25  ; THE BUG: 32-byte store into 40-byte alloca
  %rv.26 = load {i1, {{ptr, i64}, {i64, ptr}}}, ptr %rc.25  ; load 40 bytes
```

The mismatch is visible: `%t7.a.23` is the small shape; `%rc.25`
is the big shape; the 32-byte store leaves the trailing 8 bytes
zero, and on load that zero-padding becomes the Err's tag.

### Self-host has the fix already

`mapanare/self/lower.mn:2259-2306` (the v5.26.1 Eu.2 fix on the
self-host side):

```
if fn_name == "Ok":
    if len(args) == 1:
        let mut res_ty_ok: MIRType = mir_result()
        match st.current_fn {
            Some(cf) => {
                if cf.return_type.kind == TK_RESULT() {
                    res_ty_ok = cf.return_type
                }
            },
            _ => {}
        }
        ...
```

Self-host stage1 (`mapanare/self/mnc-stage1`) produces **correct
output for all three repros**:

```bash
$ mapanare/self/mnc-stage1 emit-llvm /tmp/diag_lf1_real.mn -o /tmp/...stg1.ll
$ clang ...stg1.ll libmapanare_rt.a -lm -lpthread -o exe && ./exe
kind=3                # ✓ correct (Python prints kind=1)

$ mapanare/self/mnc-stage1 emit-llvm /tmp/diag_lf2_complex.mn -o ...stg1.ll
$ ... && ./exe
kind=3                # ✓ correct (Python rejects at IR validation)

$ mapanare/self/mnc-stage1 emit-llvm /tmp/diag_lf3_min.mn -o ...stg1.ll
$ ... && ./exe
got NoKey             # ✓ correct (Python silently no-fires)
```

This is the load-bearing finding: **the bug is Python-bootstrap-
only**. The fix is a port of the self-host's existing v5.26.1 Eu.2
logic into the Python `Ok`/`Err` constructor lowering branches.

### Self-host source audit

```bash
# Result<NonTrivialOk, NonTrivialErr> in mapanare/self/:
$ grep -nE "Result<[A-Z][a-zA-Z_]+\s*," mapanare/self/*.mn
mapanare/self/emit_llvm.mn:3724:        // (golden 47 — `?` operator on Result<Int, String>). Two
mapanare/self/from_go.mn:733:    // Multiple return types: (Type, error) → Result<Type, String>
# Both are comments, not actual usage.

# Err/Ok at return position in self-host:
$ grep -nE "^\s*(da|return)\s+(Err|Ok)\(" mapanare/self/*.mn
# (no matches)

# Matches with 15+ arms in mapanare/self/ (heuristic):
mapanare/self/lower.mn:3449  12 arms
mapanare/self/mnc_all.mn:350 241 arms  # the chained_cmp lowering match
mapanare/self/mnc_all.mn:5907 184 arms
mapanare/self/mnc_all.mn:7384 12 arms
mapanare/self/mnc_all.mn:10893 12 arms
```

The 184/241-arm matches are existing chained_cmp arm tables that
work today — they are not nested inside an outer `Err(e)`
destructure with mismatched Result wrap shape, so Lf.3's specific
trigger condition does not apply. Self-host stage1 builds and runs
correctly, and STRICT 3-stage fixed point holds.

The self-host neither emits buggy `da Err(...)` returns nor
exercises the nested-match-on-corrupt-tag pattern. **Stage1's own
behavior is not affected by the bugs.**

---

## Fix-site localization

| Bug | Fix site | Notes |
|---|---|---|
| Lf.1 | `mapanare/lower.py:2398-2412` (`Ok` branch) and `:2413-2429` (`Err` branch) | Backport v5.26.1 Eu.2 `current_fn.return_type` consultation. |
| Lf.2 | Same as Lf.1 | Inner function's wrap propagates the wrong shape. |
| Lf.3 | Same as Lf.1 | The corrupt tag is a downstream effect of Lf.1's wrap. |
| Lf.4 | `mapanare/semantic.py:2069` (variant registration) + lookup site | Out of scope for v5.46.0 — see decision below. |

---

## Lf.4 bundle/split decision

**Decision: SPLIT to v5.46.x.**

**Rationale:** the Lf.4 fix needs:

1. A multimap of `(variant_name) → list[(enum_name, return_type, arity)]`
   built during `_register_definitions`.
2. Constructor expression resolution that consults the binding's
   declared type when present, falls back to the existing single-
   match path otherwise.
3. Match-pattern resolution that keys on `(subject_type, variant_name)`.
4. Coordinated edits in `mapanare/semantic.py` (resolution sites)
   and possibly `mapanare/lower.py` (variant-name dispatch).

LOC estimate: ≥ 50, distributed across two files. Exceeds PLAN's
≤ 30 LOC bundle threshold. Per `PROMPT.md` policy
(>30 → split; default to split), Lf.4 ships at v5.46.x as a
separate release.

This is the same scope-discipline pattern as v5.41.0 (option-B
split: tensor reshape v5.41.0, mutable views + stepped slices
deferred), v5.39.x (typed-serde TypeKind closure across releases),
and v5.42.0 (As.\* supervision split — strategy library at v5.42.0,
spawn-restart ergonomic at v5.43.0).

---

## PLAN deviations surfaced

1. **Lf.5 self-host mirror is a NO-OP gate.** The PLAN budgeted ~4h
   for self-host mirror edits. Phase 0 found the self-host
   already has the v5.26.1 Eu.2 fix (Python is the side that
   needs to mirror, not the other way around). Lf.5 collapses to
   a STRICT preservation check; zero `mapanare/self/*.mn` edits.
2. **Lf.1 + Lf.2 + Lf.3 share one root cause** — the PLAN
   hypothesized Lf.1 + Lf.2 may share, with Lf.3 independent.
   IR diagnosis confirms all three trace to the same WrapErr/
   WrapOk default-Result-shape bug. **One fix closes all three.**
3. **Lf.4 splits** — see decision above. PLAN allowed for split.
4. **No new C runtime exports.** PLAN flagged this as a possibility;
   confirmed not needed.
5. **No drop-glue / aliasing edits.** Different bug class than
   v5.45.0; standard pytest gate suffices.

---

## Estimated LOC delta (refined post-Phase-0)

| Layer | Lines | Notes |
|---|---|---|
| `mapanare/lower.py` | ~30 | Backport Eu.2 logic into Python `Ok`/`Err` branches. |
| `mapanare/self/*.mn` | 0 | Already has the fix. STRICT preserved by construction. |
| `tests/llvm/test_lowerer_fixes.py` | ~150 | Pytest harness with revert+restore round-trip per case. |
| `tests/golden/100_*.mn` | ~50 | Lf.1 regression. |
| `tests/golden/101_*.mn` | ~60 | Lf.2 regression. |
| `tests/golden/102_*.mn` | ~80 | Lf.3 regression covering arm-count {3, 10, 15, 16, 20}. |
| Lf.6 broader sweep | ~10 (no edits expected) | Audit only; SESSION_REPORT entries. |
| CHANGELOG / SPEC / CLAUDE.md | ~80 | Three `### Fixed` entries (Lf.1, Lf.2, Lf.3). |
| **Total** | **~460 LOC** | Well under v5.43.0's ~2,500 LOC delta. |

---

## Falsifiability protocol

For each fix:

1. Pre-fix: `/tmp/diag_lf{N}*.mn` produces broken output (`kind=1`,
   IR validation error, silent no-fire respectively).
2. Apply fix to `mapanare/lower.py` `Ok`/`Err` branches.
3. Re-run: each repro now produces the expected output.
4. Revert the fix: each repro reverts to broken output.
5. Re-apply the fix: green again. Round-trip locked.

Each new pytest module documents this in its docstring and
includes test cases that would FAIL without the fix.

---

## Closeout

PRE_PHASE_AUDIT confirms PLAN/PROMPT premise. Phase 1 proceeds
with the single Python lower.py edit; Phases 2 and 3 fold into
the same edit (one fix, three regression tests). Lf.4 split.
Phase 4 (self-host mirror) reduced to STRICT preservation check.
Phases 5-7 unchanged.
