# v5.6.13 Execution Prompt — Layer 1 extension + optional Layer 2

> Read `PLAN.md` first. **CONDITIONAL release** — gated on
> v5.6.12 sanitizer sweep outcome. Skip if all clean and
> struct/enum/map cleanup not desired.
>
> Estimated: 1 session (~2-3 hours) if shipped.

---

## Read before starting

1. `docs/roadmap/v5/v5.6.13/PLAN.md` — this release's plan +
   decision tree.
2. `docs/roadmap/v5/v5.6.12/SESSION_REPORT.md` — previous release;
   confirms whether this release should ship at all.
3. `mapanare/self/lower.mn::lower_struct_init`,
   `lower_enum_init`, `lower_map_init`.
4. `mapanare/self/emit_llvm.mn::emit_struct_init`,
   `emit_enum_init`, `emit_map_init`.

---

## Phase 0 — Decision gate (~15 min)

Run the v5.6.12 sanitizer matrix again to confirm baseline:
```bash
bash scripts/build_asan.sh
ASAN_OUTDIR=/tmp/asan-v5.6.12-recheck bash scripts/run_asan_goldens.sh
ASAN_LEAK_OUTDIR=/tmp/asan-leak-v5.6.12-recheck bash scripts/run_asan_leak_goldens.sh
python3 scripts/check_leak_summary.py /tmp/asan-leak-v5.6.12-recheck/asan-leak-summary.tsv
```

**Decision tree** (per PLAN §"Decision tree"):

| Outcome | Action |
|---|---|
| All sanitizers clean; no leak surface; struct/enum/map cleanup not desired | **SKIP this release.** Bump VERSION → 5.7.0 directly. |
| Share-mutate leak surfaced | Ship Layer 1 extension + Layer 2. |
| Cleanup desired, no leak | Ship Layer 1 extension only. |

If skipping, document the decision in
`docs/roadmap/v5/v5.6.13/SKIPPED.md` and proceed to v5.7.0.

If shipping, continue to Phase 1.

---

## Phase 1 — Layer 1 extension (~60 min)

### 1.1 — Struct let-bindings

Add `lower_struct_init_into(st, type_name, fields, dest_alloca)`
parallel to v5.6.12's `lower_list_typed_into`. Emits StructInit
with dest derived from the alloca's name (strip `.addr`).

Update `lower_let` to detect fresh struct init (via expr_kind
== "struct_init") and route through the destination-passing
variant.

### 1.2 — Enum let-bindings

Same pattern for `lower_enum_init`. Note: enum payloads may be
boxed (heap-allocated), which adds tracking concerns. Verify
`emit_enum_init`'s boxed-payload path still tracks correctly
when destination passing is active.

### 1.3 — Map let-bindings

Same pattern for `lower_map_init`. Map runtime allocates the
hashtable internally; the let's alloca holds the map header
(similar to list).

### 1.4 — Verify

Rebuild stage1, regenerate stage2.ll, compare alloca counts:
```bash
bash scripts/concat_self.sh
python3 scripts/build_stage1.py
mapanare/self/mnc-stage1 mapanare/self/mnc_all.mn > /tmp/stage2-v5.6.13.ll
echo "stage2.ll lines: $(wc -l < /tmp/stage2-v5.6.13.ll)"
llvm-as /tmp/stage2-v5.6.13.ll -o /dev/null && echo OK

# Allocations should DECREASE
grep -c "= alloca" /tmp/stage2-v5.6.13.ll
# Compare to v5.6.12's count
```

---

## Phase 2 — Layer 2 (CONDITIONAL, only if share-mutate leak surfaced)

### 2.1 — Detect share-then-mutate in lower_let

```mn
fn lower_let(st, name, mutable, type_ann, value) -> LowerState {
    // ... existing fast-path checks ...

    // v5.6.13 Layer 2: detect `let b = a` where a is a tracked
    // resource. Emit a memcpy + transfer ownership tracking.
    if expr_kind(value) == "ident" {
        let a_name: String = expr_ident_name(value)
        if is_tracked_resource_var(s, a_name) {
            // Pre-create b's alloca, memcpy from a.addr,
            // mark a as consumed, transfer tracking.
            // ... emit MemCpy(b.addr, a.addr, sizeof(val_ty)) ...
            // ... s.consumed_locals.push(a_name) ...
            // ... transfer list_owned/str_owned/boxed_owned entries ...
            return s
        }
    }

    // ... existing fall-through ...
}
```

### 2.2 — Use-after-move warning

After lowering each function, scan the IR for loads from
consumed locals and emit a warning. Non-fatal (no compile
error); we're not implementing a borrow checker.

### 2.3 — Verify

Reproducer for share-mutate:
```mn
fn build() -> Int {
    let mut a: List<Int> = []
    a.push(1)
    let mut b: List<Int> = a    // move
    b.push(2)
    let mut sum: Int = 0
    for i in 0..len(b) { sum = sum + b[i] }
    return sum
}
```

Verify via LSan that `b` correctly drops its buffer (not
just `a`'s).

---

## Phase 3 — Sanitizer + lint gate (~30 min)

```bash
ASAN_OUTDIR=/tmp/asan-v5.6.13 bash scripts/run_asan_goldens.sh
VG_OUTDIR=/tmp/vg-v5.6.13 bash scripts/valgrind_all_goldens.sh
ASAN_LEAK_OUTDIR=/tmp/asan-leak-v5.6.13 bash scripts/run_asan_leak_goldens.sh
python3 scripts/check_leak_summary.py /tmp/asan-leak-v5.6.13/asan-leak-summary.tsv

python3 -m pytest tests/ --ignore=tests/bootstrap -q --tb=no
make lint
python3 scripts/check_struct_registry.py
```

Per PROMPT D2: any sanitizer regression → REVERT.

---

## Phase 4 — Documentation (~15 min)

- `docs/roadmap/v5/v5.6.13/SESSION_REPORT.md`
- `CLAUDE.md` v5.6.13 entry (or "skipped — no leak surface" note)
- `docs/roadmap/ROADMAP.md` stanza
- `docs/roadmap/v5/CLOSEOUT_ARC.md` — final arc completion note

---

## Ready-to-ship checklist

- [ ] `VERSION` reads `5.6.13` (or skipped, `5.7.0`)
- [ ] Goldens 64/66 preserved
- [ ] `verify_fixed_point.sh` NEAR or STRICT
- [ ] Full sanitizer matrix clean
- [ ] If Layer 2 shipped: share-mutate reproducer LSan CLEAN
- [ ] stage2.ll growth ≤ 1% vs v5.6.12 (likely DECREASE)
- [ ] `make lint` clean
- [ ] `check_struct_registry.py` 23/23/91 clean
- [ ] Non-bootstrap pytest 0 failures
- [ ] SESSION_REPORT (or SKIPPED note) written
- [ ] Docs updated

---

## What NOT to do

- Do not ship Layer 2 unless a share-mutate leak surfaced.
- Do not extend to function returns (sret already does this).
- Do not implement a borrow checker.
- Do not enforce move semantics as compile-time errors.
- Do not commit `/tmp/*` artifacts.
- Do not tag without user approval.
- Do not push without user approval.

---

## Commit

```bash
git commit -m "$(cat <<'EOF'
v5.6.13: Layer 1 extension to struct/enum/map [+ Layer 2]

Extends v5.6.12's destination-passing pattern from List let-
bindings to struct/enum/map let-bindings. Same structural fix:
the let's alloca IS the resource init's storage; no
intermediate scratch alloca, no copy.

[If Layer 2 shipped:] Adds move-on-assignment tracking. `let b
= a` for a tracked resource transfers ownership: memcpy of the
value header, tracking entry swap, a marked as consumed.
Closes the share-then-mutate leak class without a borrow
checker — diagnostics are warnings, not errors.

Goldens 64/66 preserved; full sanitizer gate clean; the v5.6.x
closeout arc is now genuinely complete with zero v6.0
deferrals from this arc.

What's next: v5.7.0 — Sh.7 closure-typed + B or-pattern → 66/66.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```
