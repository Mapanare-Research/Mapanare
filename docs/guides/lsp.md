# Mapanare Language Server

Real-time editor support for `.mn` files: diagnostics, hover types,
jump-to-definition, find references, completion, and rename.

Implemented as a Python LSP server in `mapanare/lsp/`, using
[`pygls`](https://github.com/openlawlibrary/pygls) and
[`lsprotocol`](https://github.com/microsoft/lsprotocol). Ships with
the Mapanare package.

> Status: **v0.5.0** — first public release of the LSP, shipped with
> Mapanare v5.18.0.

## Launch

```bash
mapanare lsp     # Python CLI
mapanare-lsp     # console-script alias (same binary)
mnc lsp          # native CLI; shells out to `mapanare lsp`
```

All three speak [LSP](https://microsoft.github.io/language-server-protocol/)
over stdio.

## Editor setup

### Visual Studio Code

The official extension lives in a sibling repo:
[**Mapanare-Research/mapanare-vscode**](https://github.com/Mapanare-Research/mapanare-vscode).

```bash
code --install-extension mapanare-research.mapanare
```

The extension launches `mapanare lsp` over stdio. Override the
binary via the `mapanare.lsp.path` setting if `mapanare` is not
on `PATH`. Source + build instructions live in the extension repo.

### Neovim

`nvim-lspconfig` doesn't ship a Mapanare entry yet. Add this to your
`init.lua`:

```lua
local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

if not configs.mapanare then
  configs.mapanare = {
    default_config = {
      cmd = { "mapanare", "lsp" },
      filetypes = { "mapanare" },
      root_dir = lspconfig.util.root_pattern("mapanare.toml", ".git"),
      single_file_support = true,
    },
  }
end

lspconfig.mapanare.setup({})
```

You'll also need a filetype detector — drop this in
`~/.config/nvim/ftdetect/mapanare.vim`:

```vim
au BufNewFile,BufRead *.mn set filetype=mapanare
```

### Helix

`languages.toml`:

```toml
[[language]]
name = "mapanare"
scope = "source.mapanare"
file-types = ["mn"]
roots = ["mapanare.toml", ".git"]
language-servers = ["mapanare-lsp"]

[language-server.mapanare-lsp]
command = "mapanare"
args = ["lsp"]
```

### Zed

A native Zed extension is not available yet. Community contributions
welcome.

## Capabilities (v5.18.0)

| LSP method | Status | Notes |
|---|---|---|
| `initialize` / `initialized` | ✅ | |
| `shutdown` / `exit` | ✅ | |
| `textDocument/didOpen` | ✅ | Triggers full analysis + diagnostics |
| `textDocument/didChange` | ✅ | Full re-parse; debounced 300 ms |
| `textDocument/didClose` | ✅ | Drops the document from the cache |
| `textDocument/publishDiagnostics` | ✅ | Push mode |
| `textDocument/hover` | ✅ | Type info, signatures |
| `textDocument/definition` | ✅ | Local + workspace-wide |
| `textDocument/references` | ✅ | Top-level functions, structs, enums, enum variants |
| `textDocument/completion` | ✅ | Identifiers, member access, type position, import paths |
| `textDocument/rename` | ✅ | Cross-module; rejects keywords + name collisions |
| `textDocument/codeAction` | ❌ | v5.20.0+ |
| `textDocument/semanticTokens` | ❌ | v5.20.0+ |
| `textDocument/inlayHint` | ❌ | v5.20.0+ |
| `workspace/symbol` | ❌ | v5.20.0+ |

## Diagnostics

Push-based on `didOpen` and after a 300 ms debounce on `didChange`.
The server runs the same `parse_recovering` + `check` pipeline used
by `mapanare check`, then maps each `Diagnostic` to LSP `Diagnostic`
shape.

Severity mapping:

| Internal | LSP |
|---|---|
| `error` | `Error` |
| `warning` | `Warning` |
| `info` | `Information` |
| `hint` | `Hint` |

## Workspace index

`WorkspaceIndex` (in `mapanare/lsp/workspace.py`) walks the project's
`.mn` files at startup and builds a name → location map. It powers
cross-module go-to-def and rename. Files are re-indexed on save.

## Troubleshooting

**The server doesn't start.** Run `mapanare lsp` directly in a
terminal. If it errors, the LSP error message is the same one your
editor would surface. Common cause: `pygls` not installed —
`pip install --upgrade mapanare` or `pip install pygls lsprotocol`.

**Diagnostics never appear.** Set
`mapanare.lsp.trace.server: "verbose"` (VS Code) or the equivalent
in your editor and inspect the JSON-RPC traffic. Look for
`publishDiagnostics` notifications. If they never arrive, the
parser likely hit an internal error — file an issue with the trace.

**Hover shows no type info.** The symbol probably wasn't resolved
— the hover provider only returns information for symbols the
semantic checker recognized. Check that the file type-checks via
`mapanare check`.

## Limitations

- **Full re-parse on every change.** No incremental parsing yet.
  Large files (>1000 LOC) may feel sluggish on rapid edits.
- **No inline diagnostics for cross-module type errors during
  edit** — the workspace index updates on save, not on change.
- **Rename:** the implementation is conservative; if it can't
  resolve every reference statically (e.g. through dynamic
  reflection paths) the rename is rejected rather than partial.

## Roadmap

- v5.20.0 — code actions, semantic tokens, inlay hints, workspace
  symbol search.
- v6.0+ — incremental parsing, refactoring beyond rename
  (extract function/method).
