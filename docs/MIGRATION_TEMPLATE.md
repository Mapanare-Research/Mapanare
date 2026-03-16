# Migration Guide Template

Use this template when writing migration guides for breaking changes. Save completed
guides to `docs/migrations/NNNN-short-title.md` where `NNNN` matches the RFC number
(if applicable).

---

## Template

```markdown
# Migrating from vX.Y to vX.Z: [Short Description]

**Affects:** vX.Y.0 through vX.Y.* (all patch releases)
**Deprecated in:** vX.Y.0
**Removed in:** vX.Z.0
**RFC:** [NNNN-title](../rfcs/NNNN-title.md) (if applicable)

---

## What Changed

[One or two paragraphs explaining what changed and why. Focus on the motivation --
why was this change necessary? Link to the RFC for full design rationale.]

---

## How to Update Your Code

### Before (vX.Y)

\```mn
// Old usage that is now deprecated or removed
let result = old_function(x, y)
\```

### After (vX.Z)

\```mn
// New usage
let result = new_function(x, y)
\```

[Add as many before/after pairs as needed to cover different usage patterns.]

### Pattern: [Name of common pattern]

**Before:**
\```mn
// ...
\```

**After:**
\```mn
// ...
\```

---

## Automated Migration

[Describe any automated tooling available. If none, state that explicitly.]

- **Compiler warnings:** The compiler emits `warning[MN-DNNNN]` with a suggested fix
  starting in vX.Y.0.
- **`mapanare fix`:** Run `mapanare fix --migration NNNN` to automatically rewrite
  affected code. (If this command exists for this migration.)
- **Manual only:** No automated migration is available. Follow the examples above.

### Running the automated fix

\```bash
# Dry run -- shows what would change without modifying files
mapanare fix --migration NNNN --dry-run

# Apply the fix
mapanare fix --migration NNNN
\```

---

## Timeline

| Date       | Version | Action                                    |
|------------|---------|-------------------------------------------|
| YYYY-MM-DD | vX.Y.0  | Feature deprecated, compiler warns        |
| YYYY-MM-DD | vX.Z.0  | Feature removed, old code fails to compile|

---

## Troubleshooting

### "error[MN-ENNNN]: ..."

This error means [explanation]. To fix it, [specific steps].

### Other issues

If you encounter problems not covered here, file an issue at
https://github.com/Mapanare-Research/Mapanare/issues with the label `migration`.
```

---

## Guidelines for Authors

- Keep migration guides short and actionable. Link to the RFC for design discussion.
- Every before/after example must compile. Test them before publishing.
- If multiple independent changes ship in the same release, write separate migration
  guides for each.
- File the migration guide in the same PR that implements the removal.
