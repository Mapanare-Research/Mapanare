# Coral -- Language Design Review of Mapanare v4.41.0

**Reviewer:** Coral
**Personality:** The Philosopher -- thoughtful, poetic, fair but challenging
**Previous Version Reviewed:** v4.36.0
**Arc:** v4.37.0 -> v4.41.0 (Arc 2 -- LSP maturity)
**Verdict:** PASS
**Confidence:** 9/10
**Score:** 9.2/10

**Files Reviewed:**

- `mapanare/lsp/completion.py` -- 242 lines; builtin method tables, four completion contexts
- `mapanare/lsp/rename.py` -- 91 lines; `_KEYWORDS` frozenset, validate + apply rename
- `mapanare/lsp/workspace.py` -- 362 lines; WorkspaceIndex, SymbolDef, ReferenceSite, `_collect_references`
- `mapanare/lsp/server.py` -- 691 lines; LSP handler wiring (hover, go-to-def, find-refs, completion, rename, diagnostics, code actions, formatting)
- `mapanare/lsp/diagnostics.py` -- 115 lines; semantic error to LSP diagnostic conversion
- `mapanare/lsp/analysis.py` -- `_KEYWORDS` list (lines 977-1008), `completions_at`, `receiver_type_at` (absent)
- `mapanare/mapanare.lark` -- lines 360-414; bilingual keyword terminals
- `mapanare/lexer.py` -- lines 44-78; `KEYWORDS` dict, `KEYWORD_SET`
- `mapanare/semantic.py` -- lines 486-506; string method type table
- `mapanare/emit_llvm_text.py` -- lines 2566-2582; `_smeth` string method dispatch
- `docs/SPEC.md` -- sections 2.1 (keywords), 4.6 (Option), 4.7 (Result), 11 (Streams), 12 (Signals), 16.3 (List ops), 17.3 (Map ops)
- `docs/cookbook.md` -- 100 lines sampled
- `tests/lsp/test_completion.py` -- 164 lines; 13 tests across 4 completion contexts
- `tests/lsp/test_rename.py` -- 98 lines; 8 tests (validate + apply)
- `editor/vscode/package.json` -- VS Code extension scaffold
- `.reviews/v4.41.0/MEASUREMENTS.md` -- arc metrics
- `.reviews/v4.41.0/PRE_PANEL_AUDIT.md` -- 17/17 claims verified
- `.reviews/v4.36.0/07-coral.md` -- my previous review

---

## Executive Summary

Arc 1 was about correctness under the microscope: guards, or-patterns,
exhaustiveness, the `?` operator. Arc 2 is about the developer reaching
for the language with a cursor. The question is no longer "does the
language compute correctly?" but "does the editor know what the
language knows?"

The answer is: mostly yes, with three places where the editor's
knowledge falls short of the compiler's, and one place where the
rename guard has a blind spot that could silently accept a keyword.

The arc delivered nine LSP features across four releases (v4.37.0
through v4.40.0), four new modules in `mapanare/lsp/`, 49
LSP-specific tests, and a VS Code extension scaffold. The
architecture is sound: a `WorkspaceIndex` that scans `.mn` files,
extracts top-level symbols, and indexes references provides the
foundation for cross-module go-to-def, find-references, rename,
and completion. The completion engine dispatches on four contexts
(import, type, field/method, fallback) and provides method tables
for Option, Result, List, and String. Diagnostics stream via
debounced semantic re-checks on `didChange`.

My evaluation focuses on five questions:

1. Does `complete_type` offer the right types?
2. Does `complete_field_method` know the right methods?
3. Does rename reject all language keywords?
4. Are the completion tables honest -- do they promise methods the
   compiler actually implements?
5. Is the documentation adequate?

---

## Design Evaluation: The Five Questions

### 1. Does `complete_type` Offer the Right Types?

`complete_type` (completion.py:113-137) offers 14 builtin types from
`_BUILTIN_TYPES` plus user-defined types from the workspace index.
The builtin list:

| Offered | In `types.py` | In SPEC |
|---------|---------------|---------|
| Int | Yes (TypeKind.INT) | Yes |
| Float | Yes (TypeKind.FLOAT) | Yes |
| String | Yes (TypeKind.STRING) | Yes |
| Bool | Yes (TypeKind.BOOL) | Yes |
| Char | Yes (TypeKind.CHAR) | Yes |
| Void | Yes (TypeKind.VOID) | Yes |
| List\<T\> | Yes (TypeKind.LIST) | Yes |
| Map\<K, V\> | Yes (TypeKind.MAP) | Yes |
| Option\<T\> | Yes (TypeKind.OPTION) | Yes |
| Result\<T, E\> | Yes (TypeKind.RESULT) | Yes |
| Signal\<T\> | Yes (TypeKind.SIGNAL) | Yes |
| Stream\<T\> | Yes (TypeKind.STREAM) | Yes |
| Agent | Yes (TypeKind.AGENT) | Yes |
| Tensor | Yes (TypeKind.TENSOR) | Yes |

All 14 map to real TypeKind variants in `types.py` and documented
types in the SPEC. The user-defined type lookup filters on
`sym.kind in ("struct", "enum", "trait", "type")`, which correctly
catches all user-creatable type forms. Agents are indexed with
`kind="agent"` and thus excluded from type completion, which is
correct: `agent` definitions are not usable as type annotations
in the grammar (an agent is spawned, not used as a type parameter).

**Finding: clean.** The type completion is honest and complete.

### 2. Does `complete_field_method` Know the Right Methods?

This is where the review gets interesting. The method tables in
completion.py cover four types:

**Option\<T\>** -- 4 methods: `is_some`, `is_none`, `unwrap`, `map`.
**Result\<T, E\>** -- 4 methods: `is_ok`, `is_err`, `unwrap`, `map`.
**List\<T\>** -- 6 methods: `len`, `push`, `pop`, `get`, `map`, `filter`.
**String** -- 10 methods: `len`, `contains`, `starts_with`, `ends_with`,
`replace`, `split`, `trim`, `to_upper`, `to_lower`, `substr`.

I cross-referenced these against three sources of truth:

#### String Methods

The semantic checker (`semantic.py:487-503`) recognizes 13 string
methods. The LLVM emitter (`emit_llvm_text.py:2567-2581`) implements
14 string methods. The completion table offers 10.

Missing from completion but implemented in the compiler:

| Method | In semantic.py | In emit_llvm_text.py | In completion.py |
|--------|---------------|---------------------|-----------------|
| `find` | Yes (returns Int) | Yes (`__mn_str_find`) | **No** |
| `byte_at` | Yes (returns Int) | Yes (`__mn_str_byte_at`) | **No** |
| `char_at` | Yes (returns String) | Yes (`__mn_str_char_at`) | **No** |
| `trim_start` | Yes (returns String) | Yes (`__mn_str_trim_start`) | **No** |
| `trim_end` | Yes (returns String) | Yes (`__mn_str_trim_end`) | **No** |
| `length` | Yes (returns Int) | No (uses `len` builtin) | No (uses `len` instead) |

Five implemented string methods are invisible to the completion
engine. A developer typing `my_string.` will not see `find`,
`char_at`, `byte_at`, `trim_start`, or `trim_end`. These are real
methods that compile and run -- the semantic checker types them,
the LLVM emitter dispatches them. The editor simply does not know
about them.

#### Option/Result Methods

The completion table offers `is_some`, `is_none`, `unwrap`, and
`map` for Option, and the corresponding set for Result. I searched
the entire `mapanare/` tree for evidence that these methods are
implemented in the lowerer or any emitter. The results:

- `is_some`, `is_none`, `is_ok`, `is_err`: **not found** in
  `lower.py`, `emit_llvm_text.py`, or `emit_c.py` as method
  dispatch targets. The C emitter uses `is_ok` as a struct field
  name (the tag bit), not as a callable method.
- `unwrap`: **not found** as a method dispatch target. The `?`
  operator performs unwrapping, but `opt.unwrap()` as a method
  call is not wired in the lowerer.
- `map`: **not found** as a method on Option/Result.

This means the completion engine promises four methods on Option
and four on Result that **do not compile**. A developer who
selects `unwrap()` from the completion list will get a compilation
error. This is the worst category of completion bug: the editor
actively misleads the user.

The Option/Result operations that actually work today are:
- Pattern matching (`match opt { Some(v) => ..., None => ... }`)
- The `?` operator (postfix error propagation)
- Construction (`Some(v)`, `Ok(v)`, `Err(e)`, `none`)

There is no method dispatch for Option/Result. These are enums,
not objects with `impl` blocks (no user-visible `impl Option<T>`
exists in the language).

#### List Methods

The completion table offers `len`, `push`, `pop`, `get`, `map`,
and `filter`. The SPEC (section 16.3) documents only `push` and
`len(list)` (as a builtin function, not a method). I could not
find evidence that `pop`, `get`, `map`, or `filter` are
implemented as method calls on List in the lowerer or LLVM emitter.
The `map` and `filter` operations exist as stream operators
(SPEC section 11.3) and as higher-order functions in the cookbook,
but not as `list.map(f)` method calls.

The `len` entry is ambiguous: in the language, list length is
obtained via the builtin `len(list)`, not `list.len()`. If
`list.len()` compiles, the completion is correct; if only
`len(list)` works, then the completion is misleading.

#### Map Methods

No Map methods are offered in the completion table. The SPEC
(section 17.3) documents `map.contains(key)` and `map.delete(key)`
as method calls. These are absent from completion. This is the
opposite of the Option/Result problem: here the language has
methods but the editor does not know about them.

#### Signal/Stream Methods

No Signal or Stream methods are offered. The SPEC documents
`signal.value` (field access), `signal.subscribe(fn)` (method),
and 14 stream operators (`map`, `filter`, `take`, `skip`, etc.).
These are absent from completion. This is a gap but a defensible
one: Signal and Stream methods may not be fully implemented in
the LLVM backend, and offering them in completion would repeat
the Option/Result problem.

**Finding (HIGH): The Option and Result method tables promise
four methods each that are not implemented in any compiler
backend. The completion engine will mislead users.**

**Finding (MEDIUM): Five implemented String methods are missing
from the completion table.**

**Finding (MEDIUM): Map methods documented in the SPEC are absent
from completion.**

### 3. Does Rename Reject All Language Keywords?

The `_KEYWORDS` frozenset in `rename.py:19-28` contains 37 entries.
I compared this against every keyword source in the codebase.

**Grammar keywords** (from `mapanare.lark:367-407`):

| Keyword | In grammar | In rename `_KEYWORDS` |
|---------|-----------|----------------------|
| `let` | Yes (KW_LET) | Yes |
| `mut` | Yes (KW_MUT) | Yes |
| `fn` | Yes (KW_FN) | Yes |
| `return` | Yes (KW_RETURN) | Yes |
| `pub` | Yes (KW_PUB) | Yes |
| `self` | Yes (KW_SELF) | Yes |
| `agent` | Yes (KW_AGENT) | Yes |
| `spawn` | Yes (KW_SPAWN) | Yes |
| `sync` | Yes (KW_SYNC) | Yes |
| `signal` | Yes (KW_SIGNAL) | Yes |
| `stream` | Yes (KW_STREAM) | Yes |
| `pipe` | Yes (KW_PIPE) | Yes |
| `if` | Yes (KW_IF) | Yes |
| `else` | Yes (KW_ELSE) | Yes |
| `match` | Yes (KW_MATCH) | Yes |
| `for` | Yes (KW_FOR) | Yes |
| `while` | Yes (KW_WHILE) | Yes |
| `in` | Yes (KW_IN) | Yes |
| `type` | Yes (KW_TYPE) | Yes |
| `struct` | Yes (KW_STRUCT) | Yes |
| `enum` | Yes (KW_ENUM) | Yes |
| `impl` | Yes (KW_IMPL) | Yes |
| `trait` | Yes (KW_TRAIT) | Yes |
| `import` | Yes (KW_IMPORT) | Yes |
| `export` | Yes (KW_EXPORT) | Yes |
| `extern` | Yes (KW_EXTERN) | Yes |
| `true` | Yes (KW_TRUE) | Yes |
| `false` | Yes (KW_FALSE) | Yes |
| `none` | Yes (KW_NONE) | **No** |
| `new` | Yes (KW_NEW) | **No** |
| `assert` | Yes (KW_ASSERT) | Yes |
| `break` | Yes (KW_BREAK) | Yes |
| `continue` | Yes (KW_CONTINUE) | Yes |
| `di` | Yes (KW_DI) | **No** |
| `loop` | No terminal | Yes (in `_KEYWORDS` but not in grammar) |

**Bilingual keywords** (from `mapanare.lark:367-399` and SPEC section 2.1):

| Spanish | English equiv | In rename `_KEYWORDS` |
|---------|--------------|----------------------|
| `pon` | `let` | Yes |
| `si` | `if` | Yes |
| `sino` | `else` | Yes |
| `da` | `return` | **No** |
| `yo` | `self` | **No** |
| `cada` | `for` | **No** |
| `mien` | `while` | **No** |
| `en` | `in` | **No** |
| `tipo` | `type` | Yes |
| `modo` | `trait` | **No** |
| `way` | `trait` | **No** |
| `usa` | `import` | **No** |
| `nada` | `none` | **No** |
| `sal` | `break` | **No** |
| `sigue` | `continue` | **No** |

**Contextual keywords** (from `mapanare.lark:409-413`):

| Keyword | In rename `_KEYWORDS` |
|---------|----------------------|
| `input` | **No** |
| `output` | **No** |
| `Tensor` | **No** |
| `_` | **No** |

The rename `_KEYWORDS` list in `rename.py` includes `pon`, `si`,
`sino`, `para`, `mientras`, `retorna`, `tipo`, `importar`, and
`exportar` as bilingual keywords. But cross-referencing against
the grammar and SPEC:

- `para` is listed in rename but **does not exist in the grammar**.
  The grammar uses `cada` as the Spanish `for`. `para` is a
  phantom keyword.
- `mientras` is listed in rename but **does not exist in the
  grammar**. The grammar uses `mien` as the Spanish `while`.
  `mientras` is a phantom keyword.
- `retorna` is listed in rename but **does not exist in the
  grammar**. The grammar uses `da` as the Spanish `return`.
  `retorna` is a phantom keyword.
- `importar` is listed in rename but the grammar uses `usa`.
  `importar` is a phantom keyword.
- `exportar` is listed in rename but `export` has no Spanish
  alias in the grammar. `exportar` is a phantom keyword.

Meanwhile, the real bilingual keywords that **are** in the grammar
are missing from rename:

- `da` (return), `yo` (self), `cada` (for), `mien` (while),
  `en` (in), `modo` (trait), `way` (trait alias), `usa` (import),
  `nada` (none), `sal` (break), `sigue` (continue).

Additionally, three English keywords are missing:

- `none` -- a keyword literal (KW_NONE in grammar)
- `new` -- the struct construction keyword (KW_NEW in grammar)
- `di` -- the print statement keyword (KW_DI in grammar)

And four contextual keywords are missing: `input`, `output`,
`Tensor`, `_`. Whether contextual keywords should be blocked by
rename is debatable (they are only keywords in specific positions),
but `_` should certainly be blocked since it is the wildcard
pattern.

**Finding (HIGH): The rename keyword list contains 5 phantom
bilingual keywords that do not exist in the grammar (`para`,
`mientras`, `retorna`, `importar`, `exportar`) and is missing
11 real bilingual keywords, 3 English keywords, and the wildcard
`_`. A user can rename a symbol to `da`, `cada`, `mien`, `new`,
`none`, or `di` and the rename will succeed, producing code that
does not parse.**

### 4. Are the Completion Tables Honest?

As analyzed in question 2:

- **String methods:** 10 out of 15 implemented methods are offered.
  Honest but incomplete.
- **Option methods:** 4 methods offered, 0 implemented. Dishonest.
- **Result methods:** 4 methods offered, 0 implemented. Dishonest.
- **List methods:** 6 methods offered, implementation status unclear
  for `pop`, `get`, `map`, `filter`. Potentially dishonest.
- **Map methods:** 0 methods offered, at least 2 documented
  (`contains`, `delete`). An omission, not a lie.
- **Signal/Stream:** 0 methods offered. Correct omission if the
  methods are not yet callable via method dispatch.

The Option and Result tables are the most concerning. They appear
to be aspirational -- describing the API the language *should*
have, not the API it *does* have. In an LSP completion provider,
aspiration is a bug.

### 5. Is the Documentation Adequate?

The SPEC (section 2.1) is the definitive keyword reference. The
bilingual keyword table (SPEC lines 149-165) is correct and
exhaustive. The problem is that the LSP code does not faithfully
transcribe it.

The cookbook does not reference LSP features, which is expected --
the cookbook is for the language, not the tooling.

The VS Code extension scaffold (`editor/vscode/package.json`)
declares the right language ID, file extensions, and activation
events. It lists trigger characters `[".", ":", "<"]` which match
the server's `CompletionOptions`. This is adequate.

The `MEASUREMENTS.md` file accurately reports the 9 LSP features
and test counts. The `PRE_PANEL_AUDIT.md` verifies 17/17 claims.

---

## Progress on Carry-Forward Items from v4.36.0

| # | Item | Status |
|---|------|--------|
| C1 | SPEC section 3.10 tensor Status line stale | **DEFERRED** -- still outside scope |
| C2 | CARRY_FORWARD.md peer reviewer coverage | **OBSERVATION** -- not audited this cycle |
| C3 | `examples/` missing agents/signals/streams demos | **UNCHANGED** -- 4th cycle now |
| C4 | SPEC section 5.6 "compatible types" vs name-set check | **NOT CHECKED** -- outside Arc 2 scope |
| C5 | No golden test for `Option<T>` + `?` | **NOT CHECKED** -- outside Arc 2 scope |
| C6 | Pipe + `?` precedence undocumented | **NOT CHECKED** -- outside Arc 2 scope |
| C7 | Cookbook missing combined guards + or-patterns recipe | **NOT CHECKED** -- outside Arc 2 scope |
| C8 | SPEC section 5.8 missing error-case specification | **NOT CHECKED** -- outside Arc 2 scope |

Items C4-C8 are outside the scope of Arc 2 (LSP maturity). I am
not closing or re-evaluating them here; they carry forward to the
next arc that touches pattern matching or the `?` operator.

---

## Strengths

1. **The WorkspaceIndex architecture is correct.** The two-pass
   design (first pass indexes symbols, second pass collects
   references) ensures that cross-module references are resolved
   against a complete symbol table. Incremental rebuilds on save
   (`rebuild_file`) correctly remove old symbols and re-collect
   references. This is the right foundation for an LSP: a single
   shared index that every handler queries.

2. **Completion context detection is pragmatic.** The
   `_detect_completion_context` function in server.py uses simple
   string heuristics (line prefix matching) rather than attempting
   a partial parse. This is the right trade: partial parsing is
   fragile for incomplete code, and the four contexts (import,
   type, field, identifier) cover the common cases. The trigger
   characters `[".", ":", "<"]` are well-chosen.

3. **Visibility is respected in fallback completion.** The
   `complete_identifiers` function only offers `pub` symbols from
   other modules, while offering all symbols from the current
   module. The test `test_visibility_respected` verifies this.
   This is correct module-boundary enforcement.

4. **Rename validation is structurally sound.** The three-rule
   architecture (valid identifier, not a keyword, no name
   collision in same module) is the right set of checks. The
   cross-module collision check (allowing the same name in
   different modules) is correct for Mapanare's module system.

5. **Diagnostic streaming with debounce is well-designed.** The
   300ms debounce on `didChange` with immediate re-check on save
   is the standard pattern for LSP diagnostics. Threading is
   correctly daemonized. The timer cancellation on superseding
   edits prevents stale diagnostics.

6. **Sort-text ranking is correct.** Local symbols get `0_`,
   cross-module public symbols get `2_`, builtins get `3_`. This
   ensures that the developer sees the most relevant completions
   first: local context, then imported names, then language
   builtins.

---

## Issues

### HIGH

**H1. Option and Result method tables are aspirational, not real.**

`_OPTION_METHODS` and `_RESULT_METHODS` in `completion.py:36-48`
promise `is_some`, `is_none`, `unwrap`, `map` (and the Result
equivalents). None of these are implemented as method calls in
any compiler backend. Option and Result are enums accessed via
pattern matching and the `?` operator. A developer who accepts
`unwrap()` from the completion list will get a compilation error.

**Fix:** Remove the Option and Result method tables from
`completion.py`, or add a `(not yet implemented)` suffix to the
documentation field. Alternatively, implement these methods in
the lowerer and LLVM emitter (this is a language feature, not
an LSP fix).

**H2. Rename keyword list has 5 phantom keywords and is missing
14+ real keywords.**

`_KEYWORDS` in `rename.py:19-28` contains `para`, `mientras`,
`retorna`, `importar`, `exportar` -- none of which exist in the
grammar. Meanwhile, `da`, `yo`, `cada`, `mien`, `en`, `modo`,
`way`, `usa`, `nada`, `sal`, `sigue`, `none`, `new`, and `di`
are all real keywords that rename will accept as valid new names.

**Fix:** Replace the `_KEYWORDS` frozenset with a programmatic
import from `mapanare/lexer.py:KEYWORD_SET` (which is the
authoritative set), plus the bilingual aliases extracted from
the grammar. A single source of truth prevents drift.

### MEDIUM

**M1. Five implemented String methods missing from completion.**

`find`, `char_at`, `byte_at`, `trim_start`, `trim_end` are
recognized by the semantic checker and implemented in the LLVM
emitter but absent from `_STRING_METHODS`. A developer using
these methods will not get completion assistance.

**Fix:** Add the missing methods to `_STRING_METHODS`.

**M2. Map methods absent from completion.**

The SPEC documents `map.contains(key)` and `map.delete(key)` as
method calls. These are not offered by `complete_field_method`.

**Fix:** Add a `_MAP_METHODS` table and handle the `"map"`
receiver type prefix in `complete_field_method`.

**M3. `"method"` completion kind not mapped in server.py.**

`CompletionCandidate` uses `kind="method"` for Option/Result/List/
String method completions, but `_map_completion_kind` in
server.py:667-679 does not include `"method"` in its dictionary.
It falls through to the default `CompletionItemKind.Text`. This
means all method completions appear as plain text items in the
editor, without the method icon.

**Fix:** Add `"method": lsp.CompletionItemKind.Method` to the
kind mapping dictionary.

### LOW

**L1. `_KEYWORDS` list in analysis.py is also incomplete.**

The `_KEYWORDS` list in `analysis.py:977-1008` (used for fallback
keyword completion) contains 29 entries. It is missing: `new`,
`assert`, `break`, `continue`, `loop`, `self`, `send`, and all
bilingual keywords. This means keyword completion will not offer
`break`, `continue`, `new`, or `assert` -- all of which are
common keywords a developer would expect to see.

**L2. No `receiver_type_at` method on DocumentAnalysis.**

`server.py:468` checks `hasattr(analysis, "receiver_type_at")`
before calling it. A grep of `analysis.py` confirms that no
such method exists. This means the `"field"` completion context
in server.py always passes an empty string as the receiver type,
so `complete_field_method` can never match a specific type and
will always return an empty list for workspace-level field
completion. The within-file `_dot_completions` in analysis.py
may partially compensate, but the workspace-aware method
completion is effectively dead code.

**L3. `complete_import` offers `"stdlib"` as a hardcoded hint
but no stdlib submodules.**

The import completion adds `"stdlib"` as a completion candidate,
but after typing `import stdlib/` or `import stdlib.` there is
no further completion for stdlib submodules (`math`, `io`, etc.).
This is a stub, not a feature.

**L4. Snippet insertion inconsistency in String methods.**

For Option, Result, and List methods, `complete_field_method`
generates `insert_text` with snippet syntax (`$1`, `$0`) for
methods with parameters. For String methods (line 167-169), no
`insert_text` is set -- the user gets the bare method name
without parentheses or parameter placeholders. This inconsistency
means String method completions require more typing than
Option/Result method completions.

**L5. `examples/` directory still missing showcase demos.**

Fourth cycle carrying this forward. Still no standalone
`examples/agents/`, `examples/signals/`, `examples/streams/`
directories. Elevating to MEDIUM at next review if unchanged.

---

## Recommendations

### R1. Derive keyword lists from a single source.

Create a `mapanare/keywords.py` module (or extend `types.py`)
that exports the complete keyword set -- English keywords,
bilingual aliases, and contextual keywords -- as a single
`frozenset`. Both `rename.py:_KEYWORDS` and
`analysis.py:_KEYWORDS` should import from this source. The
grammar terminals in `mapanare.lark` are the authoritative
definition; the Python keyword set should be derived from them.
This eliminates the class of bugs found in H2 and L1.

### R2. Remove Option/Result method tables until implemented.

The completion engine should not promise what the compiler cannot
deliver. Remove `_OPTION_METHODS` and `_RESULT_METHODS` now.
When the language ships `impl Option<T>` and `impl Result<T, E>`
(either as built-in lowering or as stdlib `.mn` files), add the
method tables back.

### R3. Wire `receiver_type_at` in DocumentAnalysis.

The field/method completion path in server.py is dead without
this method. Either implement type inference at the cursor
position (using the semantic checker's `_infer_expr` on the
receiver expression) or remove the `hasattr` guard and
acknowledge the limitation.

### R4. Add the five missing String methods.

Append to `_STRING_METHODS`:

```python
("find", "fn(sub: String) -> Int", "Returns index of first occurrence, or -1"),
("char_at", "fn(idx: Int) -> String", "Returns character at index"),
("byte_at", "fn(idx: Int) -> Int", "Returns byte value at index"),
("trim_start", "fn() -> String", "Removes leading whitespace"),
("trim_end", "fn() -> String", "Removes trailing whitespace"),
```

### R5. Add `"method"` to the completion kind map.

In `server.py:_map_completion_kind`, add:

```python
"method": lsp.CompletionItemKind.Method,
"module": lsp.CompletionItemKind.Module,
```

(`"module"` is also used by `complete_import` but not mapped.)

---

## Comparison with Peer LSP Implementations

### LSP Feature Matrix (v4.41.0)

| Feature | rust-analyzer | pylsp | Mapanare LSP |
|---------|--------------|-------|-------------|
| Go-to-definition | Cross-crate | Cross-module | Cross-module |
| Find references | Cross-crate | Cross-module | Cross-module |
| Rename | Cross-crate + keyword check | Cross-module | Cross-module + keyword check (incomplete) |
| Completion (types) | All types in scope | All types | Builtin + workspace types |
| Completion (methods) | Trait-resolved methods | All methods | Hardcoded tables (4 types) |
| Diagnostics | Real-time via cargo check | Real-time via pyflakes | Debounced semantic check |
| Code actions | 50+ quick fixes | Moderate | 2 (unused import, unnecessary mut) |
| Formatting | rustfmt integration | autopep8/black | Built-in formatter |

### Assessment

The Mapanare LSP is at the right maturity level for a v4.x
language: cross-module navigation works, the symbol index is
architecturally sound, and the completion engine has the right
dispatch structure. The gap is in method resolution: a mature
LSP derives method completions from the type system (trait
resolution in rust-analyzer, attribute lookup in pylsp), while
Mapanare uses hardcoded tables. Hardcoded tables are fine for a
young language with a small method surface, but they introduce
a maintenance burden: every new method must be added to both the
compiler and the completion table, and the two can drift (as they
already have for String, Option, and Result).

---

## Score Justification

**9.2/10.**

The 0.2 decrease from v4.36.0's 9.4 reflects the two HIGH issues:

1. **H1 (aspirational Option/Result methods):** The completion
   engine actively misleads users by offering methods that do not
   compile. This is the LSP equivalent of a SPEC claim that
   overclaims -- the same kind of honesty issue that the recovery
   arc was built to prevent. The fix is simple (remove the tables
   or implement the methods), but the existence of the bug
   suggests the completion tables were written from a design
   document rather than cross-referenced against the compiler.

2. **H2 (phantom keywords in rename):** The rename guard contains
   fabricated bilingual keywords while missing real ones. This is
   a factual error, not a design disagreement. `para` is not a
   Mapanare keyword. `da` is. The rename validator should not
   invent keywords.

The arc's strengths are substantial: the WorkspaceIndex
architecture, the cross-module features, the diagnostic streaming,
the test coverage (49 LSP tests). These are not diminished by the
issues above. The infrastructure is correct; the data tables
within it are not.

The 0.8 gap from 10.0 breaks down as:
- 0.3 for H1 + H2 (honesty of completion tables and keyword list)
- 0.2 for M1 + M2 + M3 (incomplete but not misleading)
- 0.2 for L2 (dead code in the method completion path)
- 0.1 for the example corpus (4th cycle)

---

## Carry-Forward Items

| # | Item | Severity | Cycles | Status | Owner |
|---|------|----------|--------|--------|-------|
| C1 | SPEC section 3.10 tensor Status line stale | LOW | 3 | DEFERRED | v5.0.0 |
| C2 | CARRY_FORWARD.md peer reviewer coverage | LOW | 3 | OBSERVATION | Standing |
| C3 | `examples/` missing agents/signals/streams demos | **MEDIUM** | **4** | OPEN | v4.42.0 |
| C4 | SPEC section 5.6 "compatible types" vs name-set check | MEDIUM | 2 | DEFERRED | Next pattern-matching arc |
| C5 | No golden test for `Option<T>` + `?` | LOW | 2 | DEFERRED | Next pattern-matching arc |
| C6 | Pipe + `?` precedence undocumented | LOW | 2 | DEFERRED | Next pattern-matching arc |
| C7 | Cookbook missing combined guards + or-patterns recipe | LOW | 2 | DEFERRED | Next pattern-matching arc |
| C8 | SPEC section 5.8 missing error-case specification | LOW | 2 | DEFERRED | Next pattern-matching arc |
| C9 | Option/Result completion methods not implemented (H1) | **HIGH** | 1 | OPEN | v4.42.0 |
| C10 | Rename keyword list drift from grammar (H2) | **HIGH** | 1 | OPEN | v4.42.0 |
| C11 | 5 String methods missing from completion (M1) | MEDIUM | 1 | OPEN | v4.42.0 |
| C12 | Map methods absent from completion (M2) | MEDIUM | 1 | OPEN | v4.42.0 |
| C13 | `"method"` kind not mapped in server.py (M3) | MEDIUM | 1 | OPEN | v4.42.0 |
| C14 | `receiver_type_at` not implemented (L2) | LOW | 1 | OPEN | v4.42.0 |

---

## Verdict

**PASS.**

The arc built the right thing: a workspace-wide symbol index that
enables cross-module navigation, rename, and context-aware
completion. The architecture will scale. The test coverage is
adequate. The VS Code extension scaffold is ready for users.

The data that feeds the architecture has gaps. The completion
tables promise methods that do not exist. The rename guard
rejects keywords that are not keywords and accepts keywords
that are. These are inventory errors, not architectural errors.
They are fixable in a single release without structural changes.

The language's editor story has gone from "nothing" at v4.36.0
to "functional but imperfect" at v4.41.0. That is the right
trajectory. The next step is to close the honesty gaps: derive
keyword lists from the grammar, derive method tables from the
compiler, and stop offering what has not been built.

The editor should know exactly what the language knows. No more,
no less.
