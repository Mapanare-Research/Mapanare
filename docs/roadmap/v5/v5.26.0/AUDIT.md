# v5.26.0 — AUDIT

Phase 0 root-cause documentation for **Mb.7** (i64/i1 tag-emit
in `mapanare/self/emit_llvm.mn`) and **Mb.9** (Win64 ABI in
`runtime/native/mapanare_core.c`). Per `PROMPT.md` Phase 0:
both audits must answer their 5 hard-exit-criterion questions
before a single line of fix code is written.

---

## Mb.7 — i64/i1 tag-emit

### Q1 — Which canary?

`tests/golden/47_try_operator.mn` (4 lines exercise `?`-operator
on `Result<Int, String>`; 2 of them in `do_work()` and
`do_work_fail()` are the target).

### Q2 — The exact link error (verbatim)

```
$ ./mapanare/self/mnc-stage1 emit-llvm tests/golden/47_try_operator.mn > /tmp/v5260/47_native.ll
$ clang /tmp/v5260/47_native.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o /tmp/v5260/47_native
47_native.ll:229:9: error: '%tag2' defined with type 'i64' but expected 'i1'
  229 |   br i1 %tag2, label %prop_ok0, label %prop_err1
      |         ^
1 error generated.
```

The same shape recurs at line 256 (`do_work_fail`).

### Q3 — The exact emit_* function in `emit_llvm.mn`

`emit_enum_tag` at `mapanare/self/emit_llvm.mn:3507-3519`:

```mn
fn emit_enum_tag(st: EmitState, dest: Value, val: Value) -> EmitState:
    let mut s: EmitState = st
    let enum_ty: String = resolve_type(st, val.ty)
    let dn: String = dest.name
    // For Result/Option the tag field is i1; for enums it's i64.
    // Extract field 0 and zext to i64 if needed.
    if val.ty.kind == TK_RESULT() || val.ty.kind == TK_OPTION():
        let raw_tag: String = dn + ".raw"
        s = emit_line(s, emit_extractvalue(raw_tag, enum_ty, val.name, "0"))
        s = emit_line(s, "  " + dn + " = zext i1 " + raw_tag + " to i64")  // <-- ALWAYS zexts
    else:
        s = emit_line(s, emit_extractvalue(dn, enum_ty, val.name, "0"))
    s
```

For Result/Option subjects the function unconditionally extracts
the i1 tag and zexts it to i64. This produces the IR shape:

```
%tag.raw = extractvalue {i1, ...} %v, 0   ; i1
%tag = zext i1 %tag.raw to i64             ; i64
```

`emit_mir_branch` at `mapanare/self/emit_llvm.mn:1875-1877`
then writes the bare branch:

```mn
fn emit_mir_branch(st: EmitState, inst: Instruction) -> EmitState:
    let cond: Value = instr_branch_cond(inst)
    emit_line(st, emit_cbranch(cond.name, instr_branch_true(inst), instr_branch_false(inst)))
```

`emit_cbranch` (`emit_llvm_ir.mn:143`) is hard-coded to
`"  br i1 " + cond + ", label %..."` — no type coercion. Result:
the i64 SSA value is referenced from a `br i1`, which `clang -c`
rejects.

### Q4 — Python emitter's contract for the same site

Python `_do_enum_tag` (`mapanare/emit_llvm_text.py:5063-5089`)
also produces an i64 dest (it ZEXTs the i1 field 0 → i64 and
records the dest type as `I64` via `_put`). Python's contract
matches the self-host's: **EnumTag dest is i64**.

The difference is in `_do_branch`
(`mapanare/emit_llvm_text.py:4399-4413`):

```python
def _do_branch(self, i: Branch) -> None:
    cv, ct = self._get(i.cond)
    if ct != I1:
        ...
        if ct == I64:
            t = self._f("bc")
            self._L(f"{t} = icmp ne i64 {cv}, 0")
            cv = t
        ...
    self._L(f"br i1 {cv}, label %{i.true_block}, label %{i.false_block}")
```

Python actively coerces non-i1 conditions back to i1 via
`icmp ne i64 %cv, 0` before emitting the branch. This is the
missing step on the self-host side.

The Python output for golden 47 (lines 89-94 of /tmp/v5260/47_python.ll):

```
%et.6 = extractvalue {i1, {i64, {ptr, i64}}} %l.5, 0
%etz.7 = zext i1 %et.6 to i64
store i64 %etz.7, ptr %tag2.a.8
%l.9 = load i64, ptr %tag2.a.8
%bc.10 = icmp ne i64 %l.9, 0     ; <-- the missing step
br i1 %bc.10, label %prop_ok0, label %prop_err1
```

(Note: golden 47's Python IR also fails to compile at line 98
for an unrelated bug in the Result-payload `extractvalue`/store
shape — `%uw.12` is `{i64, {ptr, i64}}` stored into an `i64`
slot. That is a separate Python bootstrap bug, not on Mb.7's
docket — held for a future release. Mb.7 only targets the
self-host emitter; the link error on the self-host output is
the actionable one.)

### Q5 — Proposed minimal fix

Two call paths hit `emit_enum_tag`:

| Site | dest.ty.kind | Consumer | Required IR width |
|---|---|---|---|
| `lower.mn:3197` (try-op) | `TK_BOOL` | `Branch` → `br i1` | **i1** |
| `lower.mn:4470-4472` (match) | `TK_RESULT` / `TK_OPTION` / `TK_ENUM` | `Switch` → `switch i64` | **i64** |

The lowerer types the dest correctly per call site
(`make_value(s, mir_bool(), "tag")` for try-op vs
`make_value(s, subject_r.value.ty, "tag")` for match). The
emitter ignores `dest.ty.kind` and always zexts.

**Fix** — make `emit_enum_tag` honor `dest.ty.kind`. When the
lowerer asked for an i1 (`TK_BOOL`), emit i1; when it asked
for the wider enum type, keep the existing zext-to-i64 path
(load-bearing for `emit_mir_switch`, which hard-codes
`switch i64`).

```mn
fn emit_enum_tag(st: EmitState, dest: Value, val: Value) -> EmitState:
    let mut s: EmitState = st
    let enum_ty: String = resolve_type(st, val.ty)
    let dn: String = dest.name
    if val.ty.kind == TK_RESULT() || val.ty.kind == TK_OPTION():
        // Mb.7: dest type from the lowerer is the contract.
        // Try-op typed dest as mir_bool() (TK_BOOL) → emit i1.
        // Match typed dest as the enum type → zext to i64
        // for emit_mir_switch (which hardcodes "switch i64").
        if dest.ty.kind == TK_BOOL():
            s = emit_line(s, emit_extractvalue(dn, enum_ty, val.name, "0"))
        else:
            let raw_tag: String = dn + ".raw"
            s = emit_line(s, emit_extractvalue(raw_tag, enum_ty, val.name, "0"))
            s = emit_line(s, "  " + dn + " = zext i1 " + raw_tag + " to i64")
    else:
        s = emit_line(s, emit_extractvalue(dn, enum_ty, val.name, "0"))
    s
```

Diff: ~5 LOC (one new conditional branch). Match-path codegen
byte-identical (same zext path); try-op path emits the i1
directly, dropping the redundant zext.

**Why not change `emit_mir_branch` instead?** That mirror would
work too, but it requires runtime-tracking the actual emitted
type (Python has `_get` returning the SSA name + emitted type;
the self-host doesn't track emitted types separately from MIR
types). Routing the fix through the lowerer's contract
(`dest.ty.kind`) is the closest analog the self-host has. The
lowerer is the source of truth and has already declared the
correct expected type at each call site — the emitter just
ignored it.

**Falsifiability: minimal-fix hypothesis.** Expected diff: 5
LOC. If the fix grows past ~30 LOC, the hypothesis was wrong
and we go back to investigation per `PROMPT.md` discipline.

### Reproducibility

```bash
mkdir -p /tmp/v5260
python3 -m mapanare emit-llvm tests/golden/47_try_operator.mn -o /tmp/v5260/47_python.ll
./mapanare/self/mnc-stage1 emit-llvm tests/golden/47_try_operator.mn > /tmp/v5260/47_native.ll
diff /tmp/v5260/47_python.ll /tmp/v5260/47_native.ll | head -50
clang /tmp/v5260/47_native.ll runtime/native/libmapanare_rt.a -lm -lpthread -ldl -o /tmp/v5260/47 2>&1 | head -5
# expected: error: '%tag2' defined with type 'i64' but expected 'i1' at line 229
```

### Post-fix scope discovery — the PLAN's 9-goldens premise was incorrect

Phase 1 applied the surgical fix above. Re-running the link
contract on all 9 PLAN-listed goldens showed:

| Golden | Pre-Mb.7 | Post-Mb.7 | Cause |
|---|---|---|---|
| 47_try_operator | LINK_FAIL | **LINK_FAIL** (different) | `emit_unwrap` on `Result<T,E>` does single `extractvalue` at index 1 → returns the inner `{Ok_ty, Err_ty}` aggregate, but downstream code stores it into the Ok-payload slot. Distinct bug — affects both Python and self-host emitters. |
| 48_match_nested_exhaustive | LINK_FAIL | **LINK_FAIL** (different) | `Result<Int,String>` literal construction has three disagreeing types in the `insertvalue` chain (outer `{i1, {ptr, ptr}}`, inner `{i64, ptr}` — neither is the canonical `{i64, {ptr, i64}}` for `Result<Int,String>`). Distinct bug. |
| 49_match_guards | LINK_FAIL | **LINK_FAIL** (different) | `match n:` where `n: Int` emits `extractvalue i64 %n, 0` — i.e. an `EnumTag` is being lowered against a non-enum Int subject. Distinct bug — match-on-primitive lowering surface. |
| 51_match_guards_and_or | LINK_FAIL | **LINK_FAIL** (different) | `match opt: Some(0) \| None => ...` emits 4× `i64 1` cases in `switch` (every constructor-pattern arm uses the same Some=1 tag, so or-patterns + guards collapse onto duplicate cases). Distinct bug — or-pattern lowering surface. |
| 55_async_basic | LINK_FAIL | **PASS** | Mb.7 closes. |
| 56_async_await | LINK_FAIL | **PASS** | Mb.7 closes. |
| 57_real_await | LINK_FAIL | **PASS** | Mb.7 closes. |
| 58_async_file_io | LINK_FAIL | **PASS** | Mb.7 closes. |
| 59_async_fanout | LINK_FAIL | **PASS** | Mb.7 closes. |

**5 of 9 close at v5.26.0; 4 of 9 are distinct bug classes.** The
PLAN's framing ("9 LINK_FAIL goldens trip an i64/i1 tag-emit bug")
was correct only for the async cluster (55-59). Goldens 47/48/49/51
fail for unrelated reasons — they were grouped under "LINK_FAIL"
in v5.23.1 SESSION_REPORT because the investigation never actually
linked the IR (the test harness does AST/IR comparison, not link).
Both Python and self-host emit the same broken IR, so harness
comparisons report PASS while link-time validation fails.

This finding aligns with the PROMPT's risk #1 ("fix surfaces a
deeper bug"). Per the PROMPT's discipline ("If you find yourself
writing more than 30 LOC, stop — the hypothesis was wrong, scope
back to Phase 0 and re-investigate"), v5.26.0 ships the Mb.7 fix
as-scoped (the actual i64/i1 tag-emit bug, which closes the async
cluster) and **rescopes the remaining 4 distinct bugs to
v5.26.1+**. Each will need its own Phase 0 audit.

**Goldens-95/95 invariant:** preserved at HEAD per
`python3 scripts/test_native.py --stage1 mapanare/self/mnc-stage1`.
The harness PASS bar (Python ↔ self-host IR match) is unchanged;
only the (separate) link-time bar improves on 5/9 canaries.

---

## Mb.9 — Win64 ABI for `__mn_count_user_brace_block_openers`

### Q1 — Reproducer / canary

The publish-run-#48 Windows `build-native (windows-latest,
mnc-win-x64.exe, x86_64-w64-mingw32)` job runs:

```bash
./mapanare/self/mnc-stage1.exe emit-llvm mapanare/self/mnc_all.mn > stage2.ll
```

`mnc-stage1.exe` is built by `python scripts/build_stage1.py`,
which uses Python's `emit_llvm_text.py` to lower `mnc_all.mn`
(the concatenated 21k-line self-host) into LLVM IR; gcc + the
C runtime then link `mnc-stage1.exe`.

When `mnc-stage1.exe` then parses `mnc_all.mn`, its parser
calls `__mn_count_user_brace_block_openers(source)` (per
`mapanare/self/parser.mn:367`, the v5.23.2 Te.3.B.2 Python
mirror). The call OOMs on Windows.

### Q2 — The exact OOM (verbatim from publish run #48)

```
mapanare: oom in count_user_brace_block_openers
warning: HEAP[mnc-stage1.exe]:
warning: Invalid allocation size - 65746172656e6567 (exceeded 7ffffffdefff)
```

`0x65746172656e6567` is little-endian for the 8 ASCII bytes
`g e n e r a t e`. `mnc_all.mn` starts with the comment
`// Auto-generated:`; bytes 8..16 are exactly `g e n e r a t e`.
So the function read `source.len` and got the **first 8 bytes
of the data buffer pointed to by source.data** rather than
the actual length stored in the struct.

### Q3 — The exact ABI mismatch

Python's `_do_call` user-function path
(`mapanare/emit_llvm_text.py:4180-4236`) classifies args
through `_use_byref(t)` which uses a 64-byte threshold:

```python
_BYREF_BYTES = 64

@staticmethod
def _use_byref(ty: str) -> bool:
    return ty.startswith("{") and ty.endswith("}") and _tsz(ty) > LLVMTextEmitter._BYREF_BYTES
```

`MnString` lowers to `{ptr, i64}` = 16 bytes. `_use_byref`
returns False (16 < 64). The call site emits the struct by
value:

```
call i64 @__mn_count_user_brace_block_openers({ptr, i64} %s)
```

But the **declaration** of the function (via `_decl_fn`,
`mapanare/emit_llvm_text.py:1330-1339`) DOES check
`_is_large_struct(t)` (8-byte threshold) on Win64:

```python
if self._use_win64_abi:
    abi_pts = ["ptr" if self._is_large_struct(t) else t for t in pts]
```

`_is_large_struct({ptr, i64})` = True. So the declaration is:

```
declare i64 @__mn_count_user_brace_block_openers(ptr) ...
```

Mismatch: **decl says ptr, call passes struct**. LLVM's Win64
backend lowers the call by passing the 16-byte struct directly
in two registers (rcx=data, rdx=len), but gcc's C compiler
implements `int64_t fn(MnString)` per Win64 ABI = pass struct
by hidden pointer in rcx. Result: gcc reads
`source.data = *rcx` (the data pointer) and
`source.len = *(rcx + 8)` (whatever's at offset 8 of the data
buffer — for `mnc_all.mn` that's `"generate"` →
`0x65746172656e6567`). Then `malloc((size_t)n)` blows up.

### Q4 — Why does `__mn_indent_to_braces` work?

It has a **dedicated handler** in `_do_call` that routes
through `_rt` instead of falling through to the user-call
path:

```python
# mapanare/emit_llvm_text.py:3614-3638 (v5.23.1 Mb.1)
if fn == "__mn_indent_to_braces" and args:
    a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
    r = self._rt("__mn_indent_to_braces", STR, [STR], [(a, STR)])
    self._track_string(r)
    self._last_tracked_str_slot = None
    self._put(i.dest, r, STR)
    return
```

`_rt` (`mapanare/emit_llvm_text.py:1599-1626`) uses
`_is_large_struct` (8-byte threshold) on Win64 and emits the
correct alloca + store + ptr-pass pattern. The handler was
added in v5.23.1 Mb.1 to fix a memory leak; it incidentally
also fixes the Win64 ABI for that function.

`__mn_count_user_brace_block_openers` and
`__mn_emit_brace_deprecation_warning` were added in v5.23.2
**without an analogous handler**. They fall through to the
user-call path and get the buggy 64-byte threshold.

### Q5 — Self-host parallel + sister symbol

`mapanare/self/emit_llvm.mn::is_byref_type_st` (lines 2536–2546)
also uses the 64-byte threshold. The `emit_mir_call` user-call
path (lines 4179–4185) exhibits the same shape. So the
self-host has the same latent bug — it doesn't manifest yet
because the only Win64 caller of these functions is `mnc-stage1.exe`
itself (built by Python). Once `mnc-stage1.exe` is fixed, the
self-host emitter (running natively on Windows targeting
Windows) will also need the parallel fix to keep stage2.ll
correct.

Sister symbol `__mn_emit_brace_deprecation_warning(MnString,
i64)` has the same MnString parameter — same latent bug. It's
called from parser.mn immediately after the count function:

```mn
let brace_count: Int = __mn_count_user_brace_block_openers(source)
if brace_count > 0:
    __mn_emit_brace_deprecation_warning(filename, brace_count)
```

In production it just happens to be called only when count > 0,
so the bug shape would be: garbage `count` from the OOM'd call
above, followed by garbage `path.len` from `filename` for the
warning emit. Both must be fixed in lockstep.

### Proposed minimal fix

Mirror the v5.23.1 Mb.1 pattern for `__mn_indent_to_braces`:
add explicit handlers in `_do_call` (Python) AND `emit_mir_call`
(self-host) for both v5.23.2 functions, routing them through
the runtime-call path that already has correct Win64 ABI
handling.

Python (~10 LOC in `mapanare/emit_llvm_text.py`):

```python
if fn == "__mn_count_user_brace_block_openers" and args:
    a = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
    r = self._rt(fn, I64, [STR], [(a, STR)])
    self._put(i.dest, r, I64)
    return
if fn == "__mn_emit_brace_deprecation_warning" and len(args) >= 2:
    pa = self._coerce(args[0][0], args[0][1], STR) if args[0][1] != STR else args[0][0]
    cv = self._coerce(args[1][0], args[1][1], I64) if args[1][1] != I64 else args[1][0]
    self._rt(fn, VOID, [STR, I64], [(pa, STR), (cv, I64)])
    self._put(i.dest, "0", I1)
    return
```

Self-host (~12 LOC in `mapanare/self/emit_llvm.mn`):
analogous routing through `emit_rt_call` / `emit_rt_call_void`.

**Why not a C-side fix?** The PLAN suggested editing
`runtime/native/mapanare_core.c`, but the C side is correct —
gcc generates Win64-conformant code from the `MnString` C
signature. The mismatch is on the IR side: the call expression
diverges from the declaration. Fixing the C side would mean
contradicting the actual Win64 ABI just to align with broken IR
— textbook v5.7.0 "sledgehammer anti-pattern" which the PROMPT
explicitly forbids.

**Why not a C-runtime call-shape change (Bb.\* seed refresh
trigger)?** No new C-runtime exports are added. The seed
refresh is **NOT triggered by Mb.9.B** as the PLAN expected —
the IR-side fix doesn't change call shapes the seed has to
re-emit. Documenting this in SESSION_REPORT and skipping the
seed refresh.

### Reproducibility (Linux ctypes proxy)

The Linux ctypes call works because Linux SysV ABI passes
16-byte structs in two registers, exactly matching what the IR
emits. This is why the bug is Windows-only. The Linux-side
ctypes call is therefore a **lower-bound contract**, not a
reproducer:

```python
import ctypes
lib = ctypes.CDLL("runtime/native/libmapanare_runtime.so")

class MnString(ctypes.Structure):
    _fields_ = [("data", ctypes.c_char_p), ("len", ctypes.c_uint64)]

src = b"// Auto-generated:\nfn main() { print(1) }\n"
s = MnString(src, len(src))
lib.__mn_count_user_brace_block_openers.argtypes = [MnString]
lib.__mn_count_user_brace_block_openers.restype = ctypes.c_int64
print(lib.__mn_count_user_brace_block_openers(s))
# Linux: 1 (correct)
# Windows would crash here pre-fix, succeed post-fix.
```

A Linux regression test using ctypes locks in the Linux contract;
the Windows-specific ABI fix is verified by the publish-run
going green on next push.
