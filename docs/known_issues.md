# Known Issues — User-Facing

Last updated: v4.143.0.

## Self-hosted compiler feature gaps

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Sh.4 | async code compiles through Python bootstrap only | use Python bootstrap for async programs | v5.x |
| Sh.5 | `const` in function bodies partially supported in self-hosted | use `let` in fn bodies; `const` works at module level | v5.x |
| Sh.6 | tensor literals not yet in self-hosted emitter | Python bootstrap works; self-hosted emits through boxed path | v5.x |
| Sh.7 | closure-typed function parameters: self-hosted declines | use concrete fn types | v5.x |
| Sh.9a | async emitter bug: see `docs/guides/async.md` for workaround | documented workaround in async guide | v5.x |
| Sh.9b | async emitter bug #2: see `docs/guides/async.md` | documented workaround in async guide | v5.x |

## Grammar / language

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Gr.1 | multi-line list/tensor literals parse-error | put literal on one line; wrap in parens on next | v5.x |

## Runtime

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| Rt.2 | `dir_create(recursive=true)` ignores the flag | call `dir_create` per path level | v5.x |
| Rt.3 | `tmpfile_path` returns literal `/tmp/mn_tmp_XXXXXX` without calling `mkstemp` | use `io_tmpfile()` which returns a real handle | v5.x |

## Ecosystem

| Docket | Symptom | Workaround | Track |
|---|---|---|---|
| — | No package manager yet | pin `mapanare.toml` deps by git SHA | v5.x ecosystem |

Last verified: v4.143.0 (2026-04-18).
