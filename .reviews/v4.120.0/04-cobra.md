# Cobra v4.120.0 Review — Bootstrap / Self-hosted

## Score: 7.9 / 10
## Verdict: PASS WITH NOTES

## Context

At v4.99.0 I gave **6.5 PASS WITH NOTES**. The self-hosted compiler
existed but `mnc-stage1` couldn't run its own goldens (0/61). The
Python bootstrap was the reference; the self-hosted pipeline was
aspirational.

At v4.114.0 I gave **8.0 PASS WITH NOTES**. Phase D had done the
work I wanted: `mnc-stage1` rebuilt cleanly, 26/64 golden passing,
all failures catalogued in `GOLDEN_FAILURES.md`, fixed-point-
adjacent divergence analysis published. The byref fix from v4.112.0
was real (`struct_byte_size` + `is_byref_type_st`).

Phase E + F added nothing to the self-hosted compiler. No
compiler or runtime code changes after v4.106.1. My lens:

1. Has anything regressed?
2. Has the fixed-point story matured?
3. Where does the self-hosted compiler sit vs a v5 tag?

---

## Re-verification

### mnc-stage1 golden pass rate unchanged

**26/64 strict / 39/64 effective.** Same as v4.114.0. No
regressions. No unblocks. Phase E was documentation / testing; it
did not touch the self-hosted lowerer, emitter, or `mir_opt.mn`.

Re-ran `scripts/test_native.py --stage1 mapanare/self/mnc-stage1`
on 2026-04-14. 26 passed, 38 failed in 6.3 s. Identical test list
to v4.114.0 output saved in `docs/roadmap/v4/v4.111.0/GOLDEN_
FAILURES.md`.

### Stage2 validation unchanged

Per v4.111.0 session report: **0/11 modules** compile cleanly
through `mnc-stage1` to re-emit self-hosted `.ll`. Attempt blocks
at `semantic.mn` (Sh.8: None/Some/Ok constructor registration).
The Python bootstrap at `build_stage1.py` uses `skip_check=True` to
bypass this; `mnc-stage1` has no bypass.

I did not re-run stage2 today because the blocker is structural and
the path to unblock is clear (register None as a constructor in
`semantic.mn` to mirror the Python bootstrap's behaviour). Phase D3
originally scoped this for v4.113.0 and it slipped to v5.x. That
slippage is documented.

### Byref fix (v4.112.0) verified in isolation

`/tmp/byref_test.mn` exercises both shapes:

```mn
type Small = struct { a: Int, b: Int }       # 16 bytes
type Large = struct { ... 10 Int fields ... } # 80 bytes

fn take(s: Small, l: Large) -> Int { return s.a + l.a }
```

Compiled through `mnc-stage1`:
- `Small` passed by value as `%struct.Small %s` — matches Python
  bootstrap
- `Large` passed by reference as `ptr %l.byref` — matches Python
  bootstrap
- Output correct

`emit_llvm.mn` has `struct_byte_size(st, ty)` at line 1495 and 7
call sites of `is_byref_type_st` (confirmed via grep). The
implementation resolves `%struct.Foo` through `st.structs` table
and computes actual size — not the 256-byte pessimistic fallback
that was the old heuristic.

Docket #7 from v4.99.0: **CLOSED**. I am comfortable.

### Self-hosted size growth

`mapanare/self/*.mn` is 39,763 lines (up from 38,824 at v4.99.0, so
+939 net). Changes:

- +coroutine frame prefix struct (v4.113.0)
- +async-I/O-adjacent additions (v4.115.0-supporting helpers)
- -4 zero-ROI MIR optimiser passes disabled (v4.111.0) — these are
  "disabled" not "deleted," so they contribute lines but no
  behaviour

The self-hosted compiler is **holding** while the Python bootstrap
is **shrinking** (-2,434 lines from v4.99.0). Both facts are
correct. The direction is healthy — reference emitter simplifying,
self-hosted emitter gaining features.

---

## The fixed-point question

This is where I sit.

**Sh.8 is the gate.** Until self-hosted `semantic.mn` registers
`None` as a constructor (along with `Some`, `Ok`, `Err`, and the
rest of the builtin constructor table), `mnc-stage1` cannot
re-compile `mapanare/self/mnc_all.mn`, which means stage1 → stage2
→ stage3 convergence cannot be demonstrated.

The Python bootstrap's `build_stage1.py` skips this check
(`skip_check=True`) because the bootstrap already has the
constructor table in Python. So Python-bootstrapped `mnc-stage1`
produces correct IR. What we cannot show is the self-hosted
compiler's internal coherence under self-compilation.

That is a **legitimate** self-hosting gap. It is **not** a
correctness gap in the compiler's output. Users do not hit Sh.8
because they compile their `.mn` programs, not `mapanare/self/
mnc_all.mn`.

### Is that "self-hosting"?

The v4.116.0 SPEC §29 and the README both say "the self-hosted
compiler is 39,000+ lines of .mn across 10 modules; the compiler
compiles itself." I want to be precise about what that sentence
means:

- ✅ The Python bootstrap compiles every `.mn` file in `mapanare/
  self/*.mn`.
- ✅ The resulting `mnc-stage1` binary compiles real user `.mn`
  programs and produces correct IR.
- ✅ 26/64 of those programs pass the literal golden harness; 39/64
  pass once Category A (inlining drift) is accounted for.
- ◐ `mnc-stage1` **cannot** re-compile `mapanare/self/mnc_all.mn`
  end-to-end because of Sh.8.

"The compiler compiles itself" is **partially** true. It compiles
*user* programs. It does not compile *itself* end-to-end.

This is the v5 readiness question Coral and I will agree on: is the
bar for a v5 tag "compiler compiles user programs" (yes) or
"compiler self-compiles end-to-end" (no)?

I think **both are defensible**. Python, Go, Rust have all shipped
stable major releases with imperfect self-hosting stories. As long
as the documentation is precise about what "self-hosted" means, v5
is not a lie.

But: the current language in README and SPEC is **not** precise. A
reader comes away thinking self-compilation converges. It does not.
If v5 ships, that language should be corrected.

---

## What I'd dock

### 1. Sh.8 documentation precision (0.2)

Already discussed above. The fix is one sentence in the README + one
paragraph in SPEC §29 — not compiler work. But it should land
before v5.

### 2. GOLDEN_FAILURES.md 3 releases old (0.1)

`docs/roadmap/v4/v4.111.0/GOLDEN_FAILURES.md` is the canonical
catalogue of the 38 self-hosted failures. It has not been updated
since v4.111.0 — 7 releases ago. The failure list has not changed
in those 7 releases, so the content is still correct, but a
reviewer landing on it would not know that without checking. A one-
line "verified unchanged at v4.120.0" footer would fix this.

### 3. v4.112.0 name was overclaimed (0.0 — already patched)

v4.112.0 was originally titled "fixed-point verification" in
SESSION_REPORT and CHANGELOG. It did not verify fixed-point; it
analysed divergence. v4.114.1 renamed to "divergence analysis +
byref fix." The rename is committed in CHANGELOG; no live
documentation still carries the old claim. I am not docking, but I
flag it as an example of how the cadence discipline must catch
overclaim *at release time*, not three releases later.

## What I credit

- **Every self-hosted test that was red at v4.99.0 and had a clear
  fix is green at v4.118.0.** The failures that remain are
  documented features the self-hosted compiler has not yet learned
  (async, tensor, const, closure types — Sh.4/5/6/7). None are
  regressions from v4.99.0; all are "missing, not broken."
- **Cross-module imports + extern C + stdlib/math land and run** —
  these are from v3.4.0 but they survive Phase E intact. User
  programs that `import` work correctly.
- **Cooperative scheduler runs user async code** — from v4.115.0,
  the `async_file_io.mn` and `async_http_demo.mn` examples compile
  through Python bootstrap, link against `libmapanare_rt.a`, and
  execute under valgrind clean. That's self-hosted *adjacent* —
  not self-compiled, but user-code runs.

## Final score

Last panel (v4.114.0): **8.0**
This panel: **7.9** (−0.1)

Small drop: the self-hosted story is genuinely the same, but
Anaconda's observation that 51 uncatalogued pytest failures include
`test_fibonacci_run` and `test_all_builtin_functions_covered`
cracks my assumption that "the self-hosted coverage is stable
because nobody is touching it." It might be true that those tests
have been red since v4.99.0, but the *reviewer* does not know.
That's a testability issue that touches my domain too.

## Verdict: PASS WITH NOTES

The self-hosted compiler is real. Its pass rate through its own
goldens is stable. The byref fix is verified. The fixed-point block
(Sh.8) is documented. The README and SPEC should be precise about
what "self-hosted" means before a v5 tag goes out.

I support Option B → continue for reasons not primarily in my
domain. Within my domain, the self-hosted compiler is
approximately as ready as it was at v4.114.0 — 8.0-quality work
that does not decay over 6 releases of no-touch.

## Carry-forward for v4.121.0+

- **Sh.8** — None/Some/Ok constructor registration (self-hosted)
- **Sh.4/5/6/7** — self-hosted feature gaps (unchanged)
- **Cb.1** — README + SPEC precision on "self-hosted" meaning
- **Cb.2** — GOLDEN_FAILURES.md refresh footer

## Reproducibility

```bash
python scripts/test_native.py --stage1 mapanare/self/mnc-stage1
python scripts/ir_doctor.py stage2
bash scripts/verify_fixed_point.sh   # fails at Stage 1, Sh.8
wc -l mapanare/self/*.mn | tail -1   # 39,763
```
