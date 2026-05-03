# v5.23.2 — Te.3.B — bootstrap brace-deprecation mirror

**Status:** PLANNING
**Breaking:** No (additive — adds warnings on previously-silent
shape).
**Prerequisite:** v5.23.1 shipped (Mb.\* memory hygiene; CI
green; ASan baseline updated).
**Estimated effort:** 1 session (~3–4 hours).
**Arc context:** Third release in v5.23–v5.24 recovery arc.

---

## Why this exists

Closes the **asymmetric closure** flagged independently by
3 v5.22.0 panel reviewers (Coral M1, Anaconda §3, Rattler #1):

1. **Python detector misses single-line `{...}` shape.** The
   PRE_PANEL_AUDIT.md's own canonical pre-flight test
   command demonstrates the gap:
   ```bash
   echo 'fn main() { print("hi") }' > /tmp/brace.mn
   python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
   # expected: warning: ... uses deprecated {}-block syntax ...
   # actual: NO WARNING
   ```
   `mapanare/parser.py::count_user_brace_block_openers` is
   line-based — counts `{` only when the *line itself* ends
   with `{` after stripping. Single-line `fn main() { print("hi") }`
   ends with `}` so the brace is silently uncounted.

2. **Native `mnc-stage1` has zero brace-deprecation logic at
   all.** `grep MAPANARE_NO_BRACE_WARNING mapanare/self/*.mn`
   returns zero hits. The Python detector itself
   (`count_user_brace_block_openers`) has no `.mn` mirror.
   This is **PY: closed | SH: open** asymmetric closure —
   should have been tracked per
   `.reviews/CARRY_FORWARD.md` dual-closure convention.

Te.3 is a soft-deprecation contract (SPEC §22) with a
2-release soak window before v6.0 hard removal. The
contract requires the warning to fire on **every brace
shape across both compilers**. The current state violates
that contract.

---

## Goals

1. Rewrite Python `count_user_brace_block_openers` as a
   token-walker (catches single-line `{...}` shape;
   correctly excludes `#{...}` map literals; comment- /
   string-aware).
2. Port the detector to `mapanare/self/parser.mn` (~50 LOC
   of `.mn` plus tests). Honor `MAPANARE_NO_BRACE_WARNING=1`
   env via `__mn_getenv` (already exported per v5.9.0 DX.\*).
3. New `tests/bootstrap/test_brace_deprecation_mirror.py`
   cross-bootstrap test (10 cases asserting Python ↔ stage1
   byte-identical warning text).
4. Update PRE_PANEL_AUDIT.md template + arc pre-flight test
   commands to actually demonstrate the warning.
5. Strict 3-stage fixed point: **WILL BREAK** at v5.23.1's
   line count and re-establish at a new line count
   (~239–240k expected) due to bootstrap source delta. Same
   fixed-point shape as v5.14.0 → v5.14.1 colon-block
   mirror release.

---

## Items

| ID | Severity | Description | Effort |
|---|---|---|---|
| **Te.3.B.1** | MEDIUM | **Python single-line shape fix.** Rewrite `mapanare/parser.py::count_user_brace_block_openers` as a token-walker. Scan tokens (or character-by-character with state), counting any `{` that opens a block in block position (after `fn`/`if`/`else`/`while`/`for`/`match`/`impl`/`trait`/`agent`/`struct`/`enum`/`=>`/`else`). Correctly exclude `#{` map literals and `${` interpolation. Skip strings, chars, line comments. Add a regression test in `tests/test_brace_deprecation.py` exercising the single-line `fn main() { print("hi") }` shape. | 1h |
| **Te.3.B.2** | MEDIUM | **Native mirror in `mapanare/self/parser.mn`.** Port the token-walker (or character-walker) to `.mn`. Hook into `parse()` before `tokenize()` (or after the indent-preprocessor pass). Print warning to stderr via `__mn_str_eprint`. Honor `MAPANARE_NO_BRACE_WARNING=1` env via `__mn_getenv` (export was added at v5.9.0 DX.4). Match the Python warning text byte-for-byte: `warning: <path>: uses deprecated {}-block syntax (<n> occurrence<s>). Run `mnc fmt <path>` to migrate. Hard removal in v6.0.` | 2h |
| **Te.3.B.3** | LOW | **Cross-bootstrap mirror test.** New `tests/bootstrap/test_brace_deprecation_mirror.py` (mirror of `test_te5_mirror.py`). 10 cases: single-line `{...}`, multi-line block, escaped `\{`, brace inside string, brace inside comment, `#{` map, `${` interpolation, `MAPANARE_NO_BRACE_WARNING=1` opt-out, file with mixed colon + brace, file with no braces. Assert Python ↔ stage1 byte-identical warning text. | 30 min |
| **Te.3.B.4** | LOW | **PRE_PANEL_AUDIT.md template update.** Update the v5.27.0 audit template (and any other audit templates) to use the **actual** working pre-flight command:<br>`echo 'fn main():\n    print("hi")' > /tmp/colon.mn`<br>(colon syntax — confirms warning does NOT fire)<br>`echo 'fn main() { print("hi") }' > /tmp/brace.mn`<br>`python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | grep "deprecated"`<br>(brace syntax single-line — confirms warning DOES fire post-Te.3.B.1)<br>Document the v5.22.0-vintage gap in the audit's "what changed since v5.22.0" block. | 15 min |
| **Te.3.B.5** | LOW | **Bb.\* seed refresh.** Te.3.B.2 adds ~50 LOC to `mapanare/self/parser.mn`; the bootstrap seed binary needs to be refreshed to compile the updated `mnc_all.mn`. Same shape as v5.17.0 Sh.E seed refresh. Verify `bash scripts/build_from_seed.sh` succeeds post-refresh. | 30 min |

---

## Phase plan

### Phase 0 — pre-flight verification

```bash
# Baseline must hold from v5.23.1
bash scripts/verify_fixed_point.sh --keep
# expected: stage2.ll == stage3.ll at v5.23.1's line count, 0 diff
python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1
# expected: 95/95
cat VERSION
# expected: 5.23.1

# Reproduce Te.3 single-line gap
echo 'fn main() { print("hi") }' > /tmp/brace.mn
python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
# expected at v5.23.1: NO WARNING (the gap)

echo 'fn main() {
  print("hi")
}' > /tmp/multi.mn
python3 -m mapanare emit-llvm /tmp/multi.mn 2>&1 | head -3
# expected at v5.23.1: warning: /tmp/multi.mn: uses deprecated...

# Reproduce native zero-coverage
mapanare/self/mnc-stage1 emit-llvm /tmp/multi.mn -o /tmp/x.ll 2>&1 | head -3
# expected at v5.23.1: NO WARNING (asymmetric closure)
```

### Phase 1 — Te.3.B.1 Python token-walker rewrite

1. Open `mapanare/parser.py`. Locate
   `count_user_brace_block_openers` (~lines 2240-2291).

2. Replace with token-walker (or character-walker):
   ```python
   def count_user_brace_block_openers(source: str) -> int:
       """Count user-written ``{`` block openers (any position
       on a line), skipping strings, chars, comments, and
       ``#{`` map literals + ``${`` interpolation. v5.23.2:
       rewritten to catch single-line {...} shapes."""
       count = 0
       i = 0
       in_str = in_char = in_line_cmt = False
       while i < len(source):
           ch = source[i]
           if in_line_cmt:
               if ch == "\n":
                   in_line_cmt = False
               i += 1
               continue
           if in_str:
               if ch == "\\" and i + 1 < len(source):
                   i += 2
                   continue
               if ch == '"':
                   in_str = False
               i += 1
               continue
           if in_char:
               if ch == "\\" and i + 1 < len(source):
                   i += 2
                   continue
               if ch == "'":
                   in_char = False
               i += 1
               continue
           if ch == "/" and i + 1 < len(source) and source[i + 1] == "/":
               in_line_cmt = True
               i += 2
               continue
           if ch == '"':
               in_str = True; i += 1; continue
           if ch == "'":
               in_char = True; i += 1; continue
           # ``#{`` is a map literal opener, not a block opener
           if ch == "#" and i + 1 < len(source) and source[i + 1] == "{":
               i += 2
               continue
           # ``${`` is interpolation inside a string — but we're not in_str here
           # If we see ${ outside a string, it's malformed; treat as not a block
           if ch == "$" and i + 1 < len(source) and source[i + 1] == "{":
               i += 2
               continue
           if ch == "{":
               count += 1
           i += 1
       return count
   ```

3. Run regression tests:
   ```bash
   pytest tests/test_brace_deprecation.py -v
   ```
   - Existing tests must still PASS.
   - Add new test exercising single-line `fn main() { print("hi") }`:
     ```python
     def test_single_line_brace_block_counted():
         assert count_user_brace_block_openers(
             'fn main() { print("hi") }'
         ) == 1
     ```

4. Verify the canonical pre-flight test from PRE_PANEL_AUDIT
   now works:
   ```bash
   echo 'fn main() { print("hi") }' > /tmp/brace.mn
   python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
   # expected: warning: /tmp/brace.mn: uses deprecated {}-block syntax (1 occurrence). ...
   ```

### Phase 2 — Te.3.B.2 native mirror

1. Open `mapanare/self/parser.mn`. Locate `parse()` entry.

2. Add a new function `count_user_brace_block_openers(source: String) -> Int`:
   - Mirror the Python algorithm character-by-character.
   - Use `__mn_str_index_of` / `__mn_str_charat` runtime
     helpers as needed (already exported per v5.16.0 Te.4
     string-interp work).

3. Add a new function
   `emit_brace_deprecation_warning(path: String, count: Int)`:
   - Check `MAPANARE_NO_BRACE_WARNING=1` env via
     `__mn_getenv("MAPANARE_NO_BRACE_WARNING")` (returns
     `Option<String>`).
   - Format the warning string:
     `"warning: " + path + ": uses deprecated {}-block syntax (" + str(count) + " occurrence" + (count == 1 ? "" : "s") + "). Run `mnc fmt " + path + "` to migrate. Hard removal in v6.0.\n"`
   - Print to stderr via `__mn_str_eprint`.

4. In `parse()`, before `tokenize()` (or after the
   indent-preprocessor pass), call:
   ```mn
   let brace_count: Int = count_user_brace_block_openers(source)
   if brace_count > 0:
       emit_brace_deprecation_warning(path, brace_count)
   ```

5. Rebuild stage1: `python3 scripts/build_stage1.py`.
   - **Will likely require Bb.\* seed refresh** (Te.3.B.5)
     because the seed predates the new functions.

6. Verify warning fires from native:
   ```bash
   echo 'fn main() { print("hi") }' > /tmp/brace.mn
   mapanare/self/mnc-stage1 emit-llvm /tmp/brace.mn -o /tmp/x.ll 2>&1 | head -3
   # expected: warning: /tmp/brace.mn: uses deprecated {}-block syntax (1 occurrence). ...

   MAPANARE_NO_BRACE_WARNING=1 mapanare/self/mnc-stage1 emit-llvm /tmp/brace.mn -o /tmp/x.ll 2>&1 | head -3
   # expected: no warning
   ```

### Phase 3 — Te.3.B.3 cross-bootstrap mirror test

1. Create `tests/bootstrap/test_brace_deprecation_mirror.py`:

   ```python
   """v5.23.2 Te.3.B cross-bootstrap brace-deprecation mirror test.

   Asserts that Python `mapanare emit-llvm` and native
   `mnc-stage1 emit-llvm` produce byte-identical warning text
   for every brace shape.
   """
   import subprocess
   from pathlib import Path
   import pytest

   STAGE1 = "mapanare/self/mnc-stage1"

   CASES = [
       ("single_line", 'fn main() { print("hi") }', 1),
       ("multi_line", 'fn main() {\n    print("hi")\n}\n', 1),
       ("escaped_brace", 'fn main():\n    print("\\{not a block}")', 0),
       ("brace_in_string", 'fn main():\n    print("{")', 0),
       ("brace_in_comment", 'fn main(): // {\n    print("hi")', 0),
       ("map_literal", 'fn main():\n    let m = #{ 1: 2 }', 0),
       ("interp_inside_string", 'fn main():\n    let n = 5\n    print("${n}")', 0),
       ("mixed_colon_brace", 'fn a(): pass\nfn b() { return 1 }', 1),
       ("no_braces", 'fn main():\n    print("hi")', 0),
       ("multiple", 'fn a() { 1 }\nfn b() { 2 }\nfn c():\n    pass\nfn d() { 3 }', 3),
   ]

   @pytest.mark.parametrize("name,src,expected_count", CASES)
   def test_python_native_warning_match(tmp_path, name, src, expected_count):
       fixture = tmp_path / f"{name}.mn"
       fixture.write_text(src, encoding="utf-8")

       py_out = subprocess.run(
           ["python3", "-m", "mapanare", "emit-llvm", str(fixture), "-o", str(tmp_path / "py.ll")],
           capture_output=True, text=True, timeout=30,
       )
       sh_out = subprocess.run(
           [STAGE1, "emit-llvm", str(fixture), "-o", str(tmp_path / "sh.ll")],
           capture_output=True, text=True, timeout=30,
       )

       py_warning = "\n".join(line for line in py_out.stderr.splitlines() if "deprecated" in line)
       sh_warning = "\n".join(line for line in sh_out.stderr.splitlines() if "deprecated" in line)

       if expected_count == 0:
           assert py_warning == "", f"Python: unexpected warning: {py_warning}"
           assert sh_warning == "", f"Native: unexpected warning: {sh_warning}"
       else:
           # Both must match (modulo path normalization)
           assert "deprecated" in py_warning, f"Python: missing warning"
           assert "deprecated" in sh_warning, f"Native: missing warning"
           assert f"({expected_count} occurrence" in py_warning
           assert f"({expected_count} occurrence" in sh_warning

   def test_no_brace_warning_env_opt_out(tmp_path):
       """MAPANARE_NO_BRACE_WARNING=1 suppresses warning in both bootstraps."""
       fixture = tmp_path / "brace.mn"
       fixture.write_text('fn main() { print("hi") }', encoding="utf-8")
       env = {"MAPANARE_NO_BRACE_WARNING": "1"}

       import os
       full_env = {**os.environ, **env}
       py = subprocess.run(
           ["python3", "-m", "mapanare", "emit-llvm", str(fixture), "-o", str(tmp_path / "py.ll")],
           capture_output=True, text=True, env=full_env, timeout=30,
       )
       sh = subprocess.run(
           [STAGE1, "emit-llvm", str(fixture), "-o", str(tmp_path / "sh.ll")],
           capture_output=True, text=True, env=full_env, timeout=30,
       )
       assert "deprecated" not in py.stderr
       assert "deprecated" not in sh.stderr
   ```

2. Run: `pytest tests/bootstrap/test_brace_deprecation_mirror.py -v`. All 11 cases (10 + opt-out) must PASS.

### Phase 4 — Te.3.B.4 PRE_PANEL_AUDIT.md template update

1. Open `.reviews/v5.22.0/PRE_PANEL_AUDIT.md`. Find the
   "Pre-flight commands the panel should run" section. Update
   the brace-deprecation flow:
   ```bash
   echo 'fn main() { print("hi") }' > /tmp/brace.mn
   python3 -m mapanare emit-llvm /tmp/brace.mn 2>&1 | head -3
   # expected: warning: /tmp/brace.mn: uses deprecated {}-block syntax (1 occurrence). ...
   ```

   This is now the canonical command. **Note**: this file is
   the past audit — don't rewrite history; rather, update for
   future audits at v5.27.0 by adding a "what changed since
   v5.22.0" block: "Te.3.B.1 fix at v5.23.2 makes this command
   work as documented; pre-v5.23.2 audits would fail this
   pre-flight."

2. If there's a future audit template at
   `.reviews/v5.27.0/PRE_PANEL_AUDIT.md` (or a generic
   template at `.reviews/PANEL_AUDIT_TEMPLATE.md`), update
   it with the post-Te.3.B language.

### Phase 5 — Te.3.B.5 Bb.* seed refresh

1. Run `bash scripts/build_from_seed.sh` post-Te.3.B.2.
   - **If it fails** with "old seed predates new functions",
     the seed needs refresh.
2. Refresh per v5.17.0 Sh.E pattern:
   ```bash
   # Use current mnc-stage1 (built from updated source) as the
   # new seed binary
   cp mapanare/self/mnc-stage1 bootstrap/seed/linux-x86_64/mnc
   ```
3. Re-run `bash scripts/build_from_seed.sh`. Must succeed.
4. Document seed refresh in SESSION_REPORT.

### Phase 6 — closeout

1. SESSION_REPORT.md.
2. CHANGELOG `## [5.23.2]` entry.
3. CLAUDE.md release note.
4. Bump VERSION 5.23.1 → 5.23.2.
5. `python3 scripts/bump_version.py 5.23.2`.
6. CRLF restoration.
7. `.reviews/CARRY_FORWARD.md` update — mark Te.3 hollow /
   asymmetric closure as CLOSED with v5.23.2.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Token-walker regex/algorithm differs subtly between Python and `.mn`, causing byte-identity test to fail | MEDIUM | Mirror the Python algorithm character-by-character; use the cross-bootstrap mirror test (Te.3.B.3) as the contract; if any case diverges, fix at the algorithm level |
| Bb.\* seed refresh breaks the no-Python build path | MEDIUM | Mirror v5.17.0 Sh.E precedent — the seed refresh has shipped before. Verify `bash scripts/build_from_seed.sh` succeeds at v5.23.2 HEAD post-refresh |
| Strict 3-stage fixed point grows unexpectedly | HIGH | Te.3.B.2 adds ~50 LOC to `mapanare/self/parser.mn`; expected stage2.ll growth is ~3-5k lines (similar to v5.14.1 Te.1.B colon-block mirror at +1,977 lines). Document new fixed-point in SESSION_REPORT |
| Native warning text diverges from Python (extra newline, capitalization, etc.) | MEDIUM | The cross-bootstrap mirror test will catch this; iterate until byte-identical |
| `MAPANARE_NO_BRACE_WARNING=1` opt-out not honored in native | LOW | The env var is read via `__mn_getenv` which has been exported since v5.9.0 DX.4; pattern is well-trodden |
| `mnc fmt` auto-migration default doesn't apply to single-line shape | UNKNOWN | This is out of scope for v5.23.2 (Te.3.C is in `mapanare/format.py`, separate from the warning detector). If `mnc fmt` doesn't migrate single-line braces, file as a follow-up at v5.24.x |

---

## Success criteria

- [ ] Python detector catches single-line `{...}` shape
- [ ] Native `mnc-stage1` fires the brace-deprecation warning on every brace shape
- [ ] `MAPANARE_NO_BRACE_WARNING=1` opt-out honored in both bootstraps
- [ ] Cross-bootstrap mirror test 11/11 PASS
- [ ] Goldens 95/95 preserved
- [ ] Strict 3-stage fixed point preserved (at new line count from bootstrap delta — documented)
- [ ] `make lint` clean
- [ ] `bash scripts/build_from_seed.sh` clean (post-Bb.\* seed refresh)
- [ ] CARRY_FORWARD.md updated (Te.3 asymmetric closure CLOSED)
- [ ] SESSION_REPORT.md written
- [ ] CHANGELOG `## [5.23.2]` entry
- [ ] CLAUDE.md release note
- [ ] VERSION bumped 5.23.1 → 5.23.2

---

## Out of scope (explicitly held)

- **Te.3 hard removal of `{}`.** v6.0.
- **`mnc fmt` auto-migration polish for single-line shapes.**
  v5.24.x if needed; not blocking v5.23.2.
- **Hy.\* structural hygiene gates.** v5.24.0.
- **Manifesto M2 / SPEC corpus M3.** v5.24.1.

---

## What this release CANNOT do

- Hard-remove `{}` syntax. That's v6.0; this is the
  warning-shape closure.
- Touch the v6.0 single-line `if x: y` deferral (Decision-1
  Path B at v5.21.1).
- Change the warning text shape after v5.23.2 ships — the
  cross-bootstrap mirror test pins it.
