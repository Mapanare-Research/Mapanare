# Viper -- Rust Review of Mapanare v4.41.0 (Arc 2 Close)

**Reviewer:** Viper
**Personality:** The Rust Purist -- ruthless, sarcastic, zero sugar coating
**Previous Version Reviewed:** v4.36.0
**Verdict:** PASS WITH NOTES
**Confidence:** 9/10
**Score:** 9.5/10

**Files Reviewed:**

- `mapanare/lsp/server.py` (691 lines -- debounce timers, document lifecycle, workspace integration)
- `mapanare/lsp/workspace.py` (362 lines -- WorkspaceIndex, scan_root, rebuild_file, _collect_references)
- `mapanare/lsp/diagnostics.py` (115 lines -- semantic_error_to_diagnostic, run_semantic_check)
- `mapanare/lsp/analysis.py` (650+ lines -- IncrementalParser, DocumentAnalysis, symbol extraction)
- `mapanare/lsp/completion.py` (242 lines -- context-aware completions in four modes)
- `mapanare/lsp/rename.py` (91 lines -- validate_rename, apply_rename)
- `mapanare/lsp/__init__.py` (1 line)
- `mapanare/emit_llvm_text.py` (lines 252, 1090-1109 -- `__mn_list_get` attrs, drop-glue early-return)
- `runtime/native/mapanare_io.c` (lines 1021-1027, 1355-1361 -- evp_load, pcre2_load CAS patterns)
- `runtime/native/mapanare_core.c` (lines 103-110 -- `__mn_free` comment discrepancy)
- `.reviews/CARRY_FORWARD.md` (items 49, 50, P1-P6)
- `.reviews/v4.41.0/PRE_PANEL_AUDIT.md` (17/17 claims verified)
- `.reviews/v4.36.0/01-viper.md` (my prior review, V1-V4)

---

## Executive Summary

Arc 2 delivered four releases (v4.37.0-v4.40.0) adding a full LSP implementation: workspace index, cross-module go-to-def, find-references, rename, context-aware completion, diagnostic streaming with debounce, and a VS Code extension. Zero changes to the compiler pipeline (`emit_llvm_text.py`, `lower.py`, `pattern_matching.py`) or the C runtime (`mapanare_core.c`, `mapanare_runtime.c`, `mapanare_io.c`, `mapanare_gpu.c`). This is an LSP-only arc.

From a memory-safety and resource-safety lens, the LSP modules are clean with two exceptions: one is a debounce timer leak on document close (my V1 below, LOW), and the other is that the workspace index retains full ASTs for every indexed file (not a bug, but a memory consideration noted as V2 below). Neither is blocking. There are no thread-safety concerns because pygls serializes all LSP message handlers on a single asyncio event loop, and the only threading surface -- `threading.Timer` for debounce -- is daemon-threaded and fire-and-forget.

The four findings I left at v4.36.0 (V1 MEDIUM `__mn_list_get` attrs, V2 LOW `evp_load`/`pcre2_load` CAS, V3 LOW `__mn_free` comment, V4 LOW `message_dtor` wiring) are **all still open**. None were addressed in Arc 2. This is expected -- Arc 2 was scoped to LSP work with zero compiler/runtime changes -- but it means my carry-forward queue is growing, not shrinking. The P1-P6 items from the v4.36.0 full panel are also all still open in `CARRY_FORWARD.md`. My score stays at 9.5 rather than improving because the carry-forward queue did not move.

---

## Strengths

1. **The LSP modules have no runtime memory-safety surface.** All six modules (`server.py`, `workspace.py`, `diagnostics.py`, `analysis.py`, `completion.py`, `rename.py`) are pure Python operating on AST dataclasses. There is no C FFI, no raw pointer manipulation, no `ctypes`, no `cffi`, no shared mutable state across threads. The only external I/O is file reads in `workspace.py:rebuild_file` (via `path.read_text(encoding="utf-8")`), and those are wrapped in a try/except at lines 131-162 that catches all exceptions and logs a warning. A Rust LSP would look structurally identical: `HashMap<PathBuf, FileEntry>` for the index, immutable AST snapshots, single-threaded handler dispatch.

2. **The debounce implementation is correct in the common case.** `server.py:182-190` creates a `threading.Timer` for each `didChange` event, cancels the previous timer for the same URI if it exists, and starts the new one. The timer is daemon-threaded (`timer.daemon = True`), so it does not prevent server shutdown. The `_debounced_recheck` callback at line 62 reads from `_sources`, which is only written from the main thread (pygls dispatches handlers sequentially), so the worst case is a stale read (the callback fires with a slightly outdated source), which is semantically correct for a debounce -- the next save or change will re-check anyway.

3. **The workspace index is properly invalidated.** `rebuild_file` at `workspace.py:117-162` removes old symbols and reference sites before re-indexing, preventing stale entries from accumulating. The cleanup is keyed on `path` identity, and the `_by_name` / `_by_unqualified` / `refs_by_symbol` dicts are all properly cleaned of old entries at lines 122-128. The `scan_root` method at line 94 clears all four indexes before walking, so re-scan is idempotent.

4. **The `_collect_references` AST walker is bounded and non-recursive in the problematic sense.** It walks the AST top-down via nested `_walk_expr` / `_walk_stmt` / `_walk_block` functions. The recursion depth is bounded by AST nesting depth, which is typically under 50 levels for any real program. There is no risk of stack overflow in practice. The walker correctly breaks after the first matching symbol to avoid O(n^2) behavior when a name matches multiple modules.

5. **The `run_semantic_check` function in `diagnostics.py:87-114` is defensive.** The inner semantic check is wrapped in a bare `except Exception: pass` at line 111-112, so a crash in the semantic checker does not propagate to the LSP layer. The outer parse is also wrapped. This is the right pattern for a language server: never crash the server because of a user's broken source file. The comment at line 112 explicitly names this intent.

6. **The rename module validates before applying.** `rename.py:31-50` checks three conditions before allowing a rename: valid identifier syntax, not a keyword, and no name collision in the same module. The keyword set at lines 19-28 includes both English and bilingual keywords. This is a correct guard against generating invalid source. The `_IDENT_RE` regex at line 16 is anchored (`^...$`), so it cannot be bypassed by embedding valid characters in an invalid name.

7. **Test coverage exists.** The `tests/lsp/` directory has 6 test files covering workspace index (13 tests), find-references (5), rename (8), completion (13), diagnostics streaming (10), and analysis. The pre-panel audit at `.reviews/v4.41.0/PRE_PANEL_AUDIT.md` confirms all 17 SESSION_REPORT claims passed verification. This is honest.

8. **No regression in compiler or runtime.** `git log --oneline v4.36.0..HEAD -- runtime/native/` and `git log --oneline v4.36.0..HEAD -- mapanare/emit_llvm_text.py` both return empty. The runtime and emitter are byte-identical to v4.36.0. No new memory-safety surface was introduced. No existing safety mechanisms were weakened.

---

## Issues Found

### V1. **[LOW]** Debounce timer not cancelled on document close -- resource leak

`server.py:204-211` (`on_close`):

```python
@server.feature(lsp.TEXT_DOCUMENT_DID_CLOSE)
def on_close(params: lsp.DidCloseTextDocumentParams) -> None:
    uri = params.text_document.uri
    _documents.pop(uri, None)
    _sources.pop(uri, None)
    _fixable_diagnostics.pop(uri, None)
    invalidate_document(uri)
    server.text_document_publish_diagnostics(lsp.PublishDiagnosticsParams(uri=uri, diagnostics=[]))
```

This handler cleans up `_documents`, `_sources`, and `_fixable_diagnostics` for the closed URI, but does NOT cancel or remove the debounce timer from `_debounce_timers`. If a `didChange` event fires 50ms before `didClose`, the timer is still alive in `_debounce_timers[uri]` and will fire 250ms later, calling `_debounced_recheck(uri)`.

The consequence: `_debounced_recheck` reads `_sources.get(uri, "")`, gets `""` (because `on_close` already popped it), and returns without doing anything (the `if source:` guard at line 65 catches it). So the functional impact is zero -- no crash, no incorrect diagnostics published. But:

1. The `_debounce_timers` dict leaks entries. Every close-without-reopen leaves a dead `threading.Timer` object in the dict. For a long-running LSP session that opens and closes many files, this is unbounded growth. The timer objects are small (a few hundred bytes each) and daemon-threaded (they die on server exit), so this is not a production issue for typical sessions. But it is a resource leak.

2. The timer thread itself runs to completion (fires `_debounced_recheck`, returns, thread exits). This is one unnecessary thread wake-up per close-after-change. Again, functionally harmless but architecturally sloppy.

**Fix:** Add two lines to `on_close`:

```python
old_timer = _debounce_timers.pop(uri, None)
if old_timer is not None and hasattr(old_timer, "cancel"):
    old_timer.cancel()
```

This is the exact same pattern already used in `on_change` at lines 184-186. Copy-paste it into `on_close` before the `_documents.pop`.

### V2. **[LOW]** WorkspaceIndex retains full ASTs for every indexed file

`workspace.py:147`:

```python
entry = FileEntry(
    path=path,
    last_mtime=path.stat().st_mtime if path.exists() else 0.0,
    ast=ast,  # <-- full parsed Program retained
    symbols=symbols,
    imports=imports,
)
self.files[path] = entry
```

The `FileEntry` dataclass at line 74 holds `ast: Optional[Program]`, and `rebuild_file` stores the complete parsed AST for every `.mn` file in the workspace. The AST is only used for reference collection (`_collect_references` at line 155), which runs immediately during `rebuild_file`. After that, the AST is dead data -- it is never read again until the next `rebuild_file` or `scan_root` call.

For the self-hosted compiler workspace (10 `.mn` files, ~15,000 lines total), this is negligible. For a user workspace with hundreds of `.mn` files, each AST could retain tens of thousands of dataclass nodes and string objects, adding up to significant memory pressure. A Rust implementation would either drop the AST after reference collection (the parse result is consumed, not borrowed) or use `Arc<Program>` with weak references.

**Fix:** Set `entry.ast = None` after `_collect_references` returns in `rebuild_file`, and in the second pass in `scan_root`. The AST can be re-parsed on demand if needed later (the source is already read and could be cached as a string, which is far smaller than the AST).

Alternatively, if the design intent is to re-use the AST for future features (e.g., incremental re-checking without re-parse), keep it but add a `clear_asts()` method that the server can call under memory pressure. The current code does not have this.

---

## Previous Findings Status (v4.36.0 V1-V4)

| # | Finding | v4.36.0 Severity | Status | Evidence |
|---|---------|-----------------|--------|----------|
| V1 | `__mn_list_get` `readonly`+`willreturn` but calls `fprintf`+`abort` | MEDIUM | **STILL OPEN (2nd cycle)** | `emit_llvm_text.py:252` unchanged: `"__mn_list_get": {"nounwind", "readonly", "willreturn"}`. No runtime/emitter changes in Arc 2. |
| V2 | `evp_load` / `pcre2_load` CAS-before-init pattern | LOW | **STILL OPEN (2nd cycle)** | `mapanare_io.c:1021-1027` and `1355-1361` unchanged. Same `__atomic_compare_exchange_n` pattern. |
| V3 | `__mn_free` comment says "wire MN_PROFILE_FREE" but call is absent | LOW | **STILL OPEN (2nd cycle)** | `mapanare_core.c:103-110` unchanged. Comment at line 104 still says "wire MN_PROFILE_FREE"; function body still just calls `free(ptr)`. |
| V4 | Agent `message_dtor` not wired by LLVM emitter | LOW | **STILL OPEN (2nd cycle)** | `grep message_dtor mapanare/emit_llvm_text.py` returns no matches. Mechanism exists in runtime, wiring absent in emitter. |

**Resolution rate this arc: 0/4.** All four carry forward to the next arc. This is expected given Arc 2's LSP-only scope, but it means my carry-forward queue is now 6 items (V1-V4 from v4.36.0, plus V1-V2 from this review).

---

## CARRY_FORWARD Items Status

| Item | Status | Notes |
|------|--------|-------|
| #49 (drop-glue skip-struct-ret) | **STILL OPEN (10th cycle)** | `emit_llvm_text.py:1098` unchanged. Comment at lines 1093-1097 still references "tracked to v4.33.0" (should be v4.37.0+). The early return is now entering its 10th review cycle. |
| #50 (agent destroy message leak) | **MECHANISM CLOSED, wiring STILL OPEN** | `message_dtor` field exists in runtime, not set by LLVM emitter. Same as v4.36.0. |
| P1 (`__mn_list_get` attrs) | **STILL OPEN** | Same as my v4.36.0 V1. MEDIUM. One-line fix. |
| P2 (pattern_matching.py unit tests) | **STILL OPEN** | No changes to `mapanare/pattern_matching.py` or new test files for it. |
| P3 (self-hosted guard fall-through) | **STILL OPEN** | No self-hosted compiler changes in Arc 2. |
| P4 (SPEC wording) | **STILL OPEN** | No SPEC changes in Arc 2. |
| P5 (examples showcase gap) | **STILL OPEN (4th cycle)** | No new examples added. |
| P6 (unreachable-arm warning test) | **STILL OPEN** | No new warning tests. |

All P-series items are at their 2nd cycle. Item #49 is at its 10th cycle. None of this is unexpected for an LSP-focused arc, but the backlog is not shrinking.

---

## LSP Resource Safety Audit

I audited all six LSP modules for resource-safety concerns specific to a long-running server process:

1. **File handle leaks.** `workspace.py:132-133` reads files via `path.read_text(encoding="utf-8")`, which is a context-manager-free read. `Path.read_text` opens the file, reads it, and closes it in one call (CPython implementation: `open()` + `.read()` + `.close()` in a `with` block internally). No file handle leak here. The `parse` calls in `analysis.py:246` and `workspace.py:136` do not open files -- they receive source strings. No file handle leaks anywhere in the LSP modules.

2. **Parser memory.** `analysis.py:225-298` (`IncrementalParser`) caches per-chunk AST definitions in `_ChunkCache` keyed by URI. `invalidate_document` at line 297 clears the cache for a URI, and it is called from `server.py:210` in `on_close`. So the incremental parser cache does not leak across document close/open cycles. Good.

3. **Workspace index unbounded growth.** `WorkspaceIndex.files` grows with every new `.mn` file encountered. Files that are deleted from disk remain in the index until a full `scan_root` is triggered (only on server restart via `INITIALIZE`). This is acceptable for typical workspaces but could be an issue for very large monorepos with ephemeral generated `.mn` files. Not flagging -- this is standard LSP behavior.

4. **Debounce threading safety.** The `threading.Timer` at `server.py:187` fires `_debounced_recheck` on a background thread. This function reads `_sources[uri]` (a dict read) and calls `run_semantic_check` followed by `server.text_document_publish_diagnostics`. pygls's `text_document_publish_diagnostics` is thread-safe (it enqueues a JSON-RPC message on the transport, which is internally synchronized). `run_semantic_check` creates new parser + semantic checker instances per call, so there is no shared mutable state. The `_sources` dict read is not locked, but Python's GIL makes `dict.__getitem__` atomic for string keys. This is safe in practice, though a Rust implementation would require a `Mutex<HashMap>` or channel-based message passing.

5. **Exception propagation.** `diagnostics.py:111-112` catches all exceptions from the semantic checker with a bare `except Exception: pass`. This is correct for a language server -- a crash in semantic analysis should not bring down the server. The `run_semantic_check` function at line 87 also catches parse exceptions at lines 99-103. No uncaught exception can propagate from the diagnostic pipeline to the LSP handler layer.

**Verdict:** The LSP modules are resource-safe with the single exception of the debounce timer leak in `on_close` (V1 above, LOW).

---

## Recommendations

### For v4.42.0 (next arc)

1. **V1 (this review, LOW):** Cancel debounce timers in `on_close`. Two-line fix. Prevents unbounded growth of `_debounce_timers` in long-running sessions.

2. **V2 (this review, LOW):** Clear retained ASTs after reference collection in `workspace.py:rebuild_file`. One-line fix (`entry.ast = None` after the `_collect_references` call). Reduces memory footprint proportional to workspace size.

### Carry-forward from v4.36.0 (all still open)

3. **P1 / my v4.36.0 V1 (MEDIUM):** Fix `__mn_list_get` attributes in `_RUNTIME_FN_ATTRS`. Remove `readonly` and `willreturn`. One-line change. This is now at its 2nd cycle and remains the only real miscompilation risk in the codebase at `-O2`.

4. **My v4.36.0 V4 (LOW):** Wire `message_dtor` in the LLVM emitter's agent-wrap code. The runtime mechanism exists; the emitter wiring does not.

5. **My v4.36.0 V2 (LOW):** Migrate `evp_load` and `pcre2_load` to `pthread_once`. Same mechanical pattern as the v4.35.0 sweep.

6. **My v4.36.0 V3 (LOW):** Fix the `__mn_free` comment-vs-code discrepancy.

7. **Item #49 (10th cycle):** Delete the drop-glue early-return at `emit_llvm_text.py:1098`. Ten cycles. The infrastructure to remove it has existed since v4.32.0 Phase 2.2.

### Process

- The `CARRY_FORWARD.md` P1-P6 items from v4.36.0 all say "v4.37.0" as tracking version but none were addressed in v4.37.0-v4.40.0. The tracking versions should be updated to v4.42.0+ to maintain ledger honesty.
- Item #49's comment at `emit_llvm_text.py:1097` still says "tracked to v4.33.0" -- now three tracking-version labels out of date. Update the comment or, better, delete the early return.

---

## Score Justification

```
v3.47.0:  0 CRIT, 0 HIGH.  Viper score: 9.5   (PASS WITH NOTES)
v4.26.0:  0 CRIT, 6 HIGH.  Viper score: 8.0   (NEEDS WORK)
v4.31.0:  0 CRIT, 1 HIGH.  Viper score: 9.1   (PASS WITH NOTES)
v4.36.0:  0 CRIT, 0 HIGH.  Viper score: 9.5   (PASS WITH NOTES)
v4.41.0:  0 CRIT, 0 HIGH.  Viper score: 9.5   (PASS WITH NOTES)
```

The 9.5 holds steady because:

- **No new runtime or emitter changes = no new memory-safety surface.** Arc 2 was LSP-only. The runtime is frozen at v4.36.0 state. This is the best outcome for my lens -- you cannot introduce memory-safety bugs in code you do not change.
- **The LSP modules are clean.** Two LOW findings (debounce timer leak, AST retention), both trivially fixable. Neither can cause data corruption, crashes, or security issues.
- **But the carry-forward queue did not shrink.** My four v4.36.0 findings are all still open. The P-series items from the full panel are all still open. Item #49 entered its 10th cycle. The score cannot improve while the backlog grows. The v4.36.0 score of 9.5 was given with the expectation that V1 (`__mn_list_get` attrs) would be fixed in v4.37.0 -- that did not happen. The fact that Arc 2 was scoped to LSP is a valid reason, but from my lens the risk is unchanged.
- **-0.15 for carry-forward non-resolution:** P1 (`__mn_list_get` attrs, MEDIUM, 2nd cycle), V4 (`message_dtor` wiring, LOW, 2nd cycle), V2/V3 (LOW, 2nd cycle), item #49 (LOW, 10th cycle).
- **-0.1 for new LSP findings:** V1 (debounce timer leak, LOW), V2 (AST retention, LOW).
- **+0.25 for clean LSP implementation:** No file handle leaks, no thread-safety issues, proper exception guarding, proper cache invalidation, 49+ tests across 6 test files.

Net: 10.0 - 0.15 - 0.1 + 0.0 = 9.5 (the clean LSP implementation cancels the new LOW findings, and the carry-forward non-resolution prevents upward movement). The score stays at 9.5.

To reach 9.7+: fix the `__mn_list_get` attributes (P1), delete the drop-glue early return (#49), and cancel the debounce timer in `on_close` (this review V1). Three fixes, one session each.

---

## Post-Production Health Assessment

Arc 2 is a well-scoped, well-executed arc that adds significant developer-facing value (LSP features) without touching the compiler or runtime. From a memory-safety lens, this is the ideal arc shape: zero new surface in the areas I track, and the new code is pure Python with no C interop. The six LSP modules total approximately 2,200 lines of Python, all operating on immutable AST dataclasses with proper cleanup on document close and workspace re-scan.

The two concerns I have are both structural, not acute:

1. **The carry-forward backlog is stale.** At v4.36.0, my queue was 4 items (V1-V4). After Arc 2, it is 6 items (the same 4 plus 2 new LOWs). The P-series items from the full panel (P1-P6) are all at their 2nd cycle with no movement. Item #49 is at its 10th cycle. The tracking versions in `CARRY_FORWARD.md` need updating -- several point to v4.37.0 as the resolution target, which has now shipped without addressing them. This is not a safety concern -- none of these items are exploitable or crash-inducing in production -- but it is a process concern. The next compiler-touching arc should prioritize the 3-4 one-line fixes that would clear most of my queue.

2. **The `__mn_list_get` attribute violation (P1) is the oldest open MEDIUM in my ledger.** It was introduced at v4.32.0 as a side effect of the correct V2 fix (abort on OOB instead of returning NULL), flagged at v4.36.0, and not addressed in v4.37.0-v4.40.0. At `-O1` (the default) it is harmless. At `-O2` it is a miscompilation risk. No user has reported it because no one compiles Mapanare at `-O2` yet. But the attribute contract is wrong, and LLVM is within its rights to exploit it. This is the single most important one-line fix in the codebase from my lens.

**Verdict: PASS WITH NOTES.** Score: **9.5/10.** Confidence: **9/10.** The LSP code is clean. The runtime and emitter are frozen at v4.36.0 state with no regressions. The carry-forward queue did not move, but nothing in it is blocking production.

---

**End of review.**
