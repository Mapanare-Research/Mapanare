# LEGACY — mn_json

This example does **not compile** on `mnc` v0.7.0+ because it uses
`extern "Python" fn`, which was removed at v4.29.0. The example was
authored against the v0.x Python-interop bridge for `json.loads` /
`json.dumps`.

## Don't model new packages on this

JSON support lives in `stdlib/encoding/json.mn` (v5.36.0+ Js.\*),
backed by Mapanare-native parser + serializer. There's no remaining
case for routing JSON through Python interop.

## What to model new packages on instead

`examples/packages/mn_collections/` — pure `.mn`, no extern blocks,
the blessed exemplar for v5.44.0 Ps.\* package work.

`examples/packages/consumer_collections/` — the package-aware
consumer demo showing `mapanare.toml + mapanare.lock + mn_modules/`
end-to-end.

## Why this dir still exists

The package metadata + the broken source have value as a frozen
record of the v0.x Python-interop shape. They show what **not** to do
when porting old packages forward.
