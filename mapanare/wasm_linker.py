"""wasm-ld linker integration for multi-module WASM linking.

Provides wasm-ld invocation for combining multiple WASM object files
into a single binary, with support for:
- Memory layout configuration (stack size, heap start, data segments)
- Import/export table management
- Library vs executable export modes
- Browser (wasm32-unknown-unknown) and WASI (wasm32-wasi) targets
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_WASM_PAGE_SIZE = 65536  # 64KB per WASM page


@dataclass
class WasmLinkerConfig:
    """Configuration for wasm-ld linking."""

    target: str = "wasm32-unknown-unknown"  # or "wasm32-wasi"
    stack_size: int = 65536  # 64KB default stack
    initial_memory: int = 1048576  # 1MB initial memory
    max_memory: int | None = None  # None = growable
    export_all: bool = False  # --export-all for library mode
    exports: list[str] = field(default_factory=lambda: ["main", "memory"])
    entry: str = "_start"  # entry point (WASI) or "" (no entry, reactor)
    allow_undefined: bool = False  # --allow-undefined for browser imports
    import_memory: bool = False  # --import-memory for JS-provided memory
    shared_memory: bool = False  # --shared-memory for threading
    import_table: bool = False  # --import-table for indirect calls
    strip_all: bool = False  # --strip-all to remove debug info
    extra_args: list[str] = field(default_factory=list)

    @property
    def initial_memory_pages(self) -> int:
        """Initial memory size in WASM pages (64KB each)."""
        return (self.initial_memory + _WASM_PAGE_SIZE - 1) // _WASM_PAGE_SIZE

    @property
    def max_memory_pages(self) -> int | None:
        """Maximum memory size in WASM pages, or None for growable."""
        if self.max_memory is None:
            return None
        return (self.max_memory + _WASM_PAGE_SIZE - 1) // _WASM_PAGE_SIZE

    @classmethod
    def for_browser(cls) -> WasmLinkerConfig:
        """Create a config suitable for browser execution."""
        return cls(
            target="wasm32-unknown-unknown",
            entry="",
            allow_undefined=True,
            import_memory=True,
            exports=["main", "_start", "_initialize"],
        )

    @classmethod
    def for_wasi(cls) -> WasmLinkerConfig:
        """Create a config suitable for WASI execution."""
        return cls(
            target="wasm32-wasi",
            entry="_start",
            allow_undefined=False,
            import_memory=False,
            exports=["main", "memory", "_start"],
        )

    @classmethod
    def for_library(cls) -> WasmLinkerConfig:
        """Create a config for building a WASM library."""
        return cls(
            target="wasm32-unknown-unknown",
            entry="",
            export_all=True,
            allow_undefined=True,
        )


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class WasmLinkResult:
    """Result of a wasm-ld invocation."""

    success: bool
    output_path: Path | None = None
    stderr: str = ""
    command: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------


def find_wasm_ld() -> str | None:
    """Find wasm-ld binary on the system.

    Checks:
    1. ``wasm-ld`` on PATH
    2. ``wasm-ld-*`` versioned binaries on PATH (e.g. wasm-ld-17)
    3. Common LLVM installation directories

    Returns:
        Path to wasm-ld binary, or None if not found.
    """
    # Check plain wasm-ld
    path = shutil.which("wasm-ld")
    if path:
        return path

    # Check versioned binaries (wasm-ld-15, wasm-ld-16, wasm-ld-17, etc.)
    for version in range(20, 13, -1):
        path = shutil.which(f"wasm-ld-{version}")
        if path:
            return path

    # Check common LLVM installation directories
    import platform as _platform

    system = _platform.system()
    candidates: list[str] = []
    if system == "Linux":
        candidates = [
            "/usr/bin/wasm-ld",
            "/usr/local/bin/wasm-ld",
        ]
        for v in range(20, 13, -1):
            candidates.append(f"/usr/lib/llvm-{v}/bin/wasm-ld")
    elif system == "Darwin":
        candidates = [
            "/opt/homebrew/bin/wasm-ld",
            "/usr/local/opt/llvm/bin/wasm-ld",
        ]
    elif system == "Windows":
        candidates = [
            r"C:\Program Files\LLVM\bin\wasm-ld.exe",
        ]

    for candidate in candidates:
        p = Path(candidate)
        if p.is_file():
            return str(p)

    return None


def find_wat2wasm() -> str | None:
    """Find wat2wasm binary (from WebAssembly Binary Toolkit).

    Returns:
        Path to wat2wasm binary, or None if not found.
    """
    return shutil.which("wat2wasm")


# ---------------------------------------------------------------------------
# WAT to WASM object conversion
# ---------------------------------------------------------------------------


def wat_to_wasm_object(
    wat_path: Path,
    output_path: Path,
    relocatable: bool = True,
) -> bool:
    """Convert WAT to WASM object file using wat2wasm.

    Args:
        wat_path: Path to the .wat source file.
        output_path: Path for the output .wasm or .o file.
        relocatable: If True, produce a relocatable object (``--relocatable``).
            Required for linking with wasm-ld.

    Returns:
        True if conversion succeeded, False otherwise.
    """
    wat2wasm = find_wat2wasm()
    if wat2wasm is None:
        _logger.error("wat2wasm not found; install the WebAssembly Binary Toolkit (wabt)")
        return False

    cmd = [wat2wasm, str(wat_path), "-o", str(output_path)]
    if relocatable:
        cmd.append("--relocatable")

    _logger.debug("wat2wasm command: %s", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        _logger.error("wat2wasm binary disappeared during execution")
        return False
    except subprocess.TimeoutExpired:
        _logger.error("wat2wasm timed out after 30 seconds")
        return False

    if result.returncode != 0:
        _logger.error("wat2wasm failed: %s", result.stderr.strip())
        return False

    return True


# ---------------------------------------------------------------------------
# wasm-ld command building
# ---------------------------------------------------------------------------


def _build_link_command(
    wasm_ld: str,
    object_files: list[Path],
    output: Path,
    config: WasmLinkerConfig,
    extra_libs: list[Path] | None = None,
) -> list[str]:
    """Build the wasm-ld command line from configuration.

    Args:
        wasm_ld: Path to the wasm-ld binary.
        object_files: List of .o/.wasm object files to link.
        output: Output .wasm file path.
        config: Linker configuration.
        extra_libs: Additional library files to link.

    Returns:
        Command as a list of strings.
    """
    cmd = [wasm_ld]

    # Memory layout: stack first, then data, then heap
    cmd.append("--stack-first")
    cmd.extend(["--stack-size", str(config.stack_size)])

    # Initial memory (must be a multiple of page size)
    initial_pages = config.initial_memory_pages
    initial_bytes = initial_pages * _WASM_PAGE_SIZE
    cmd.extend(["--initial-memory", str(initial_bytes)])

    # Max memory
    if config.max_memory is not None:
        max_pages = config.max_memory_pages
        assert max_pages is not None
        max_bytes = max_pages * _WASM_PAGE_SIZE
        cmd.extend(["--max-memory", str(max_bytes)])

    # Entry point
    if config.entry:
        cmd.extend(["--entry", config.entry])
    else:
        cmd.append("--no-entry")

    # Export control
    if config.export_all:
        cmd.append("--export-all")
    else:
        for export_name in config.exports:
            cmd.extend(["--export", export_name])

    # Import flags
    if config.allow_undefined:
        cmd.append("--allow-undefined")

    if config.import_memory:
        cmd.append("--import-memory")

    if config.shared_memory:
        cmd.append("--shared-memory")

    if config.import_table:
        cmd.append("--import-table")

    # Strip
    if config.strip_all:
        cmd.append("--strip-all")

    # Extra args
    cmd.extend(config.extra_args)

    # Input files
    for obj in object_files:
        cmd.append(str(obj))

    # Extra libraries
    if extra_libs:
        for lib in extra_libs:
            cmd.append(str(lib))

    # Output
    cmd.extend(["-o", str(output)])

    return cmd


# ---------------------------------------------------------------------------
# Linking
# ---------------------------------------------------------------------------


def link_wasm_modules(
    object_files: list[Path],
    output: Path,
    config: WasmLinkerConfig | None = None,
) -> WasmLinkResult:
    """Link multiple WASM object files into a single WASM binary using wasm-ld.

    Args:
        object_files: List of .o (relocatable WASM) files to link.
        output: Path for the output .wasm binary.
        config: Optional linker configuration. Defaults to browser config.

    Returns:
        WasmLinkResult with success status, output path, and diagnostics.
    """
    if config is None:
        config = WasmLinkerConfig()

    wasm_ld = find_wasm_ld()
    if wasm_ld is None:
        return WasmLinkResult(
            success=False,
            stderr=(
                "wasm-ld not found. Install LLVM/lld with WebAssembly support:\n"
                "  - Ubuntu/Debian: apt install lld\n"
                "  - macOS: brew install llvm\n"
                "  - Windows: install LLVM from https://releases.llvm.org/"
            ),
        )

    # Validate input files exist
    for obj in object_files:
        if not obj.is_file():
            return WasmLinkResult(
                success=False,
                stderr=f"Object file not found: {obj}",
            )

    cmd = _build_link_command(wasm_ld, object_files, output, config)
    _logger.debug("wasm-ld command: %s", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return WasmLinkResult(
            success=False,
            stderr="wasm-ld binary disappeared during execution",
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        return WasmLinkResult(
            success=False,
            stderr="wasm-ld timed out after 60 seconds",
            command=cmd,
        )

    if result.returncode != 0:
        return WasmLinkResult(
            success=False,
            stderr=result.stderr.strip(),
            command=cmd,
        )

    return WasmLinkResult(
        success=True,
        output_path=output,
        stderr=result.stderr.strip(),
        command=cmd,
    )


def link_with_wasi(
    object_files: list[Path],
    output: Path,
    config: WasmLinkerConfig | None = None,
    wasi_sysroot: Path | None = None,
) -> WasmLinkResult:
    """Link WASM modules with WASI libc for server-side execution.

    This wraps ``link_wasm_modules`` with WASI-specific defaults and
    optionally links against wasi-libc if a sysroot is provided.

    Args:
        object_files: List of .o files to link.
        output: Output .wasm path.
        config: Optional configuration (defaults to WASI preset).
        wasi_sysroot: Path to WASI sysroot (containing lib/wasm32-wasi/libc.a).

    Returns:
        WasmLinkResult with success status and diagnostics.
    """
    if config is None:
        config = WasmLinkerConfig.for_wasi()

    extra_libs: list[Path] = []

    # Look for wasi-libc if sysroot is provided
    if wasi_sysroot is not None:
        libc = wasi_sysroot / "lib" / "wasm32-wasi" / "libc.a"
        if libc.is_file():
            extra_libs.append(libc)
            _logger.info("Linking with wasi-libc: %s", libc)
        else:
            _logger.warning("WASI sysroot provided but libc.a not found at %s", libc)

    wasm_ld = find_wasm_ld()
    if wasm_ld is None:
        return WasmLinkResult(
            success=False,
            stderr="wasm-ld not found. See link_wasm_modules for installation instructions.",
        )

    cmd = _build_link_command(wasm_ld, object_files, output, config, extra_libs=extra_libs)
    _logger.debug("wasm-ld (WASI) command: %s", " ".join(cmd))

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return WasmLinkResult(
            success=False,
            stderr="wasm-ld binary disappeared during execution",
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        return WasmLinkResult(
            success=False,
            stderr="wasm-ld timed out after 60 seconds",
            command=cmd,
        )

    if result.returncode != 0:
        return WasmLinkResult(
            success=False,
            stderr=result.stderr.strip(),
            command=cmd,
        )

    return WasmLinkResult(
        success=True,
        output_path=output,
        stderr=result.stderr.strip(),
        command=cmd,
    )


# ---------------------------------------------------------------------------
# High-level pipeline: WAT files -> linked WASM
# ---------------------------------------------------------------------------


def link_wat_files(
    wat_files: list[Path],
    output: Path,
    config: WasmLinkerConfig | None = None,
    work_dir: Path | None = None,
) -> WasmLinkResult:
    """Compile WAT files to relocatable objects and link them.

    This is the high-level entry point for the multi-module WASM linking
    pipeline: WAT -> .o (via wat2wasm --relocatable) -> .wasm (via wasm-ld).

    Args:
        wat_files: List of .wat source files.
        output: Output .wasm binary path.
        config: Optional linker configuration.
        work_dir: Directory for intermediate .o files. Defaults to output's parent.

    Returns:
        WasmLinkResult with success status and diagnostics.
    """
    if not wat_files:
        return WasmLinkResult(success=False, stderr="No WAT files provided")

    if work_dir is None:
        work_dir = output.parent

    # Step 1: Convert each WAT to a relocatable object
    object_files: list[Path] = []
    for idx, wat in enumerate(wat_files):
        obj_path = work_dir / (f"{idx}_{wat.stem}.o")
        if not wat_to_wasm_object(wat, obj_path, relocatable=True):
            return WasmLinkResult(
                success=False,
                stderr=f"Failed to assemble {wat} to relocatable object",
            )
        object_files.append(obj_path)

    # Step 2: Link all objects
    is_wasi = config is not None and config.target == "wasm32-wasi"
    if is_wasi:
        return link_with_wasi(object_files, output, config=config)
    return link_wasm_modules(object_files, output, config=config)
