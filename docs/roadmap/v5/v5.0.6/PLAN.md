# Mapanare v5.0.6 — "Multi-Cycle Hygiene Closeout"

> **The "errors that got dragged from earlier versions" release.**
> Every v4.x panel after v4.135.0 has flagged a handful of trivial
> items that never closed — the JSON version field, the stale README
> benchmark numbers, the misleading enum-size comment. This release
> closes them in one sitting. No new features. No compiler source
> changes beyond replacing stale constants.

**Status:** SHIPPED (2026-04-21)
**Breaking:** No
**Prerequisite:** v5.0.5 shipped
**Estimated work:** 1 session (~90 min — these are all 1-30 minute fixes)
**Session report:** `SESSION_REPORT.md`

---

## Why this release exists

Cobra v4.154.0 flagged a 27% undercount in the v4.153.0 DOCKET_LEDGER
(three items closed in SESSION_REPORTs but absent from tracking).
Multi-cycle carry-forwards are the *same* failure mode:
known → small → unfixed for 2+ panels. The user explicitly named
these as "errors dragged from earlier versions."

Raw list:

| ID | Cycles | Fix size | Severity | Source |
|---|:---:|---|:---:|---|
| **Bo.12-table** | 2 | ~20 min | **MEDIUM** | Boa v4.144+v4.154 |
| **Bo.12-i18n** | 2 (9 releases behind) | ~20 min | **MEDIUM** | Boa v4.144+v4.154, Coral v4.154 |
| **Rt.4** | 1 (new) | ~20 min | **MEDIUM** (latent heap overflow — enum under-sized by 8B) | Rattler v4.154 |
| Bn.3 | 3 | ~5 min (1 line) | LOW | Mamba v4.143+v4.144+v4.154 |
| Cb.6-test | 2 | ~20 min | LOW | Rattler v4.144+v4.154 |
| An.9 | 1 (new) | ~30 min | LOW | Anaconda v4.154 |
| An.10 | 1 (new) | ~15 min | LOW | Anaconda v4.154 |
| Dr.1-mutation | 2 | ~45 min | LOW | Rattler v4.144+v4.154 |

Total: ~3.5 hours. Doing them one at a time across 6 releases adds
per-release overhead (version bump, CI run, release notes) that
dwarfs the actual work. Bundling is cheaper.

## Scope

### Bo.12-table (MEDIUM) — README benchmark table contradicts its own text

`README.md:397-398` prose was corrected at v4.144.0 but the benchmark
**table** at `README.md:408-415` still has the retracted pre-Bn.1
numbers. The front door tells two different stories in two paragraphs.

**Fix:** re-run `benchmarks/run_benchmarks.py --output /tmp/v5.0.6-bench.json`
and regenerate the README table from it (rows: workload, Mapanare,
Rust, C, ratio). Prose and table must agree.

### Bo.12-i18n (MEDIUM) — localized READMEs 9 releases behind

`docs/README.es.md`, `docs/README.zh-CN.md`, `docs/README.pt.md`
still cite "1.12× of Rust (within noise)" and "4.86× slower than C".
Both numbers were retracted at v4.144.0 — 9 releases ago. Any
non-English reader lands on objectively false performance claims.

**Fix:** apply the same benchmark-number update from Bo.12-table to
each localized README. Also bump the version badges on each (they
likely still say v4.x).

### Bn.3 — JSON version field hardcoded

`benchmarks/run_benchmarks.py` writes `"version": "4.125.0"` into
every output JSON. Three review cycles unresolved.

**Fix:** read VERSION file at runtime:
```python
MAPANARE_VERSION = (ROOT / "VERSION").read_text().strip()
```

### Rt.4 (MEDIUM — latent heap overflow) — stale enum-size hardcode

`mapanare/self/emit_llvm.mn:1646` in `llvm_type_size` returns **16**
for any `%enum.X` type. Rt.1 (v4.124.0) changed inline enums to
`{i64, i64, i64}` = **24B** for 2-slot variants. Comment at that
line says "enums are always {i64, ptr}" which is actively false.

This is MEDIUM not LOW: any `memcpy` or `alloca` sized by
`llvm_type_size` under-allocates by 8 bytes. Self-hosted doesn't
currently construct inline enums (that's Cb.15, which v5.0.4 closes)
so the bug isn't observed *yet* — but **after v5.0.4 lands, this bug
activates as a latent heap overflow** on every enum wider than 16 B.

v5.0.4 and v5.0.6 are ordered to land together; shipping v5.0.4
without v5.0.6's Rt.4 fix ships a heap-overflow regression.

**Fix:** two-part —
1. Update comment to reflect Rt.1 reality
2. Return `max(24, parsed_size)` as a safe upper bound; or parse
   the type definition properly via `state.struct_sizes.get(name)`.
   If `state.struct_sizes` doesn't have the entry, assume 24 (not 16).

### Cb.6-test — Missing regression gate

Self-hosted `type_fits_inline_slot` at `emit_llvm.mn::...` correctly
rejects `i64*` (Cb.6 closed v4.134-ish), but there's no test asserting
this. Two cycles. A future refactor could silently re-enable typed-
pointer acceptance and propagate through self-compilation.

**Fix:** add one test in `tests/llvm/test_enum_inline_parity.py`:
```python
def test_self_hosted_rejects_typed_pointer_slot():
    # Assert type_fits_inline_slot(Ptr(i64)) returns false
```

### An.9 — IR-shape gate for E1 unified-return

v4.145.0 E1 unified-return-block optimization is integration-tested
via `enum_match` checksum match. No dedicated test asserts the IR
shape (single switch post-inline, not two). A regression that
re-splits the switch would pass the checksum but lose the perf win.

**Fix:** add `tests/llvm/test_unified_return_shape.py` that compiles
`enum_match.mn`, greps optimized IR for `switch.*i64` occurrence
count, asserts exactly 1 in the hot loop.

### An.10 — Test count bookkeeping drift

v4.144.0 PR claimed +27 test delta; Anaconda's count showed +34 new
tests actually landed. Delta meta is wrong somewhere — either the
release notes, the CI summary, or the counting methodology.

**Fix:** add a `scripts/count_tests.py` that walks `tests/` and emits
a deterministic count. Wire into `make test` or CI so the delta is
authoritative, not hand-counted.

### Dr.1-mutation — Source-tree mutation during build

`scripts/build_stage1.py:60-90` mutates `.mn` files in-place to
substitute `__MN_VERSION__`, then restores via `try/finally`. If the
try body crashes, the finally restores — but if the *restore* crashes,
the tree is corrupt. Pattern since v4.139.0.

**Fix:** substitute into a temp directory, compile from there. Never
mutate the source tree. Pattern:

```python
with tempfile.TemporaryDirectory() as td:
    for mn_file in SELF_DIR.glob("*.mn"):
        substituted = _substitute_version(mn_file.read_text())
        (Path(td) / mn_file.name).write_text(substituted)
    # compile from td
```

## Scope (out)

- No Python→self-hosted parity changes (Cb.15, Gr.2/Cb.9a were
  their own releases)
- No MIR / emitter changes
- No language changes

## Exit criteria

1. `grep -rn '1\.12x\|1\.13x' README.md docs/README.*.md` → 0 hits
2. `grep -n '4.125.0' benchmarks/` → 0 hits
3. `grep -n 'always {i64, ptr}' mapanare/self/emit_llvm.mn` → 0 hits
4. New tests: `test_self_hosted_rejects_typed_pointer_slot`,
   `test_unified_return_shape`, `scripts/count_tests.py`
5. `build_stage1.py` — no `.write_text` back into `SELF_DIR`
6. `PARITY_GAPS.md`: Bo.12, Bn.3, Rt.4, Cb.6-test, An.9, An.10,
   Dr.1-mutation all move to Historical
7. Strict 3-stage fixed point holds
8. 54/66 goldens unchanged (no code-path changes besides the hygiene
   fixes)

## Risks

**Risk 1 — README updates conflict with in-flight PRs.**
*Mitigation:* merge this release's hygiene edits before any feature
branch is cut that also touches README. The benchmark section is
hotspot-ish.

**Risk 2 — `build_stage1.py` refactor breaks CI.**
The tempdir pattern is new plumbing. A typo in the path resolution
could make CI fail to find `main.ll`.
*Mitigation:* test locally on both WSL and Windows bash before push.
Keep the old `try/finally` code path behind an environment flag
(`MAPANARE_USE_LEGACY_BUILD=1`) for one release; remove in v5.0.7 /
v5.1.0.
