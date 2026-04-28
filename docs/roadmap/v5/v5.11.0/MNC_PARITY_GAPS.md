# v5.11.0 Pk.3 — `mnc` (native) vs `mapanare` (PyInstaller) parity gaps

**Status:** EVALUATE-ONLY (per v5.11.0 PLAN). The PyInstaller→native
bundle swap is **deferred**. This document captures the surface-area
delta between the two CLIs so future-you can plan the swap when the
gap closes (or accept the gap and ship a hybrid bundle).

**Decision:** **Defer.** Native `mnc` is missing 18 of `mapanare`'s
25 subcommands. Shipping a native-only Windows ZIP today would be a
visible regression on developer experience (no `lsp`, no `fmt`, no
`init`, no transpile/lint/doc surface).

**Re-evaluate at:** v5.12.x or later, once the high-priority gaps
below are closed in `mapanare/self/main.mn`'s dispatcher.

---

## Methodology

Compared `python -m mapanare --help` (PyInstaller bundle's underlying
CLI) against `./mapanare/self/mnc-stage1 --help` at v5.10.0 HEAD on
2026-04-28. Probed each missing subcommand with a no-arg invocation
to confirm it is genuinely absent vs hidden.

---

## What `mnc` already supports

| Subcommand | Notes |
|---|---|
| `mnc <file.mn>` (default = run) | v5.9.1 DX.5 |
| `mnc emit-llvm <file>` | v5.9.1 DX.5 carved this out as the IR path |
| `mnc run <file>` | Explicit form of the default |
| `mnc build <file\|dir>` | Native binary build |
| `mnc compile <file>` | Transpile + build (.py/.php/.ts/.go). Wider scope than `mapanare transpile`, which only transpiles. |
| `mnc test <file>` | Run `@test` functions |
| `mnc cache <stats\|clean>` | v5.9.0 DX.4 |
| `mnc version` / `mnc --version` | v5.9.0 DX.2 |
| `mnc --help` | v5.9.0 DX.1 |

7 visible commands, 1 default-dispatch path.

---

## What `mapanare` supports that `mnc` does not

### High priority (developer-facing, high traffic)

| `mapanare` subcommand | What it does | Why it matters |
|---|---|---|
| `lsp` | LSP server over stdio | Editor/IDE integration. Removing this breaks every Mapanare editor extension. |
| `fmt` | Format `.mn` source | Daily-driver tool; users running `mnc-only` expect `mnc fmt` to work |
| `init` | Initialize new project (mapanare.toml + main.mn scaffold) | Getting-started flow on every onboarding walks the user through `mnc init myproject` per install.ps1's tail. |
| `check` | Type-check without compiling | Faster iteration than `run`/`build`; CI gating |
| `lint` | Code-quality lints | Same as `check` for usage cadence |

### Medium priority (cross-language emit + ecosystem)

| `mapanare` subcommand | What it does |
|---|---|
| `emit-c` | C source emission (v3.0.0 fallback path) |
| `emit-mir` | MIR dump for compiler debugging |
| `emit-wasm` | WebAssembly (WAT/WASM) emission. The WASM CI lane uses this. |
| `targets` | List supported compilation targets |
| `build-multi` | Multi-file linked LLVM IR build |
| `transpile` | Transpile-only (.py/.php → .mn). Subset of `mnc compile`. |
| `bind` | FFI binding generation (Python/TypeScript/Go) |
| `doc` | HTML doc generation |
| `migrate` | v2→v3 syntax migration. Rarely used today; could be deprecated. |

### Lower priority (registry + deployment — could be Python-shelled)

| `mapanare` subcommand | What it does |
|---|---|
| `install` | Install packages from registry / `mapanare.toml` |
| `publish` | Publish package to registry |
| `search` | Search registry |
| `login` | Authenticate with registry |
| `deploy` | Generate Dockerfile + docker-compose.yml |

---

## Decision

**Defer the PyInstaller→native swap.** The bundled Windows ZIP stays
on the PyInstaller bundle for v5.12.x. Reasons:

1. **`lsp` alone is a hard blocker.** Native `mnc` has no LSP server.
   Switching the bundle would silently break VS Code / JetBrains
   plugins, with no in-bundle fallback.
2. **`init` is in the post-install instructions.** install.ps1's
   verify step prints "Get started: mnc init myproject". A native-
   only bundle would break the very first command in the
   getting-started flow.
3. **`fmt` is a daily tool.** Removing it from the default install
   creates a "where did `mapanare fmt` go?" support load.
4. **`emit-wasm` is exercised by CI.** The WASM lane uses
   `python -m mapanare emit-wasm`. Swapping to a native-only bundle
   would force the CI lane to keep an explicit Python install,
   defeating the bundle's own purpose for that workflow.

The swap also has **no urgency**:

- The 95 MB v5.10.0 bundled-LLVM ZIP is dominated by `clang.exe` +
  `LLVM-C.dll` (~85 MB), not by the PyInstaller bundle (~10 MB).
  Swapping the PyInstaller layer for native `mnc` saves at most
  ~7 MB. Not worth the surface-area regression.
- Users who want a small footprint already have
  `MAPANARE_NO_BUNDLED_LLVM=1` → `mapanare-${V}-win-x64-minimal.zip`
  at ~10 MB.

---

## What would unblock the swap

Track these in v5.12.x roadmap as **Mc.* (mnc parity)**:

- **Mc.1** — `mnc lsp` (port `mapanare/lsp/` to native or shell to a
  bundled Python sidecar)
- **Mc.2** — `mnc fmt` (port the formatter; pure-Mapanare, no LLVM dep)
- **Mc.3** — `mnc init` (template scaffold; trivial)
- **Mc.4** — `mnc check` (type-check-only path is already inside the
  emitter pipeline; just needs CLI surface)
- **Mc.5** — `mnc emit-wasm` (port WASM backend to native — significant)

After Mc.1–Mc.5 close, re-evaluate the swap. Mc.6+ (registry
commands, deploy, bind) are lower priority — those can stay in a
Python sidecar without harming the swap decision.

---

## Cross-references

- v5.11.0 PLAN — `docs/roadmap/v5/v5.11.0/PLAN.md` Phase 3
- v5.10.0 SESSION — `docs/roadmap/v5/v5.10.0/SESSION_REPORT.md` —
  context on bundle layout and 95 MB cost breakdown
- v5.9.0 SESSION — DX.* docket that closed `mnc --help`, `mnc
  version`, `mnc cache`. Mc.* is the next docket along this axis.
