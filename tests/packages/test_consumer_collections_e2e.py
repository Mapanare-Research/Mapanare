"""End-to-end test for the v5.44.0 Ps.5 consumer_collections example.

Validates that the staged consumer demo at
``examples/packages/consumer_collections/`` resolves the
``mn_collections`` package end-to-end:

* `mapanare.toml` parses
* `mapanare.lock` parses
* the staged `mn_modules/mn_collections-0.1.0/` is discovered
* `import mn_collections` from `main.mn` resolves to the staged
  package's main.mn
* the resolver records exactly one ImportRecord with
  (mn_collections, 0.1.0, mn_modules)

Falsifiability: deleting the staged `mn_modules/` directory or the
lockfile entry fails the discovery; renaming the import in main.mn
fails the resolution check.
"""

from __future__ import annotations

import os
from pathlib import Path

from mapanare.pkg_discovery import (
    build_resolver_for_source,
    discover_package_roots,
    find_project_dir,
)
from stdlib.pkg import load_lockfile, load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONSUMER_DIR = REPO_ROOT / "examples" / "packages" / "consumer_collections"


def test_consumer_dir_exists() -> None:
    assert CONSUMER_DIR.is_dir(), (
        f"consumer_collections example missing at {CONSUMER_DIR} — "
        f"v5.44.0 Ps.5 requires it"
    )


def test_consumer_manifest_parses() -> None:
    manifest = load_manifest(str(CONSUMER_DIR))
    assert manifest.name == "consumer_collections"
    assert manifest.version == "0.1.0"
    assert "mn_collections" in manifest.dependencies
    assert manifest.dependencies["mn_collections"].version == "0.1.0"


def test_consumer_lockfile_parses() -> None:
    lock = load_lockfile(str(CONSUMER_DIR))
    pkg_names = [p.name for p in lock.packages]
    assert "mn_collections" in pkg_names


def test_staged_mn_modules_discoverable() -> None:
    """The staged mn_modules/mn_collections-0.1.0/ is found by discovery."""
    roots = discover_package_roots(CONSUMER_DIR)
    assert len(roots) == 1
    assert roots[0].package_name == "mn_collections"
    assert roots[0].version == "0.1.0"
    assert roots[0].source == "mn_modules"
    assert roots[0].entry_module.name == "main.mn"


def test_consumer_main_imports_resolve() -> None:
    """`import mn_collections` from consumer/main.mn resolves to the
    staged package's main.mn."""
    main_mn = CONSUMER_DIR / "main.mn"
    resolver = build_resolver_for_source(str(main_mn))
    found = resolver.resolve_path(["mn_collections"], str(main_mn.parent))
    assert found is not None
    expected = (
        CONSUMER_DIR / "mn_modules" / "mn_collections-0.1.0" / "main.mn"
    )
    assert os.path.normpath(found) == os.path.normpath(str(expected))
    log = resolver.import_log()
    assert len(log) == 1
    assert log[0].package_name == "mn_collections"
    assert log[0].version == "0.1.0"
    assert log[0].source == "mn_modules"


def test_find_project_dir_finds_consumer() -> None:
    """Walking up from main.mn reaches the consumer project root."""
    main_mn = CONSUMER_DIR / "main.mn"
    found = find_project_dir(main_mn)
    assert found is not None
    assert found.resolve() == CONSUMER_DIR.resolve()


def test_consumer_main_parses() -> None:
    """The example's main.mn parses cleanly."""
    from mapanare.parser import parse

    main_mn = CONSUMER_DIR / "main.mn"
    source = main_mn.read_text(encoding="utf-8")
    ast = parse(source, filename=str(main_mn))
    # Spot-check: main.mn declares `import mn_collections` and `fn main`.
    from mapanare.ast_nodes import FnDef, ImportDef

    has_import = any(
        isinstance(d, ImportDef)
        and d.path == ["mn_collections"]
        for d in ast.definitions
    )
    has_main = any(
        isinstance(d, FnDef) and d.name == "main" for d in ast.definitions
    )
    assert has_import, "consumer main.mn must `import mn_collections`"
    assert has_main, "consumer main.mn must define `fn main`"


def test_consumer_legacy_examples_marked() -> None:
    """mn_http and mn_json have LEGACY.md (Ps.6)."""
    legacy_dirs = [
        REPO_ROOT / "examples" / "packages" / "mn_http",
        REPO_ROOT / "examples" / "packages" / "mn_json",
    ]
    for d in legacy_dirs:
        legacy_md = d / "LEGACY.md"
        assert legacy_md.is_file(), (
            f"{legacy_md} missing — v5.44.0 Ps.6 requires it because the "
            f"example uses extern \"Python\" which was removed at v4.29.0"
        )
        text = legacy_md.read_text(encoding="utf-8")
        assert "LEGACY" in text
        assert "extern" in text  # explains why it's legacy
