# `mapanare init` — Project Scaffolding

Bootstrap a runnable Mapanare project in one command.

```bash
mapanare init demo            # scaffolds ./demo/
cd demo && mapanare run main.mn
```

`mnc init` shells out to the same Python implementation; the
flags and behavior are identical.

## What it creates

`mapanare init <path>` copies every file under
`mapanare/templates/init/<template>/` (default: `default`) into
`<path>`, substituting `{{NAME}}` with the project name. The
default template ships:

```
demo/
├── main.mn          # fn main(): print("Hello from demo!")
├── mapanare.toml    # package manifest
├── .gitignore       # build artifacts, caches, IDE files
└── README.md        # build/run/test commands
```

All four files use the canonical post-v5.17 terse syntax.
`main.mn` parses + type-checks cleanly through `mapanare check`.

## Options

| Flag | Default | Effect |
|---|---|---|
| `<path>` | required | Directory to scaffold into. Created if missing. |
| `--name NAME` | basename of `<path>` | Project name; substituted into `{{NAME}}` placeholders. Must match `[A-Za-z_][A-Za-z0-9_-]*`. |

## Re-running on an existing directory

`init` is **non-destructive** on collisions. If a file already
exists at the destination it is left untouched; only missing files
are created. `mapanare.toml` is the exception — it is always
re-emitted from a fresh `MapanareManifest`, so re-running `init`
on a project with a corrupt or hand-edited manifest restores a
canonical baseline (other fields are reset to defaults).

## Templates

v5.18.0 ships one template: `default`. Templates are directory
trees under `mapanare/templates/init/`; the in-tree path is
discovered relative to the installed `stdlib/pkg.py` so it works
from a `pip install -e .` checkout, a wheel install, or a
PyInstaller bundle.

A future release (v5.18.x or v5.19.x) will add `--template`:

```bash
mapanare init webapp --template web-server   # planned
mapanare init bot    --template agent        # planned
```

## What's next

After `init`, you can:

```bash
mapanare check main.mn      # type-check
mapanare run main.mn        # run via Python bootstrap
mnc run main.mn             # run native (faster)
mapanare test .             # discover & run @test functions
```

See `docs/SPEC.md` for the language reference.
