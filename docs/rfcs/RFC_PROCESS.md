# RFC Process

This document defines when and how RFCs (Requests for Comments) are used in Mapanare.

---

## When an RFC Is Required

An RFC is required for any change that:

- **Modifies frozen syntax.** Any change to grammar productions that are stable per
  `docs/STABILITY.md`.
- **Modifies frozen semantics.** Any change to type checking rules, scoping, evaluation
  order, or pattern matching behavior.
- **Removes or changes a stable stdlib API.** Removing a public function, changing its
  signature, or altering its documented behavior.
- **Removes or changes a builtin function.** Changing the signature or behavior of any
  builtin listed in `docs/STABILITY.md`.
- **Removes a CLI command or flag.** Any command or flag documented as stable.
- **Adds new syntax.** New keywords, operators, or grammar productions (even if
  backwards-compatible) require an RFC to ensure design coherence.
- **Changes the type system.** New type kinds, changes to inference rules, or new
  type-level features.
- **Changes the memory model.** Modifications to arena lifecycle, ownership rules, or
  agent message passing semantics.

## When an RFC Is NOT Required

The following changes do not need an RFC:

- **Bug fixes.** Fixing compiler or runtime bugs, even if the fix changes observable
  behavior that contradicted the spec.
- **New stdlib modules.** Adding entirely new modules (e.g., `db/sql.mn`) that do not
  modify existing APIs.
- **New functions in existing stdlib modules.** Adding functions or types, provided
  existing signatures are unchanged.
- **Optimizer changes.** Adding, removing, or modifying MIR optimizer passes.
- **C runtime internals.** Changes to `runtime/native/` that do not affect language
  semantics.
- **Documentation.** Corrections, additions, or reorganization of docs.
- **Tooling improvements.** LSP, formatter, linter, test runner enhancements.
- **Performance improvements.** Faster compilation, faster generated code, lower memory
  usage.
- **New compilation targets.** Adding WASM, ARM64, or other targets.
- **CI and infrastructure.** Build system, packaging, release automation.
- **Diagnostic improvements.** Better error messages, new warning categories.

---

## RFC Numbering and Location

RFCs are stored in `docs/rfcs/` with the naming convention:

```
docs/rfcs/NNNN-short-title.md
```

Numbers are assigned sequentially (0001, 0002, ...). Use the next available number.

---

## RFC Template

Every RFC must include the following sections:

```markdown
# RFC NNNN: [Title]

**Author:** [Name]
**Date:** YYYY-MM-DD
**Status:** Draft | Under Review | Accepted | Rejected | Withdrawn | Superseded by NNNN

---

## Summary

[One paragraph. What is this RFC proposing?]

## Motivation

[Why is this change needed? What problem does it solve? What happens if we do nothing?
Include concrete examples of code or workflows that are currently painful.]

## Design

[The detailed design. Include:
- Syntax changes (grammar diffs if applicable)
- Semantic rules
- Type system implications
- How it interacts with existing features (agents, signals, streams, etc.)
- Error handling
- Edge cases]

### Examples

[Show complete, compilable code examples of the proposed feature or change.]

## Alternatives Considered

[What other designs were considered? Why were they rejected? This section must have
at least one alternative, even if it is "do nothing."]

## Migration

[How will existing code be affected? Include:
- Is existing code broken? If so, how common is the pattern?
- What does the deprecation/migration path look like?
- Can migration be automated?
- Link to migration guide template: `docs/MIGRATION_TEMPLATE.md`]

## Drawbacks

[Why might we NOT want to do this? Be honest about costs, complexity, and risks.]

## Unresolved Questions

[What aspects of the design are still open? These must be resolved before the RFC
is accepted.]
```

---

## Review Process

### 1. Draft

The author opens a pull request adding `docs/rfcs/NNNN-title.md` with status `Draft`.
The PR description links to the RFC and summarizes the proposal.

### 2. Discussion

Review happens on the pull request. Anyone can comment. The author is expected to
respond to feedback and update the RFC accordingly. Discussion should focus on:

- Does the motivation justify the change?
- Is the design sound and complete?
- Are alternatives adequately explored?
- Is the migration path reasonable?

### 3. Acceptance Criteria

An RFC is accepted when:

- The motivation is clear and justified.
- The design is complete -- no unresolved questions remain.
- Migration impact is understood and a path is documented.
- At least one maintainer approves the PR.
- No unaddressed blocking concerns remain open.

The RFC status is updated to `Accepted` and the PR is merged.

### 4. Rejection

An RFC may be rejected if:

- The motivation is insufficient.
- The design has fundamental flaws that cannot be resolved.
- The change conflicts with the language's design philosophy.
- The migration cost outweighs the benefit.

The RFC status is updated to `Rejected` with a summary of reasons. The PR is closed.

### 5. Implementation

Accepted RFCs are implemented in subsequent PRs. The implementation PR should reference
the RFC number. The RFC itself is not modified after acceptance (except to update status
to reflect implementation).

---

## Existing RFCs

| Number | Title | Status |
|--------|-------|--------|
| 0001 | Agent Syntax | Accepted |
| 0002 | Memory Management | Accepted |
| 0003 | Module Resolution | Accepted |
| 0004 | Traits | Accepted |
