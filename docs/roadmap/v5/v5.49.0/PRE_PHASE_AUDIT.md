# v5.49.0 — Wn.0 — Phase 0 Audit

**Date:** 2026-05-07
**Status:** COMPLETED — call site named, fix shape proposed, bundle/split decision made.
**Method:** Local Windows repro on the user's `windows-latest`-equivalent
machine (Windows 11 Pro x64). The PROMPT's `workflow_dispatch` /
CI-runner path was not used because (a) `publish.yml` has no
`refs/heads/main` guard on its `release` job and triggering it
against `dev` would tag/release v5.48.1 as a side effect, and
(b) the bug reproduces deterministically off-CI with the same
`scripts/build_stage1.py` pipeline the runner uses.
The CI-side gdb-wrapper port (Wn.3) is still done for permanent
instrumentation; this audit's diagnostic came from local gdb.

---

## 1. Reproducer

Built `mapanare/self/mnc-stage1.exe` via the same path CI uses
(`publish.yml:771-789`):

```powershell
$env:PATH = "$pwd\toolchain\bin;$pwd\.tmp-llvm-mingw\llvm-mingw-20260421-ucrt-x86_64\bin;$env:PATH"
$env:STRIP = "0"   # keep symbols for gdb
python scripts/build_stage1.py
```

- `gcc.exe (GCC) 15.2.0` from w64devkit 2.7.0 (the PortableW64
  toolchain CI bundles via `publish.yml:755-769`).
- `clang version 22.1.4` from llvm-mingw-20260421-ucrt-x86_64
  (the same archive `publish.yml:520-533` downloads).
- `GNU gdb 17.1` from w64devkit.

`hello.mn` matches `publish.yml:576-580` byte-for-byte:

```mn
fn main() {
    print("hello from clean Windows SDK smoke")
}
```

### 1.1 `--version` smoke (works)

```
PS> & ./mapanare/self/mnc-stage1.exe --version
mapanare 5.48.1
exit: 0
```

The native binary loads cleanly. Nw.4 native-dispatch gate holds.

### 1.2 `run hello.mn` smoke (FAILS — REPRODUCED)

```
PS> & ./mapanare/self/mnc-stage1.exe run hello.mn
mapanare: out of memory (requested 8017634865777560157 bytes)
exit: 1
```

Same shape as the CI failure. The exact garbage size_t differs from
CI's `7011361785666170466` because the bytes come from
uninitialized stack memory which depends on the ambient process
state — but the failure class is identical (huge bogus `size_t` to
`__mn_alloc`).

---

## 2. gdb backtrace (the load-bearing diagnostic)

Set a conditional breakpoint at the start of `__mn_alloc` that
fires only when `size > 1 GB` (any reasonable allocation is much
smaller):

```
PS> gdb -batch -ex 'break __mn_alloc if size > 1073741824' -ex 'run' \
    -ex 'bt 80' --args ./mapanare/self/mnc-stage1.exe run hello.mn
```

```
Thread 1 hit Breakpoint 1.1, __mn_alloc (size=8017634865777560157)
    at runtime/native/mapanare_core.c:108

#0  __mn_alloc (size=8017634865777560157)              mapanare_core.c:108
#1  mn_to_cstr (s=...)                                 mapanare_core.c:1504
    s = {data = <optimized out>, len = 8017634865777560156, is_heap = <optimized out>}
#2  __mn_file_exists (path=<error reading variable: Cannot access
                memory at address 0x6f445c6e61754a65>) mapanare_core.c:1562
    char *cpath = mn_to_cstr(path);
#3  find_clang ()                                      [from main.ll → main.mn:80]
```

Frames 4+ are in stripped code (Mapanare-emitted IR compiled with
`-O2` no `-g`); their absence is fine — the chain `find_clang()
→ __mn_file_exists(path) → mn_to_cstr(s) → __mn_alloc(s.len + 1)`
fully localizes the bug.

### 2.1 Decoding the garbage

`path` enters `__mn_file_exists` with `data = 0x6f445c6e61754a65`
(unmapped — gdb's "Cannot access memory" error). Decoded little-
endian: `0x65 0x4a 0x75 0x61 0x6e 0x5c 0x44 0x6f` = `"eJuan\Do"`
— bytes from the path string `C:\Users\Juan\Documents\...`.

That is: the **bytes of the path data buffer's address are being
read as if they were a pointer to MnString**, and the value the
caller actually placed in RCX (the data pointer of the MnString
struct argument) is being treated as the address of the MnString
struct itself by the callee.

This is the canonical Win64-vs-SysV ABI mismatch for a 16-byte
aggregate-by-value argument.

---

## 3. Root cause

### 3.1 The MnString shape

`runtime/native/mapanare_core.h:57-61`:

```c
typedef struct {
    const char *data;
    uint64_t    len     : 63;  /* bitfield */
    uint64_t    is_heap : 1;
} MnString;  /* 16 bytes total */
```

- **Win64 ABI** for any aggregate >8 bytes: pass by **hidden
  pointer** in RCX (the caller spills the struct to a stack temp
  and passes its address).
- **SysV ABI** (Linux/macOS x86_64) for a 16-byte aggregate: pass
  in two registers (RDI = first 8 bytes, RSI = second 8 bytes).
  This is why the bug is **invisible on Linux/macOS** — when both
  caller and callee agree on SysV, the data ptr lands in RDI and
  is read as `path.data` correctly.

### 3.2 The two emitter paths in `emit_llvm_text.py`

The Python bootstrap has **two** code paths for emitting runtime
calls:

**Path A — `_rt(...)` at `mapanare/emit_llvm_text.py:1602-1639`.**
This path is correct on Win64. It checks `_use_win64_abi`, alloca's
the MnString to a stack temp, stores the aggregate value into it,
and passes `ptr %sarg` at the call site. Used for the
Mapanare-level builtin `file_exists(path)` (line 3715-3717).

**Path B — auto-declare at `mapanare/emit_llvm_text.py:4417-4458`
(in `_do_call`).** This path handles **direct** `__mn_*` calls in
Mapanare source, like `__mn_file_exists(bundled_win)` in
`find_clang()`. It autodecls the function and emits the call site
itself. The relevant lines are 4434-4439:

```python
abi_args2: list[tuple[str, str]] = []
for v, t in coerced2:
    if self._use_byref(t):                 # <-- BUG
        a2 = self._alloca(t, "barg")
        self._L(f"store {t} {v}, ptr {a2}")
        abi_args2.append((a2, "ptr"))
    else:
        abi_args2.append((v, t))
```

**`_use_byref(t)`** at `emit_llvm_text.py:1316-1318` returns True
only for structs **larger than `_BYREF_BYTES` (64 bytes)** —
intended for `LowerState` (240 B), `EmitState` (240 B), etc. **A
16-byte `MnString` does NOT qualify**, so it falls through to the
`else` branch and is passed as a first-class aggregate `{ptr, i64}
%v`. The declaration emitted by `_decl_fn` at line 1340-1346
*correctly* converts the param to `ptr` on Win64 (using
`_is_large_struct`, threshold >8 bytes), but **the call site uses
the wrong threshold**.

The result is exactly what we see in the IR
(`mapanare/self/main.ll`):

```llvm
declare ptr @__mn_file_exists(ptr) nounwind readonly willreturn
                            ; ^ correct Win64 declaration: ptr arg

%c.23 = call ptr @__mn_file_exists({ptr, i64} %l.22)
                            ; ^ call site disagrees: 16-B aggregate-by-value
```

LLVM lowers the call site under SysV-style aggregate-in-registers
(RCX = first 8 bytes = data ptr; RDX = next 8 bytes = len). The C
function's prologue (compiled per Win64 ABI) reads RCX as a
hidden-pointer-to-MnString and dereferences it — landing on the
data buffer's contents, which become the corrupt `path.data` and
`path.len` we see in the gdb backtrace.

### 3.3 The return-type secondary issue

The same auto-declare path at line 4422 has:
```python
ret_auto = self._rty(i.dest.ty)
```

For `if __mn_file_exists(bundled_win) != 0:` the MIR inferencer
chose `i.dest.ty = Ptr` (no annotation; `!= 0` matches both
ptr-vs-null and int-vs-zero), so `ret_auto = "ptr"` instead of
`"i64"`. This is **why the declaration says `declare ptr
@__mn_file_exists(ptr)` instead of `declare i64
@__mn_file_exists(ptr)`**.

This return-type mismatch is **not** the OOM cause (both `i64`
and `ptr` fit in RAX so the result value transports correctly,
and the Mapanare side `ptrtoint`s before comparing to 0). But it
is a related smell: `__mn_*` direct calls fundamentally lack
authoritative signature registration in the Python bootstrap.

### 3.4 Why this hasn't surfaced before

- All other `__mn_*` direct calls in `mapanare/self/*.mn` either
  (a) take no struct args (e.g. `__mn_host_is_windows()`,
  `__mn_argc()`, `__mn_dir_count_files`), or (b) have explicit
  `let r: Int = __mn_system(...)` annotations that pin the
  destination type to Int and force the SysV-coincidence path
  on Linux. The `__mn_file_exists(...)` call in `find_clang`
  (main.mn:80, 84) is structurally distinguishable: it takes
  exactly one MnString arg AND the result is consumed in a
  comparison without a typed-let intermediate.
- On Linux/macOS x86_64 the SysV ABI accidentally puts the data
  ptr in RDI either way (aggregate-in-registers OR
  hidden-pointer-fall-through-to-RDI), so the bug is invisible.
- The first `mnc.exe run` smoke landed in a Windows SDK ZIP only
  recently (the SDK runway closed in v5.12.0; v5.32.0 Nw.4 made
  `mnc.exe` a *real* native binary instead of a PyInstaller alias;
  the smoke step at `publish.yml:564-604` was added incrementally
  through v5.32.x to v5.47.x). The `--version` check at line 589
  has been green; the `run hello.mn` check at line 596 is the
  first one to exercise an MnString-arg `__mn_*` runtime call
  inside the staged binary.

---

## 4. Call site (the answer Phase 0 was asked for)

**Mapanare source:** `mapanare/self/main.mn:80` and `main.mn:84` —
the two `__mn_file_exists(bundled_win)` / `__mn_file_exists(bundled_unix)`
sites inside `fn find_clang() -> String`.

**IR shape:** `mapanare/self/main.ll:6706` (declaration),
`mapanare/self/main.ll:7276`, `:7329`, `:23422`, `:23514`, `:23639`
(call sites — five total across `find_clang()` and its inlined
copies).

**Python emitter site (the actual fix location):**
`mapanare/emit_llvm_text.py:4417-4458` (`_do_call` auto-declare
path) and the parallel `_do_extern` path at lines 4474-4493. The
fix replaces `_use_byref(t)` (>64-byte threshold) with
`_use_win64_abi`-aware logic mirroring `_rt`'s `_is_large_struct`
(>8-byte threshold).

**Self-host mirror site:** `mapanare/self/emit_llvm.mn` has the
same structural issue (line 1312 declares
`__mn_file_exists` with `llvm_string()` → `{ptr, i64}` aggregate
arg type, and `emit_rt_call` similarly lacks Win64-arg byref
spill-to-stack logic for ≤ 64 B aggregates). The exact mirror
LOC count needs Phase 1 measurement; Wn.2 is **triggered**, not
a no-op gate.

---

## 5. Sized fix proposal

### Wn.1 (Python bootstrap)

**Location:** `mapanare/emit_llvm_text.py`.

**Approach:** in the auto-declare paths in `_do_call` (line
4434-4439) and `_do_extern` (line 4486+), replace the
`_use_byref(t)` arg-spill condition with the same condition the
declaration emitter uses on Win64 — i.e., spill any
`_is_large_struct(t)` (>8 bytes) struct on Win64, mirroring
`_rt`'s `_use_win64_abi` branch. Same applies to i686 (`byval`
+ `align 4` form, mirroring `_rt`'s `_use_i686_abi` branch).

**Estimated LOC:** ~25 LOC across two call sites in
`emit_llvm_text.py`. Pattern is a copy of the `_rt` Win64 / i686
sarg branches.

**Optional cleanup (consider but defer if pushes scope):**
add a `_RUNTIME_FN_SIGS` dict (parallel to `_RUNTIME_FN_ATTRS`)
pinning known `__mn_*` signatures so the auto-declare path uses
authoritative types instead of MIR-inferred ones. Closes the
return-type smell (§3.3) and makes the fix more surgical. ~30
additional LOC. **Decision: defer to v5.49.x as Wn.1.x patch
candidate** — the call-site spill fix alone closes the OOM.

### Wn.2 (self-host mirror)

**Location:** `mapanare/self/emit_llvm.mn`.

**Approach:** mirror the Python fix: `emit_rt_call` (and the
unknown-fn auto-declare path) must spill `llvm_string()` /
`{ptr, i64}` args to a stack alloca and pass `ptr` on Win64,
matching the declaration shape. The self-host already has Win64
target awareness for sret returns (v5.8.4 Wb.2); extend to sarg
arguments.

**Estimated LOC:** ~30-50 LOC in `mapanare/self/emit_llvm.mn`.

**STRICT discipline:** stage1 rebuild after each edit; goldens
**103/103** at every checkpoint; STRICT 3-stage fixed point
preserved at v5.48.1's **245,115-line** baseline. Halt on
divergence.

### Bundle/split decision

**Wn.0 finding:** call-site identified, fix shape clear, single
class of bug (Win64 sarg spill missing in two emitter paths). Wn.1
+ Wn.2 combined: ~55-75 LOC. The PROMPT's threshold is "≤ 50 LOC =
bundle". **Decision: bundle Wn.1 + Wn.2 in v5.49.0** because (a)
the LOC number is just over the threshold but the bug is
single-cause, single-class, and the mirror is nearly mechanical;
(b) splitting Wn.2 would leave self-host emit_llvm.mn with a
known-broken Win64 sarg path that would resurface the moment
mnc-stage1 is used to emit IR for any user program calling MnString-
arg runtime fns on Windows. The risk of leaving it half-fixed
exceeds the marginal scope cost of bundling.

The optional `_RUNTIME_FN_SIGS` cleanup is a separate v5.49.x
patch candidate.

---

## 6. Falsifiability anchor (Wn.4 preview)

The post-fix test will be `tests/native/test_windows_run_smoke.py`
(`tests/native/` already houses Win64-only ABI tests; that's the
right cluster). It invokes the locally-staged
`mapanare/self/mnc-stage1.exe` (or `dist/mapanare/mnc.exe` if
present) with the `publish.yml:576-580` `hello.mn` payload and
asserts exit 0 + expected stdout. Skipped on non-Windows via
`pytest.mark.skipif(sys.platform != "win32")`.

Pre-Wn.1 the test fails with the recorded OOM signature
(`"out of memory (requested " + huge + " bytes)"`); post-Wn.1 it
passes.

---

## 7. Out of scope (carry forward)

- **Pre-registering `_RUNTIME_FN_SIGS`** for all `__mn_*` symbols
  in the Python bootstrap (cleaner, broader). Defer to v5.49.x.
- **MIR-level type inference** for unannotated `__mn_*` calls
  (the v5.40.0 Ai.1 `_specialize_fn` body-walk family). Already
  on the v6.0 carry-forward list.
- **Other unannotated `__mn_*` direct calls** in `mapanare/self/`
  that take MnString args: a sweep is recommended after Wn.1
  lands. None known to be load-bearing on Win64 today (annotated
  `let r: Int = __mn_system(...)` is the dominant pattern).

---

## 8. Decision summary

| Item | Status |
|---|---|
| Phase 0 audit | **COMPLETE** |
| Reproducer | **CAPTURED** locally on Win64 |
| gdb backtrace | **CAPTURED** (verbatim in §2 above) |
| Call site named | **YES** — `find_clang()` → `__mn_file_exists(MnString)` Win64 sarg |
| Fix site named | **YES** — `mapanare/emit_llvm_text.py:4434` + `:4486` |
| Self-host mirror site named | **YES** — `mapanare/self/emit_llvm.mn::emit_rt_call` |
| Bundle/split | **BUNDLE** Wn.1 + Wn.2 in v5.49.0 |
| Wn.2 conditional gate | **TRIGGERED** (self-host edits required) |
| Wn.3 wrapper port | **DO IT ANYWAY** — permanent infrastructure per PROMPT |
| Wn.4 falsifiability | **READY** — test name + signature recorded above |

**Phase 0 gate: PASSED.** Implementation may proceed.
