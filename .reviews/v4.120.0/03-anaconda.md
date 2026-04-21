# Anaconda v4.120.0 Review — CI / Testing

## Score: 7.6 / 10
## Verdict: NEEDS WORK

## Context

At v4.99.0 I gave **6.5 / 10 NEEDS WORK**. Tests claimed but not
present, CI green was not the same as compiler-works. I was one of
the three reviewers who triggered Option B.

At v4.114.0 I gave **7.8 PASS WITH NOTES**. The ASan / TSan /
valgrind CI gates from v4.105.0 had landed. `DOCKET_AUDIT.md`
walked the 11 v4.99.0 items with line-references. The
infrastructure was grown-up.

Phase E had one release dedicated to my domain (v4.117.0 — flaky
audit, coverage, integration hardening). Phase F had zero changes
beyond the benchmark measurement. So I expected v4.120.0 to grade
the v4.117.0 work + any regression.

What I found instead moved me **back** toward NEEDS WORK.

---

## The big finding

**`make test` on `dev` at v4.120.0 is red.** Not a little red.
73 test failures out of 5,484 collected. The v4.117.0 flaky audit
measured 22 — but that audit restricted itself to 9 subdirectories
(golden / integration / llvm / lexer / parser / semantic / mir /
emit / cli, total 1,501 tests). The full `tests/` suite includes
bootstrap / wasm / lsp / transpiler / tensor / emit_c / test_ci /
and more. **51 extra failures live in those directories.**

I ran:

```bash
pytest tests/ -q --tb=no -n auto
```

Output:
```
73 failed, 5301 passed, 103 skipped, 7 xfailed, 64 warnings
in 113.06s (0:01:53)
```

The v4.117.0 SESSION_REPORT called the 22 numbered failures "pre-
existing deterministic failures" and catalogued them. That part is
true. What it did not say: **there are 51 more failures outside the
audited subset that nobody has catalogued.**

### Spot-check of the un-catalogued

I pulled 10 random failures from the 51 and classified them:

| Test | Class | Panel severity |
|---|---|---|
| `test_phase5_self_hosted::TestStructLiteralSyntax::test_parse_struct_literal_*` (3 tests) | feature gap — struct literal syntax not in grammar | MEDIUM |
| `test_semantic_mn::TestSemanticMnCoverage::test_all_builtin_functions_covered` | self-hosted `semantic.mn` missing builtin coverage | MEDIUM (tracks Sh.4/5/6) |
| `test_verification::TestFixedPoint::test_lexer_full_fixed_point` | fixed-point test (Sh.8 surfaced here too) | MEDIUM |
| `test_verification::TestSamplePrograms::test_fibonacci_run` | sample program regression | **unknown** until investigated |
| `test_ci::TestToolsRunLocally::test_ruff_check_passes` | meta-test: runs `ruff check` subprocess | LOW (but reveals lint debt) |
| `test_ci::TestToolsRunLocally::test_mypy_passes` | meta-test: runs `mypy` subprocess | LOW (reveals 34 mypy errors) |

The first three are feature gaps the V5_READINESS matrix already
knows about. But `test_fibonacci_run` being red and nobody flagging
it is exactly the kind of "tests claimed but not present / not
passing" pattern I dinged at v4.99.0.

Either that test is a known gap (in which case it should be
catalogued), or it's a real regression (in which case it must be
fixed). Neither the v4.117.0 session report nor the v4.119.0
retrospective mentions it.

**0.4 point deduction.** The v4.117.0 flaky audit was honest within
its scope but claimed "complete test infrastructure." It is not
complete if 51 failures live outside the audit's scope.

---

## Lint debt

`black --check .` — **64 files would be reformatted.**
`ruff check .` — **204 errors** (81 line-too-long, 48 unused
imports, 31 f-strings without placeholders, 24 import-sort, 10
multiple-statements, plus smaller buckets).
`mypy mapanare/ runtime/` — **34 errors** in 7 files, concentrated
in `mapanare/lsp/`.

The v4.117.0 release did not touch any of this. The v4.117.0
coverage report explicitly scoped itself to seven core-pipeline
subdirectories (`ast_nodes.py`, `mir.py`, `types.py`, `lexer.py`,
`pattern_matching.py`, `multi_module.py`, `semantic.py`, `parser.py`,
`mir_opt.py`, `lower.py`, `emit_llvm_text.py`) and reported 73%
coverage *within* that scope. Fine. But lint ran across the whole
project, and no release in the recovery arc addressed it.

I understand the scope-honest argument: "v4.117.0 scoped itself to
N modules." I accept that scoping, but a reviewer looking at `make
lint` sees 64 + 204 + 34 = **302 findings** and concludes the
project has abandoned its own quality gates. That's not the panel
the lead wants.

**0.2 point deduction.** Auto-fixable (ruff --fix handles ~104;
black formats cleanly). One release to close. It just wasn't.

---

## What I credit

### v4.117.0 flaky audit was real work

The 5-run pairwise-diff methodology produced the right answer
(zero flaky tests within scope). The audit text is transparent
about what it tested. If I had asked "is anything in the suite
flaky?" I would have gotten a confident "no." That's worth
something.

### Integration hardening tests land

`tests/integration/test_pipeline_hardening.py` with 6 new tests,
all PASS, each exercising a distinct failure mode (unparseable →
emit, invalid IR → llvm-as, 42-exit binary → nonzero captured,
sleep(60) → TimeoutExpired, stdout mismatch → reported, hello.mn
happy path still passes). This is the kind of negative-control
testing that catches harness regressions. I've wanted this since
v3.x.

### Sanitizer CI regression gates

`scripts/check_asan_baseline.py` means a new ASan finding blocks
the PR. TSan on async goldens + v4.115.0 demos blocks races.
Valgrind over full golden suite. This is the architecture I'd have
built if I owned it. +0.3 credit embedded in the score, not broken
out.

### Coverage report honest about scope

43% aggregate / 73% core pipeline, 13 modules at 0% because their
tests live out-of-scope (lsp / emit_c / wasm / transpilers), 12
real gaps named. Could have framed 43% as bad; instead it makes the
right distinction and publishes 5 recommendations for future work.

---

## What I'd demand before PASS

1. **Close the 51 un-audited failures**, OR catalogue them the same
   way v4.117.0 catalogued the 22. The lead cannot decide what "CI
   green" means if the failure inventory is incomplete.
2. **One release to clear lint debt.** `black .; ruff check --fix
   .; <investigate the 34 mypy errors>`. Estimated: one sprint.
3. **Expand the flaky audit to `pytest tests/` (full suite).** The
   methodology is sound; the scope is too narrow.
4. **Decide on `test_ci.py::TestToolsRunLocally`**: either the CI
   self-tests run, or they're `skip`-ed with a reason. Right now
   they fail silently inside the full suite.

None of these are compiler work. They're build / CI hygiene. One
release closes most.

---

## Final score

Last panel (v4.114.0): **7.8**
This panel: **7.6** (−0.2)

The score drop is not about compiler correctness — v4.117.0 did
real work within its declared scope. It's about the panel-visible
gap between "testing sweep" in the title and the reality that
`make test` and `make lint` are red on `dev`.

## Verdict: **NEEDS WORK**

I am sorry to deliver this. The recovery arc has been disciplined
elsewhere. But the CI testability story — the thing a new
contributor sees first — is not panel-ready. The flaky audit was
honest; the scope was too narrow. The 51 failures outside the
audited subset are either known (catalogue them) or unknown
(investigate them). Right now nobody knows.

**Fix before the next panel:** one release with `make test` green
and `make lint` green. That's enough. The rest of Phase E was
genuinely good.

## Carry-forward for v4.121.0+

- **An.1** — 51 uncatalogued pytest failures outside v4.117.0 audit scope
- **An.2** — lint debt (64 black, 204 ruff, 34 mypy)
- **An.3** — `test_fibonacci_run` regression (unknown cause)
- **An.4** — expand flaky audit to full `tests/` suite
- **An.5** — decide CI self-tests (`test_ci.py::TestToolsRunLocally`)

## Reproducibility

```bash
pytest tests/ -q --tb=no -n auto           # 73 failed
pytest tests/ -q --tb=no -n auto 2>&1 | grep '^FAILED' | wc -l   # 73
black --check . 2>&1 | tail -2            # 64 reformat
ruff check . 2>&1 | tail -5                # 204 errors
mypy mapanare/ runtime/ 2>&1 | tail -3     # 34 errors
```
