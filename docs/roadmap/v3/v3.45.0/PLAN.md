# Mapanare v3.45.0 — "Turpial" (Package Manager + Polish)

> `mapanare install` works. Error messages are helpful.
> Documentation matches reality. Ready for v4.0.0.

**Status:** DONE
**Breaking:** No
**Prerequisite:** v3.44.0 (real examples)

---

## The Problem

The package manager parses `mapanare.toml` manifests but `install` is a
no-op. Error messages are good for some cases but the compiler crashes on
others. The README and website claim features that don't work natively.

---

## Checklist

### 1. Package Manager — Basics

- [ ] `mapanare install <local-path>` — copy package to `.mapanare/packages/`
  - Read `mapanare.toml` from the package directory
  - Copy source files preserving directory structure
  - Register package name + version in `.mapanare/packages/registry.json`
- [ ] `mapanare install <git-url>` — clone repo, then install as local
- [ ] `import pkg_name` resolution in compiler:
  - Check `.mapanare/packages/{pkg_name}/` for source files
  - Fall back to `stdlib/{pkg_name}/`
- [ ] `mapanare.toml` [dependencies] section:
  ```toml
  [dependencies]
  mn_json = { path = "../mn_json" }
  mn_collections = { git = "https://github.com/Mapanare-Research/mn_collections" }
  ```
- [ ] `mapanare install` (no args) — install all dependencies from `mapanare.toml`

### 2. Example Packages

Create and test 3 packages:

- [ ] `packages/mn_collections/` — stack, queue, deque (pure Mapanare)
  - `mapanare.toml` with name, version, description
  - `src/lib.mn` with public functions
  - `tests/test_collections.mn` with @test functions
- [ ] `packages/mn_json/` — JSON parser (pure Mapanare)
  - Parse JSON strings into Mapanare structs/maps
  - `json_parse(input: String) -> Result<JsonValue, String>`
  - `json_stringify(value: JsonValue) -> String`
- [ ] `packages/mn_text/` — text processing utilities
  - `pad_left`, `pad_right`, `center`, `wrap`, `truncate`
  - `slug(input: String) -> String`

**Verify:**
```bash
cd my_project/
mapanare install ../packages/mn_json
# then in main.mn:
# import mn_json
# let data = mn_json::parse('{"name": "test"}')
mnc run main.mn
```

### 3. Error Recovery

- [ ] Compiler reports up to 10 errors before stopping (not crash on first)
- [ ] Missing import: "module 'xyz' not found. Did you mean 'xyz2'?" with Levenshtein
- [ ] Type mismatch: "expected Int, got String at line 15, column 8"
- [ ] Undefined variable: "variable 'x' not defined. Did you mean 'y'?"
- [ ] Audit `mapanare/self/main.mn` — replace `panic()` with diagnostic error + continue
- [ ] Audit `mapanare/self/parser.mn` — synchronize on statement boundaries after error

### 4. Documentation — Match Reality

- [ ] `README.md`:
  - Version badge: 3.45.0
  - Self-hosted compiler stats: 15,500+ lines, 11 modules
  - Feature status table: mark what ACTUALLY works natively
  - Test count: current number
  - Examples section: point to working examples
- [ ] `docs/getting-started.md` — rewrite to work end-to-end:
  1. Install Mapanare
  2. Write hello.mn
  3. `mnc run hello.mn` → "Hello, World!"
  4. Write a file processor
  5. Transpile a Python file
  6. Install a package
- [ ] Website: update version, self-hosted stats, feature claims
- [ ] SPEC: verify all disclaimers current (tensor §3.10, batch §10.5, GPU §23)

### 5. Culebra Full Audit

- [ ] `culebra scan` on ALL golden tests — zero critical
- [ ] `culebra scan` on ALL example IR — zero critical
- [ ] `culebra triage --brief` — clean report
- [ ] `culebra summary main.ll` — healthy
- [ ] `culebra abi main.ll --header runtime/native/mapanare_core.h` — all signatures match

### 6. Final Code Review

- [ ] Run `/code-review` — target 9.5+/10
- [ ] Address all CRITICAL and HIGH findings
- [ ] Document all MEDIUM findings with timeline

---

## Exit Criteria

```bash
# New user experience:
curl -fsSL https://mapanare.dev/install | bash
mapanare init my_project
cd my_project
cat > main.mn << 'EOF'
fn main() {
    print("What's your name?")
    let name = read_line()
    print("Hello, " + name + "!")

    write_file("greeting.txt", "Hello, " + name)
    print("Saved to greeting.txt")
}
EOF
mnc run main.mn
# What's your name?
# > Juan
# Hello, Juan!
# Saved to greeting.txt
```

If this works, ship v4.0.0.
