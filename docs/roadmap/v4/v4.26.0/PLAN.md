# Mapanare v4.26.0 — `const` Keyword + Roadmap Consolidation

> Compile-time constants land as a real language feature, usable in tensor
> shape annotations. The roadmap, README, CHANGELOG, and master prompt are
> reconciled with reality after v4.18.0–v4.25.0 outpaced the original plan.

**Status:** PLANNED
**Breaking:** No
**Prerequisite:** v4.25.0

---

## The Problem

After v4.25.0, the project state had drifted from the docs:

- Top-level `ROADMAP.md` "Where We Are" section still said v4.0.0, even though
  v4.1.0 through v4.25.0 had all shipped
- The "What's Next" section in `ROADMAP.md` still listed v4.1.0–v4.7.0 as
  upcoming, despite all of them being done
- The `MASTER_PROMPT.md` arc only covered v4.22.0 → v4.25.0
- `CLAUDE.md` was pinned to v4.25.0 with no v4.26.0 entry
- The `const` keyword existed as a synonym for module-level `let` (v4.18.0)
  but was never properly wired through semantic analysis or documented as a
  language feature
- Tensor shape annotations from v4.25.0 cannot reference symbolic dimensions —
  shapes have to be literal integers (`Tensor<Float, [3, 3]>`) instead of
  named constants (`const N: Int = 3; Tensor<Float, [N, N]>`)

This version closes those gaps.

---

## Phase 1: `const` keyword as a real feature

- [ ] Audit current `const` parsing in `mapanare.lark` — confirm whether it
      maps directly to `let` or has its own AST node
- [ ] If `const` is just `let`: introduce `ConstDef` AST node distinct from
      `LetDef`, store immutability flag
- [ ] Semantic checker rejects assignment to `const` names (even module-level)
- [ ] Constant folding pass treats `const`-bound names as compile-time literals
      when the RHS is a literal expression
- [ ] Self-hosted parser/AST/lowerer mirror the change in `mapanare/self/`

## Phase 2: `const` in tensor shape annotations

- [ ] Allow identifier references inside `Tensor<T, [...]>` shape lists in the
      grammar
- [ ] Semantic resolver looks up identifiers in const scope, errors if the name
      isn't a `const Int`
- [ ] Constant folder substitutes the literal value before shape comparison
- [ ] Add test: `const N: Int = 3; let m: Tensor<Float, [N, N]>` compiles and
      `[N, N]` matches `[3, 3]` for shape checking

## Phase 3: Tests

- [ ] `tests/parser/test_const.py` — `const` parses, distinct from `let`
- [ ] `tests/semantic/test_const.py` — assignment to `const` is an error,
      `const` propagates through expressions, `const` in tensor shapes resolves
- [ ] `tests/golden/47_const.mn` — golden test exercising module-level `const`
      and `const`-shaped tensor

## Phase 4: Roadmap consolidation

- [x] Bump `VERSION` to 4.26.0
- [x] Add v4.26.0 entry to `CHANGELOG.md`
- [x] Update `README.md` and `docs/README.es.md` version badge
- [x] Refresh `docs/roadmap/ROADMAP.md` "Where We Are" section to reflect
      v4.26.0 (not v4.0.0)
- [x] Extend `docs/roadmap/ROADMAP.md` release history table with v4.7.1
      through v4.26.0 rows
- [x] Reframe ROADMAP.md "What's Next" — original v4.1–v4.7 sequence is done,
      next targets are v5.x growth features
- [x] Update `docs/roadmap/v4/MASTER_PROMPT.md` arc to v4.22.0 → v4.26.0
- [x] Update `docs/roadmap/v4/README.md` versions table with v4.21.0–v4.26.0
- [x] Update `CLAUDE.md` current version to v4.26.0
- [x] Update `.reviews/prompt.md` to target v4.26.0 (next code review pass)

---

## Exit Criteria

| Check | Required |
|-------|----------|
| `const NAME: Type = value` parses at module level | YES |
| Assignment to `const` is a compile error | YES |
| `const` Int usable in tensor shape annotation | YES |
| 47/47+ golden | YES |
| 11/11 stage2 | YES |
| black/ruff/mypy clean | YES |
| `VERSION` = `4.26.0` | YES (done) |
| Roadmap docs reflect v4.26.0 as current | YES (done) |
| `.reviews/prompt.md` retargeted to v4.26.0 | YES (done) |
