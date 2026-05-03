# Formatter Guide

`mnc fmt` (and the equivalent `mapanare fmt`) is the canonical source
formatter for `.mn` files, introduced in **v5.13.0** as Mc.2 in the
mnc-parity docket.

The formatter is intentionally **conservative** — it only normalizes
whitespace. It does not rewrite expressions, change brace style,
re-indent code, or sort imports. Aggressive style choices are deferred
to later releases (see
[`docs/roadmap/v5/v5.13.0/STYLE_AUDIT.md`](../roadmap/v5/v5.13.0/STYLE_AUDIT.md)).

## What it does

In order:

1. Normalizes line endings: `\r\n` and bare `\r` → `\n`.
2. Strips trailing whitespace from every line.
3. Replaces leading tabs with 4 spaces (mid-line tabs are left alone).
4. Collapses 2+ consecutive blank lines to 1.
5. Strips leading and trailing blank lines.
6. Ensures the file ends with exactly one `\n`.

## What it does NOT do (yet)

- Re-indent code based on brace depth — deferred (the corpus is
  already 4-space indented; v5.13.0 codifies that without enforcing
  it line-by-line).
- Rewrite expressions, calls, or operator spacing.
- ~~Sort or rewrite `import` statements.~~ **As of v5.27.0 (Mc.9)**:
  `--sort-imports` sorts contiguous top-level `import` blocks
  alphabetically. See below.
- ~~Wrap long lines.~~ **As of v5.27.0 (Mc.8)**: `--line-length N`
  is detect-only — long lines are reported on stderr but the source
  is never modified, because Mapanare's grammar rejects multi-line
  expressions. See below.
- Add or remove trailing commas in struct/list/map literals.
- Reformat comments — `//`, `///`, and `/* */` are preserved verbatim.
- Migrate `{}` blocks to `:` blocks — that is **v5.14.0 (Te.1)**, via
  a future `--to-terse` flag layered on top of this core.

## CLI

```text
mnc fmt <path>...                # format .mn files (in place)
mnc fmt <dir>                    # recursively format every .mn under a directory
mnc fmt --check <path>...        # exit 1 if any file would change; do not write
mnc fmt --stdout <path>          # print formatted output to stdout
mnc fmt --to-terse <path>        # migrate {} blocks to colon blocks (v5.14.0)
mnc fmt --to-braces <path>       # migrate colon blocks to {} blocks (v5.14.0)
mnc fmt --keep-braces <path>     # whitespace-only; suppress {}->colon auto-migration
mnc fmt --sort-imports <path>    # sort contiguous top-level import blocks (v5.27.0)
mnc fmt --line-length N <path>   # report lines exceeding N chars on stderr (v5.27.0)
```

`mapanare fmt` accepts the same flags. Both refuse to format a file
that fails to parse (exits 1 with the usual diagnostic so you can
fix the syntax error before the formatter rewrites anything).

### `--sort-imports` (v5.27.0 Mc.9)

Sorts contiguous top-level `import` blocks alphabetically. Block
boundaries are any non-import line — blank lines, comments, or
other top-level declarations — so the user's existing groupings are
preserved as the de-facto group structure. Each contiguous run of
imports sorts independently; blank-line separators between groups
stay put.

```mn
// before
import self::mir
import self::ast
import self::lower

import stdlib::math
import stdlib::io

// after `mnc fmt --sort-imports`
import self::ast
import self::lower
import self::mir

import stdlib::io
import stdlib::math
```

A comment between two imports splits the surrounding block into two
sub-blocks; neither side reorders across the comment. This keeps
intentional adjacency comments (e.g. `// keep this first`) attached
to the imports they describe.

The pass is idempotent and AST-preserving: Mapanare's import
resolution does not depend on source order for the shapes the
corpus uses, so the resulting AST has the same `ImportDecl`
multiset, just sorted.

### `--line-length N` (v5.27.0 Mc.8 — detect-only)

Reports every line that exceeds `N` characters on stderr. Under
`--check`, the presence of any overlong line causes a non-zero exit
so CI gates can enforce the ceiling. **The source is never modified
by `--line-length`**, regardless of mode.

This is detect-only because Mapanare's grammar is strictly
single-line for all expressions: newlines are not implicit
continuations inside parens, brackets, or braces. The parser rejects
every wrap shape (split arg list at comma, multi-line method chain
at dot, multi-line `&&` / `||` / `|>` operator chain), so an
auto-wrapping rewriter would necessarily break the v5.13.0 Mc.2
**AST-preservation** invariant. v5.27.0 closes Mc.8 honestly by
shipping the detector now and deferring auto-wrap to a future
release that also adds newline-tolerant grammar inside grouping
delimiters.

```bash
# CI gate: refuse a PR that introduces lines over 100 chars
mnc fmt --check --line-length 100 mapanare/self/ tests/golden/

# Local survey
mnc fmt --line-length 100 mapanare/self/ 2>&1 | grep "exceeds"

# Disabled: --line-length 0 (the default) skips the check entirely
mnc fmt --line-length 0 mapanare/self/
```

Refactoring an overlong line is up to the user — split the
expression into intermediate `let` bindings, extract a helper
function, or shorten an identifier. Mapanare's design preference is
that an expression that does not fit on one line is asking to be
named.

### Examples

```bash
# Format a single file in place
mnc fmt mapanare/self/lower.mn

# Format every .mn file in a directory recursively
mnc fmt tests/golden/

# Verify a directory is clean (CI-friendly)
mnc fmt --check mapanare/self/ tests/golden/ examples/

# See what the formatter would change without writing
mnc fmt --stdout mapanare/self/lower.mn | diff -u mapanare/self/lower.mn -
```

## Pre-commit hook

Drop this in `.git/hooks/pre-commit` (and `chmod +x`) to gate every
commit on a clean fmt:

```sh
#!/usr/bin/env bash
set -e

# Collect staged .mn files
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.mn$' || true)
if [ -z "$files" ]; then
    exit 0
fi

# Hand them to mnc fmt --check
echo "$files" | xargs mnc fmt --check
```

If `mnc` is not on the developer's `PATH` yet, swap the last line for
`xargs python3 -m mapanare.cli fmt --check`.

## Editor integration

There is no language-server integration in v5.13.0 — that ships with
**v5.18.0 (Mc.1 / Mc.3 / Mc.4 — LSP server, `mnc init`, `mnc check`,
VSCode extension)**. Until then, configure your editor to run
`mnc fmt --stdout` on save:

- **VSCode** — the upcoming `mapanare.vscode` extension will wire
  this up automatically. For now, the
  [`emeraldwalk.runonsave`](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave)
  extension can call `mnc fmt $FILE` after every save.
- **Vim/Neovim** — `:autocmd BufWritePost *.mn !mnc fmt %`.
- **Emacs** — `(add-hook 'after-save-hook ...)` calling `(shell-command "mnc fmt …")`.

## Invariants (for tooling and CI)

The formatter is contractually:

- **Idempotent**. `format(format(x)) == format(x)` for every input.
- **AST-preserving**. `parse(format(x)) == parse(x)` for every input
  that parses today. (Files with pre-existing parse errors are
  preserved with the same failure shape — the formatter never makes
  a syntax error worse.)
- **UTF-8 only**. Files that are not valid UTF-8 are reported on
  stderr and skipped.

These guarantees are checked on the entire `.mn` corpus by
[`tests/test_format.py`](../../tests/test_format.py).

## Why a formatter ships before the syntax overhaul

v5.13.0 is the first release in the **terseness arc** (v5.13.0 →
v5.21.0). Every later release in the arc adds a rewrite pass to
`mnc fmt --to-terse`, which is how the 14k-line self-hosted compiler
will be migrated from `{}` blocks to the new `:` block syntax in
**v5.17.0 (Sh.\*)** without weeks of hand-editing.

For that to work, the formatter has to be **rock solid first** —
which is why v5.13.0 ships with nothing more ambitious than
whitespace normalization. Solid foundations beat clever ones.
