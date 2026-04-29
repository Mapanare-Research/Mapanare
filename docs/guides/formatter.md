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
- Sort or rewrite `import` statements.
- Wrap long lines.
- Add or remove trailing commas in struct/list/map literals.
- Reformat comments — `//`, `///`, and `/* */` are preserved verbatim.
- Migrate `{}` blocks to `:` blocks — that is **v5.14.0 (Te.1)**, via
  a future `--to-terse` flag layered on top of this core.

## CLI

```text
mnc fmt <path>...               # format .mn files (in place)
mnc fmt <dir>                   # recursively format every .mn under a directory
mnc fmt --check <path>...       # exit 1 if any file would change; do not write
mnc fmt --stdout <path>         # print formatted output to stdout
```

`mapanare fmt` accepts the same flags. Both refuse to format a file
that fails to parse (exits 1 with the usual diagnostic so you can
fix the syntax error before the formatter rewrites anything).

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
