"""Mapanare compiler CLI -- entry point for the mapanare command."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

from mapanare.diagnostics import (
    Diagnostic,
    Label,
    Severity,
    format_diagnostic,
    format_summary,
)
from mapanare.emit_python import PythonEmitter
from mapanare.modules import ModuleResolver
from mapanare.optimizer import OptLevel, optimize
from mapanare.parser import ParseError, parse, parse_recovering
from mapanare.semantic import SemanticErrors, check_or_raise
from mapanare.targets import get_target, list_targets

try:
    from importlib.metadata import version as _pkg_version

    __version__ = _pkg_version("mapanare")
except Exception:
    __version__ = "0.0.0"


def _read_source(path: str) -> str:
    """Read an .mn source file, exiting on error."""
    if not os.path.isfile(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _emit_parse_error(e: ParseError, source: str, filename: str) -> None:
    """Print a single ParseError as a colorized diagnostic."""
    from mapanare.ast_nodes import Span

    span = Span(line=e.line, column=e.column, end_line=e.line, end_column=e.column + 1)
    diag = Diagnostic(
        severity=Severity.ERROR,
        message=e.message,
        filename=filename,
        labels=[Label(span=span, primary=True)],
    )
    print(format_diagnostic(diag, source), file=sys.stderr)


def _emit_semantic_errors(e: SemanticErrors, source: str) -> None:
    """Print semantic errors as colorized diagnostics."""
    from mapanare.ast_nodes import Span

    diagnostics: list[Diagnostic] = []
    for err in e.errors:
        span = Span(line=err.line, column=err.column, end_line=err.line, end_column=err.column + 1)
        diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message=err.message,
                filename=err.filename,
                labels=[Label(span=span, primary=True)],
            )
        )
    for diag in diagnostics:
        print(format_diagnostic(diag, source), file=sys.stderr)
    summary = format_summary(diagnostics)
    if summary:
        print(summary, file=sys.stderr)


def _parse_opt_level(args: argparse.Namespace) -> OptLevel:
    """Extract optimization level from parsed args."""
    return OptLevel(getattr(args, "opt_level", 2))


def _compile_source(
    source: str,
    filename: str,
    opt_level: OptLevel = OptLevel.O2,
    resolver: ModuleResolver | None = None,
    python_path: list[str] | None = None,
) -> str:
    """Parse, check, optimize, and emit Python from Mapanare source. Returns Python code."""
    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename, resolver=resolver)
    ast, stats = optimize(ast, opt_level)
    emitter = PythonEmitter(python_path=python_path)
    return emitter.emit(ast)


def _compile_to_llvm_ir(
    source: str,
    filename: str,
    opt_level: OptLevel = OptLevel.O2,
    target_name: str | None = None,
    resolver: ModuleResolver | None = None,
) -> str:
    """Parse, check, optimize, and emit LLVM IR from Mapanare source."""
    from mapanare.emit_llvm import LLVMEmitter

    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename, resolver=resolver)
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
    python_path: list[str] = getattr(args, "python_path", None) or []
    resolver = ModuleResolver()
    try:
        python_code = _compile_source(
            source, args.source, opt_level=opt_level, resolver=resolver, python_path=python_path
        )
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)

    out_path = args.o or args.source.replace(".mn", ".py")
    out_dir = os.path.dirname(os.path.abspath(out_path))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(python_code)
    print(f"compiled {args.source} -> {out_path}")

    # Also compile any resolved imported modules
    _compile_resolved_modules(resolver, opt_level, out_dir)


def _compile_resolved_modules(resolver: ModuleResolver, opt_level: OptLevel, out_dir: str) -> None:
    """Compile all resolved imported modules to Python in the output directory."""
    for filepath, module in resolver.all_modules():
        mod_name = os.path.splitext(os.path.basename(filepath))[0]
        mod_out = os.path.join(out_dir, mod_name + ".py")
        if os.path.abspath(mod_out) == os.path.abspath(filepath.replace(".mn", ".py")):
            # Already compiled as the main file
            continue
        ast, _ = optimize(module.program, opt_level)
        emitter = PythonEmitter()
        code = emitter.emit(ast)
        with open(mod_out, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  compiled module {mod_name} -> {mod_out}")


def cmd_check(args: argparse.Namespace) -> None:
    """Type-check an .mn source file with error recovery."""
    source = _read_source(args.source)
    resolver = ModuleResolver()

    # Parse with recovery to collect multiple parse errors
    ast, parse_errors = parse_recovering(source, filename=args.source)

    all_diagnostics: list[Diagnostic] = []

    # Convert parse errors to diagnostics
    for pe in parse_errors:
        from mapanare.ast_nodes import Span

        span = Span(line=pe.line, column=pe.column, end_line=pe.line, end_column=pe.column + 1)
        all_diagnostics.append(
            Diagnostic(
                severity=Severity.ERROR,
                message=pe.message,
                filename=pe.filename,
                labels=[Label(span=span, primary=True)],
            )
        )

    # Run semantic analysis even if there were parse errors (on partial AST)
    if ast.definitions:
        from mapanare.semantic import check

        sem_errors = check(ast, filename=args.source, resolver=resolver)
        for err in sem_errors:
            from mapanare.ast_nodes import Span

            span = Span(
                line=err.line, column=err.column, end_line=err.line, end_column=err.column + 1
            )
            all_diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    message=err.message,
                    filename=err.filename,
                    labels=[Label(span=span, primary=True)],
                )
            )

    if all_diagnostics:
        for diag in all_diagnostics:
            print(format_diagnostic(diag, source), file=sys.stderr)
        summary = format_summary(all_diagnostics)
        if summary:
            print(summary, file=sys.stderr)
        sys.exit(1)

    print(f"check: {args.source} OK")


def cmd_run(args: argparse.Namespace) -> None:
    """Compile and run an .mn source file."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    python_path: list[str] = getattr(args, "python_path", None) or []
    resolver = ModuleResolver()
    try:
        python_code = _compile_source(
            source, args.source, opt_level=opt_level, resolver=resolver, python_path=python_path
        )
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)

    # When frozen (PyInstaller), sys.executable points to the mapanare binary,
    # not a Python interpreter.  Fall back to exec() in that case.
    if getattr(sys, "frozen", False):

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(python_code)
            tmp_path = tmp.name
        try:
            code = compile(python_code, tmp_path, "exec")
            exec(code, {"__name__": "__main__", "__file__": tmp_path})
        except SystemExit as exc:
            sys.exit(exc.code)
        except Exception as exc:
            print(f"runtime error: {exc}", file=sys.stderr)
            sys.exit(1)
        finally:
            os.unlink(tmp_path)
    else:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
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


def cmd_repl(args: argparse.Namespace) -> None:
    """Start an interactive Mapanare REPL."""
    opt_level = _parse_opt_level(args)
    namespace: dict[str, object] = {"__name__": "__repl__"}
    # Accumulated definitions to re-emit with each evaluation
    definitions: list[str] = []

    print(f"Mapanare {__version__} REPL — type 'exit' or Ctrl+D to quit")

    while True:
        try:
            line = input("mn> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        text = line.strip()
        if not text:
            continue
        if text in ("exit", "quit"):
            break

        # Multi-line: collect until braces balance
        brace_depth = text.count("{") - text.count("}")
        while brace_depth > 0:
            try:
                continuation = input("... ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            text += "\n" + continuation
            brace_depth += continuation.count("{") - continuation.count("}")

        # Try compiling as a top-level definition or statement
        try:
            python_code = _compile_source(text, "<repl>", opt_level=opt_level)
        except ParseError as e:
            print(f"parse error: {e}")
            continue
        except SemanticErrors as e:
            for err in e.errors:
                print(f"error: {err.message}")
            continue

        # Track function/struct/enum definitions for persistence
        is_def = text.lstrip().startswith(("fn ", "pub fn ", "struct ", "enum ", "agent ", "pipe "))
        if is_def:
            definitions.append(text)

        try:
            code = compile(python_code, "<repl>", "exec")
            exec(code, namespace)
        except SystemExit:
            break
        except Exception as exc:
            print(f"runtime error: {exc}")


def cmd_fmt(args: argparse.Namespace) -> None:
    """Format an .mn source file (normalize whitespace and indentation)."""
    source = _read_source(args.source)

    # Verify the file parses before formatting
    try:
        parse(source, filename=args.source)
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
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
    """Publish a package to the Mapanare registry."""
    from stdlib.pkg import (
        ManifestError,
        PackageError,
        _save_token,
        bump_version,
        load_manifest,
        publish_package,
    )

    project_dir = getattr(args, "path", ".")
    token = getattr(args, "token", None)

    # If --token provided, save it for future use
    if token:
        _save_token(token)
        print("token saved to ~/.mapanare/token")

    # Auto-bump version (patch by default, skip with --no-bump)
    bump_type = getattr(args, "bump", "patch")
    if bump_type and bump_type != "none":
        try:
            old_ver = load_manifest(project_dir).version
            new_ver = bump_version(project_dir, bump_type)
            print(f"version: {old_ver} -> {new_ver}")
        except ManifestError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        result = publish_package(project_dir, token=token)
        print(f"published {result['name']}@{result['version']}")
        print(f"  checksum: {result['checksum']}")
    except PackageError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_bump(args: argparse.Namespace) -> None:
    """Bump the project version in mapanare.toml."""
    from stdlib.pkg import ManifestError, bump_version, load_manifest

    project_dir = getattr(args, "path", ".")
    bump_type = getattr(args, "bump_type", None)

    try:
        manifest = load_manifest(project_dir)
        if bump_type is None:
            print(manifest.version)
            return
        old_version = manifest.version
        new_version = bump_version(project_dir, bump_type)
        print(f"{old_version} -> {new_version}")
    except ManifestError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args: argparse.Namespace) -> None:
    """Search the Mapanare package registry."""
    from stdlib.pkg import PackageError, search_packages

    query = getattr(args, "query", "")
    keyword = getattr(args, "keyword", "")

    try:
        result = search_packages(query=query, keyword=keyword)
    except PackageError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    packages = result.get("packages", [])
    total = result.get("total", 0)

    if not packages:
        print("no packages found")
        return

    print(f"found {total} package(s):\n")
    for pkg in packages:
        name = pkg.get("name", "?")
        version = pkg.get("latest_version", "?")
        desc = pkg.get("description", "")
        keywords = pkg.get("keywords", [])

        print(f"  {name} ({version})")
        if desc:
            print(f"    {desc}")
        if keywords:
            print(f"    keywords: {', '.join(keywords)}")
        print()


def cmd_login(args: argparse.Namespace) -> None:
    """Authenticate with the Mapanare package registry via GitHub OAuth."""
    import json
    import secrets
    import time
    import urllib.error
    import urllib.request
    import webbrowser

    from stdlib.pkg import REGISTRY_URL, _save_token

    session_id = secrets.token_urlsafe(32)
    login_url = f"{REGISTRY_URL}/auth/github?session={session_id}"

    print("opening browser for GitHub authentication...")
    print(f"  {login_url}")
    print()

    try:
        webbrowser.open(login_url)
    except Exception:
        print("could not open browser automatically.")
        print(f"open this URL manually: {login_url}")

    print("waiting for authentication", end="", flush=True)

    poll_url = f"{REGISTRY_URL}/auth/poll?session={session_id}"
    for _ in range(120):  # Poll for up to 2 minutes
        time.sleep(1)
        print(".", end="", flush=True)
        try:
            req = urllib.request.Request(poll_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ready":
                    token = data["token"]
                    username = data.get("username", "user")
                    _save_token(token)
                    print(f"\n\nlogged in as {username}")
                    print("token saved to ~/.mapanare/token")
                    return
        except (urllib.error.HTTPError, urllib.error.URLError):
            pass

    print("\n\ntimed out waiting for authentication.")
    print("try again with: mapanare login")
    sys.exit(1)


def cmd_jit(args: argparse.Namespace) -> None:
    """JIT-compile an .mn source file via LLVM and execute natively."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    resolver = ModuleResolver()
    try:
        llvm_ir = _compile_to_llvm_ir(source, args.source, opt_level=opt_level, resolver=resolver)
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    from mapanare.jit import jit_compile_and_run

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
        print("peak_memory_kb=0")
    else:
        jit_compile_and_run(llvm_ir, opt_level=opt_level.value)


def cmd_build(args: argparse.Namespace) -> None:
    """Compile an .mn source file to a native binary via LLVM."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    target_name: str | None = getattr(args, "target", None)
    resolver = ModuleResolver()
    try:
        llvm_ir = _compile_to_llvm_ir(
            source, args.source, opt_level=opt_level, target_name=target_name, resolver=resolver
        )
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    from mapanare.jit import jit_compile_to_object

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

    # Collect --link-lib flags as -l<lib> / <lib>.lib for linker
    link_libs: list[str] = getattr(args, "link_lib", None) or []

    # Try common linkers
    linked = False
    link_flags_unix = [f"-l{lib}" for lib in link_libs]
    link_flags_msvc = [f"{lib}.lib" for lib in link_libs]
    for linker_cmd in (
        ["clang", obj_path, "-o", exe_path] + link_flags_unix,
        ["gcc", obj_path, "-o", exe_path] + link_flags_unix,
        [
            "link.exe",
            f"/OUT:{exe_path}",
            obj_path,
            "msvcrt.lib",
            "legacy_stdio_definitions.lib",
        ]
        + link_flags_msvc,
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
    resolver = ModuleResolver()
    try:
        llvm_ir = _compile_to_llvm_ir(
            source, args.source, opt_level=opt_level, target_name=target_name, resolver=resolver
        )
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.o or args.source.replace(".mn", ".ll")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(llvm_ir)
    target = get_target(target_name)
    print(f"emitted {args.source} -> {out_path} (target: {target.triple})")


def cmd_emit_mir(args: argparse.Namespace) -> None:
    """Emit MIR (Mid-level IR) for an .mn source file."""
    from mapanare.mir import pretty_print_module as mir_pretty_print
    from mapanare.mir_builder import build_mir

    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    resolver = ModuleResolver()
    try:
        ast = parse(source, filename=args.source)
        check_or_raise(ast, filename=args.source, resolver=resolver)
        ast, _ = optimize(ast, opt_level)
        mir_module = build_mir(ast, module_name=os.path.splitext(os.path.basename(args.source))[0])
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)

    output = mir_pretty_print(mir_module)
    out_path = args.o
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"emitted {args.source} -> {out_path} (MIR)")
    else:
        print(output, end="")


def cmd_lint(args: argparse.Namespace) -> None:
    """Lint an .mn source file for code quality issues."""
    source = _read_source(args.source)

    # Parse (abort on parse error)
    try:
        ast = parse(source, filename=args.source)
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)

    # Semantic check (abort on type errors)
    try:
        check_or_raise(ast, filename=args.source)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)

    # Lint
    if args.fix:
        from mapanare.linter import lint_and_fix

        diagnostics, fixed_source = lint_and_fix(source, ast, filename=args.source)
        if fixed_source != source:
            with open(args.source, "w", encoding="utf-8") as f:
                f.write(fixed_source)
            fixed_count = sum(
                1 for d in diagnostics if "[W002]" in d.message or "[W005]" in d.message
            )
            print(f"fixed {fixed_count} issue(s) in {args.source}")
    else:
        from mapanare.linter import lint

        diagnostics = lint(ast, filename=args.source)

    if diagnostics:
        for diag in diagnostics:
            print(format_diagnostic(diag, source), file=sys.stderr)
        summary = format_summary(diagnostics)
        if summary:
            print(summary, file=sys.stderr)
        sys.exit(0)  # Lint warnings are not fatal
    else:
        print(f"lint: {args.source} OK — no warnings")


def cmd_doc(args: argparse.Namespace) -> None:
    """Generate HTML documentation from doc comments in .mn source files."""
    source = _read_source(args.source)
    try:
        ast = parse(source, filename=args.source)
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)

    from mapanare.docgen import extract_doc_items, generate_html

    module_name = os.path.splitext(os.path.basename(args.source))[0]
    items = extract_doc_items(ast)
    html = generate_html(items, module_name=module_name)

    out_path = args.o or args.source.replace(".mn", ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"doc: {args.source} -> {out_path} ({len(items)} items)")


def cmd_targets(args: argparse.Namespace) -> None:
    """List all supported compilation targets."""
    print("Supported targets:\n")
    for name, desc in list_targets():
        print(f"  {name:<30s} {desc}")
    print()
    from mapanare.targets import host_target_name

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
    """Build the argument parser for mapanare."""
    parser = argparse.ArgumentParser(
        prog="mapanare",
        description="Mapanare compiler -- compile, check, run, and format .mn source files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"mapanare {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # compile
    p_compile = subparsers.add_parser("compile", help="Compile .mn source to Python")
    p_compile.add_argument("source", help="Path to .mn source file")
    p_compile.add_argument("-o", metavar="OUTPUT", help="Output file path", default=None)
    p_compile.add_argument(
        "--python-path",
        metavar="DIR",
        action="append",
        help='Add directory to Python module search path (for extern "Python" interop)',
    )
    _add_opt_level_args(p_compile)
    p_compile.set_defaults(func=cmd_compile)

    # check
    p_check = subparsers.add_parser("check", help="Type-check .mn source")
    p_check.add_argument("source", help="Path to .mn source file")
    p_check.set_defaults(func=cmd_check)

    # run
    p_run = subparsers.add_parser("run", help="Compile and run .mn source")
    p_run.add_argument("source", help="Path to .mn source file")
    p_run.add_argument(
        "--python-path",
        metavar="DIR",
        action="append",
        help='Add directory to Python module search path (for extern "Python" interop)',
    )
    _add_opt_level_args(p_run)
    p_run.set_defaults(func=cmd_run)

    # repl
    p_repl = subparsers.add_parser("repl", help="Start interactive REPL")
    _add_opt_level_args(p_repl)
    p_repl.set_defaults(func=cmd_repl)

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
    p_publish = subparsers.add_parser("publish", help="Publish package to the Mapanare registry")
    p_publish.add_argument("path", nargs="?", default=".", help="Project directory (default: .)")
    p_publish.add_argument("--token", default=None, help="API token (saved to ~/.mapanare/token)")
    bump_group = p_publish.add_mutually_exclusive_group()
    bump_group.add_argument(
        "--patch",
        dest="bump",
        action="store_const",
        const="patch",
        help="Bump patch version (default)",
    )
    bump_group.add_argument(
        "--minor",
        dest="bump",
        action="store_const",
        const="minor",
        help="Bump minor version (0.1.0 -> 0.2.0)",
    )
    bump_group.add_argument(
        "--major",
        dest="bump",
        action="store_const",
        const="major",
        help="Bump major version (0.1.0 -> 1.0.0)",
    )
    bump_group.add_argument(
        "--no-bump",
        dest="bump",
        action="store_const",
        const="none",
        help="Publish without bumping version",
    )
    p_publish.set_defaults(func=cmd_publish, bump="patch")

    # version (bump)
    p_bump = subparsers.add_parser(
        "version",
        help="Show or bump the project version (major, minor, patch, or explicit)",
    )
    p_bump.add_argument(
        "bump_type",
        nargs="?",
        default=None,
        help="Bump type: major, minor, patch, or an explicit version (e.g. 1.2.3)",
    )
    p_bump.add_argument("--path", default=".", help="Project directory (default: .)")
    p_bump.set_defaults(func=cmd_bump)

    # search
    p_search = subparsers.add_parser("search", help="Search the Mapanare package registry")
    p_search.add_argument("query", nargs="?", default="", help="Search query")
    p_search.add_argument("--keyword", default="", help="Filter by keyword")
    p_search.set_defaults(func=cmd_search)

    # login
    p_login = subparsers.add_parser("login", help="Authenticate with the Mapanare package registry")
    p_login.set_defaults(func=cmd_login)

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
    p_build.add_argument(
        "--link-lib",
        metavar="LIB",
        action="append",
        help="Link against a C library (e.g. --link-lib m for libm)",
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

    # emit-mir
    p_emit_mir = subparsers.add_parser("emit-mir", help="Emit MIR (mid-level IR) for .mn source")
    p_emit_mir.add_argument("source", help="Path to .mn source file")
    p_emit_mir.add_argument("-o", metavar="OUTPUT", help="Output file path", default=None)
    _add_opt_level_args(p_emit_mir)
    p_emit_mir.set_defaults(func=cmd_emit_mir)

    # lint
    p_lint = subparsers.add_parser("lint", help="Lint .mn source for code quality issues")
    p_lint.add_argument("source", help="Path to .mn source file")
    p_lint.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix lint warnings (unused imports, unnecessary mut)",
    )
    p_lint.set_defaults(func=cmd_lint)

    # targets
    p_targets = subparsers.add_parser("targets", help="List supported compilation targets")
    p_targets.set_defaults(func=cmd_targets)

    # doc
    p_doc = subparsers.add_parser("doc", help="Generate HTML docs from doc comments")
    p_doc.add_argument("source", help="Path to .mn source file")
    p_doc.add_argument("-o", metavar="OUTPUT", help="Output .html file path", default=None)
    p_doc.set_defaults(func=cmd_doc)

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
