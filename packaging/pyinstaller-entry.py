"""
Standalone entry point for PyInstaller-bundled Mapanare CLI.

Produces the `mapanare` binary — compile, run, check, build, and format .mn files.
"""


def main():
    from mapanare.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
