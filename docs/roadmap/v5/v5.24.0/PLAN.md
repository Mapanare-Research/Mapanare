# v5.24.0 — Hy.* — structural hygiene gates

**Status:** PLANNING
**Breaking:** No.
**Prerequisite:** v5.23.2 shipped (Te.3.B closure; Te.3
deprecation symmetric across both compilers).
**Estimated effort:** 1 session (~3–4 hours).
**Arc context:** Fourth release in v5.23–v5.24 recovery arc.

---

## Why this exists

The "this should never have slipped" infrastructure release.
Coral M1 / Anaconda §2.D / Boa Bo.27 all converged on the
same recommendation in different shapes:

- **Anaconda §2.D — `make ci-gates`** Makefile target running
  the full CI gate inventory locally as a single command.
  Pre-release checklist shrinks to "run `make ci-gates`,
  expect zero violations." Eliminates the
  wired-but-unchecked failure mode that produced Reg.1 /
  hollow-feature gate / docs-drift gate silent failures.
- **Coral / Boa Bo.27 — `scripts/check_doc_freshness.py`** —
  fail when README badges, fixed-point line count, goldens
  count, or version references in any tracked README / SPEC
  / manifesto file are stale. Closes the H.\* / Bo.\* drift
  class **structurally** (vs the closure-by-hygiene-release
  pattern that capped at 9.55–9.66).
- **Anaconda §1 — Cadence enforcement gate** — CI gate or
  pre-release script firing when ≥5 minor versions OR ≥5
  language-feature releases have shipped without a panel.
  Prevents the v5.16.0 / v5.20.0 silent-skip class.

Plus 3 long-running carries that close cleanly with
infrastructure work:
- **Hy.4** Cobra `>= 45` magic — 3rd-time ask, replace with
  self-evident formula.
- **Hy.5** Pk.1.A — Linux/macOS versioned-tarball smoke
  gates (11-release carry; closes the asymmetric
  Windows-only smoke gate from v5.10.0).
- **Hy.6** Pe.1 framing retire — "curve flattening" → "growth
  proportional to bootstrap AST surface" (Mamba's #2; also
  refers to v5.11.0 Mamba's reframe).

---

## Goals

1. **Hy.1** `make ci-gates` Makefile target.
2. **Hy.2** `scripts/check_doc_freshness.py` MVP shipped.
3. **Hy.3** Cadence enforcement gate (CI gate or pre-release script).
4. **Hy.4** `>= 45` magic-number self-evident formula.
5. **Hy.5** Pk.1.A Linux/macOS versioned-tarball smoke gates.
6. **Hy.6** Pe.1 framing retire.
7. Strict 3-stage fixed point preserved at v5.23.2's line
   count (zero compiler edits).

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Hy.1** | MEDIUM (structural) | **`make ci-gates` Makefile target.** New target in `Makefile` running the full CI-gate inventory locally as a single command. Each sub-gate's exit code is collected; the overall target exits 1 on any sub-gate failure with a summary table. Sub-gates: `check_silent_skips`, `check_changelog_honesty`, `check_workflow_shapes`, `check_docs_drift`, `check_no_hollow_features`, `check_struct_registry`, `check_doc_freshness` (after Hy.2). New `tests/test_ci.py::test_make_ci_gates_target` verifying invocation. | 30 min |
| **Hy.2** | MEDIUM (structural) | **`scripts/check_doc_freshness.py`** — MVP that compares the README badges, fixed-point line count, goldens count, and version references against the current state of: `VERSION` file, `tests/golden/*.mn` count, recent `bash scripts/verify_fixed_point.sh` output (or a cached value from `tests/golden/BENCHMARKS.md`). Fail with a structured report on drift. ~150 LOC; ships at v5.24.0. Wider scope (every prose claim about every metric) is correctly v6.0+. | 2-3h |
| **Hy.3** | MEDIUM | **Cadence enforcement gate.** Either: (A) a CI workflow `cadence.yml` that runs on push to main and fires a soft warning (or hard fail with `if: failure()`) when ≥5 minor versions OR ≥5 language-feature releases have shipped without a `.reviews/v5.X.Y/` panel directory; or (B) a `scripts/check_cadence.py` invoked at pre-release time. Recommendation: A (warn at push; hard-fail at next-tagged-release-minor-bump). | 1h |
| **Hy.4** | LOW | **`>= 45` magic-number** in `scripts/build_from_seed.sh:159` → self-evident formula. Replace `if [ "${PASS}" -lt 45 ]` with: `EXPECTED_SEED_FAILS=20  # Te.5/Te.6/comprehensions/complex closures predate the seed`<br>`EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))`<br>`if [ "${PASS}" -lt "${EXPECTED_PASS}" ]; then ...`<br>Where `TOTAL_GOLDENS=$(ls tests/golden/*.mn \| wc -l)`. **Closes Cobra 3rd-panel ask.** | 30 min |
| **Hy.5** | LOW | **Pk.1.A — Linux/macOS versioned-tarball smoke gates** at `.github/workflows/publish.yml`. Mirror the existing Windows-bundled-llvm-smoke job's shape: download the published tarball, extract to a clean directory, run `mnc --version`, `mnc emit-llvm <a-golden>.mn`, fail on non-zero exit. **11-release carry from v5.10.0 → v5.22.0.** | 1h |
| **Hy.6** | LOW | **Pe.1 framing retire** — update `.reviews/CARRY_FORWARD.md` Pe.1 row + the Pe.1 references in `CLAUDE.md` preamble (v5.11.0 / v5.22.0 release notes). Replace "downgraded — flattening" with "growing in proportion to bootstrap-side AST additions; not a v6.0 budget concern at current rate (need another 30+ releases at +0.5%/release before doubling)." Documentation-only. | 15 min |

---

## Phase plan

### Phase 0 — pre-flight verification

```bash
# Baseline must hold from v5.23.2
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll at v5.23.2's line count
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95
cat VERSION
# expected: 5.23.2

# Verify Te.3.B closure from v5.23.2
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | grep -c "deprecated"
# expected: 1
mapanare/self/mnc-stage1 emit-llvm /tmp/brace.mn -o /tmp/x.ll 2>&1 | grep -c "deprecated"
# expected: 1

# Verify all v5.23.x CI gates green
python3 scripts/check_struct_registry.py && echo "Reg.1 ✓"
python3 scripts/check_no_hollow_features.py && echo "hollow ✓"
python3 scripts/check_docs_drift.py && echo "docs-drift ✓"
python3 scripts/check_changelog_honesty.py && echo "changelog ✓"
```

If any gate is RED, abort — v5.23.x left work undone.

### Phase 1 — Hy.1 `make ci-gates`

1. Open `Makefile`. Add new target:

   ```makefile
   .PHONY: ci-gates
   ci-gates:
       @echo "=== Mapanare CI Gates ==="
       @python3 scripts/check_silent_skips.py tests/ && echo "  silent_skips: GREEN" || (echo "  silent_skips: RED"; exit 1)
       @python3 scripts/check_changelog_honesty.py && echo "  changelog_honesty: GREEN" || (echo "  changelog_honesty: RED"; exit 1)
       @python3 scripts/check_workflow_shapes.py && echo "  workflow_shapes: GREEN" || (echo "  workflow_shapes: RED"; exit 1)
       @python3 scripts/check_docs_drift.py && echo "  docs_drift: GREEN" || (echo "  docs_drift: RED"; exit 1)
       @python3 scripts/check_no_hollow_features.py && echo "  hollow_features: GREEN" || (echo "  hollow_features: RED"; exit 1)
       @python3 scripts/check_struct_registry.py && echo "  struct_registry: GREEN" || (echo "  struct_registry: RED"; exit 1)
       @python3 scripts/check_doc_freshness.py && echo "  doc_freshness: GREEN" || (echo "  doc_freshness: RED"; exit 1)
       @echo "=== All gates GREEN ==="
   ```

2. Add a test in `tests/test_ci.py`:

   ```python
   def test_make_ci_gates_target_runs():
       result = subprocess.run(["make", "ci-gates"], capture_output=True, text=True, timeout=120)
       assert result.returncode == 0, f"make ci-gates failed: {result.stderr}"
       assert "All gates GREEN" in result.stdout
   ```

3. Run `make ci-gates` locally; must be GREEN.

### Phase 2 — Hy.2 `check_doc_freshness.py`

1. Create `scripts/check_doc_freshness.py`:

   ```python
   #!/usr/bin/env python3
   """v5.24.0 Hy.2 — docs-freshness gate.

   Compares README badges / fixed-point status / goldens count
   against the current state of the repo. Fails with a structured
   report on drift.

   Closes the H.* / Bo.* drift class structurally that capped
   the v5.7.1 / v5.11.0 / v5.22.0 panel aggregates at 9.55–9.66.
   """

   from __future__ import annotations
   import re
   import sys
   from pathlib import Path

   # 1. VERSION badge sync
   def check_version_badges() -> list[str]:
       version = Path("VERSION").read_text().strip()
       readme_files = [
           "README.md",
           "docs/README.es.md",
           "docs/README.pt.md",
           "docs/README.zh-CN.md",
       ]
       violations = []
       version_re = re.compile(r"version-([\d.]+)-")
       version_pt_re = re.compile(r"versao-([\d.]+)-")
       version_zh_re = re.compile(r"%E7%89%88%E6%9C%AC-([\d.]+)-")  # 版本

       for path_str in readme_files:
           path = Path(path_str)
           if not path.exists():
               continue
           text = path.read_text()
           for regex in (version_re, version_pt_re, version_zh_re):
               m = regex.search(text)
               if m and m.group(1) != version:
                   violations.append(
                       f"{path}: version badge {m.group(1)} != VERSION {version}"
                   )
       return violations

   # 2. Goldens count badge sync
   def check_goldens_badge() -> list[str]:
       goldens = len(list(Path("tests/golden").glob("*.mn")))
       readme_files = [
           "README.md",
           "docs/README.es.md",
           "docs/README.pt.md",
           "docs/README.zh-CN.md",
       ]
       violations = []
       goldens_re = re.compile(r"goldens-(\d+)%2F(\d+)-")

       for path_str in readme_files:
           path = Path(path_str)
           if not path.exists():
               continue
           text = path.read_text()
           m = goldens_re.search(text)
           if m and (int(m.group(1)) != goldens or int(m.group(2)) != goldens):
               violations.append(
                   f"{path}: goldens badge {m.group(1)}/{m.group(2)} != actual {goldens}/{goldens}"
               )
       return violations

   # 3. Fixed-point line count drift in README body
   def check_fixed_point_line_count() -> list[str]:
       readme = Path("README.md").read_text()
       violations = []

       # Look for "238,086" (or similar exact line-count claims) outside the
       # documented STRICT line. If multiple distinct exact-line-count
       # claims are present, flag drift.
       exact_counts = re.findall(r"\b(\d{3},\d{3})\s+lines\b", readme)
       distinct = set(exact_counts) - {""}
       if len(distinct) > 1:
           violations.append(
               f"README.md: multiple distinct exact-line-count claims: {distinct}"
           )
       return violations

   # 4. Goldens count in body matches badge
   def check_goldens_body_consistency() -> list[str]:
       goldens = len(list(Path("tests/golden").glob("*.mn")))
       readme_files = [
           "README.md",
           "docs/README.es.md",
           "docs/README.pt.md",
           "docs/README.zh-CN.md",
       ]
       violations = []

       # Pattern: "(NN/NN native goldens" or similar
       body_re = re.compile(r"\((\d+)/(\d+)\s+(?:native\s+)?goldens?")

       for path_str in readme_files:
           path = Path(path_str)
           if not path.exists():
               continue
           text = path.read_text()
           m = body_re.search(text)
           if m and (int(m.group(1)) != goldens or int(m.group(2)) != goldens):
               violations.append(
                   f"{path}: body goldens claim {m.group(1)}/{m.group(2)} != actual {goldens}/{goldens}"
               )
       return violations

   # 5. SPEC.md header version freshness
   def check_spec_header() -> list[str]:
       spec = Path("docs/SPEC.md")
       if not spec.exists():
           return []
       header = "\n".join(spec.read_text().splitlines()[:10])
       version = Path("VERSION").read_text().strip()
       violations = []

       # Look for "synced to the v5.X.Y cut" pattern
       m = re.search(r"synced to the v(\S+) cut", header)
       if m:
           spec_version = m.group(1)
           # Allow lag of 1 patch release; flag if minor version is behind
           current_major_minor = ".".join(version.split(".")[:2])
           spec_major_minor = ".".join(spec_version.split(".")[:2])
           if current_major_minor != spec_major_minor:
               violations.append(
                   f"docs/SPEC.md: header references v{spec_version} but VERSION is {version} ({current_major_minor} vs {spec_major_minor})"
               )
       return violations

   def main() -> int:
       all_violations = []
       all_violations.extend(check_version_badges())
       all_violations.extend(check_goldens_badge())
       all_violations.extend(check_fixed_point_line_count())
       all_violations.extend(check_goldens_body_consistency())
       all_violations.extend(check_spec_header())

       if all_violations:
           print(f"check_doc_freshness: {len(all_violations)} drift violation(s):")
           for v in all_violations:
               print(f"  - {v}")
           print("\nTo opt out a specific check, add ``# noqa: doc-freshness`` "
                 "at the line; or update the stale reference at the source.")
           return 1
       print("check_doc_freshness: clean")
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. Make executable: `chmod +x scripts/check_doc_freshness.py`.

3. Run: `python3 scripts/check_doc_freshness.py`. Expect
   GREEN at v5.24.0 HEAD post-RC.\* / Mb.\* / Te.3.B fixes.

4. Wire into `.github/workflows/ci.yml`:
   ```yaml
   - name: check_doc_freshness
     run: python3 scripts/check_doc_freshness.py
   ```

5. Add to `make ci-gates` (already in Hy.1).

6. Add unit test in `tests/test_doc_freshness.py` with
   constructed fixtures for each violation class.

### Phase 3 — Hy.3 cadence enforcement gate

1. Create `scripts/check_cadence.py`:

   ```python
   #!/usr/bin/env python3
   """v5.24.0 Hy.3 — cadence enforcement gate.

   Per .reviews/REVIEW_CADENCE.md: panels run every 5 minor
   versions and on five language-feature releases. This script
   warns when either trigger has fired without a panel.
   """

   from __future__ import annotations
   import re
   import sys
   from pathlib import Path
   import subprocess

   def get_current_version() -> tuple[int, int, int]:
       v = Path("VERSION").read_text().strip()
       parts = v.split(".")
       return (int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

   def get_last_panel_version() -> tuple[int, int, int] | None:
       review_dir = Path(".reviews")
       if not review_dir.exists():
           return None
       panels = []
       for sub in review_dir.iterdir():
           if sub.is_dir() and sub.name.startswith("v"):
               m = re.match(r"v(\d+)\.(\d+)\.(\d+)", sub.name)
               if m:
                   panels.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
       if not panels:
           return None
       return max(panels)

   def main() -> int:
       current = get_current_version()
       last_panel = get_last_panel_version()
       if last_panel is None:
           print("check_cadence: no prior panel found")
           return 0

       minors_since = (current[0] - last_panel[0]) * 100 + (current[1] - last_panel[1])
       if minors_since >= 5:
           print(f"check_cadence: WARNING — {minors_since} minor versions since last panel (v{'.'.join(map(str, last_panel))})")
           print(f"  Per .reviews/REVIEW_CADENCE.md, a panel is OVERDUE.")
           print(f"  Schedule a v5.{last_panel[1] + 5}.0 panel cycle.")
           return 1
       print(f"check_cadence: OK ({minors_since} minor versions since v{'.'.join(map(str, last_panel))})")
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

2. Add as a soft-warn job in `.github/workflows/ci.yml`:
   ```yaml
   cadence-check:
     name: Cadence enforcement (warn-only)
     runs-on: ubuntu-latest
     continue-on-error: true  # warn, don't block
     steps:
       - uses: actions/checkout@v4
       - run: python3 scripts/check_cadence.py
   ```

3. Add to `make ci-gates`:
   ```makefile
   @python3 scripts/check_cadence.py || echo "  cadence: WARN (non-blocking)"
   ```

### Phase 4 — Hy.4 / Hy.5 / Hy.6 (LOW carries)

1. **Hy.4** — `scripts/build_from_seed.sh:159`:
   ```bash
   # Replace:
   if [ "${PASS}" -lt 45 ]; then
       echo "  ERROR: expected >=45 pass, got ${PASS}"
       exit 1
   fi

   # With:
   TOTAL_GOLDENS=$(ls tests/golden/*.mn | wc -l)
   EXPECTED_SEED_FAILS=20  # Te.5/Te.6/comprehensions/complex closures predate the seed
   EXPECTED_PASS=$((TOTAL_GOLDENS - EXPECTED_SEED_FAILS))
   if [ "${PASS}" -lt "${EXPECTED_PASS}" ]; then
       echo "  ERROR: expected >=${EXPECTED_PASS} pass (of ${TOTAL_GOLDENS} goldens, ${EXPECTED_SEED_FAILS} seed-incompatible), got ${PASS}"
       exit 1
   fi
   ```

2. **Hy.5** — open `.github/workflows/publish.yml`. Locate
   the `windows-bundled-llvm-smoke` job. Add parallel jobs:
   ```yaml
   linux-tarball-smoke:
     name: Linux versioned-tarball smoke gate
     runs-on: ubuntu-latest
     steps:
       - name: Download release tarball
         run: curl -L -o /tmp/mapanare.tar.gz https://github.com/${{ github.repository }}/releases/download/v${{ env.VERSION }}/mapanare-${{ env.VERSION }}-linux-x64.tar.gz
       - name: Extract and run smoke
         run: |
           mkdir /tmp/mapanare-extracted
           tar -xzf /tmp/mapanare.tar.gz -C /tmp/mapanare-extracted
           PATH=/tmp/mapanare-extracted/bin:$PATH mnc --version
           echo 'fn main(): print("hi")' > /tmp/hello.mn
           PATH=/tmp/mapanare-extracted/bin:$PATH mnc emit-llvm /tmp/hello.mn -o /tmp/hello.ll
           [ -s /tmp/hello.ll ] || (echo "FAIL: hello.ll empty"; exit 1)

   macos-tarball-smoke:
     name: macOS versioned-tarball smoke gate
     runs-on: macos-latest
     steps:
       # mirror linux job with the macOS tarball
       ...
   ```

3. **Hy.6** — open `.reviews/CARRY_FORWARD.md`. Find the
   Pe.1 row (in v5.22.0 panel new findings table). Update
   the wording per Mamba's recommendation. Also update
   `CLAUDE.md` preamble if Pe.1 is mentioned there.

### Phase 5 — closeout

1. SESSION_REPORT.md.
2. CHANGELOG `## [5.24.0]` entry.
3. CLAUDE.md release note.
4. Bump VERSION 5.23.2 → 5.24.0.
5. `python3 scripts/bump_version.py 5.24.0`.
6. CRLF restoration.
7. Run `make ci-gates` post-bump — verify GREEN at v5.24.0
   HEAD; this is the first release where the target exists.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| `check_doc_freshness.py` MVP scope-creeps to v6.0 shape | LOW | Hold to the 5 specific checks in Phase 2; broader prose-claim verification is explicitly out of scope |
| `make ci-gates` reveals MORE silently-failing gates than v5.23.0 fixed | MEDIUM | Each new finding either lands at v5.24.0 (if 30-min fix) or v5.24.x. Don't ship v5.24.0 with red sub-gates |
| Cadence enforcement gate fires immediately at v5.24.0 (5 minors past v5.22.0 = v5.27.0; not yet) | LOW | At v5.24.0, only 2 minors past v5.22.0; gate should NOT fire. If it does, the script logic is wrong |
| Hy.5 macOS / Linux smoke gates fail at v5.24.0 because the Linux/macOS tarballs aren't being built | MEDIUM | Investigate first if `publish.yml` actually builds those tarballs at this point. If not, Hy.5 expands to add the tarball-build steps too. May need to defer to v5.24.x |
| Hy.4 `>= 45` threshold change causes false-positive in CI on a release where seed-incompatible count temporarily spikes | LOW | The formula is conservative (TOTAL - 20); if the actual seed-incompatible count exceeds 20, bump `EXPECTED_SEED_FAILS` accordingly |

---

## Success criteria

- [ ] `make ci-gates` target exists and passes at v5.24.0 HEAD
- [ ] `scripts/check_doc_freshness.py` exists, wired into ci.yml, GREEN
- [ ] `scripts/check_cadence.py` exists, wired into ci.yml as soft-warn
- [ ] `>= 45` magic replaced with self-evident formula
- [ ] Pk.1.A — Linux + macOS versioned-tarball smoke gates in publish.yml
- [ ] Pe.1 framing retired in CARRY_FORWARD + CLAUDE.md
- [ ] Goldens 95/95 preserved
- [ ] Strict 3-stage fixed point preserved at v5.23.2's line count (zero compiler edits)
- [ ] `make lint` clean
- [ ] CARRY_FORWARD.md updated
- [ ] SESSION_REPORT.md written
- [ ] CHANGELOG entry
- [ ] CLAUDE.md release note
- [ ] VERSION bumped 5.23.2 → 5.24.0

---

## Out of scope (explicitly held)

- **Manifesto M2 / SPEC corpus M3.** v5.24.1 (Wd.\*).
- **Coral L1–L5 / TR1.** v5.24.1.
- **Bo.27 audit cross-reference column.** v5.27.0 audit
  (the convention applies at next pre-panel audit).
- **Compiler / runtime / `mapanare/self/*.mn` edits.** None.
- **v6.0 carries** (Rt.04, Te.3 hard removal, etc.).

---

## What this release CANNOT do

- Tag-promotion automation. Multi-session integration.
- Panel-spawning automation. Same shape; same defer.
- Scope-creep `check_doc_freshness.py` to verify every prose
  claim. v6.0+ shape.
