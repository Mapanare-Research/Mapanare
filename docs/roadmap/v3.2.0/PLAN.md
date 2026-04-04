# Mapanare v3.2.0 — Real Programs

> From toy tests to real software. The compiler grows up.

**Status:** IN PROGRESS
**Author:** Juan Denis
**Date:** April 2026
**Breaking:** No

---

## Goal

Expand the self-hosted compiler from compiling toy golden tests to handling
real-world programs: file I/O, string escapes, proper error handling, and
a stdlib written in Mapanare.

---

## Inherited State (from v3.1.0)

| Component | Status |
|-----------|--------|
| Three-stage fixed point | Verified |
| 15/15 golden tests | Correct output + exit 0 |
| Bootstrap seed | Checked in (no Python needed to build) |
| C runtime | mapanare_core.c (~2000 lines) |
| Self-hosted compiler | 9,400+ lines, 10 modules |

---

## Phase 1: Native File I/O

The self-hosted compiler currently reads source files via `mnc_driver.c`
(C wrapper that calls `fopen`/`fread`). The compiler itself should handle
file I/O natively.

### 1.1 — Add File Read to C Runtime

Add to `mapanare_core.c`:
```c
MnString __mn_file_read(MnString path);  // read entire file to string
```

### 1.2 — Extern Declaration in main.mn

```mapanare
extern fn __mn_file_read(path: String) -> String
```

### 1.3 — CLI Argument Access

Add to C runtime:
```c
MnString __mn_argv(int64_t index);  // get command-line argument
int64_t __mn_argc();                // get argument count
```

### 1.4 — Self-Contained main.mn

Replace the `mnc_driver.c` dependency:

```mapanare
fn main() {
    if __mn_argc() < 2 {
        print("usage: mnc <file.mn>")
        return
    }
    let filename: String = __mn_argv(1)
    let source: String = __mn_file_read(filename)
    compile_and_print(source, filename)
}
```

Now the compiler is fully self-contained — no C driver needed.

---

## Phase 2: String Escapes

The self-hosted compiler currently handles raw string literals only.
Add escape sequence support:

| Escape | Character |
|--------|-----------|
| `\n` | newline (0x0A) |
| `\t` | tab (0x09) |
| `\\` | backslash |
| `\"` | double quote |
| `\0` | null byte |
| `\r` | carriage return |

### Where to Fix

1. **Self-hosted lexer** (`lexer.mn`): `scan_string` function — process
   escape sequences when scanning string literals
2. **Self-hosted emitter** (`emit_llvm.mn`): string constant emission —
   emit `\0A` for `\n`, etc. in LLVM IR string constants
3. **C runtime**: no changes needed (already handles raw bytes)

---

## Phase 3: Proper Error Handling

### 3.1 — Stderr Output

Add to C runtime:
```c
void __mn_eprint(MnString s);   // print to stderr
void __mn_eprintln(MnString s); // print to stderr + newline
```

Update the self-hosted compiler to print errors to stderr:
```mapanare
fn compile_and_print(source: String, filename: String) {
    let cr: CompileResult = compile(source, filename)
    if cr.success {
        print(cr.ir_text)
    } else {
        for i in 0..len(cr.errors) {
            eprint(format_error(cr.errors[i]))
        }
    }
}
```

### 3.2 — Exit Codes for Errors

Return non-zero exit code when compilation fails:
```mapanare
fn main() {
    ...
    let cr: CompileResult = compile(source, filename)
    if !cr.success { __mn_exit(1) }
    print(cr.ir_text)
}
```

---

## Phase 4: Expanded Test Suite

### 4.1 — New Golden Tests

Add tests for features not yet covered:

| Test | Feature |
|------|---------|
| 16_string_escape.mn | `\n`, `\t`, `\\` in strings |
| 17_option.mn | Option<T> creation, unwrap, match |
| 18_method_chain.mn | `s.to_upper().contains("X")` |
| 19_multifile.mn | Module imports |
| 20_agent_basic.mn | Agent spawn + send + sync |
| 21_signal.mn | Signal creation + update |
| 22_pipe.mn | `value \|> fn1 \|> fn2` |
| 23_error_prop.mn | `value?` error propagation |
| 24_lambda.mn | `\|x\| x * 2` closures |
| 25_map.mn | Dictionary operations |

### 4.2 — Error Tests

Tests that should produce compilation ERRORS:

| Test | Expected Error |
|------|---------------|
| err_undefined_var.mn | "Undefined variable 'x'" |
| err_type_mismatch.mn | "Type mismatch: expected Int, got String" |
| err_missing_return.mn | "Missing return value" |

### 4.3 — Runtime Test Harness Update

Update `scripts/test_runtime.sh` to handle:
- New golden tests (16-25)
- Error tests (expect non-zero exit + error message on stderr)
- Multi-line expected output

---

## Phase 5: Stdlib in .mn (may spill to v3.3.0)

Port essential stdlib modules from Python to Mapanare:

| Module | Size | Priority |
|--------|------|----------|
| `string_utils.mn` | ~100 lines | High — used by compiler |
| `math.mn` | ~50 lines | Medium |
| `io.mn` | ~80 lines | High — file read/write |
| `fmt.mn` | ~60 lines | Medium — formatted output |

These compile through stage1 and link with user programs. The stdlib
becomes native code (no Python runtime).

---

## Success Criteria

- [x] Self-hosted compiler reads files natively (mn_main in main.mn)
- [x] String escape sequences work (`\n`, `\t`, `\\`)
- [x] Errors print to stderr with non-zero exit code (mn_main + __mn_str_eprint)
- [x] 25+ golden tests pass through runtime harness (25/25)
- [ ] At least 2 stdlib modules ported to .mn
- [ ] Three-stage fixed point preserved

---

## Tools

```bash
bash scripts/build_from_seed.sh        # build from seed
bash scripts/verify_fixed_point.sh     # fixed point check
bash scripts/test_runtime.sh           # runtime correctness
python3 scripts/ir_doctor.py golden    # IR validation
```
