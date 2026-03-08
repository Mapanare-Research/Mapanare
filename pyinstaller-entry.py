"""
Standalone entry point for PyInstaller-bundled Mapanare CLI.

Produces the `mapa` binary — compile, run, check, build, and format .mn files.
"""


def main():
    from mapa.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
