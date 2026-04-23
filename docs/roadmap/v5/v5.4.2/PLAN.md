# Mapanare v5.4.2 — "ASan leak-detection gate + reassignment-leak fixes"

> **Flip ASan leak detection on across all 66 goldens. Fix every leak
> it reveals.** v5.4.1 made drop-glue fire on normal return paths;
> v5.4.2 proves the end-to-end story is actually leak-clean on the
> full corpus and closes any reassignment-leak edge cases the gate
> exposes.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v5.4.1 shipped (drop-glue functional on simple
returns)
**Estimated work:** 1–2 sessions (~3–5 hours), **bounded by how many
leak findings the first sweep produces** — could be 1 hour if clean,
6 hours if every golden leaks something subtle.

---

## Why this release exists

v5.4.1 added drop-glue + return-escape detection and validated on
one narrow test (`greet` → "hello"). It did **not** run with ASan
leak detection across the full golden corpus because a single leak
anywhere would block the release and the PLAN's cadence depended on
v5.4.1 shipping.

v5.4.2 makes leak detection a first-class gate:

1. Flip `detect_leaks=1` in `scripts/run_asan_goldens.sh` for a
   dedicated leak-detection pass (preserve the existing `detect_leaks=0`
   UAF/overflow pass — they serve different purposes).
2. Run the leak pass across all 66 goldens.
3. Classify findings:
   - **Expected leaks** — `mnc-stage1`-compiled test program leaks a
     local it should have freed. Fix in v5.4.1's tracking/drop path.
   - **Pre-existing leaks** — runtime artefacts (string interning,
     registered cleanup handlers) already on the ledger. Document in
     `.asan_leak_suppressions` so the gate is signal, not noise.
4. Close every expected-leak finding.
5. Ratify the leak-detection sweep as a CI gate going forward.

---

## Scope

### What ships

#### 5.4.2a — Dedicated leak-detection harness

New script `scripts/run_asan_leak_goldens.sh` (or flag on the
existing one). Mirrors `run_asan_goldens.sh` but with
`ASAN_OPTIONS=detect_leaks=1:leak_check_at_exit=1` AND **runs the
compiled test binary, not just mnc-stage1**. The two passes are
different:

- **Existing sweep** (UAF/overflow): mnc-stage1 compiles each
  golden, any mnc-stage1 ASan error is flagged. Checks the compiler
  itself.
- **New sweep** (leak detection): mnc-stage1 compiles each golden to
  IR, `llc` produces an object, link with `libmapanare_rt.a`, run
  the resulting binary under ASan with leak detection. Checks the
  compiled output.

Output: TSV summary like `asan-leak-summary.tsv` — `test`,
`compile_rc`, `run_rc`, `leak_count`, `leak_bytes`, `class`.

#### 5.4.2b — Suppression file for known runtime leaks

`scripts/asan_leak_suppressions.txt`. Entries documented with why:

```
# String intern table — allocated once per process, never freed by
# design (compiler is short-lived and intern entries are hot-path
# lookups). Tracked as Rt.NN; the leak is intentional.
leak:__mn_str_intern_alloc

# ... more entries discovered during the first sweep ...
```

`ASAN_OPTIONS=suppressions=$PWD/scripts/asan_leak_suppressions.txt`.

#### 5.4.2c — Fix every compiler-introduced leak

Expected classes:

**Reassignment leaks.** v5.4.1's shadow-slot architecture already
handles these if every assignment emits a fresh track call. If the
leak-sweep reveals a reassignment path that skips tracking (e.g.
`emit_store` called directly on a String slot without a preceding
`emit_track_string`), add the missing track.

**Struct field ownership.** `let s = MyStruct { name: "hello" +
"world" }` — the concat result's ownership transfers into the
struct. When the struct goes out of scope, who frees the field? Two
options:

- Track struct allocas whose type has owning fields. On drop-glue,
  extract each field and free it. Python does this via
  `_emit_drop_glue_boxed` recursive walk. Can be expensive.
- Declare a per-struct drop glue function during `emit_struct_init`
  registration. Python does NOT do this today. Out of scope for
  v5.4.2 unless struct-field leaks dominate the sweep output.

**FieldSet reassignment.** `obj.name = new_value` overwrites the
field's old owning String. v5.4.2 adds a free-old + track-new
semantics to `emit_field_set` if the field's type is an owning kind.

**Enum payload leaks.** Boxed payloads of non-nested types are
handled by v5.4.1's `emit_track_boxed`. Nested boxes (a
`Result<String, Box<Error>>`) hit Python's conservative
skip-all-boxed guard and leak. v5.4.2 does **not** close this —
deep-pointer walking is v5.4.3+ scope.

#### 5.4.2d — CI integration

Add the leak sweep to `.github/workflows/native.yml` (or wherever
the ASan sweep currently runs). Make it required for merge.

Update `Makefile`:

```make
.PHONY: leak-check
leak-check:
	bash scripts/run_asan_leak_goldens.sh
	python3 scripts/check_leak_summary.py /tmp/asan-leak/asan-leak-summary.tsv
```

`check_leak_summary.py` compares against the baseline table and
fails if any golden gained leaks vs baseline.

### What does NOT ship

- **Deep pointer walking** for nested boxes. v5.4.3+.
- **Maps / Signals / Streams / Tensors drop-glue.** v5.4.3+.
- **LSan under every test class** — leak detection is costly; only
  the ASan leak pass runs it. Plain pytest stays fast.
- **Reference counting.** v6.0+ if ever — the compile-time drop-glue
  pattern is the design decision for Mapanare's default.

---

## Exit criteria

1. `bash scripts/run_asan_leak_goldens.sh` → **0 leaks** across 66
   goldens (after suppression file absorbs known-intentional runtime
   leaks).
2. Suppression file has < 10 entries, each with a `# tracked as Rt.NN`
   comment pointing at a ledger docket.
3. Goldens 54/66 (unchanged).
4. Valgrind 0 new ERRORS.
5. ASan (UAF/overflow pass): 55 CLEAN / 11 CRASH_NO_ASAN unchanged.
6. Fixed-point stage2 `llvm-as` OK (Ve.1 preserved).
7. Non-bootstrap pytest 0 failures.
8. `make lint` clean.
9. `make leak-check` added and green.
10. CI workflow `native.yml` runs the leak pass.

---

## Design decisions

### D1 — Separate passes for UAF and leak

Existing ASan sweep checks `mnc-stage1` itself for UAF / overflow
during compilation. Leak sweep checks the COMPILED OUTPUT after
execution. Different targets, different reporting. Don't merge them.

### D2 — Suppression list is small and justified

Each entry has a comment pointing at a ledger docket. The list
should not grow silently. CI fails if suppression entries exceed 10
without a corresponding docket.

### D3 — Reassignment is v5.4.1's responsibility

If v5.4.1 got the shadow-slot architecture right, reassignment-leak
is automatic. v5.4.2 only fixes the RESIDUAL cases the sweep reveals
— typically places where an emit site was missed in v5.4.1 Phase 3.

### D4 — Deep pointer walking is out of scope

Python's conservative `skip-all-boxed-on-struct-return` guard will
leak nested boxes; the self-hosted emitter already copies that
guard in v5.4.0. Closing it requires ABI-aware type metadata that
Mapanare doesn't ship yet. v5.4.3 or v6.0.

---

## Risks

### R1 — Sweep finds too many leaks to fix in a session

**Risk: MEDIUM.** Compiler leaks in struct-returning code paths
could be systemic.

**Mitigation:** Triage the first sweep's output aggressively. If >20
classes of leak, split the release: fix the top 5, defer the rest to
v5.4.3 with explicit suppressions.

### R2 — Suppression file masks a real regression

**Risk: LOW.** Every entry requires a ledger docket comment.
Monthly audit: re-run sweep with suppressions disabled; diff the
list against last audit.

### R3 — CI time blows up

**Risk: LOW.** ASan-instrumented compile + execute for 66 goldens
is probably 3-5 min. Acceptable for a gated job.

---

## Release sequencing

| Outcome of first sweep | Action |
|---|---|
| 0 leaks across 66 goldens | Ship v5.4.2 as a docs-only leak-gate add |
| 1–5 leak classes | Fix in session, ship |
| 6–20 leak classes | Fix 5 biggest, suppress rest with dockets, ship |
| > 20 leak classes | Abort v5.4.2; open v5.4.2-audit release to triage, v5.4.3 for fixes |

---

## What NOT to do

- **Do not fix leaks that don't appear in the sweep.** Speculative
  fixes add risk without evidence.
- **Do not suppress leaks without a ledger docket.** Suppressions
  are commitments to come back.
- **Do not add deep pointer walking to close "edge case" nested-box
  leaks.** Out of scope — document and move on.
- **Do not touch the UAF sweep.** v5.4.1 established baseline; don't
  drift.
- **Do not bump v5 tag without explicit user approval.** Saved rule.
