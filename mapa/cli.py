"""Mapanare compiler CLI -- entry point for the mapa command."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

from mapa.emit_python import PythonEmitter
from mapa.optimizer import OptLevel, optimize
from mapa.parser import ParseError, parse
from mapa.semantic import SemanticErrors, check_or_raise
from mapa.targets import get_target, list_targets

__version__ = "0.1.0"


def _read_source(path: str) -> str:
    """Read an .mn source file, exiting on error."""
    if not os.path.isfile(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _parse_opt_level(args: argparse.Namespace) -> OptLevel:
    """Extract optimization level from parsed args."""
    return OptLevel(getattr(args, "opt_level", 2))


def _compile_source(source: str, filename: str, opt_level: OptLevel = OptLevel.O2) -> str:
    """Parse, check, optimize, and emit Python from Mapanare source. Returns Python code."""
    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)
    ast, stats = optimize(ast, opt_level)
    emitter = PythonEmitter()
    return emitter.emit(ast)


def _compile_to_llvm_ir(
    source: str, filename: str, opt_level: OptLevel = OptLevel.O2, target_name: str | None = None
) -> str:
    """Parse, check, optimize, and emit LLVM IR from Mapanare source."""
    from mapa.emit_llvm import LLVMEmitter

    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)
    ast, stats = optimize(ast, opt_level)
    target = get_target(target_name)
    emitter = LLVMEmitter(
        module_name=os.path.splitext(os.path.basename(filename))[0],
        target_triple=target.triple,
        data_layout=target.data_layout,
    )
    module = emitter.emit_program(ast)
    return str(module)


def cmd_compile(args: argparse.Namespace) -> None:
    """Compile an .mn source file to Python."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    try:
        python_code = _compile_source(source, args.source, opt_level=opt_level)
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticErrors as e:
        for err in e.errors:
            print(f"error: {err.filename}:{err.line}:{err.column}: {err.message}", file=sys.stderr)
        sys.exit(1)

    out_path = args.o or args.source.replace(".mn", ".py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(python_code)
    print(f"compiled {args.source} -> {out_path}")


def cmd_check(args: argparse.Namespace) -> None:
    """Type-check an .mn source file."""
    source = _read_source(args.source)
    try:
        ast = parse(source, filename=args.source)
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        check_or_raise(ast, filename=args.source)
    except SemanticErrors as e:
        for err in e.errors:
            print(f"error: {err.filename}:{err.line}:{err.column}: {err.message}", file=sys.stderr)
        sys.exit(1)

    print(f"check: {args.source} OK")


def cmd_run(args: argparse.Namespace) -> None:
    """Compile and run an .mn source file."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    try:
        python_code = _compile_source(source, args.source, opt_level=opt_level)
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticErrors as e:
        for err in e.errors:
            print(f"error: {err.filename}:{err.line}:{err.column}: {err.message}", file=sys.stderr)
        sys.exit(1)

    # Write to a temp file and run it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(python_code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
        sys.exit(result.returncode)
    finally:
        os.unlink(tmp_path)


def cmd_fmt(args: argparse.Namespace) -> None:
    """Format an .mn source file (normalize whitespace and indentation)."""
    source = _read_source(args.source)

    # Verify the file parses before formatting
    try:
        parse(source, filename=args.source)
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    formatted = _format_mapanare(source)

    with open(args.source, "w", encoding="utf-8") as f:
        f.write(formatted)
    print(f"formatted {args.source}")


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new Mapanare project with mapanare.toml."""
    from stdlib.pkg import init_project

    project_dir = args.path or "."
    name = args.name
    manifest = init_project(project_dir, name=name)
    print(f"initialized project '{manifest.name}' in {os.path.abspath(project_dir)}")


def cmd_install(args: argparse.Namespace) -> None:
    """Install a package from a git repository."""
    from stdlib.pkg import PackageError, install_package

    project_dir = "."
    try:
        locked = install_package(
            package_name=args.package,
            project_dir=project_dir,
            git_url=args.git,
            branch=args.branch,
        )
        print(f"installed {locked.name} @ {locked.commit[:8]}")
    except PackageError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_publish(args: argparse.Namespace) -> None:
    """Show publish stub documentation."""
    from stdlib.pkg import cmd_publish_stub

    print(cmd_publish_stub())


def cmd_jit(args: argparse.Namespace) -> None:
    """JIT-compile an .mn source file via LLVM and execute natively."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    try:
        llvm_ir = _compile_to_llvm_ir(source, args.source, opt_level=opt_level)
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticErrors as e:
        for err in e.errors:
            print(f"error: {err.filename}:{err.line}:{err.column}: {err.message}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    from mapa.jit import jit_compile_and_run

    bench = getattr(args, "bench", False)
    if bench:
        import time

        wall0 = time.perf_counter()
        cpu0 = time.process_time()
        jit_compile_and_run(llvm_ir, opt_level=opt_level.value)
        wall1 = time.perf_counter() - wall0
        cpu1 = time.process_time() - cpu0
        print("__BENCH_METRICS__")
        print(f"wall_time_s={round(wall1, 6)}")
        print(f"cpu_time_s={round(cpu1, 6)}")
        print(f"peak_memory_kb=0")
    else:
        jit_compile_and_run(llvm_ir, opt_level=opt_level.value)


def cmd_build(args: argparse.Namespace) -> None:
    """Compile an .mn source file to a native binary via LLVM."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    target_name: str | None = getattr(args, "target", None)
    try:
        llvm_ir = _compile_to_llvm_ir(
            source, args.source, opt_level=opt_level, target_name=target_name
        )
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticErrors as e:
        for err in e.errors:
            print(f"error: {err.filename}:{err.line}:{err.column}: {err.message}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    from mapa.jit import jit_compile_to_object

    obj_bytes = jit_compile_to_object(llvm_ir, opt_level=opt_level.value)

    # Write object file
    base = os.path.splitext(args.source)[0]
    obj_ext = ".obj" if os.name == "nt" else ".o"
    obj_path = args.o or (base + obj_ext)
    with open(obj_path, "wb") as f:
        f.write(obj_bytes)

    # Try to link into executable
    exe_ext = ".exe" if os.name == "nt" else ""
    exe_path = base + exe_ext

    # Try common linkers
    linked = False
    for linker_cmd in (
        ["clang", obj_path, "-o", exe_path],
        ["gcc", obj_path, "-o", exe_path],
        ["link.exe", f"/OUT:{exe_path}", obj_path, "msvcrt.lib", "legacy_stdio_definitions.lib"],
    ):
        import shutil

        if shutil.which(linker_cmd[0]):
            result = subprocess.run(linker_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                linked = True
                print(f"built {args.source} -> {exe_path}")
                break
            else:
                print(f"link warning ({linker_cmd[0]}): {result.stderr[:200]}", file=sys.stderr)

    if not linked:
        print(f"compiled {args.source} -> {obj_path} (object file)")
        print(
            "note: no linker found (install clang, gcc, or MSVC build tools to produce executables)"
        )


def cmd_emit_llvm(args: argparse.Namespace) -> None:
    """Emit LLVM IR for an .mn source file."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    target_name: str | None = getattr(args, "target", None)
    try:
        llvm_ir = _compile_to_llvm_ir(
            source, args.source, opt_level=opt_level, target_name=target_name
        )
    except ParseError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticErrors as e:
        for err in e.errors:
            print(
                f"error: {err.filename}:{err.line}:{err.column}: {err.message}",
                file=sys.stderr,
            )
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.o or args.source.replace(".mn", ".ll")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(llvm_ir)
    target = get_target(target_name)
    print(f"emitted {args.source} -> {out_path} (target: {target.triple})")


def cmd_targets(args: argparse.Namespace) -> None:
    """List all supported compilation targets."""
    print("Supported targets:\n")
    for name, desc in list_targets():
        print(f"  {name:<30s} {desc}")
    print()
    from mapa.targets import host_target_name

    print(f"Host target: {host_target_name()}")


def _format_mapanare(source: str) -> str:
    """Basic Mapanare source formatter.

    Normalizes:
    - Trailing whitespace on each line
    - Consistent indentation (4 spaces)
    - No more than 2 consecutive blank lines
    - Single trailing newline at end of file
    - Spaces around binary operators
    """
    lines = source.split("\n")
    result: list[str] = []
    consecutive_blank = 0

    for line in lines:
        # Strip trailing whitespace
        stripped = line.rstrip()

        if stripped == "":
            consecutive_blank += 1
            if consecutive_blank <= 2:
                result.append("")
            continue

        consecutive_blank = 0

        # Normalize leading whitespace: convert tabs to 4 spaces
        content = stripped.lstrip()
        leading = stripped[: len(stripped) - len(content)]
        # Replace tabs with 4 spaces
        leading = leading.replace("\t", "    ")
        result.append(leading + content)

    # Strip trailing blank lines, ensure single trailing newline
    while result and result[-1] == "":
        result.pop()
    result.append("")

    return "\n".join(result)


def _add_opt_level_args(parser: argparse.ArgumentParser) -> None:
    """Add -O0 through -O3 optimization level flags to a subcommand parser."""
    opt_group = parser.add_mutually_exclusive_group()
    opt_group.add_argument(
        "-O0",
        dest="opt_level",
        action="store_const",
        const=0,
        help="No optimization",
    )
    opt_group.add_argument(
        "-O1",
        dest="opt_level",
        action="store_const",
        const=1,
        help="Basic optimization (constant folding)",
    )
    opt_group.add_argument(
        "-O2",
        dest="opt_level",
        action="store_const",
        const=2,
        help="Standard optimization (default)",
    )
    opt_group.add_argument(
        "-O3",
        dest="opt_level",
        action="store_const",
        const=3,
        help="Aggressive optimization (includes stream fusion)",
    )
    parser.set_defaults(opt_level=2)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for mapa."""
    parser = argparse.ArgumentParser(
        prog="mapa",
        description="Mapanare compiler -- compile, check, run, and format .mn source files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mapa {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # compile
    p_compile = subparsers.add_parser("compile", help="Compile .mn source to Python")
    p_compile.add_argument("source", help="Path to .mn source file")
    p_compile.add_argument("-o", metavar="OUTPUT", help="Output file path", default=None)
    _add_opt_level_args(p_compile)
    p_compile.set_defaults(func=cmd_compile)

    # check
    p_check = subparsers.add_parser("check", help="Type-check .mn source")
    p_check.add_argument("source", help="Path to .mn source file")
    p_check.set_defaults(func=cmd_check)

    # run
    p_run = subparsers.add_parser("run", help="Compile and run .mn source")
    p_run.add_argument("source", help="Path to .mn source file")
    _add_opt_level_args(p_run)
    p_run.set_defaults(func=cmd_run)

    # fmt
    p_fmt = subparsers.add_parser("fmt", help="Format .mn source")
    p_fmt.add_argument("source", help="Path to .mn source file")
    p_fmt.set_defaults(func=cmd_fmt)

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new Mapanare project")
    p_init.add_argument("path", nargs="?", default=".", help="Project directory (default: .)")
    p_init.add_argument("--name", default=None, help="Project name (default: directory name)")
    p_init.set_defaults(func=cmd_init)

    # install
    p_install = subparsers.add_parser("install", help="Install an Mapanare package (git-based)")
    p_install.add_argument("package", help="Package name to install")
    p_install.add_argument("--git", default=None, help="Git repository URL")
    p_install.add_argument("--branch", default=None, help="Git branch (default: main)")
    p_install.set_defaults(func=cmd_install)

    # publish
    p_publish = subparsers.add_parser("publish", help="Publish package (not yet implemented)")
    p_publish.set_defaults(func=cmd_publish)

    # jit
    p_jit = subparsers.add_parser("jit", help="JIT-compile and run .mn source natively via LLVM")
    p_jit.add_argument("source", help="Path to .mn source file")
    p_jit.add_argument("--bench", action="store_true", help="Output benchmark metrics")
    _add_opt_level_args(p_jit)
    p_jit.set_defaults(func=cmd_jit)

    # build
    p_build = subparsers.add_parser("build", help="Compile .mn source to native binary")
    p_build.add_argument("source", help="Path to .mn source file")
    p_build.add_argument("-o", metavar="OUTPUT", help="Output file path", default=None)
    p_build.add_argument(
        "--target",
        metavar="TARGET",
        help="Target triple (e.g. x86_64-linux-gnu, x86_64-windows-msvc)",
        default=None,
    )
    _add_opt_level_args(p_build)
    p_build.set_defaults(func=cmd_build)

    # emit-llvm
    p_emit_llvm = subparsers.add_parser("emit-llvm", help="Emit LLVM IR for .mn source")
    p_emit_llvm.add_argument("source", help="Path to .mn source file")
    p_emit_llvm.add_argument("-o", metavar="OUTPUT", help="Output .ll file path", default=None)
    p_emit_llvm.add_argument(
        "--target",
        metavar="TARGET",
        help="Target triple (e.g. x86_64-linux-gnu, aarch64-apple-macos, x86_64-windows-msvc)",
        default=None,
    )
    _add_opt_level_args(p_emit_llvm)
    p_emit_llvm.set_defaults(func=cmd_emit_llvm)

    # targets
    p_targets = subparsers.add_parser("targets", help="List supported compilation targets")
    p_targets.set_defaults(func=cmd_targets)

    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
