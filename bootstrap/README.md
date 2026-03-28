> **ARCHIVED -- v0.6.0 snapshot, do not modify.**
> This directory contains the frozen Python bootstrap compiler from v0.6.0.
> It is preserved for historical reference and self-hosted compiler bootstrapping only.
> All active development targets the LLVM and WebAssembly backends.

# Bootstrap Compiler (v0.6.0 Snapshot)

This directory contains a frozen copy of the v0.6.0 Python-based Mapanare
compiler. It is preserved as a reference and used to bootstrap the self-hosted
compiler written in Mapanare itself (see `mapanare/self/*.mn`).

**Snapshot date:** v0.6.0 release
**Source:** `mapanare/*.py` and `mapanare/mapanare.lark`

## What's Frozen

This snapshot captures the complete v0.6.0 compiler including:

- **MIR pipeline** — AST → MIR lowering → MIR optimizer → MIR emitters
- **Dual emitters** — Python transpiler and LLVM IR (both AST-direct and MIR-based)
- **Optimizer** — Constant folding, DCE, agent inlining, stream fusion (O0–O3)
- **Linter** — 8 rules with `--fix` support
- **Diagnostics** — Rust-style colorized error output with spans
- **Module resolution** — File-based imports with `pub` visibility
- **Doc generator** — `mapanare doc` from `///` comments

## Why Frozen

The Python bootstrap is frozen at this point because:

1. The self-hosted compiler (`mapanare/self/*.mn`) is approaching completion
2. All future compiler development happens in Mapanare itself
3. This snapshot serves as Stage 0 for three-stage bootstrap verification

## Bootstrap Chain

1. **Stage 0 (this directory):** Python compiler compiles `.mn` files
2. **Stage 1:** Python compiler compiles `mapanare/self/*.mn` → native binary A
3. **Stage 2:** Binary A compiles `mapanare/self/*.mn` → native binary B
4. **Stage 3:** Binary B compiles `mapanare/self/*.mn` → native binary C

When Binary B and Binary C are byte-identical, the bootstrap reaches a fixed
point and the self-hosted compiler is verified.

## Files

Frozen copies of the v0.6.0 Python compiler modules:

### Core Pipeline
- `lexer.py` — Lark-based tokenizer
- `parser.py` — LALR parser + AST transformer
- `ast_nodes.py` — AST node dataclasses
- `semantic.py` — Type checking and scope analysis
- `types.py` — Type system (TypeKind enum, builtins, registries)
- `optimizer.py` — AST optimization passes (O0–O3)

### MIR Pipeline (new in v0.6.0)
- `mir.py` — MIR instruction definitions and data structures
- `mir_builder.py` — MIR builder (SSA temp generation, basic blocks)
- `lower.py` — AST → MIR lowering pass
- `mir_opt.py` — MIR-level optimizer
- `emit_llvm_mir.py` — MIR → LLVM IR emitter
- `emit_python_mir.py` — MIR → Python emitter

### Emitters (AST-direct, legacy)
- `emit_llvm.py` — AST → LLVM IR emitter via llvmlite
- `emit_python.py` — AST → Python transpiler

### Tools & Infrastructure
- `cli.py` — Command-line interface
- `diagnostics.py` — Colorized error output with source spans
- `linter.py` — Code quality checks (8 rules)
- `docgen.py` — Documentation generator
- `jit.py` — JIT compilation support
- `modules.py` — Module resolution and imports
- `targets.py` — Cross-compilation target triples
- `mapanare.lark` — LALR grammar definition

## Building from Bootstrap

```bash
cd bootstrap
make bootstrap    # Build self-hosted compiler from this snapshot
```
