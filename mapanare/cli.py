"""Mapanare compiler CLI -- entry point for the mapanare command."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from mapanare.diagnostics import (
    Diagnostic,
    Label,
    Severity,
    format_diagnostic,
    format_summary,
)
from mapanare.format import (
    find_long_lines,
    format_source,
    sort_imports,
    to_braces,
    to_terse,
    to_terse_markdown,
)
from mapanare.mir_opt import MIROptLevel as OptLevel
from mapanare.modules import ModuleResolver
from mapanare.parser import ParseError, parse, parse_recovering
from mapanare.semantic import SemanticErrors, check_or_raise
from mapanare.targets import get_target, host_target_name, list_targets

_VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
__version__ = _VERSION_FILE.read_text().strip() if _VERSION_FILE.exists() else "unknown"


# v5.31.0 Bn.1: subcommands that don't compile or execute Mapanare code never
# warrant the dev-clone banner. When adding a new pure-metadata subcommand,
# add it here in the same PR so the banner doesn't fire spuriously.
NO_BANNER_COMMANDS = frozenset({"--version", "--help", "-h", "init", "list"})


@lru_cache(maxsize=1)
def _is_release_install() -> bool:
    """True if the current Mapanare install is a release artifact, not a dev clone.

    Primary signal: ``MAPANARE_RELEASE=1`` env var (set by the PyInstaller
    entry and SDK launchers). Fallback: dev clones have ``pyproject.toml`` and
    a ``.git`` directory at the repo root (parent of ``mapanare/``); release
    installs do not.
    """
    if os.environ.get("MAPANARE_RELEASE") == "1":
        return True
    pkg_dir = Path(__file__).resolve().parent
    repo_root_candidate = pkg_dir.parent
    return not (
        (repo_root_candidate / "pyproject.toml").exists()
        and (repo_root_candidate / ".git").is_dir()
    )


def _should_show_dev_banner(argv: list[str]) -> bool:
    """Show the dev-mode banner only on dev clones for compile/run commands."""
    if _is_release_install():
        return False
    for tok in argv[1:]:
        if tok in NO_BANNER_COMMANDS:
            return False
        if not tok.startswith("-"):
            return tok not in NO_BANNER_COMMANDS
    return False


def _read_source(path: str) -> str:
    """Read a source file, exiting on error.

    If *path* ends with ``.py``, the file is first translated from Python
    to Mapanare source text via :mod:`mapanare.from_python`.
    """
    if not os.path.isfile(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        source = f.read()

    if path.endswith(".py"):
        from mapanare.from_python import TranslateError, translate_to_mn

        try:
            source = translate_to_mn(source, filename=path)
        except TranslateError as e:
            print(f"error: Python translation failed: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"info: translated {path} from Python to Mapanare", file=sys.stderr)

    if path.endswith(".php"):
        from mapanare.from_php import TranslateError as PhpTranslateError
        from mapanare.from_php import translate_to_mn as php_translate_to_mn

        try:
            source = php_translate_to_mn(source, filename=path)
        except PhpTranslateError as e:
            print(f"error: PHP translation failed: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"info: translated {path} from PHP to Mapanare", file=sys.stderr)

    return source


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
    """Print semantic errors as colorized diagnostics.

    v4.27.0: routes every ``SemanticError`` through its ``to_diagnostic()``
    helper so the underline matches the offending expression's full span
    instead of always pointing at a single character. Closes v4.26.0 panel
    CRITICAL #8 (Anaconda).
    """
    diagnostics: list[Diagnostic] = [err.to_diagnostic() for err in e.errors]
    for diag in diagnostics:
        print(format_diagnostic(diag, source), file=sys.stderr)
    summary = format_summary(diagnostics)
    if summary:
        print(summary, file=sys.stderr)


def _parse_opt_level(args: argparse.Namespace) -> OptLevel:
    """Extract optimization level from parsed args."""
    return OptLevel(getattr(args, "opt_level", 2))


def _verify_mir_or_exit(mir_module: object, no_verify: bool) -> None:
    """Run the MIR verifier unless the caller explicitly bypassed it.

    The verifier checks block terminators, branch targets, phi placement, and
    SSA definition uniqueness. This is the v4.27.0 wiring that closes the
    v4.5.0 CHANGELOG claim: prior to this, ``MIRVerifier`` was defined but had
    zero call sites in the compile pipeline.
    """
    if no_verify:
        return
    from mapanare.mir import MIRModule, MIRVerifier

    assert isinstance(mir_module, MIRModule)
    errors = MIRVerifier().verify_module(mir_module)
    if errors:
        print("error: MIR verifier detected malformed IR before emission:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        print(
            "hint: pass --no-verify to bypass (debugging only); the crash this "
            "prevents is usually easier to diagnose than the LLVM error it would cause.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _compile_to_llvm_ir(
    source: str,
    filename: str,
    opt_level: OptLevel = OptLevel.O2,
    target_name: str | None = None,
    resolver: ModuleResolver | None = None,
    debug: bool = False,
    werror: bool = False,
    skip_check: bool = False,
    no_verify: bool = False,
    ffi_mode: bool = False,
) -> str:
    """Parse, check, optimize, and emit LLVM IR from Mapanare source.

    When the source contains ``import`` statements, automatically uses
    multi-module compilation to resolve and link all imported modules
    into a single LLVM IR module.

    When ``ffi_mode`` is True, every non-underscore, non-``main`` top-level
    function is treated as if it were declared ``pub``. That single change
    flows through the pipeline: the MIR dead-function pass (``mir_opt.py``)
    keeps them, and the LLVM emitter gives them external linkage. This
    replaces the v4.25.0 ``.replace("define internal ", "define ")`` text
    hack, which stripped ``internal`` linkage from **every** function in the
    module regardless of whether the user intended to export it.
    """
    ast = parse(source, filename=filename)

    from mapanare.ast_nodes import FnDef, ImportDef

    if ffi_mode:
        for defn in ast.definitions:
            if isinstance(defn, FnDef) and defn.name != "main" and not defn.name.startswith("_"):
                defn.public = True

    has_imports = any(isinstance(d, ImportDef) for d in ast.definitions)
    if has_imports:
        from mapanare.multi_module import compile_multi_module_mir

        return compile_multi_module_mir(
            root_source=source,
            root_file=filename,
            opt_level=opt_level.value,
            target_name=target_name,
            debug=debug,
            skip_check=skip_check,
            no_verify=no_verify,
        )
    if not skip_check:
        check_or_raise(ast, filename=filename, resolver=resolver, werror=werror)

    from mapanare.lower import lower as build_mir
    from mapanare.mir_opt import MIROptLevel
    from mapanare.mir_opt import optimize_module as mir_optimize

    module_name = os.path.splitext(os.path.basename(filename))[0]
    source_file = os.path.basename(filename)
    source_dir = os.path.dirname(os.path.abspath(filename))
    mir_module = build_mir(
        ast,
        module_name=module_name,
        source_file=source_file,
        source_directory=source_dir,
    )
    mir_opt_level = MIROptLevel(opt_level.value)
    mir_module, _ = mir_optimize(mir_module, mir_opt_level)
    _verify_mir_or_exit(mir_module, no_verify)
    target = get_target(target_name)

    from mapanare.emit_llvm_text import LLVMTextEmitter

    emitter = LLVMTextEmitter(
        module_name=module_name,
        target_triple=target.triple,
        data_layout=target.data_layout,
        debug=debug,
    )
    return emitter.emit(mir_module)


def _compile_multi_module_text(
    source_files: list[str],
    opt_level: OptLevel = OptLevel.O2,
    target_name: str | None = None,
    skip_check: bool = False,
    no_verify: bool = False,
) -> str:
    """Compile multiple .mn files into a single linked LLVM IR module.

    Uses the first file as root and treats the rest as dependencies via
    the MIR-based multi-module pipeline.
    """
    if not source_files:
        raise ValueError("no source files provided")

    root_file = source_files[0]
    root_source = _read_source(root_file)

    from mapanare.multi_module import compile_multi_module_mir

    return compile_multi_module_mir(
        root_source=root_source,
        root_file=root_file,
        opt_level=opt_level.value,
        target_name=target_name,
        skip_check=skip_check,
        no_verify=no_verify,
    )


def _check_one(path: str, *, werror: bool) -> bool:
    """Type-check a single .mn file. Return True iff it has zero errors.

    Prints diagnostics to stderr and an "OK" line to stdout, matching the
    historical single-file output.
    """
    source = _read_source(path)
    resolver = ModuleResolver()
    ast, parse_errors = parse_recovering(source, filename=path)

    all_diagnostics: list[Diagnostic] = []

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

    if ast.definitions:
        from mapanare.semantic import check

        sem_errors = check(ast, filename=path, resolver=resolver)
        for err in sem_errors:
            diag = err.to_diagnostic()
            is_warning = err.severity == "warning"
            if is_warning and not werror:
                all_diagnostics.append(diag)
                continue
            if is_warning and werror:
                diag.severity = Severity.ERROR
            all_diagnostics.append(diag)

    if all_diagnostics:
        for diag in all_diagnostics:
            print(format_diagnostic(diag, source), file=sys.stderr)
        summary = format_summary(all_diagnostics)
        if summary:
            print(summary, file=sys.stderr)
        return False

    print(f"check: {path} OK")
    return True


def _walk_mn_files(root: str = ".") -> list[str]:
    """Walk a directory tree and return .mn files in stable sorted order.

    Skips common build/cache directories so `mapanare check --all` stays
    fast on real projects.
    """
    skip = {".git", ".mn-cache", ".mapanare-cache", "dist", "build", "node_modules"}
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".mn"):
                out.append(os.path.join(dirpath, fn))
    out.sort()
    return out


def cmd_check(args: argparse.Namespace) -> None:
    """Type-check one or many .mn source files with error recovery."""
    werror = getattr(args, "werror", False)
    walk_all = getattr(args, "all", False)

    if walk_all:
        paths = _walk_mn_files(".")
        if not paths:
            print("check: no .mn files found", file=sys.stderr)
            sys.exit(1)
    else:
        if not args.source:
            print(
                "error: provide a source file or pass --all to walk the current dir",
                file=sys.stderr,
            )
            sys.exit(2)
        paths = [args.source]

    failed = 0
    for path in paths:
        if not _check_one(path, werror=werror):
            failed += 1

    if failed:
        if walk_all:
            print(f"check: {failed}/{len(paths)} file(s) had errors", file=sys.stderr)
        sys.exit(1)


def cmd_run(args: argparse.Namespace) -> None:
    """Compile and run an .mn source file via the C backend (emit C → gcc → run)."""
    # Enable tracing if --trace is passed
    trace_mode = getattr(args, "trace", None)
    if trace_mode:
        from mapanare.tracing import enable_tracing

        exporter = "otlp" if trace_mode.startswith("otlp") else "console"
        otlp_endpoint = None
        if "=" in trace_mode:
            otlp_endpoint = trace_mode.split("=", 1)[1]
        enable_tracing(
            service_name=os.path.basename(args.source),
            exporter=exporter,
            otlp_endpoint=otlp_endpoint,
        )

    # Enable metrics if --metrics is passed
    metrics_addr = getattr(args, "metrics", None)
    if metrics_addr:
        from mapanare.metrics import start_metrics_server

        start_metrics_server(metrics_addr)

    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    debug = _resolve_debug(args)

    try:
        c_source = _compile_to_c(source, args.source, opt_level=opt_level, debug=debug)
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    _run_c_source(c_source, args.source)


def cmd_fmt(args: argparse.Namespace) -> None:
    """Format .mn source — normalize whitespace canonically.

    Accepts files and directories (directories are recursively scanned for
    ``.mn`` files). Default behavior writes formatted output back in place
    for backwards compatibility with v5.12.x and earlier; ``--check``
    reports diff candidates without writing (exit 1 if any), ``--stdout``
    prints to stdout instead of writing.

    Files that fail to parse are reported on stderr and skipped; the
    overall exit code is 1 if any file errored or (under --check) needed
    changes.
    """
    paths = _expand_fmt_paths(args.sources)
    if not paths:
        print("error: no .mn files found", file=sys.stderr)
        sys.exit(1)

    # v5.14.0 Te.1: choose surface-syntax transformer.
    # v5.19.0 Te.3.B: bare ``mnc fmt`` auto-migrates ``{}`` to colon
    # syntax by running ``to_terse`` whenever the source contains
    # user-written brace blocks. ``--keep-braces`` opts out.
    if getattr(args, "to_terse", False) and getattr(args, "to_braces", False):
        print("error: --to-terse and --to-braces are mutually exclusive", file=sys.stderr)
        sys.exit(1)
    if getattr(args, "to_terse", False) and getattr(args, "keep_braces", False):
        print("error: --to-terse and --keep-braces are mutually exclusive", file=sys.stderr)
        sys.exit(1)
    if getattr(args, "to_braces", False) and getattr(args, "keep_braces", False):
        print("error: --to-braces and --keep-braces are mutually exclusive", file=sys.stderr)
        sys.exit(1)

    explicit_terse = bool(getattr(args, "to_terse", False))
    explicit_braces = bool(getattr(args, "to_braces", False))
    keep_braces = bool(getattr(args, "keep_braces", False))
    # v5.27.0 Mc.8 / Mc.9 — additive options.
    line_length = int(getattr(args, "line_length", 0) or 0)
    do_sort_imports = bool(getattr(args, "sort_imports", False))

    if explicit_terse:
        transformer: Callable[[str], str] = to_terse
        per_file_auto_terse = False
    elif explicit_braces:
        transformer = to_braces
        per_file_auto_terse = False
    elif keep_braces:
        transformer = format_source
        per_file_auto_terse = False
    else:
        # Auto-migration default: per-file decision. format_source for
        # files that already use colon syntax; to_terse for files that
        # contain user-written brace blocks.
        transformer = format_source  # placeholder; chosen per file
        per_file_auto_terse = True

    changed: list[Path] = []
    errored: list[Path] = []

    for path in paths:
        # Read in binary mode so universal-newline translation does not
        # silently mask CRLF / CR endings — the formatter is supposed to
        # canonicalize line endings, and that requires actually seeing them.
        try:
            raw = path.read_bytes()
        except OSError as e:
            print(f"error: cannot read {path}: {e}", file=sys.stderr)
            errored.append(path)
            continue
        try:
            source = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            print(f"error: {path}: not valid UTF-8: {e}", file=sys.stderr)
            errored.append(path)
            continue

        # v5.24.1 Wd.2: markdown sources are processed via
        # ``to_terse_markdown`` — only `````mn`` fence
        # bodies are rewritten; prose and other-language fences pass
        # through verbatim. ``--to-terse`` is the only meaningful flag
        # for markdown; other flags either no-op or are rejected.
        is_markdown = path.suffix.lower() in {".md", ".markdown"}
        if is_markdown:
            if not explicit_terse:
                print(
                    f"error: {path}: markdown sources require --to-terse",
                    file=sys.stderr,
                )
                errored.append(path)
                continue
            formatted = to_terse_markdown(source)
            if formatted == source:
                continue
            changed.append(path)
            if args.check:
                print(f"would format: {path}", file=sys.stderr)
            elif args.stdout:
                sys.stdout.write(formatted)
            else:
                path.write_bytes(formatted.encode("utf-8"))
                print(f"formatted {path}")
            continue

        # Verify the file parses before formatting — prevents fmt from
        # silently rewriting a file that the rest of the pipeline can't
        # consume. v5.19.0: temporarily suppress the brace-deprecation
        # warning during the parse-validation call — the user is
        # already running fmt, the "Run mnc fmt to migrate" hint would
        # be redundant noise.
        prior_no_warn = os.environ.get("MAPANARE_NO_BRACE_WARNING")
        os.environ["MAPANARE_NO_BRACE_WARNING"] = "1"
        try:
            parse(source, filename=str(path))
        except ParseError as e:
            _emit_parse_error(e, source, str(path))
            errored.append(path)
            continue
        finally:
            if prior_no_warn is None:
                os.environ.pop("MAPANARE_NO_BRACE_WARNING", None)
            else:
                os.environ["MAPANARE_NO_BRACE_WARNING"] = prior_no_warn

        # v5.19.0 Te.3.B: per-file auto-migration. If the source has
        # user-written brace blocks AND the user did not pass an
        # explicit flag, route through to_terse instead of format_source.
        if per_file_auto_terse:
            from mapanare.parser import count_user_brace_block_openers

            if count_user_brace_block_openers(source) > 0:
                file_transformer: Callable[[str], str] = to_terse
            else:
                file_transformer = format_source
        else:
            file_transformer = transformer

        formatted = file_transformer(source)
        # v5.27.0 Mc.9 — sort imports as an additive pass after the
        # primary transformer. Pure text-level sort; idempotent.
        if do_sort_imports:
            formatted = sort_imports(formatted)

        # v5.27.0 Mc.8 — long-line detection. Pure read-only scan; the
        # source is never modified. Reported on stderr; long lines under
        # --check cause a non-zero exit so CI gates can enforce the
        # ceiling.
        long_lines: list[tuple[int, int]] = []
        if line_length > 0:
            long_lines = find_long_lines(formatted, line_length)
            for line_no, length in long_lines:
                print(
                    f"{path}:{line_no}: line exceeds {line_length} chars ({length})",
                    file=sys.stderr,
                )

        if formatted == source:
            if args.check and long_lines:
                changed.append(path)
            continue
        changed.append(path)

        if args.check:
            print(f"would format: {path}", file=sys.stderr)
        elif args.stdout:
            sys.stdout.write(formatted)
        else:
            # Write in binary so the LF-normalized output lands on disk
            # exactly as produced (no platform-specific re-translation).
            path.write_bytes(formatted.encode("utf-8"))
            print(f"formatted {path}")

    if errored:
        sys.exit(1)
    if args.check and changed:
        sys.exit(1)


def _expand_fmt_paths(sources: list[str]) -> list[Path]:
    """Expand a mix of files and directories into a sorted list of .mn files.

    Directories are walked recursively; only ``.mn`` files are included.
    Non-.mn explicit files are still included (the caller asked for them).
    """
    seen: set[Path] = set()
    out: list[Path] = []
    for s in sources:
        p = Path(s)
        if not p.exists():
            print(f"error: path not found: {s}", file=sys.stderr)
            continue
        if p.is_dir():
            for f in sorted(p.rglob("*.mn")):
                rp = f.resolve()
                if rp not in seen:
                    seen.add(rp)
                    out.append(f)
        else:
            rp = p.resolve()
            if rp not in seen:
                seen.add(rp)
                out.append(p)
    return out


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize a new Mapanare project with mapanare.toml."""
    from stdlib.pkg import init_project

    project_dir = args.path or "."
    name = args.name
    overlays: list[str] = []
    if getattr(args, "docker", False):
        overlays.append("docker")
    manifest = init_project(project_dir, name=name, overlays=overlays)
    print(f"initialized project '{manifest.name}' in {os.path.abspath(project_dir)}")


def cmd_install(args: argparse.Namespace) -> None:
    """Install a package from the Mapanare registry (or git fallback)."""
    from stdlib.pkg import PackageError, install_all, install_package

    project_dir = "."
    package_arg = getattr(args, "package", None)

    # No argument: install all deps from mapanare.toml
    if not package_arg:
        try:
            results = install_all(project_dir)
            if not results:
                print("no dependencies in mapanare.toml")
                return
            for locked in results:
                print(f"installed {locked.name} @ {locked.version}")
        except PackageError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Parse name@version syntax
    pkg_name = package_arg
    version = "*"
    if "@" in package_arg:
        pkg_name, version = package_arg.rsplit("@", 1)

    try:
        locked = install_package(
            package_name=pkg_name,
            project_dir=project_dir,
            git_url=getattr(args, "git", None),
            branch=getattr(args, "branch", None),
            version=version,
        )
        print(f"installed {locked.name} @ {locked.version}")
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


def cmd_build(args: argparse.Namespace) -> None:
    """Compile an .mn source file to a native binary.

    Preferred path: emit LLVM IR → clang -c → link. Falls back to C source
    → gcc when no clang is available (e.g. w64devkit-only bundle on Windows).
    """
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    target_name: str | None = getattr(args, "target", None)
    debug = _resolve_debug(args)
    stdlib_path: str | None = getattr(args, "stdlib_path", None)
    search_paths = [stdlib_path] if stdlib_path else None
    resolver = ModuleResolver(search_paths=search_paths)
    werror = getattr(args, "werror", False)

    import tempfile

    from mapanare.toolchain import (
        detect_toolchain,
        install_instructions,
        invocation_env,
    )

    host_tc = detect_toolchain()
    clang_exe = host_tc.clang if host_tc else None

    # Cross-compiling always needs an LLVM toolchain capable of -target.
    target_name = getattr(args, "target", None)
    is_cross_target = target_name is not None and target_name != host_target_name()

    base = os.path.splitext(args.source)[0]
    obj_ext = ".obj" if os.name == "nt" else ".o"
    obj_path = base + obj_ext

    if clang_exe or is_cross_target:
        # LLVM path: emit IR, compile via clang.
        try:
            llvm_ir = _compile_to_llvm_ir(
                source,
                args.source,
                opt_level=opt_level,
                target_name=target_name,
                resolver=resolver,
                debug=debug,
                werror=werror,
                no_verify=_resolve_no_verify(args),
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

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ll", delete=False, encoding="utf-8"
        ) as ll_file:
            ll_file.write(llvm_ir)
            ll_path = ll_file.name

        try:
            if not clang_exe:
                print(
                    "error: clang not found (required for cross-compilation to "
                    f"'{target_name}')",
                    file=sys.stderr,
                )
                print("", file=sys.stderr)
                print(install_instructions(), file=sys.stderr)
                sys.exit(1)
            clang_cmd = [
                clang_exe,
                "-c",
                f"-O{opt_level.value}",
                ll_path,
                "-o",
                obj_path,
            ]
            result = subprocess.run(
                clang_cmd,
                capture_output=True,
                text=True,
                env=invocation_env(host_tc) if host_tc else None,
            )
            if result.returncode != 0:
                print(f"error: clang failed:\n{result.stderr}", file=sys.stderr)
                sys.exit(1)
        finally:
            os.unlink(ll_path)
    else:
        # No clang — fall back to the C backend with host gcc.
        if host_tc is None:
            print("error: no C compiler found", file=sys.stderr)
            print("", file=sys.stderr)
            print(install_instructions(), file=sys.stderr)
            sys.exit(1)
        try:
            c_source = _compile_to_c(source, args.source, opt_level=opt_level, debug=debug)
        except ParseError as e:
            _emit_parse_error(e, source, args.source)
            sys.exit(1)
        except SemanticErrors as e:
            _emit_semantic_errors(e, source)
            sys.exit(1)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".c", delete=False, encoding="utf-8"
        ) as c_file:
            c_file.write(c_source)
            c_path_tmp = c_file.name

        runtime_dir = _runtime_native_dir()
        runtime_c = os.path.join(runtime_dir, "mapanare_core.c")
        try:
            gcc_cmd = [
                host_tc.compiler,
                "-c",
                f"-O{opt_level.value}",
                f"-I{runtime_dir}",
                c_path_tmp,
                "-o",
                obj_path,
            ]
            result = subprocess.run(
                gcc_cmd,
                capture_output=True,
                text=True,
                env=invocation_env(host_tc),
            )
            if result.returncode != 0:
                print(
                    f"error: {host_tc.name} compilation failed:\n{result.stderr}",
                    file=sys.stderr,
                )
                sys.exit(1)
            # Stash runtime path on host_tc so the link step below folds it in.
            # (pre-built archive wins if present, else we link mapanare_core.c fresh.)
            args._cbackend_runtime_c = runtime_c
        finally:
            os.unlink(c_path_tmp)

    # Collect --link-lib flags as -l<lib> / <lib>.lib for linker
    link_libs: list[str] = getattr(args, "link_lib", None) or []

    # Determine target and output format
    target = get_target(target_name)
    lib_mode = getattr(args, "lib", False)

    if lib_mode:
        # Library output
        if "android" in target.triple:
            out_ext = ".so"
        elif "ios" in target.triple or "apple" in target.triple:
            out_ext = ".a"
        elif "windows" in target.triple:
            out_ext = ".dll"
        else:
            out_ext = target.lib_ext or ".so"
        out_path = args.o or (base + out_ext)
    else:
        out_ext = target.exe_ext
        out_path = args.o or (base + out_ext)

    # Cross-compilation: use target-specific linker
    is_cross = target_name is not None and target_name != host_target_name()

    linked = False
    link_flags_unix = [f"-l{lib}" for lib in link_libs]
    link_flags_msvc = [f"{lib}.lib" for lib in link_libs]

    if is_cross or lib_mode:
        # Build the linker command for cross-compilation or library mode
        linker = target.linker
        linker_args: list[str] = []

        if "android" in target.triple:
            # Android NDK clang
            linker_args = [linker]
            if lib_mode:
                linker_args += ["-shared"]
            linker_args += ["-target", target.triple, obj_path, "-o", out_path]
            linker_args += link_flags_unix

        elif "ios" in target.triple:
            if lib_mode:
                # Static library via ar/libtool
                linker_args = ["libtool", "-static", "-o", out_path, obj_path]
            else:
                linker_args = [
                    linker,
                    "-target",
                    target.triple,
                    obj_path,
                    "-o",
                    out_path,
                ] + link_flags_unix

        elif "wasm" in target.triple:
            linker_args = [linker, obj_path, "-o", out_path, "--no-entry", "--export-all"]

        else:
            # Generic cross-compile with clang -target
            linker_args = [linker]
            if lib_mode:
                linker_args += ["-shared"]
            if "clang" in linker:
                linker_args += ["-target", target.triple]
            linker_args += [obj_path, "-o", out_path] + link_flags_unix

        import shutil

        if shutil.which(linker_args[0]):
            result = subprocess.run(linker_args, capture_output=True, text=True)
            if result.returncode == 0:
                linked = True
                kind = "library" if lib_mode else "binary"
                print(f"built {args.source} -> {out_path} ({kind})")
            else:
                print(
                    f"link error ({linker_args[0]}): {result.stderr[:300]}",
                    file=sys.stderr,
                )
        else:
            print(
                f"linker not found: {linker_args[0]}\n"
                f"note: install the toolchain for target '{target.triple}'",
                file=sys.stderr,
            )
    else:
        # Host compilation: find runtime archive for linking
        rt_flags_unix: list[str] = []
        rt_flags_msvc: list[str] = []

        # Prefer the toolchain's shipped runtime archive (CI builds one per
        # platform). Fall back to the in-tree libmapanare_rt.a only on non-
        # Windows — the checked-in archive is ELF x86_64 and unusable from
        # MinGW on Windows.
        rt_archive: str | None = None
        if host_tc and host_tc.rt_archive and os.path.isfile(host_tc.rt_archive):
            rt_archive = host_tc.rt_archive
        elif os.name != "nt":
            cand = os.path.join(_runtime_native_dir(), "libmapanare_rt.a")
            if os.path.isfile(cand):
                rt_archive = cand

        rt_flags_unix = [rt_archive] if rt_archive else []
        # C-backend fallback path: if no pre-built archive, compile & link
        # mapanare_core.c alongside the user's object file.
        cbackend_rt = getattr(args, "_cbackend_runtime_c", None)
        if not rt_archive and cbackend_rt and os.path.isfile(cbackend_rt):
            rt_flags_unix = [cbackend_rt]
        if host_tc is None or host_tc.needs_libm_flag:
            rt_flags_unix.append("-lm")
        if host_tc is None or host_tc.needs_pthread_flag:
            rt_flags_unix.append("-lpthread")

        host_env = invocation_env(host_tc) if host_tc else None

        # Preferred compilers: use the detected toolchain first, then common fallbacks.
        preferred = []
        if host_tc is not None:
            preferred.append(host_tc.compiler)
            if host_tc.clang and host_tc.clang != host_tc.compiler:
                preferred.append(host_tc.clang)
        # Always include these so that users with a partial install still link.
        for fallback in ("clang", "gcc"):
            if fallback not in preferred:
                preferred.append(fallback)

        import shutil

        # When the C-backend fallback kicked in, mapanare_core.c is added to
        # the link line and needs the runtime include path.
        extra_include: list[str] = []
        if cbackend_rt:
            extra_include = [f"-I{_runtime_native_dir()}"]

        attempts: list[list[str]] = []
        for linker in preferred:
            attempts.append(
                [linker]
                + extra_include
                + [obj_path, "-o", out_path]
                + rt_flags_unix
                + link_flags_unix
            )
        # MSVC path: only consider when a real MSVC toolchain is on PATH
        # (detected via cl.exe). Skipping otherwise avoids collisions with
        # Git Bash's coreutils `link.exe`, which accepts unrelated flags.
        if os.name == "nt" and shutil.which("cl.exe") is not None:
            attempts.append(
                [
                    "link.exe",
                    f"/OUT:{out_path}",
                    obj_path,
                    "msvcrt.lib",
                    "legacy_stdio_definitions.lib",
                ]
                + rt_flags_msvc
                + link_flags_msvc
            )

        for linker_cmd in attempts:
            exe = linker_cmd[0]
            resolved = exe if os.path.isabs(exe) else shutil.which(exe)
            if not resolved:
                continue
            if not os.path.isabs(exe):
                linker_cmd[0] = resolved
            result = subprocess.run(linker_cmd, capture_output=True, text=True, env=host_env)
            if result.returncode == 0:
                linked = True
                print(f"built {args.source} -> {out_path}")
                break
            else:
                print(
                    f"link warning ({os.path.basename(resolved)}): {result.stderr[:200]}",
                    file=sys.stderr,
                )

    if not linked:
        print(f"compiled {args.source} -> {obj_path} (object file)")
        if is_cross:
            print(
                f"note: install the {target.triple} toolchain to link "
                f"(e.g. Android NDK for android targets, Xcode for iOS)"
            )
        else:
            if os.name == "nt":
                print(
                    "note: no linker found. install one of:\n"
                    "  - w64devkit: https://github.com/skeeto/w64devkit/releases\n"
                    "  - MSYS2:     https://www.msys2.org (install mingw-w64-x86_64-gcc)\n"
                    "  - LLVM:      https://github.com/llvm/llvm-project/releases\n"
                    "  - MSVC:      https://visualstudio.microsoft.com/visual-cpp-build-tools/"
                )
            else:
                print("note: no linker found (install clang or gcc to produce executables)")


def cmd_emit_llvm(args: argparse.Namespace) -> None:
    """Emit LLVM IR for an .mn source file."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    target_name: str | None = getattr(args, "target", None)
    debug = _resolve_debug(args)
    resolver = ModuleResolver()
    try:
        llvm_ir = _compile_to_llvm_ir(
            source,
            args.source,
            opt_level=opt_level,
            target_name=target_name,
            resolver=resolver,
            debug=debug,
            no_verify=_resolve_no_verify(args),
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


def _compile_to_c(
    source: str,
    filename: str,
    opt_level: OptLevel = OptLevel.O2,
    debug: bool = False,
) -> str:
    """Parse, check, optimize, and emit C source from Mapanare source."""
    from mapanare.emit_c import emit_c
    from mapanare.lower import lower as build_mir
    from mapanare.mir_opt import MIROptLevel
    from mapanare.mir_opt import optimize_module as mir_optimize

    ast = parse(source, filename=filename)
    check_or_raise(ast, filename=filename)

    module_name = os.path.splitext(os.path.basename(filename))[0]
    source_file = os.path.basename(filename)
    source_dir = os.path.dirname(os.path.abspath(filename))
    mir_module = build_mir(
        ast,
        module_name=module_name,
        source_file=source_file,
        source_directory=source_dir,
    )
    mir_opt_level = MIROptLevel(opt_level.value)
    mir_module, _ = mir_optimize(mir_module, mir_opt_level)

    return emit_c(mir_module, debug=debug)


def _runtime_native_dir() -> str:
    """Locate the ``runtime/native`` directory.

    When running from a PyInstaller one-dir bundle the data is staged alongside
    the exe; in dev / editable installs it lives one level up from the package.
    Falls back to a CWD-relative path so users running from the repo still work.
    """
    # PyInstaller one-file bundle
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        cand = os.path.join(meipass, "runtime", "native")
        if os.path.isdir(cand):
            return cand

    # PyInstaller one-dir or source install
    pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cand = os.path.join(pkg_root, "runtime", "native")
    if os.path.isdir(cand):
        return cand

    # Last resort: CWD
    return os.path.join("runtime", "native")


def _run_c_source(c_source: str, source_file: str) -> None:
    """Compile C source with a C compiler and run the resulting binary."""
    import tempfile

    from mapanare.toolchain import (
        detect_toolchain,
        install_instructions,
        invocation_env,
    )

    # Find runtime headers + source
    runtime_dir = _runtime_native_dir()
    runtime_c = os.path.join(runtime_dir, "mapanare_core.c")

    tc = detect_toolchain()
    if tc is None:
        print("error: no C compiler found", file=sys.stderr)
        print("", file=sys.stderr)
        print(install_instructions(), file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        c_path = os.path.join(tmpdir, "program.c")
        bin_ext = ".exe" if os.name == "nt" else ""
        bin_path = os.path.join(tmpdir, "program" + bin_ext)

        with open(c_path, "w", encoding="utf-8") as f:
            f.write(c_source)

        cmd = [
            tc.compiler,
            "-O0",
            "-Wall",
            "-Wextra",
            f"-I{runtime_dir}",
            c_path,
        ]
        # Prefer pre-built runtime archive when the bundle shipped one;
        # otherwise compile mapanare_core.c from source alongside the user program.
        if tc.rt_archive:
            cmd.append(tc.rt_archive)
        else:
            cmd.append(runtime_c)
        cmd += ["-o", bin_path]
        if tc.needs_libm_flag:
            cmd.append("-lm")
        if tc.needs_pthread_flag:
            cmd.append("-lpthread")

        result = subprocess.run(cmd, capture_output=True, text=True, env=invocation_env(tc))
        if result.returncode != 0:
            print(f"error: {tc.name} compilation failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Run
        run_result = subprocess.run([bin_path])
        sys.exit(run_result.returncode)


def cmd_emit_c(args: argparse.Namespace) -> None:
    """Emit C source for an .mn source file."""
    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    debug = _resolve_debug(args)
    try:
        c_source = _compile_to_c(source, args.source, opt_level=opt_level, debug=debug)
    except ParseError as e:
        _emit_parse_error(e, source, args.source)
        sys.exit(1)
    except SemanticErrors as e:
        _emit_semantic_errors(e, source)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.o or args.source.replace(".mn", ".c")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(c_source)
    print(f"emitted {args.source} -> {out_path} (backend: C)")


def cmd_emit_mir(args: argparse.Namespace) -> None:
    """Emit MIR (Mid-level IR) for an .mn source file."""
    from mapanare.lower import lower as build_mir
    from mapanare.mir import pretty_print_module as mir_pretty_print
    from mapanare.mir_opt import MIROptLevel
    from mapanare.mir_opt import optimize_module as mir_optimize

    source = _read_source(args.source)
    opt_level = _parse_opt_level(args)
    resolver = ModuleResolver()
    try:
        ast = parse(source, filename=args.source)
        check_or_raise(ast, filename=args.source, resolver=resolver)
        mir_module = build_mir(ast, module_name=os.path.splitext(os.path.basename(args.source))[0])
        mir_opt_level = MIROptLevel(opt_level.value)
        mir_module, _ = mir_optimize(mir_module, mir_opt_level)
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


def cmd_emit_wasm(args: argparse.Namespace) -> None:
    """Emit WebAssembly (WAT) for .mn source file(s), optionally linking."""
    from mapanare.emit_wasm import WasmEmitter, WasmOptions
    from mapanare.lower import lower as build_mir
    from mapanare.mir_opt import MIROptLevel
    from mapanare.mir_opt import optimize_module as mir_optimize

    source_files: list[str] = args.source
    opt_level = _parse_opt_level(args)
    do_link = getattr(args, "link", False)
    do_binary = getattr(args, "binary", False)

    # Emit WAT for each source file
    wat_paths: list[str] = []
    for src_file in source_files:
        source = _read_source(src_file)
        resolver = ModuleResolver()
        try:
            ast = parse(source, filename=src_file)
            check_or_raise(ast, filename=src_file, resolver=resolver)
            module_name = os.path.splitext(os.path.basename(src_file))[0]
            mir_module = build_mir(ast, module_name=module_name)
            mir_opt_level = MIROptLevel(opt_level.value)
            mir_module, _ = mir_optimize(mir_module, mir_opt_level)

            use_wasi = getattr(args, "wasi", False)
            wasm_opts = WasmOptions(wasi=use_wasi)
            emitter = WasmEmitter(options=wasm_opts)
            wat_output = emitter.emit(mir_module)
        except ParseError as e:
            _emit_parse_error(e, source, src_file)
            sys.exit(1)
        except SemanticErrors as e:
            _emit_semantic_errors(e, source)
            sys.exit(1)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            sys.exit(1)

        if len(source_files) == 1 and args.o and not do_link:
            out_path = args.o
        else:
            out_path = src_file.replace(".mn", ".wat")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(wat_output)
        print(f"emitted {src_file} -> {out_path} (WebAssembly text format)")
        wat_paths.append(out_path)

    # Link multiple WAT modules into a single .wasm binary
    if do_link or (do_binary and len(source_files) > 1):
        from pathlib import Path

        from mapanare.wasm_linker import WasmLinkerConfig, link_wat_files

        # Build linker config from CLI args
        use_wasi = getattr(args, "wasi", False)
        if use_wasi:
            config = WasmLinkerConfig.for_wasi()
        elif getattr(args, "export_all", False):
            config = WasmLinkerConfig.for_library()
        else:
            config = WasmLinkerConfig()

        config.stack_size = getattr(args, "stack_size", 65536)
        config.initial_memory = getattr(args, "initial_memory", 1048576)

        if args.o:
            wasm_output = Path(args.o)
        else:
            wasm_output = Path(source_files[0]).with_suffix(".wasm")

        result = link_wat_files(
            [Path(p) for p in wat_paths],
            wasm_output,
            config=config,
        )
        if result.success:
            print(f"linked {len(wat_paths)} module(s) -> {wasm_output}")
        else:
            print(f"wasm-ld linking failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        return

    # Single-file binary compilation (original behavior)
    if do_binary and len(source_files) == 1:
        import shutil

        wat2wasm = shutil.which("wat2wasm")
        if wat2wasm:
            wasm_path = wat_paths[0].replace(".wat", ".wasm")
            proc = subprocess.run(
                [wat2wasm, wat_paths[0], "-o", wasm_path],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                print(f"compiled {wat_paths[0]} -> {wasm_path} (binary)")
            else:
                print(f"wat2wasm failed: {proc.stderr}", file=sys.stderr)
        else:
            print("warning: wat2wasm not found, skipping binary compilation", file=sys.stderr)


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


def cmd_migrate(args: argparse.Namespace) -> None:
    """Migrate .mn source from v2 to v3 syntax."""
    from mapanare.migrate import migrate_directory, migrate_file

    target = args.path
    style = getattr(args, "style", "spanglish")
    dry_run = getattr(args, "dry", False)
    check = getattr(args, "check", False)

    if os.path.isfile(target):
        changed = 1 if migrate_file(target, style=style, dry_run=dry_run, check=check) else 0
    elif os.path.isdir(target):
        changed = migrate_directory(target, style=style, dry_run=dry_run, check=check)
    else:
        print(f"error: {target} not found", file=sys.stderr)
        sys.exit(1)

    if check and changed > 0:
        print(f"\n{changed} file(s) need migration", file=sys.stderr)
        sys.exit(1)

    if not check:
        mode = "would migrate" if dry_run else "migrated"
        print(f"\n{changed} file(s) {mode}")


def cmd_lsp(args: argparse.Namespace) -> None:
    """Start the Mapanare language server (LSP over stdio)."""
    from mapanare.lsp.server import main as lsp_main

    lsp_main()


def cmd_build_multi(args: argparse.Namespace) -> None:
    """Compile multiple .mn source files into a single linked LLVM IR / binary."""
    source_files = args.sources
    opt_level = _parse_opt_level(args)
    target_name: str | None = getattr(args, "target", None)
    skip_check = _resolve_no_check(args)
    no_verify = _resolve_no_verify(args)
    try:
        llvm_ir = _compile_multi_module_text(
            source_files,
            opt_level=opt_level,
            target_name=target_name,
            skip_check=skip_check,
            no_verify=no_verify,
        )
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticErrors as e:
        for err in e.errors:
            print(f"error: {err.message}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.o or "linked.ll"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(llvm_ir)
    print(f"linked {len(source_files)} modules -> {out_path}")


def cmd_test(args: argparse.Namespace) -> None:
    """Discover and run @test functions in .mn files."""
    from mapanare.test_runner import format_results, run_tests

    path = getattr(args, "path", ".")
    filter_pattern: str | None = getattr(args, "filter", None)

    suite = run_tests(path, filter_pattern=filter_pattern)
    print(format_results(suite))

    if suite.failed > 0:
        sys.exit(1)
    if suite.total == 0:
        sys.exit(0)


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


def cmd_deploy(args: argparse.Namespace) -> None:
    """Generate Dockerfile + docker-compose.yml for deployment."""
    from mapanare.deploy import scaffold_deploy

    project_dir = getattr(args, "path", ".")
    entry = getattr(args, "entry", "main.mn")

    created = scaffold_deploy(project_dir, entry_point=entry)
    if not created:
        print("deploy: all files already exist, nothing to do")
    else:
        for path in created:
            print(f"  created {path}")
        print(f"\ndeploy: {len(created)} file(s) generated in {os.path.abspath(project_dir)}")


def cmd_bind(args: argparse.Namespace) -> None:
    """Generate FFI bindings from .mn source.

    Compiles .mn → .so shared library and generates a language wrapper
    (Python ctypes, TypeScript .d.ts, or Go cgo) alongside it.
    """
    path = args.source
    if not os.path.isfile(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        source = f.read()

    from mapanare.bind import generate_bindings

    module_name = os.path.splitext(os.path.basename(path))[0]

    # Determine output directory
    out_dir = args.o if args.o else "."
    os.makedirs(out_dir, exist_ok=True)

    # Step 1: Generate language wrapper
    wrapper = generate_bindings(source, lang=args.lang, module_name=module_name)
    ext = {"python": ".py", "ts": ".d.ts", "go": ".go"}.get(args.lang, ".py")
    wrapper_path = os.path.join(out_dir, f"{module_name}{ext}")
    with open(wrapper_path, "w", encoding="utf-8") as f:
        f.write(wrapper)
    print(f"Generated {args.lang} wrapper: {wrapper_path}")

    # Step 2: Compile .mn → .ll → .o → .so
    #
    # v4.27.0 recovery: ``ffi_mode=True`` marks every bindable function as
    # public before lowering, which flows through DCE and emitter linkage so
    # the .so exports every surface-area function (not just ``main``'s
    # transitive callees). The old ``ll_text.replace("define internal ",
    # "define ")`` sledgehammer — which stripped ``internal`` linkage from
    # **every** function in the module — has been removed.
    try:
        llvm_ir = _compile_to_llvm_ir(
            source, path, no_verify=_resolve_no_verify(args), ffi_mode=True
        )
        # Rename @main to @mn_main so it doesn't conflict with C main
        import re

        llvm_ir = re.sub(
            r"define (.*?)@main\(",
            r"define \1@mn_main(",
            llvm_ir,
        )

        ll_path = os.path.join(out_dir, f"{module_name}.ll")
        with open(ll_path, "w", encoding="utf-8") as f:
            f.write(llvm_ir)

        obj_path = os.path.join(out_dir, f"{module_name}.o")
        so_path = os.path.join(out_dir, f"lib{module_name}.so")

        # Compile IR → object
        import subprocess

        result = subprocess.run(
            ["clang", "-c", "-fPIC", "-O2", ll_path, "-o", obj_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"warning: clang failed: {result.stderr.strip()}", file=sys.stderr)
            return

        # Find runtime archive
        rt_dir = os.path.join(os.path.dirname(__file__), "..", "runtime", "native")
        rt_archive = os.path.join(rt_dir, "libmapanare_rt.a")

        # Link as shared library. Try with runtime first, fall back to without.
        link_cmd = ["gcc", "-shared", "-o", so_path, obj_path]
        if os.path.isfile(rt_archive):
            link_cmd_rt = link_cmd + [rt_archive, "-lm", "-lpthread"]
            result = subprocess.run(link_cmd_rt, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Compiled shared library: {so_path}")
                return
            # Runtime not -fPIC compatible — link without it (works for pure functions)
        link_cmd.extend(["-lm", "-lpthread"])
        result = subprocess.run(link_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"warning: linker failed: {result.stderr.strip()}", file=sys.stderr)
            return

        print(f"Compiled shared library: {so_path}")
    except Exception as e:
        print(f"warning: .so compilation skipped: {e}", file=sys.stderr)


def cmd_transpile(args: argparse.Namespace) -> None:
    """Transpile a source file (.py or .php) to Mapanare (.mn) source."""
    path = args.source
    if not os.path.isfile(path):
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        source = f.read()

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".php":
            from mapanare.from_php import translate_to_mn

            mn_source = translate_to_mn(source, filename=path)
        else:
            from mapanare.from_python import translate_to_mn

            mn_source = translate_to_mn(source, filename=path)
    except Exception as e:
        print(f"error: translation failed: {e}", file=sys.stderr)
        sys.exit(1)

    out_path = args.o
    if out_path is None:
        base = os.path.splitext(path)[0]
        out_path = base + ".mn"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(mn_source)

    print(f"transpiled {path} -> {out_path}")


def cmd_targets(args: argparse.Namespace) -> None:
    """List all supported compilation targets."""
    print("Supported targets:\n")
    for name, desc in list_targets():
        print(f"  {name:<30s} {desc}")
    print()
    from mapanare.targets import host_target_name

    print(f"Host target: {host_target_name()}")


def _format_mapanare(source: str) -> str:
    """Backwards-compatible thin wrapper over ``mapanare.format.format_source``.

    Kept as an internal alias so callers that imported the v5.12.x and
    earlier name keep working. New code should import ``format_source``
    from ``mapanare.format`` directly. v5.13.0 promoted the formatter to
    its own module.
    """
    return format_source(source)


def _add_debug_flag(parser: argparse.ArgumentParser) -> None:
    """Add -g/--debug flag for DWARF debug info emission (v4.62.0+)."""
    parser.add_argument(
        "-g",
        "--debug",
        action="store_true",
        default=False,
        help="Emit DWARF debug info in the generated IR/binary.",
    )


def _resolve_debug(args: argparse.Namespace) -> bool:
    """Return ``True`` if the ``-g`` / ``--debug`` flag was passed.

    v4.121.0: DWARF debug info emission is deferred to the v5.x line
    (see ``docs/SPEC.md`` §21.3). The ``-g`` / ``--debug`` flag is still
    accepted for forward compatibility with scripts and IDEs, but it is
    a no-op — the emitter does not produce DWARF metadata. Every use of
    the flag prints a stderr warning naming v5.x as the tracking
    version, so the no-op behaviour is loud rather than silent.

    The v4.62.0–v4.120.0 comment claiming the flag enabled debug
    metadata was aspirational; no such emission was ever wired up. The
    v4.29.0 stderr warning is restored here.
    """
    debug = bool(getattr(args, "debug", False))
    if debug:
        print(
            "warning: -g / --debug is a no-op; DWARF debug info "
            "emission is deferred to v5.x (see SPEC §21.3)",
            file=sys.stderr,
        )
    return debug


def _add_edition_flag(parser: argparse.ArgumentParser) -> None:
    """Add --edition flag for language edition selection."""
    parser.add_argument(
        "--edition",
        metavar="YEAR",
        default="2026",
        help="Language edition (default: 2026)",
    )


def _add_no_verify_flag(parser: argparse.ArgumentParser) -> None:
    """Add --no-verify escape hatch that bypasses the MIR verifier.

    v4.27.0: the MIR verifier runs before emission by default. This flag
    skips it for debugging the verifier itself. A warning is printed to
    stderr when used because bypassing the verifier typically turns an
    interpretable MIR-level error into a cryptic LLVM codegen crash.
    """
    parser.add_argument(
        "--no-verify",
        action="store_true",
        default=False,
        help="Skip MIR structural verification before LLVM emission (debugging only)",
    )


def _resolve_no_verify(args: argparse.Namespace) -> bool:
    """Return no_verify from argparse and warn on stderr if it was set."""
    value = bool(getattr(args, "no_verify", False))
    if value:
        print(
            "warning: --no-verify skips MIR structural checks; crashes below "
            "are almost certainly malformed IR the verifier would have caught.",
            file=sys.stderr,
        )
    return value


def _resolve_no_check(args: argparse.Namespace) -> bool:
    """Return ``skip_check`` from argparse and warn on stderr if it was set.

    v4.29.0: ``--no-check`` previously bypassed semantic analysis silently,
    which is exactly the kind of "looks fine, diagnostics hidden" problem
    that let the v4.18.0–v4.26.0 hollow-features arc ship. The flag remains
    the canonical escape hatch for bootstrapping self-hosted ``.mn`` modules
    that intentionally use not-yet-checked constructs, but every use now
    logs a loud warning to stderr so another developer reading CI logs can
    see when diagnostics were suppressed.
    """
    value = bool(getattr(args, "no_check", False))
    if value:
        print(
            "warning: --no-check bypasses semantic analysis; "
            "type errors, undefined symbols, and trait violations "
            "will NOT be reported.",
            file=sys.stderr,
        )
    return value


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

    # check
    p_check = subparsers.add_parser("check", help="Type-check .mn source")
    p_check.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Path to .mn source file (omit with --all to walk current dir)",
    )
    p_check.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Recursively check every .mn file under the current directory",
    )
    p_check.add_argument(
        "--werror",
        action="store_true",
        default=False,
        help="Treat warnings as errors",
    )
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
    p_run.add_argument(
        "--trace",
        metavar="MODE",
        nargs="?",
        const="console",
        default=None,
        help="Enable tracing: 'console' (default), 'otlp', or 'otlp=http://host:4318'",
    )
    p_run.add_argument(
        "--metrics",
        metavar="ADDR",
        nargs="?",
        const=":9090",
        default=None,
        help="Start Prometheus metrics endpoint (default :9090)",
    )
    _add_opt_level_args(p_run)
    _add_debug_flag(p_run)
    _add_edition_flag(p_run)
    _add_no_verify_flag(p_run)
    p_run.set_defaults(func=cmd_run)

    # fmt
    p_fmt = subparsers.add_parser(
        "fmt",
        help="Format .mn source (canonical whitespace)",
    )
    p_fmt.add_argument(
        "sources",
        nargs="+",
        help="One or more .mn files or directories (directories are scanned recursively)",
    )
    p_fmt.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any file would be reformatted; do not write",
    )
    p_fmt.add_argument(
        "--stdout",
        action="store_true",
        help="Print formatted source to stdout instead of writing in place",
    )
    # v5.14.0 Te.1: surface-syntax conversion modes
    p_fmt.add_argument(
        "--to-terse",
        action="store_true",
        dest="to_terse",
        help="Rewrite brace-block syntax to colon-block syntax",
    )
    p_fmt.add_argument(
        "--to-braces",
        action="store_true",
        dest="to_braces",
        help="Rewrite colon-block syntax to brace-block syntax",
    )
    # v5.19.0 Te.3.B: ``mnc fmt`` (no flag) auto-converts ``{}`` to
    # colon syntax. ``--keep-braces`` opts out for downstream projects
    # mid-migration that want canonical whitespace without surface
    # rewriting.
    p_fmt.add_argument(
        "--keep-braces",
        action="store_true",
        dest="keep_braces",
        help="Suppress automatic {}->colon migration (whitespace-only formatting)",
    )
    # v5.27.0 Mc.8 — long-line detection (detect-only).
    # Mapanare's grammar rejects multi-line expressions, so automatic
    # wrapping cannot satisfy the AST-preservation invariant. ``--line-length``
    # reports overlong lines on stderr and (under ``--check``) treats them as
    # a check failure; the source is never modified.
    p_fmt.add_argument(
        "--line-length",
        type=int,
        default=0,
        metavar="N",
        dest="line_length",
        help="Report lines exceeding N characters (default: 0 = disabled)",
    )
    # v5.27.0 Mc.9 — sort top-level import blocks alphabetically.
    p_fmt.add_argument(
        "--sort-imports",
        action="store_true",
        dest="sort_imports",
        help="Sort contiguous top-level import blocks alphabetically",
    )
    p_fmt.set_defaults(func=cmd_fmt)

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new Mapanare project")
    p_init.add_argument("path", nargs="?", default=".", help="Project directory (default: .)")
    p_init.add_argument("--name", default=None, help="Project name (default: directory name)")
    p_init.add_argument(
        "--docker",
        action="store_true",
        help="Add a multi-stage Dockerfile + .dockerignore using mapanare-builder/-runtime",
    )
    p_init.set_defaults(func=cmd_init)

    # install
    p_install = subparsers.add_parser(
        "install", help="Install packages from registry (or all deps from mapanare.toml)"
    )
    p_install.add_argument(
        "package",
        nargs="?",
        default=None,
        help="Package to install (e.g. foo or foo@1.2.3). Omit to install all deps.",
    )
    p_install.add_argument("--git", default=None, help="Git repository URL (fallback)")
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
    p_build.add_argument(
        "--stdlib-path",
        metavar="PATH",
        help="Path to stdlib directory (default: auto-detect from install)",
        default=None,
    )
    p_build.add_argument(
        "--werror",
        action="store_true",
        default=False,
        help="Treat warnings as errors",
    )
    p_build.add_argument(
        "--lib",
        action="store_true",
        default=False,
        help="Produce a shared library (.so/.dylib/.dll) instead of an executable",
    )
    _add_opt_level_args(p_build)
    _add_debug_flag(p_build)
    _add_edition_flag(p_build)
    _add_no_verify_flag(p_build)
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
    _add_debug_flag(p_emit_llvm)
    _add_edition_flag(p_emit_llvm)
    _add_no_verify_flag(p_emit_llvm)
    p_emit_llvm.set_defaults(func=cmd_emit_llvm)

    # emit-c
    p_emit_c = subparsers.add_parser("emit-c", help="Emit C source for .mn source (v3.0.0)")
    p_emit_c.add_argument("source", help="Path to .mn source file")
    p_emit_c.add_argument("-o", metavar="OUTPUT", help="Output .c file path", default=None)
    _add_opt_level_args(p_emit_c)
    _add_debug_flag(p_emit_c)
    _add_edition_flag(p_emit_c)
    p_emit_c.set_defaults(func=cmd_emit_c)

    # emit-mir
    p_emit_mir = subparsers.add_parser("emit-mir", help="Emit MIR (mid-level IR) for .mn source")
    p_emit_mir.add_argument("source", help="Path to .mn source file")
    p_emit_mir.add_argument("-o", metavar="OUTPUT", help="Output file path", default=None)
    _add_opt_level_args(p_emit_mir)
    p_emit_mir.set_defaults(func=cmd_emit_mir)

    # emit-wasm
    p_emit_wasm = subparsers.add_parser(
        "emit-wasm", help="Emit WebAssembly (WAT/WASM) for .mn source"
    )
    p_emit_wasm.add_argument("source", nargs="+", help="Path to .mn source file(s)")
    p_emit_wasm.add_argument(
        "-o", metavar="OUTPUT", help="Output .wat/.wasm file path", default=None
    )
    p_emit_wasm.add_argument(
        "--binary",
        action="store_true",
        default=False,
        help="Also compile to .wasm binary (requires wat2wasm)",
    )
    p_emit_wasm.add_argument(
        "--link",
        action="store_true",
        default=False,
        help="Link multiple WAT modules into a single .wasm binary (requires wasm-ld)",
    )
    p_emit_wasm.add_argument(
        "--wasi",
        action="store_true",
        default=False,
        help="Link for WASI target (use with --link)",
    )
    p_emit_wasm.add_argument(
        "--export-all",
        action="store_true",
        default=False,
        help="Export all functions (library mode, use with --link)",
    )
    p_emit_wasm.add_argument(
        "--stack-size",
        type=int,
        default=65536,
        help="Stack size in bytes (default: 65536, use with --link)",
    )
    p_emit_wasm.add_argument(
        "--initial-memory",
        type=int,
        default=1048576,
        help="Initial memory in bytes (default: 1048576, use with --link)",
    )
    _add_opt_level_args(p_emit_wasm)
    p_emit_wasm.set_defaults(func=cmd_emit_wasm)

    # lint
    p_lint = subparsers.add_parser("lint", help="Lint .mn source for code quality issues")
    p_lint.add_argument("source", help="Path to .mn source file")
    p_lint.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix lint warnings (unused imports, unnecessary mut)",
    )
    p_lint.set_defaults(func=cmd_lint)

    # migrate
    p_migrate = subparsers.add_parser("migrate", help="Migrate .mn source from v2 to v3 syntax")
    p_migrate.add_argument("path", help="File or directory to migrate")
    p_migrate.add_argument(
        "--to", default="v3", choices=["v3"], help="Target version (default: v3)"
    )
    p_migrate.add_argument("--dry", action="store_true", help="Preview changes without writing")
    p_migrate.add_argument(
        "--check",
        action="store_true",
        help="Check mode: fail if old syntax found (for CI)",
    )
    p_migrate.add_argument(
        "--style",
        default="spanglish",
        choices=["spanglish", "english"],
        help="Keyword style: spanglish (default) or english",
    )
    p_migrate.set_defaults(func=cmd_migrate)

    # build-multi
    p_build_multi = subparsers.add_parser(
        "build-multi", help="Compile multiple .mn files into linked LLVM IR"
    )
    p_build_multi.add_argument("sources", nargs="+", help="Paths to .mn source files")
    p_build_multi.add_argument("-o", metavar="OUTPUT", help="Output .ll file path", default=None)
    p_build_multi.add_argument("--target", metavar="TARGET", help="Target triple", default=None)
    p_build_multi.add_argument(
        "--no-check",
        action="store_true",
        default=False,
        help="Skip semantic checking (for bootstrapping self-hosted modules)",
    )
    _add_opt_level_args(p_build_multi)
    _add_no_verify_flag(p_build_multi)
    p_build_multi.set_defaults(func=cmd_build_multi)

    # targets
    p_targets = subparsers.add_parser("targets", help="List supported compilation targets")
    p_targets.set_defaults(func=cmd_targets)

    # test
    p_test = subparsers.add_parser("test", help="Run @test functions in .mn files")
    p_test.add_argument(
        "path", nargs="?", default=".", help="File or directory to search for tests (default: .)"
    )
    p_test.add_argument(
        "--filter",
        metavar="PATTERN",
        default=None,
        help="Only run tests whose name contains PATTERN",
    )
    p_test.set_defaults(func=cmd_test)

    # doc
    p_doc = subparsers.add_parser("doc", help="Generate HTML docs from doc comments")
    p_doc.add_argument("source", help="Path to .mn source file")
    p_doc.add_argument("-o", metavar="OUTPUT", help="Output .html file path", default=None)
    p_doc.set_defaults(func=cmd_doc)

    # lsp
    p_lsp = subparsers.add_parser("lsp", help="Start the Mapanare language server (LSP over stdio)")
    p_lsp.set_defaults(func=cmd_lsp)

    # deploy
    p_deploy = subparsers.add_parser(
        "deploy", help="Generate Dockerfile + docker-compose.yml for deployment"
    )
    p_deploy.add_argument("path", nargs="?", default=".", help="Project directory (default: .)")
    p_deploy.add_argument(
        "--entry",
        metavar="FILE",
        default="main.mn",
        help="Entry point .mn file (default: main.mn)",
    )
    p_deploy.set_defaults(func=cmd_deploy)

    # transpile (Python → Mapanare)
    p_transpile = subparsers.add_parser(
        "transpile", help="Transpile Python (.py) or PHP (.php) source to Mapanare (.mn)"
    )
    p_transpile.add_argument("source", help="Path to .py or .php source file")
    p_transpile.add_argument("-o", metavar="OUTPUT", help="Output .mn file path", default=None)
    p_transpile.set_defaults(func=cmd_transpile)

    # bind — generate FFI bindings
    p_bind = subparsers.add_parser(
        "bind", help="Generate FFI bindings from .mn source (Python, TypeScript, Go)"
    )
    p_bind.add_argument("source", help="Path to .mn source file")
    p_bind.add_argument(
        "--lang",
        required=True,
        choices=["python", "ts", "go"],
        help="Target language for bindings",
    )
    p_bind.add_argument("-o", metavar="OUTPUT", help="Output file path", default=None)
    _add_no_verify_flag(p_bind)
    p_bind.set_defaults(func=cmd_bind)

    return parser


def main() -> None:
    """CLI entry point."""
    if _should_show_dev_banner(sys.argv):
        print(
            f"[mapanare dev] running from source clone ({Path(__file__).resolve()}). "
            "Set MAPANARE_RELEASE=1 or install via the SDK to silence.",
            file=sys.stderr,
        )
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
