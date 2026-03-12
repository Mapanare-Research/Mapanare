# Bootstrap Compiler (v0.5.0 Snapshot)

This directory contains a frozen copy of the v0.5.0 Python-based Mapanare
compiler. It is preserved as a reference and used to bootstrap the self-hosted
compiler written in Mapanare itself (see `mapanare/self/*.mn`).

**Snapshot date:** v0.6.0 development (Phase 5)
**Source:** `mapanare/*.py` and `mapanare/mapanare.lark`

## Bootstrap Chain

1. **Stage 0 (this directory):** Python compiler compiles `.mn` files
2. **Stage 1:** Python compiler compiles `mapanare/self/*.mn` → LLVM IR
3. **Stage 2:** Stage 1 output compiles `mapanare/self/*.mn` → identical LLVM IR

When Stage 1 and Stage 2 produce identical output, the compiler is a fixed
point and the bootstrap is complete.

## Files

Frozen copies of the original Python compiler modules:

- `lexer.py` — Lark-based tokenizer
- `parser.py` — LALR parser + AST transformer
- `ast_nodes.py` — AST node dataclasses
- `semantic.py` — Type checking and scope analysis
- `emit_llvm.py` — LLVM IR emitter via llvmlite
- `emit_python.py` — Python transpiler
- `optimizer.py` — AST optimization passes
- `cli.py` — Command-line interface
- `mapanare.lark` — Grammar definition
