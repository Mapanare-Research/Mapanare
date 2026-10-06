# consumer_collections — v5.44.0 Ps.5 demo

A minimal consumer of the pure-`.mn` `mn_collections` package, demonstrating
the v5.44.0 package-aware import mechanism.

## Layout

```
consumer_collections/
├── mapanare.toml      # declares mn_collections = "0.1.0"
├── mapanare.lock      # pins the resolved version + integrity
├── main.mn            # imports + uses mn_collections
└── mn_modules/
    └── mn_collections-0.1.0/
        ├── mapanare.toml
        └── main.mn    # the package's source
```

The pre-staged `mn_modules/` directory is what `mnc install` would
materialize from a real registry / git source. It is checked in for this
demo so the example runs out-of-the-box without touching the network.

## What this proves

1. `import mn_collections` resolves through the project's installed
   packages (`mn_modules/<name>-<version>/`), not through manual
   `--stdlib-path` hacks.
2. The lockfile-keyed discovery picks the exact version pinned in
   `mapanare.lock` (Ps.1's lockfile-authoritative contract).
3. `mnc build --verbose` and `mnc build --diag-json out.json` surface
   the resolved package list (Ps.4).

## Dev loop

```bash
cd examples/packages/consumer_collections
mnc run main.mn
mnc build main.mn --verbose             # see the [package] line
mnc build main.mn --diag-json /tmp/d.json
```

Expected `--verbose` output on stderr:

```
[package] mn_collections@0.1.0 from mn_modules
```

Expected `--diag-json` payload:

```json
{
  "schema_version": 1,
  "packages": [
    {
      "name": "mn_collections",
      "import_name": "mn_collections",
      "version": "0.1.0",
      "source": "mn_modules",
      "integrity": "",
      "imports": [{"import_path": ["mn_collections"], "resolved": "..."}]
    }
  ]
}
```

## Why this is the blessed example

`mn_collections` ships pure `.mn`: no `extern "C"`, no `extern "Python"`,
no native runtime ABI requirements. Pure packages are the only class
that can move out of the bundled stdlib repo today (see
`docs/guides/stdlib-packaging.md` for the bundled / pure / runtime-bound
classification).

Counter-examples:

- `examples/packages/mn_http/` — uses `extern "Python"` (legacy
  v0.x interop, removed in v4.29.0). See `LEGACY.md` in that dir.
- `examples/packages/mn_json/` — same story; see its `LEGACY.md`.
- `stdlib/net/http.mn`, `stdlib/time.mn`, `stdlib/sql/sqlite.mn`,
  `stdlib/crypto.mn` — all runtime-bound (use `extern "C"` against
  `__mn_*` runtime symbols). These stay bundled until packages can
  declare native-ABI dependencies in `mapanare.toml` (a v6.0+ design
  surface, deliberately deferred from v5.44.0).
