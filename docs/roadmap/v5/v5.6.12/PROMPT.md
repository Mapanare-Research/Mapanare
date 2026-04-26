# v5.6.12 Execution Prompt — Lk.1 close + Ve.2 residuals + floor drop

> Read `PLAN.md` first. Single-focus release: close Lk.1 at root
> cause via destination-passing for List let-bindings. Cascading
> wins: scalar gate applied, 384-byte floor dropped, Ve.2
> residuals (7 sites) closed.
>
> Estimated: 1-2 sessions (~3-5 hours). Investigation-first per
> v5.6.11's eprint-instrumentation lesson: instrument, verify
> the predicted IR shape, then validate end-to-end.

---

## Read before starting

1. `docs/roadmap/v5/v5.6.12/PLAN.md` — this release's plan.
2. `docs/roadmap/v5/v5.6.11/SESSION_REPORT.md` — Ve.4 closure;
   the runtime-elem_size load this release piggybacks on.
3. `docs/roadmap/v5/v5.6.10/SESSION_REPORT.md` — Lk.1 opening +
   Phase 1B revert decision (the leak shape we're now fixing).
4. `docs/known_issues.md` Lk.1 + Ve.2 rows.
5. `mapanare/self/lower.mn::lower_let` (line 741) — entry point.
6. `mapanare/self/lower.mn::lower_list_typed` (~line 3398) —
   path that gets the dest hint.
7. `mapanare/self/emit_llvm.mn::emit_list_init` (~line 2416) —
   alloca creation + scalar gate site.

---

## Environment

**WSL2 required**. All commits land on `dev`. Tagging + pushing
requires explicit user approval.

`ulimit -s unlimited` is required for `mnc-stage2 mnc_all.mn`.

---

## GitNexus pre-flight (MANDATORY before edit)

```bash
npx gitnexus analyze --embeddings
```

```
gitnexus_impact({target: "lower_let", direction: "upstream"})
gitnexus_impact({target: "lower_list_typed", direction: "upstream"})
gitnexus_impact({target: "emit_list_init", direction: "upstream"})
gitnexus_query({query: "destination passing alloca let-binding"})
```

`lower_let` and `lower_list_typed` are HIGH-impact (every let
of a list literal flows through them). Treat as load-bearing.

---

## Phase 0 — Reproducer + baseline (~15 min)

```bash
echo "5.6.12" > VERSION
make build-rt

# Snapshot v5.6.11 baseline
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
    2>&1 | tee /tmp/v5.6.12-goldens-before.log
grep -c "^PASS" /tmp/v5.6.12-goldens-before.log    # expect 64

mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.12-before.ll
wc -l /tmp/stage2-v5.6.12-before.ll                 # expect ~217,273 (v5.6.11)
llvm-as /tmp/stage2-v5.6.12-before.ll -o /dev/null && echo OK

# Confirm 7 floor sites
grep -c "__mn_list_new(i64 384)" /tmp/stage2-v5.6.12-before.ll
# expect 7

# Confirm 65_list_int_indexing baseline (LSan baseline says CLEAN
# at v5.6.11 because Lk.1 floor masks the leak; we expect this to
# stay CLEAN after the fix too — but for a different reason)
grep "65_list_int_indexing" docs/roadmap/v5/v5.4.2/baseline/asan-leak-baseline.tsv
```

Reproducer for visible Lk.1 (currently masked by floor; will
become visible if scalar gate applied without destination passing):

```mn
// /tmp/lk1.mn — minimal reproducer for the alloca-aliasing pattern
fn build() -> Int {
    let mut arr: List<Int> = []
    arr.push(1)
    arr.push(2)
    arr.push(3)
    let mut sum: Int = 0
    for i in 0..len(arr) {
        sum = sum + arr[i]
    }
    return sum
}
fn main() { print(build()) }
```

Commit version bump:
```bash
git add VERSION docs/roadmap/v5/v5.6.12/PLAN.md \
    docs/roadmap/v5/v5.6.12/PROMPT.md
git commit -m "v5.6.12: planning — Lk.1 close + Ve.2 residuals"
```

---

## Phase 1 — Destination-passing infrastructure (~60 min)

### 1.1 — Add `lower_list_typed_into` in `lower.mn`

```mn
// v5.6.12 — destination-passing variant. When dest_alloca is
// Some, the ListInit's dest SSA name is derived from the alloca
// so that emit_list_init's `dn + ".addr"` convention yields the
// pre-existing alloca. No intermediate %t0.addr scratch.
fn lower_list_typed_into(st: LowerState, elements: List<Expr>, hint_elem: MIRType, dest_alloca: Option<Value>) -> LowerResult {
    match dest_alloca {
        Some(addr) => {
            // Strip the trailing ".addr" from addr.name so the
            // emitter's dn + ".addr" reconstructs the original.
            let stripped: String = strip_addr_suffix(addr.name)
            let dest: Value = new_value(stripped, mir_list_of(hint_elem))
            // ... emit ListInit(dest, hint_elem, lowered_elements) ...
            // (mirror the existing lower_list_typed body but with
            //  dest = stripped name instead of fresh_tmp)
        },
        None => {
            return lower_list_typed(st, elements, hint_elem)  // existing path
        }
    }
}

fn strip_addr_suffix(name: String) -> String {
    // "%indices0.addr" → "%indices0"
    if name.ends_with(".addr") {
        return name.substr(0, len(name) - 5)
    }
    return name
}
```

### 1.2 — Modify `lower_let` to use destination passing for empty-list

In `lower_let` at the existing fast-path:
```mn
let hint_elem: MIRType = lower_let_list_hint(st, value, type_ann)
if hint_elem.kind != TK_UNKNOWN() {
    // v5.6.12 — destination passing. Pre-create the var alloca,
    // emit ListInit directly into it, skip the post-emit
    // Alloca + Store pair (those would create a duplicate alloca
    // and a useless copy — exactly the Lk.1 pattern).
    let val_ty: MIRType = mir_list_of(hint_elem)
    let addr_name: String = "%" + name + toString(s.tmp_counter) + ".addr"
    s.tmp_counter = s.tmp_counter + 1
    let addr: Value = new_value(addr_name, val_ty)
    let r: LowerResult = lower_list_typed_into(s, expr_list_elements(value), hint_elem, Some(addr))
    s = r.state
    s = define_var(s, name, addr, mutable)
    return s
}
// ... existing fall-through path for non-empty-list values ...
```

### 1.3 — Verify the IR shape

```bash
bash scripts/concat_self.sh
python3 scripts/build_stage1.py 2>&1 | tail -3
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-phase1.ll 2>/dev/null
llvm-as /tmp/stage2-phase1.ll -o /dev/null && echo "phase1 llvm-as OK"

# Inspect build_match_arms IR — should have ONE alloca for indices,
# not two
grep -A 5 "@build_match_arms" /tmp/stage2-phase1.ll | head -30
grep -c "alloca {ptr, i64, i64, i64, i64}" /tmp/stage2-phase1.ll
# Expect: smaller count vs v5.6.11
```

The IR for `let mut indices: List<Int> = []` should now be:
```
%indices0.addr = alloca {ptr,i64,i64,i64,i64}, align 8
store {ptr,i64,i64,i64,i64} zeroinitializer, ptr %indices0.addr
%indices0.new = call ... @__mn_list_new(i64 8)
store ... %indices0.new, ptr %indices0.addr
%indices0 = load ..., ptr %indices0.addr
```

NOT (the old shape):
```
%t0.addr = alloca ...
store zeroinit, %t0.addr
%t0.new = call ... __mn_list_new(i64 384)
store %t0.new, %t0.addr
%t0 = load ..., %t0.addr
%indices0.addr = alloca ...   ← DUPLICATE
store %t0, %indices0.addr     ← USELESS COPY
```

---

## Phase 2 — Apply scalar gate + drop floor (~20 min)

In `emit_list_init` (~line 2454):

```mn
// BEFORE (v5.6.11):
let mut elem_sz_n: Int = llvm_type_size(elem_llvm_ty)
if elem_sz_n < 384 { elem_sz_n = 384 }
s = emit_line(s, emit_call_ir(list_name, llvm_list_rt(), "__mn_list_new", "i64 " + toString(elem_sz_n)))

// AFTER (v5.6.12):
// v5.6.12 — scalar gate. With Lk.1 closed via destination passing
// (let-binding alloca IS the ListInit's storage; no two-alloca
// pattern), the 384-byte floor is no longer needed to mask the
// alloca-aliasing leak. Use exact LLVM type size for known
// scalar elem_ty; keep floor as defensive fallback for
// genuinely-unknown elem_ty.kind.
let mut elem_sz_n: Int = llvm_type_size(elem_llvm_ty)
if elem_ty.kind == TK_UNKNOWN() {
    if elem_sz_n < 384 { elem_sz_n = 384 }
}
s = emit_line(s, emit_call_ir(list_name, llvm_list_rt(), "__mn_list_new", "i64 " + toString(elem_sz_n)))
```

Rebuild:
```bash
bash scripts/concat_self.sh
python3 scripts/build_stage1.py 2>&1 | tail -3
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.12.ll 2>/dev/null
echo "stage2.ll lines: $(wc -l < /tmp/stage2-v5.6.12.ll)"
llvm-as /tmp/stage2-v5.6.12.ll -o /dev/null && echo OK

# HERO METRIC #1: floor sites = 0
grep -c "__mn_list_new(i64 384)" /tmp/stage2-v5.6.12.ll
# expect: 0 (was 7)

# Sanity: List<Int> alloc uses elem_size=8
grep "__mn_list_new(i64 8)" /tmp/stage2-v5.6.12.ll | head -3
```

---

## Phase 3 — Goldens + fixed-point + sanitizers (~45 min)

```bash
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1 \
    2>&1 | tee /tmp/v5.6.12-goldens-after.log
diff /tmp/v5.6.12-goldens-before.log /tmp/v5.6.12-goldens-after.log | head
# expect: only timing variation; same 64/66

# Build stage2 binary + run reproducer
clang -O2 /tmp/stage2-v5.6.12.ll runtime/native/libmapanare_rt.a \
    -lpthread -lm -ldl -o /tmp/mnc-stage2-v5.6.12
ulimit -s unlimited
/tmp/mnc-stage2-v5.6.12 /tmp/p3.mn > /tmp/p3.ll
echo "Ve.4 regression check: lines=$(wc -l < /tmp/p3.ll)"
llvm-as /tmp/p3.ll -o /dev/null && echo OK

# HERO METRIC #2: fixed-point
ulimit -s unlimited
bash scripts/verify_fixed_point.sh --keep 2>&1 | tee /tmp/v5.6.12-fp.log
tail -10 /tmp/v5.6.12-fp.log
# expect: NEAR or STRICT
```

Sanitizer matrix (parallel):
```bash
# Rebuild ASan binary
bash scripts/build_asan.sh 2>&1 | tail -3

# Run all three sweeps in parallel
ASAN_OUTDIR=/tmp/asan-v5.6.12 bash scripts/run_asan_goldens.sh &
VG_OUTDIR=/tmp/vg-v5.6.12 bash scripts/valgrind_all_goldens.sh &
ASAN_LEAK_OUTDIR=/tmp/asan-leak-v5.6.12 bash scripts/run_asan_leak_goldens.sh &
wait

awk -F'\t' 'NR>1 {print $5}' /tmp/asan-v5.6.12/asan-summary.tsv | sort | uniq -c
# expect: 65 CLEAN / 1 CRASH_NO_ASAN

awk -F'\t' 'NR>1 {print $NF}' /tmp/vg-v5.6.12/valgrind-summary.tsv | sort | uniq -c
# expect: 66 WARNINGS_ONLY

# HERO METRIC #3: 65_list_int_indexing CLEAN under LSan
grep "65_list_int_indexing" /tmp/asan-leak-v5.6.12/asan-leak-summary.tsv
# expect class=CLEAN

python3 scripts/check_leak_summary.py \
    /tmp/asan-leak-v5.6.12/asan-leak-summary.tsv 2>&1 | tail -5
# expect PASS

python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no 2>&1 | tail -3
make lint 2>&1 | tail -3
python3 scripts/check_struct_registry.py 2>&1 | tail -2
```

Per PROMPT D2: if any sanitizer regresses, REVERT.

---

## Phase 4 — Documentation (~30 min)

- `docs/roadmap/v5/v5.6.12/SESSION_REPORT.md` — write per the
  v5.6.11 SESSION_REPORT template:
  - Headline: Lk.1 + Ve.2 closed; floor sites 7 → 0
  - Root cause analysis: why destination passing is the
    structural fix (Rust-style result-location semantics)
  - Phase-by-phase summary
  - Metrics: stage2.ll size delta, floor count, LSan baseline
    delta, sanitizer counts
- `docs/known_issues.md`:
  - Flip Lk.1 row → CLOSED v5.6.12
  - Flip Ve.2 row → CLOSED v5.6.12 (residuals closed)
  - Update header date
- `docs/roadmap/v5/PARITY_GAPS.md`:
  - Move Lk.1 + Ve.2 rows to Historical
- `CLAUDE.md`:
  - v5.6.12 entry (prepended to "Most recent releases")
  - "Current baseline" → 5.6.12
- `docs/roadmap/ROADMAP.md`:
  - v5.6.12 stanza prepended
- `docs/roadmap/v5/CLOSEOUT_ARC.md`:
  - Note Lk.1 + Ve.2 closed (the v5.6.x arc is now genuinely
    complete with no v6.0 deferrals from this arc)

---

## Ready-to-ship checklist

- [ ] `VERSION` reads `5.6.12`
- [ ] `mnc-stage2 /tmp/p3.mn` produces non-empty `llvm-as`-clean
      IR (Ve.4 stays closed)
- [ ] `__mn_list_new(i64 384)` site count = 0 in stage2.ll
- [ ] `verify_fixed_point.sh --keep` reaches NEAR or STRICT
- [ ] Goldens 64/66 preserved
- [ ] stage2.ll growth ≤ 2% vs v5.6.11 (likely DECREASE)
- [ ] `llvm-as` clean
- [ ] Valgrind 0 ERRORS / 66 WARNINGS_ONLY
- [ ] ASan UAF 0 ASAN_ERROR / 65 CLEAN / 1 CRASH_NO_ASAN
- [ ] LSan baseline gate PASS (with 65_list_int_indexing CLEAN)
- [ ] Non-bootstrap pytest 0 failures
- [ ] `make lint` clean
- [ ] `check_struct_registry.py` 23/23/91 clean
- [ ] `known_issues.md`: Lk.1 + Ve.2 → CLOSED v5.6.12
- [ ] `PARITY_GAPS.md`: Lk.1 + Ve.2 moved to Historical
- [ ] SESSION_REPORT written
- [ ] CLAUDE.md + ROADMAP.md entries added
- [ ] No `/tmp/*` artifacts committed

---

## Commit + tag + push

```bash
git diff --cached --stat
gitnexus_detect_changes({scope: "staged"})

git commit -m "$(cat <<'EOF'
v5.6.12: Lk.1 + Ve.2 CLOSED — destination passing for List let-bindings

Closes Lk.1 (alloca-aliasing in inline list-get/push, opened
v5.6.10) at the structural root cause: the lowerer no longer
creates a separate scratch alloca (%t0.addr) for ListInit when
the result is being bound to a let. Instead, the let's pre-
created alloca IS the ListInit's storage — Rust's destination-
passing model (result-location semantics).

With Lk.1 closed at the source, the v5.6.10 scalar gate is
applied: emit_list_init's known-scalar path uses exact LLVM
type size (8 for i64, etc.) instead of the 384-byte floor.
The floor remains as defensive fallback for genuinely-unknown
elem_ty.kind only.

Cascading wins:
- 7 Ve.2 residual sites (build_match_arms, expr_tensor_shape,
  instr_tensor_shape, parse_tensor_lit ×2, new_lower_state,
  new_emit_state) all stop emitting __mn_list_new(i64 384).
  Floor count: 7 → 0.
- 65_list_int_indexing under LSan: CLEAN (was: would leak 80
  bytes if scalar gate applied without Lk.1 fix).
- stage2.ll shrinks slightly (eliminating intermediate allocas
  + copies).

Hero metrics:
- __mn_list_new(i64 384) sites: 7 → 0
- 65_list_int_indexing LSan: LEAK (would-be) → CLEAN
- verify_fixed_point.sh: NEAR/STRICT preserved

Goldens 64/66 preserved; full sanitizer gate clean.

The v5.6.x closeout arc is now genuinely complete with no
v6.0 deferrals from the arc itself. v5.7.0 next: Sh.7 + B
or-pattern → 66/66.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"

# Tag + push require explicit user approval
```

After push:
```bash
npx gitnexus analyze --embeddings
```

---

## What NOT to do

- Do not bundle Layer 2 (move on assignment). v5.6.13 if needed.
- Do not extend destination passing to struct/enum/map. v5.6.13.
- Do not revert v5.6.11's runtime-elem_size load.
- Do not skip the fixed-point gate.
- Do not commit `/tmp/*` files.
- Do not tag without user approval.
- Do not push without user approval.
- Do not ship if any sanitizer regresses.
- Do not add a GC. Mapanare is no-GC.
