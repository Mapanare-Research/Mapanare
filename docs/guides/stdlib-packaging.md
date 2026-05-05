# Stdlib Packaging Policy

**Status:** v5.44.0 Ps.7. Defines the classification used to decide
which stdlib modules can move to external packages and which must
stay bundled with the compiler.

---

## TL;DR

Mapanare's stdlib has four classes of module. The class determines
whether it can ship as a `[dependencies]` entry or must stay in the
compiler repo:

| Class | Where | Why | Examples |
|---|---|---|---|
| **Bundled-core** | repo `stdlib/` | Always available; fundamental types and language primitives. Cannot be removed without breaking the language. | `option.mn`, `result.mn`, `list.mn`, `string.mn`, `map.mn`, `iter.mn` |
| **Pure-package candidate** | external repo possible | No `extern "C"`, no `extern "Python"`, no native runtime ABI dependency. Pure `.mn` data structures and algorithms. | `text/string-utils`, `encoding/csv`, collection helpers, `mn_collections` exemplar |
| **Runtime-bound (must stay bundled)** | repo `stdlib/` | Calls `extern "C"` against native runtime symbols (`__mn_*`) whose declarations must be available at link time. Cannot move out until packages can declare native-ABI deps in `mapanare.toml`. | `net/http.mn`, `time.mn`, `sql/sqlite.mn`, `crypto.mn`, `agent/node.mn`, `agent/remote.mn` |
| **Downstream-only** | never in main repo | Domain-specific; doesn't belong in a general-purpose stdlib. | Calendars beyond Gregorian, exotic ML kernels, vendor-specific cloud SDKs |

The load-bearing distinction is **runtime-bound vs pure**. The `extern
"C"` declarations in runtime-bound modules reference `__mn_*` symbols
exported by the C runtime. A consumer that imports such a module must
link against `libmapanare_rt.a`. Today there is no way for a package's
`mapanare.toml` to declare that requirement; without it, externalizing
runtime-bound modules would ship broken packages that link-fail in
unrelated codebases.

---

## Class definitions

### Bundled-core

Always present. Removing or renaming any symbol breaks every Mapanare
program. These are not stdlib in the "library you import" sense —
they're language primitives:

- `option.mn`, `result.mn` — `Option`, `Result`, `Some`, `None`, `Ok`,
  `Err`. Used by every error path and every nullable value.
- `list.mn` — `List<T>` operations beyond what the grammar provides.
- `string.mn` — string-method dispatch surface.
- `map.mn` — `Map<K, V>` operations.
- `iter.mn` — iterator protocol.

**Rule:** never propose moving these. If a future release wants to
rename one, it's a major-version surface change, not a packaging
decision.

### Pure-package candidate

Compiles cleanly through the regular pipeline (parse → MIR → LLVM IR →
clang → link), without a single `extern "C"` or `extern "Python"`
block. All work happens in `.mn` source against bundled-core types.

**Test for purity:**

```bash
grep -rln 'extern "C"\|extern "Python"' stdlib/<module>/
```

If the grep returns nothing, the module is pure-package-eligible.

Initial inventory (v5.44.0 audit):

- `text/string-utils` (if added)
- `encoding/csv` (if added)
- `mn_collections` (already shipped as `examples/packages/mn_collections/`)
- Algorithm helpers (sorting, searching, hashing-without-OpenSSL)

These are candidates today. Whether they actually move out of the main
repo depends on demand, not on technical feasibility. v5.44.0 ships the
runway; deciding which packages migrate first is v6.0+ work.

### Runtime-bound (must stay bundled)

Has at least one `extern "C"` block referencing `__mn_*` runtime
symbols. The C runtime in `runtime/native/` exports these; the
package's `.mn` source declares them as externals.

**Inventory at v5.44.0 HEAD** (as of this writing — re-audit when
runtime exports change):

| Module | Runtime exports it depends on |
|---|---|
| `stdlib/net/http.mn`, `stdlib/net/http/server.mn`, `stdlib/net/websocket.mn` | `__mn_tcp_listen`, `__mn_tcp_accept`, `__mn_tcp_send`, `__mn_tcp_recv`, TLS variants |
| `stdlib/time.mn` | `__mn_now_realtime_ns`, `__mn_utc_pack`, `__mn_local_pack`, `__mn_local_offset_minutes`, `__mn_timegm`, `__mn_normalize_pack` |
| `stdlib/sql/sqlite.mn`, `stdlib/db/sqlite.mn` | sqlite3 dlopen plumbing in `mapanare_db.c` |
| `stdlib/crypto.mn` | OpenSSL dlopen plumbing in `mapanare_io.c` (SHA, HMAC, AES, EVP) |
| `stdlib/agent/node.mn`, `stdlib/agent/remote.mn` | `__mn_node_listen_str`, `__mn_node_accept`, `__mn_node_connect_str`, `__mn_node_write_str`, `__mn_node_read_frame_str`, `__mn_node_close`, TLS server variants |
| `stdlib/fs.mn` | `__mn_file_read`, `__mn_file_write`, `__mn_file_exists`, dir ops |
| `stdlib/ai/llm.mn`, `stdlib/ai/ask.mn` | indirectly — depends on `net/http` for transport |

**Rule:** these stay in `stdlib/`. They are not candidates for external
packages until the migration prerequisite below is in place.

### Downstream-only

Belongs in user / vendor / industry-specific repos, never in the
general-purpose stdlib regardless of purity.

Examples:

- Non-Gregorian calendar systems
- Cloud-vendor SDKs (AWS, GCP, Azure)
- ML model loaders for specific architectures
- Industry-specific protocols (FIX, HL7, DICOM)

These are mentioned for completeness — they're already not in
`stdlib/` and don't need a packaging policy. The class exists so
"why isn't X in stdlib?" has a documented answer.

---

## Migration path for runtime-bound modules

For a runtime-bound module to move to an external package, two
prerequisites must ship:

1. **Native-ABI dependency declaration in `mapanare.toml`.** A
   schema like:

   ```toml
   [runtime-deps]
   __mn_tcp_listen = "1.0"
   __mn_tcp_send = "1.0"
   ```

   where the version is the ABI version of the C export (separate
   from the package's own semver). The compiler must validate at
   build time that all declared `__mn_*` symbols exist in the
   linked runtime, and that their declared ABI version matches.

2. **Runtime-export ABI versioning.** `runtime/native/` exports must
   carry a stable ABI declaration the compiler can read. v5.44.0 has
   the export inventory but no ABI version per export.

Both are deliberately deferred from v5.44.0. The PROMPT scoped this
release as "wire installed packages into the resolver"; designing a
runtime-ABI declaration schema is a separate (larger) release.

---

## What v5.44.0 Ps.\* actually delivered

- The compiler can resolve imports through `mn_modules/` (Ps.1).
- Lockfile-authoritative discovery; no silent version fallback (Ps.1).
- CLI parity: `mnc run`, `mnc build`, `mnc emit-llvm`, `mnc emit-mir`,
  `mnc emit-c`, `mnc emit-wasm`, `mnc build-multi`, `mnc test`,
  `mnc check` all use the same package-aware resolver (Ps.3).
- `--verbose` and `--diag-json` surfaces for resolved packages (Ps.4).
- `mn_collections` confirmed pure; `consumer_collections` exemplar
  added (Ps.5).
- `mn_http` and `mn_json` marked legacy (Ps.6).

What it did **not** deliver:

- Native-ABI declarations (deferred — see migration path above).
- Moving any stdlib module out of the main repo (deferred — Ps.\* is
  the runway, not the migration).
- Global package cache (deferred to v6.0+; the `PackageRoot` /
  `discover_package_roots` boundary leaves room for it).

See `docs/roadmap/v5/v5.44.0/{PLAN.md, PROMPT.md, PRE_PHASE_AUDIT.md,
SESSION_REPORT.md}` for the full release record.
