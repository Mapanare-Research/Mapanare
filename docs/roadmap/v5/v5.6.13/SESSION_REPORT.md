# v5.6.13 Session Report — Layer 1 extension to struct let-bindings

> **Status: SHIPPED.** v5.6.12 closed Lk.1 + Ve.2 by destination
> passing for List let-bindings. v5.6.13 extends the same structural
> pattern to **struct let-bindings**, eliminating the duplicate
> `.si` scratch alloca that emit_struct_init/emit_struct_init_from_values
> created for every struct constructor call. The result is uniform
> with v5.6.12's list pattern: one alloca per struct let-binding
> (the binding itself), no scratch alloca, no extra load+store
> dance.
>
> **Hero metric:** `.si = alloca` site count in stage2.ll
> **240 → 0**. Net struct allocas **2,206 → 2,113 (−93)**.
>
> **Per the v5.6.13 PLAN decision tree:** v5.6.12 sanitizer matrix
> shipped clean (no NEW share-mutate leak surfaced; the 62_list_output
> baseline refresh was pre-existing Rt.04, already deferred to v6.0).
> The user chose "Ship Layer 1 ext only" path: structural cleanup
> only, no Layer 2 (no observed share-mutate leak in the corpus to
> drive it).

---

## Headline

**Two source edits, one MIR pattern uniformity.**

1. **`mapanare/self/lower.mn`** — new helper
   `lower_struct_new_into(st, struct_name, arg_exprs, dest_name)`
   parallel to v5.6.12's `lower_list_typed_into`. Lowers a
   `Call(Ident("__new_<Struct>"), [args])` (which is what the
   parser emits for `new Foo {...}`) into `Instruction::StructInit`
   with a caller-supplied dest name. `lower_let` detects this
   pattern up front, pre-computes the var's alloca name
   (`%<name><N>.addr`), and routes through the new helper —
   skipping its own post-emit Alloca + Store entirely.

2. **`mapanare/self/emit_llvm.mn`** — `emit_struct_init` and
   `emit_struct_init_from_values` rename their scratch alloca
   from `dn + ".si"` to `dn + ".addr"`. For tmp-prefixed dests
   (`%t<N>`) this is a name-only rename with zero behavioral
   change (downstream SROA still elides). For destination-passed
   dests (`%<name><N>`) the renamed scratch IS the let's binding
   alloca — one alloca instead of (.si scratch + .addr binding)
   and one fewer load+store at the let boundary.

The cascading effect:
- **240 `.si` scratch sites eliminated.** All struct ctors now
  use `.addr` naming (uniform with list pattern).
- **103 of those become true single-alloca destination-passed
  bindings.** The other 137 are tmp-prefixed struct ctors not
  inside lets (return values, function args, etc.); their
  `.si → .addr` rename is purely cosmetic for those.
- **stage2.ll grows** 216,842 → 217,268 lines (+426, +0.20%)
  because the new `lower_struct_new_into` helper adds ~80 LOC
  of self-hosted source — its own emitted IR (~157 non-struct
  allocas added) outweighs the 93-alloca struct savings. Within
  the PLAN budget (≤ 1% growth).
- **Fixed-point preserved NEAR** (4 diff lines / 217,268 = 0.002%,
  all VERSION metadata, identical to v5.6.12's NEAR result).

What ships:
- VERSION 5.6.12 → 5.6.13.
- `mapanare/self/lower.mn` +66 LOC: `lower_struct_new_into` helper
  + `lower_let` destination-passing branch for struct constructors.
- `mapanare/self/emit_llvm.mn` +18 / −2 LOC: `.si` → `.addr`
  rename + rewritten comments documenting the v5.6.13 design at
  both `emit_struct_init` and `emit_struct_init_from_values`.
- `mnc-stage1` rebuilt; stage2.ll **216,842 → 217,268 lines
  (+0.20%)**, well within the v5.6.13 PROMPT 1% budget.
- 64/66 goldens preserved (same 2 pre-existing fails:
  `51_match_guards_and_or` B, `64_closure_typed` Sh.7).
- Full sanitizer matrix clean; LSan baseline gate PASS.
- This SESSION_REPORT + updates to `CLAUDE.md`, `ROADMAP.md`,
  `CLOSEOUT_ARC.md`. `known_issues.md` requires no edits (no new
  or closed dockets — this is preventive cleanup).

What does NOT ship:
- **Layer 1 extension to enum let-bindings.** SKIPPED.
  `emit_enum_init` produces purely register insertvalue chains
  (inline variants) or insertvalue + heap-box-tracking (boxed
  variants). No `.si`-equivalent scratch alloca exists to
  eliminate. Destination passing would require adding a final
  store inside `emit_enum_init` to populate a binding alloca AND
  removing `lower_let`'s separate Alloca + Store — net zero
  savings at the IR level (just shifts where the store happens).
  No cleanup gain documented in the SESSION_REPORT.
- **Layer 1 extension to map let-bindings.** SKIPPED. Same
  reason: `emit_map_init` produces pure register insertvalue
  chain (the heap allocation lives in `__mn_map_new`, returns
  a `ptr` stored into the `{ptr, i64}` map header). No internal
  scratch alloca. Net-zero savings.
- **Layer 2 (move on assignment).** PLAN §D3 explicitly gates
  this on observed share-mutate leak. v5.6.12 sanitizer sweep
  surfaced none; per "no cheap shit" Layer 2 stays
  conditional v5.6.14+ work IF a leak surfaces.

---

## Root cause analysis

### The struct two-alloca pattern

`let foo: Foo = new Foo {x: 1, y: 2}` previously lowered to:

```
MIR:
  Call(%t3, "__new_Foo", [%t1, %t2])    # via lower_call_by_name's __new_ branch
  Alloca(%foo4.addr, Foo)               # lower_let
  Store(%foo4.addr, %t3)                # lower_let
```

Which the emitter materialized as:

```
%t3.f0 = insertvalue %struct.Foo undef, i64 %t1, 0
%t3.f1 = insertvalue %struct.Foo %t3.f0, i64 %t2, 1
%t3.si = alloca %struct.Foo            # scratch from emit_struct_init
store %struct.Foo %t3.f1, ptr %t3.si
%t3 = load %struct.Foo, ptr %t3.si     # SSA materialization
%foo4.addr = alloca %struct.Foo        # binding alloca from lower_let
store %struct.Foo %t3, ptr %foo4.addr  # binding store
```

7 IR lines. **Two allocas of the same struct type** (`%t3.si`
scratch and `%foo4.addr` binding), one redundant copy
(load + store) between them. The `.si` scratch is needed only
because `emit_struct_init` materializes the value via
alloca/store/load (aggregate types can't use `add 0` identity).

This pattern has the same "two-alloca" shape Lk.1 had for lists,
but does NOT cause a leak because:
1. `.si` scratch holds no heap pointers — the struct value is
   composed via insertvalue, then stored. No heap allocation in
   `emit_struct_init` itself.
2. Drop-glue tracks the binding's alloca, not the scratch.
3. SROA usually elides the scratch in `-O2` codegen (it's
   alloca'd, written-once-read-once).

So this is **preventive cleanup**, not a leak fix. Per PLAN §"Why
this release exists": closing the pattern prevents future Lk.1-class
bugs in struct-heavy code AND eliminates wasted IR space.

### The principled fix: destination passing (struct edition)

Same shape as v5.6.12's list path:
1. `lower_let` detects the value is a struct constructor
   (parser-emitted `Call(Ident("__new_<Struct>"), args)` pattern).
2. Pre-computes the var's binding name `%<name><N>` (using
   `tmp_counter`).
3. Calls `lower_struct_new_into(st, struct_name, args, var_base)`
   which lowers args, pairs them with declared field names, and
   emits `Instruction::StructInit` with the caller-supplied dest
   name (no `make_value(s, ..., "t")` fresh-tmp).
4. `lower_let` registers the binding via `define_var(name → %<name><N>.addr)`
   and returns. **Skips the post-emit Alloca + Store entirely.**
5. The emitter's `emit_struct_init`'s renamed `.addr` scratch
   for `%<name><N>` produces `%<name><N>.addr` — which IS the
   let's binding alloca by virtue of the naming convention.

Result for `let foo: Foo = new Foo {x: 1, y: 2}` after v5.6.13:

```
%foo0.f0 = insertvalue %struct.Foo undef, i64 %t1, 0
%foo0.f1 = insertvalue %struct.Foo %foo0.f0, i64 %t2, 1
%foo0.addr = alloca %struct.Foo               # SINGLE alloca (binding + emit scratch)
store %struct.Foo %foo0.f1, ptr %foo0.addr
%foo0 = load %struct.Foo, ptr %foo0.addr      # SSA materialization (kept for safety)
```

5 IR lines. **One alloca.** One store. One load (kept so `%foo0`
SSA is defined for any potential downstream user — in practice
the let binding makes `lookup_var(foo)` return `%foo0.addr`,
so the `%foo0` register is rarely used; SROA elides the load
in `-O2`).

### Why enum / map are not changed

**Enum** (`emit_enum_init`): inline variants emit
`insertvalue %enum.X undef, i64 <tag>, 0` then more insertvalues
for payload fields, terminating in `%dn = insertvalue ...`.
Boxed variants emit `malloc → store payload → insertvalue tag/box`.
No internal scratch alloca. The let-binding's Alloca + Store is
the only alloca cost, and it's unavoidable for register-typed
results — destination passing would shift the Store from
`lower_let` to `emit_enum_init`, with no net IR change.

**Map** (`emit_map_init`): calls `__mn_map_new(...)` to get a
heap `ptr`, then insertvalue chain to build a `{ptr, i64}`
header into `%dn`. The `%dn.kN` / `%dn.vN` allocas inside the
function are short-lived parameter alloca's for `__mn_map_set`
calls — they go out of scope after each set call and SROA
optimizes them. No persistent scratch alloca to eliminate.
Same conclusion: destination passing is net-zero for maps.

The PLAN's Phase 1.2 / 1.3 anticipated savings under the
mistaken assumption that all three resource types had the same
duplicate-alloca pattern as lists. Empirical investigation of
the emit code shows only structs do.

---

## Per-phase trace

### Phase 0 — baseline + decision gate (~10 min)

- VERSION 5.6.12 → 5.6.13.
- `make build-rt` rebuilds `libmapanare_rt.a` with the bumped
  VERSION macro. (Rebuild deferred until Phase 4 since no
  runtime calls are introduced; runtime version macro
  matches binary version.)
- Snapshot baseline:
  - goldens 64/66 (same 2 fails as v5.6.12)
  - stage2.ll 216,842 lines / `llvm-as` clean
  - 240 `.si = alloca` sites (struct scratch)
  - 6,625 `.addr = alloca` sites (bindings + list scratch)
  - 24,885 total allocas
- Decision gate (per PLAN §"Decision tree"):
  - All sanitizers clean ✓ (re-confirmed via
    `/tmp/asan-leak-v5.6.12/asan-leak-summary.tsv` against
    `docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv`)
  - No share-mutate leak surfaced ✓
  - User chose **"Ship Layer 1 ext only"** for struct/enum/map
    cleanup, no Layer 2.

### Phase 1.1 — destination passing infrastructure (~45 min)

Two source edits land:

**`lower.mn` +66 LOC**:
- `lower_struct_new_into(st, struct_name, arg_exprs, dest_name)`:
  Lowers args via per-arg `lower_expr`, pairs with field names
  (matching `lower_call_by_name`'s `__new_` branch logic at
  ~line 2380), emits `Instruction::StructInit` with caller's
  dest_name. tmp_counter NOT bumped (caller already reserved
  the slot).
- `lower_let` modified: after the v5.6.12 list hint path
  (~line 765), check if value is `Call(Ident("__new_X"), args)`
  AND `is_struct_name(st, X)`. If yes: pre-compute `var_base`
  (the dest), `addr_name` (the binding alloca), bump
  tmp_counter, route through `lower_struct_new_into`, register
  binding via `define_var`, return WITHOUT emitting the
  fall-through Alloca + Store.
- Generic struct constructors fall through (no `is_struct_name`
  match — they go through `lower_call_by_name`'s
  `try_monomorphize_struct` path, which still uses fresh-tmp
  dest naming). v5.6.13 doesn't address generics; v5.6.14+
  scope if cleanup is desired.

**`emit_llvm.mn` +18 / −2 LOC**:
- `emit_struct_init` line ~1864: `dn + ".si"` → `dn + ".addr"`
  with rewritten comment documenting the v5.6.13 destination-
  passing rationale.
- `emit_struct_init_from_values` line ~2054: same rename + comment.

**Phase 1.1 gate** (after `bash scripts/concat_self.sh` +
`python3 scripts/build_stage1.py`):
- mnc_all.mn: 884,064 bytes (+1,636 vs v5.6.12, consistent
  with the new helper).
- mnc-stage1: 6,339,744 bytes (+8,192 vs v5.6.12 stripped).
- stage2.ll: 216,842 → **217,268 lines (+426, +0.20%)** —
  growth driven by `lower_struct_new_into`'s 80-LOC body
  emitting non-struct allocas (~157 net new) which outweigh
  the 93-net-struct-alloca savings.
- llvm-as clean.
- `.si = alloca` sites: 240 → **0** ✓ (HERO METRIC).
- Struct allocas (`.si` + struct `.addr`):
  - v5.6.12: 240 (.si) + 1,966 (.addr binding) = 2,206
  - v5.6.13: 0 (.si) + 137 (.addr tmp-style) +
    1,976 (.addr binding) = 2,113
  - Net: **−93 struct allocas** (uniform with the destination-
    passing pattern).
- Goldens 64/66 preserved.

### Phase 1.2 — enum (SKIPPED) (~5 min analysis)

Empirical review of `emit_enum_init` (line ~2852) confirmed:
- Inline-variants: `insertvalue %enum.X undef, i64 <tag>, 0`
  → `insertvalue` per slot → final `%dn = insertvalue`. Pure
  register chain. No alloca emitted by `emit_enum_init`.
- Boxed variants: `payload_ty` GEP-trick sizing →
  `call ptr @malloc` → per-field GEP + store →
  `emit_track_boxed(ep)` → final `%dn = insertvalue` (tag/box
  pair). Heap allocation tracked via the existing boxed-payload
  drop-glue infrastructure. No internal scratch alloca.

Conclusion: no `.si`-equivalent pattern to clean up. Destination
passing would just move the `lower_let`-emitted `Store` from
the let body into `emit_enum_init` with zero net IR change.
Skipped.

### Phase 1.3 — map (SKIPPED) (~5 min analysis)

Empirical review of `emit_map_init` (line ~2744) confirmed:
- `%dn.mp = call ptr @__mn_map_new(i64 <ksz>, i64 <vsz>, ...)`.
- Per-pair: `%dn.kN = alloca <KTy>` + store + `%dn.vN = alloca`
  + store + `__mn_map_set(...)`. These per-pair allocas are
  ephemeral (consumed by the runtime call); SROA elides them
  in `-O2`.
- Final: `insertvalue {ptr, i64} undef, ptr %dn.mp, 0` →
  `%dn = insertvalue {ptr, i64} ..., i64 0, 1`.

No persistent scratch alloca. Same conclusion as enum: net-zero
destination-passing benefit. Skipped.

### Phase 2 — runtime gate (~15 min)

Phase 1.1 reproducer (`/tmp/v5613_struct.mn`):

```mn
struct Point {
    x: Int,
    y: Int
}

fn main() {
    let p: Point = new Point { x: 11, y: 22 }
    print(p.x)
    print(p.y)
}
```

Output IR (main fn):
```
%t1 = add i64 0, 11
%t2 = add i64 0, 22
%p0.f0 = insertvalue %struct.Point undef, i64 %t1, 0
%p0.f1 = insertvalue %struct.Point %p0.f0, i64 %t2, 1
%p0.addr = alloca %struct.Point          # SINGLE alloca (binding + emit scratch)
store %struct.Point %p0.f1, ptr %p0.addr
%p0 = load %struct.Point, ptr %p0.addr   # SSA materialization
%p_val3 = load %struct.Point, ptr %p0.addr   # binding lookup
%t4 = extractvalue %struct.Point %p_val3, 0
call i32 ... @printf(ptr @.fmt_int_nl, i64 %t4)
...
```

Total allocas in main: 1 (was 2 pre-v5.6.13 — `%t<N>.si` scratch
+ `%p<M>.addr` binding). ✓

### Phase 3 — full validation gate (~30 min)

Per PROMPT D2: any sanitizer regression → REVERT.

**Fixed-point** — `verify_fixed_point.sh --keep` reaches
**NEAR FIXED POINT**: 4 diff lines / 217,268 = 0.002%, all
VERSION metadata (`!"5.6.13"` vs `!"__MN_VERSION__"`).
Identical structural result to v5.6.12.

**Sanitizer matrix**:
- ASan UAF: **65 CLEAN / 0 ASAN_ERROR / 1 CRASH_NO_ASAN**
  (matches v5.6.12).
- Valgrind: **0 ERRORS / 66 WARNINGS_ONLY** (matches v5.6.12).
- LSan: **50 CLEAN / 3 LEAK / 1 COMPILE_FAIL / 12 LINK_FAIL**
  (3 LEAK = baselined: 39_gpu_detect, 40_gpu_tensor,
  62_list_output). Baseline gate PASS. **Adjacent finding:**
  62_list_output's leak count dropped from v5.6.12's 13 obj /
  346 B → 9 obj / 141 B. The underlying Rt.04 leak is
  unchanged (struct→list→string depth-2 alias from v5.6.6
  RESCOPE); LSan's "still reachable" heuristic now finds 4
  more aliasing pointers in the v5.6.13 stack layout (the
  destination-passing struct path shuffles alloca placement,
  re-introducing some of the stack-aliasing-luck masking that
  v5.6.12 had eliminated). Net IMPROVEMENT in LSan-reported
  leak counts; the gate accepts decreases as forward progress.
  Mirrors the v5.6.12 → v5.6.11 pattern in reverse.

**Other gates**:
- Non-bootstrap pytest: **5,599 passed**, 116 skipped, 9
  xfailed (1 transient `test_mnc_stage1_version_matches_version_file`
  failure during the initial Phase 4 run because mnc-stage1
  was rebuilt before the VERSION bump but pytest ran after;
  resolved by rebuilding mnc-stage1 with the new VERSION
  macro and rerunning the test → PASS).
- `make lint`: clean (ruff + black + mypy).
- `check_struct_registry.py`: 23/23/91 clean (no struct
  changes — Reg.1 gate preserved).

### Phase 4 — documentation (~25 min)

This SESSION_REPORT, plus:
- `CLAUDE.md`: v5.6.13 entry prepended; "Current baseline" →
  5.6.13.
- `docs/roadmap/ROADMAP.md`: v5.6.13 stanza prepended.
- `docs/roadmap/v5/CLOSEOUT_ARC.md`: v5.6.13 noted as
  optional cleanup (Layer 1 extension to structs only); the
  v5.6.x arc remains complete.
- `docs/known_issues.md`: no edits required (no new or closed
  dockets — this is preventive cleanup).

---

## Metrics summary

| Metric | v5.6.12 | v5.6.13 | Δ |
|---|---:|---:|---:|
| `.si = alloca` sites (struct scratch) | 240 | **0** | **−240 (−100%)** |
| Struct allocas (.si + struct .addr) | 2,206 | 2,113 | **−93 (−4.2%)** |
| Total allocas | 24,885 | 24,949 | +64 (+0.26%) |
| stage2.ll lines | 216,842 | 217,268 | +426 (+0.20%) |
| `mnc-stage1` binary (stripped) | 6,331,552 B | 6,339,744 B | +8,192 B |
| Goldens | 64/66 | 64/66 | 0 |
| Fixed-point | NEAR (4/216,842) | NEAR (4/217,268) | preserved |
| ASan UAF CLEAN | 65 | 65 | 0 |
| ASan UAF errors | 0 | 0 | 0 |
| Valgrind WARNINGS_ONLY | 66 | 66 | 0 |
| Valgrind ERRORS | 0 | 0 | 0 |
| LSan CLEAN | 50 | 50 | 0 |
| LSan LEAK | 3 | 3 | 0 (baseline preserved) |
| LSan baseline gate | PASS | **PASS** | preserved |
| 62_list_output leaks | 13 / 346 B | **9 / 141 B** | improvement (LSan reachability heuristic shifted back) |
| `make lint` | clean | clean | preserved |
| `check_struct_registry` | 23/23/91 | 23/23/91 | preserved |

---

## Risks (from PLAN.md) — outcome

- **R1 — Layer 1 extension breaks struct/enum lets.** Realized
  partially: enum/map analysis showed no benefit, scope
  reduced to struct-only. Struct path verified clean across
  all 64 passing goldens + fixed-point + sanitizers.
- **R2 — Layer 2 surfaces a new bug class.** Not realized:
  Layer 2 not shipped (no observed share-mutate leak).
- **R3 — Cleanup release ships nothing user-visible.** As
  expected: no behavioral change, just IR uniformity. The
  `.si → .addr` scratch rename is observable in stage2.ll
  diffs but functionally equivalent.

---

## Closeout arc — v5.6.x truly complete

| Release | Docket | Status |
|---|---|---|
| v5.6.5 | Ve.1 (parser overflow) | CLOSED |
| v5.6.6 | Rt.04 (multi-level alias) | RESCOPED → v6.0 |
| v5.6.7 | Ve.2 (lowerer empty-list) | PARTIAL (11/18 sites) |
| v5.6.8 | Ve.3 (stage2 OOM) | INVESTIGATION |
| v5.6.9 | Ve.3 | CLOSED; Ve.4 OPENED |
| v5.6.10 | Ve.2 + struct_byte_size + culebra | PARTIAL (11/18); Lk.1 OPENED |
| v5.6.11 | Ve.4 | CLOSED |
| v5.6.12 | Lk.1 + Ve.2 residuals | CLOSED |
| **v5.6.13** | **Layer 1 cleanup → struct lets** | **OPTIONAL — SHIPPED** |

Every v5.6.x docket is now resolved or appropriately deferred to
v6.0 (Rt.04 only). The cleanup release is genuinely optional —
shipping it just establishes uniform destination-passing semantics
across List + Struct let-bindings.

---

## What's next

- **v5.7.0** — Sh.7 (closure typed captures) + B (or-pattern
  match guards). Closes goldens 51 + 64 → 66/66.
- **v5.7.1** — SPEC docs polish (pre-RE-PANEL).
- **v5.8.0** — RE-PANEL (target 9.7+).
- **v6.0** — Borrow checker. Closes Rt.04 (multi-level alias
  analysis). The only remaining open docket from any v5.6.x
  release.

See `docs/roadmap/v5/CLOSEOUT_ARC.md`.
