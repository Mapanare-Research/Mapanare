"""
Standalone entry point for PyInstaller-bundled Mapanare CLI.

Produces the `mapanare` binary — compile, run, check, build, and format .mn files.

v5.31.0 Bn.5: every PyInstaller-bundled binary is a release artifact, so flag
``MAPANARE_RELEASE=1`` before importing ``mapanare.cli``. ``_is_release_install``
uses this env var as the primary signal to suppress the dev-clone banner.
"""

import os


def main():
    os.environ.setdefault("MAPANARE_RELEASE", "1")
    from mapanare.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
