# v4.113.0 — Reserved Keyword Audit (docket #10)

Cross-reference between:
- `mapanare/mapanare.lark:380-427` (Python bootstrap lexer, Lark
  terminals)
- `mapanare/self/lexer.mn:59-177` (self-hosted lexer,
  `is_keyword` + `keyword_token_type` functions)
- `docs/SPEC.md` §2.1.1 (new master list)

## Cross-reference procedure

1. Extract every `KW_*` terminal name from `mapanare.lark` and every
   string literal tested in `is_keyword`/`keyword_token_type`.
2. Normalise bilingual groups (e.g. `let|pon` → {let, pon}).
3. Diff the three sets. Empty diff ⇒ audit passes.

## Result (v4.113.0 snapshot)

All three sources agree on the following 42 identifiers.
Bilingual pairs are shown as `english / spanish`:

```
let / pon          agent           async          di
const              spawn           await          _
mut                sync
fn                 signal          true           Tensor
return / da        stream          false
pub                pipe            none / nada
self / yo          match           new
                   if / si         input
                   else / sino     output
                   for / cada      assert
                   while / mien    break / sal
                   in / en         continue / sigue
                   type / tipo
                   struct
                   enum
                   impl
                   trait / modo / way
                   import / usa
                   export
                   extern
```

## Discrepancies

None. Both lexers list the same 42 tokens (counting `trait`/`modo`/
`way` as 3 spellings of one keyword, etc. — the bilingual form count
is 51 surface spellings).

## `const` status

`const` is tokenized (`KW_CONST.2` at `mapanare.lark:380`;
`name == "const"` at `lexer.mn:62`) but has no grammar production:
every attempt to use it raises a parse error. Documented in §2.1 as
"parser-reserved; use module-level `let`." It was promoted to a
documented keyword (not a future-reserved entry in Appendix C) in
v4.113.0 so the SPEC matches reality.

## `async` / `await` status

Promoted from "soft-reserved" to real keywords in v4.68.0 (self-
hosted) / v4.72.0 (coroutine lowering). The stale "Soft-reserved"
line in §2.1's Bilingual Keywords section was removed in v4.113.0
and replaced with an explicit list of English-only hard keywords
pointing readers to §29 for coroutine semantics.

## Ongoing gate

The audit procedure is trivial; any reviewer can re-run it by
diffing the three sources. Changes that add or remove a keyword
must update all three together; a mismatch is a bootstrap-breaking
bug.
