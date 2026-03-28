"""Tests for the WASM linker module -- wasm-ld integration.

Tests cover:
  1. Linker config defaults and presets
  2. wasm-ld binary discovery (mocked)
  3. Link command generation for browser target
  4. Link command generation for WASI target
  5. Export-all library mode
  6. Memory layout flags (stack size, initial/max memory)
  7. Import-memory for JS-provided memory
  8. Error handling (wasm-ld not found, missing files)
  9. WAT to WASM object conversion
  10. High-level link_wat_files pipeline
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from mapanare.wasm_linker import (
    WasmLinkerConfig,
    WasmLinkResult,
    _build_link_command,
    find_wasm_ld,
    find_wat2wasm,
    link_wasm_modules,
    link_wat_files,
    link_with_wasi,
    wat_to_wasm_object,
)

# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestWasmLinkerConfig:
    """Test WasmLinkerConfig defaults and presets."""

    def test_defaults(self) -> None:
        config = WasmLinkerConfig()
        assert config.target == "wasm32-unknown-unknown"
        assert config.stack_size == 65536
        assert config.initial_memory == 1048576
        assert config.max_memory is None
        assert config.export_all is False
        assert "main" in config.exports
        assert "memory" in config.exports
        assert config.entry == "_start"
        assert config.allow_undefined is False
        assert config.import_memory is False
        assert config.shared_memory is False

    def test_initial_memory_pages(self) -> None:
        config = WasmLinkerConfig(initial_memory=1048576)  # 1MB
        assert config.initial_memory_pages == 16  # 1MB / 64KB

    def test_initial_memory_pages_rounds_up(self) -> None:
        config = WasmLinkerConfig(initial_memory=70000)  # slightly over 1 page
        assert config.initial_memory_pages == 2

    def test_max_memory_pages_none(self) -> None:
        config = WasmLinkerConfig(max_memory=None)
        assert config.max_memory_pages is None

    def test_max_memory_pages_set(self) -> None:
        config = WasmLinkerConfig(max_memory=4 * 1048576)  # 4MB
        assert config.max_memory_pages == 64

    def test_for_browser(self) -> None:
        config = WasmLinkerConfig.for_browser()
        assert config.target == "wasm32-unknown-unknown"
        assert config.entry == ""
        assert config.allow_undefined is True
        assert config.import_memory is True

    def test_for_wasi(self) -> None:
        config = WasmLinkerConfig.for_wasi()
        assert config.target == "wasm32-wasi"
        assert config.entry == "_start"
        assert config.allow_undefined is False
        assert config.import_memory is False
        assert "_start" in config.exports

    def test_for_library(self) -> None:
        config = WasmLinkerConfig.for_library()
        assert config.export_all is True
        assert config.entry == ""
        assert config.allow_undefined is True


# ---------------------------------------------------------------------------
# Tool discovery tests
# ---------------------------------------------------------------------------


class TestFindTools:
    """Test wasm-ld and wat2wasm binary discovery."""

    @patch("mapanare.wasm_linker.shutil.which", return_value="/usr/bin/wasm-ld")
    def test_find_wasm_ld_on_path(self, mock_which: MagicMock) -> None:
        result = find_wasm_ld()
        assert result == "/usr/bin/wasm-ld"
        mock_which.assert_called_with("wasm-ld")

    @patch("mapanare.wasm_linker.shutil.which", return_value=None)
    def test_find_wasm_ld_not_found(self, mock_which: MagicMock) -> None:
        with patch("pathlib.Path.is_file", return_value=False):
            result = find_wasm_ld()
            assert result is None

    @patch("mapanare.wasm_linker.shutil.which")
    def test_find_wasm_ld_versioned(self, mock_which: MagicMock) -> None:
        def side_effect(name: str) -> str | None:
            if name == "wasm-ld-17":
                return "/usr/bin/wasm-ld-17"
            return None

        mock_which.side_effect = side_effect
        with patch("pathlib.Path.is_file", return_value=False):
            result = find_wasm_ld()
            assert result == "/usr/bin/wasm-ld-17"

    @patch("mapanare.wasm_linker.shutil.which", return_value="/usr/bin/wat2wasm")
    def test_find_wat2wasm(self, mock_which: MagicMock) -> None:
        result = find_wat2wasm()
        assert result == "/usr/bin/wat2wasm"


# ---------------------------------------------------------------------------
# Command building tests
# ---------------------------------------------------------------------------


class TestBuildLinkCommand:
    """Test wasm-ld command line generation."""

    def test_browser_target_command(self) -> None:
        config = WasmLinkerConfig.for_browser()
        cmd = _build_link_command(
            "wasm-ld",
            [Path("a.o"), Path("b.o")],
            Path("out.wasm"),
            config,
        )
        assert cmd[0] == "wasm-ld"
        assert "--stack-first" in cmd
        assert "--no-entry" in cmd
        assert "--allow-undefined" in cmd
        assert "--import-memory" in cmd
        assert "a.o" in cmd
        assert "b.o" in cmd
        assert "-o" in cmd
        assert "out.wasm" in cmd

    def test_wasi_target_command(self) -> None:
        config = WasmLinkerConfig.for_wasi()
        cmd = _build_link_command(
            "wasm-ld",
            [Path("main.o")],
            Path("out.wasm"),
            config,
        )
        assert "--entry" in cmd
        idx = cmd.index("--entry")
        assert cmd[idx + 1] == "_start"
        assert "--no-entry" not in cmd
        assert "--allow-undefined" not in cmd

    def test_export_all_library_mode(self) -> None:
        config = WasmLinkerConfig.for_library()
        cmd = _build_link_command(
            "wasm-ld",
            [Path("lib.o")],
            Path("lib.wasm"),
            config,
        )
        assert "--export-all" in cmd
        # Should NOT have individual --export flags when export_all is set
        assert "--export" not in cmd

    def test_explicit_exports(self) -> None:
        config = WasmLinkerConfig(exports=["main", "memory", "my_func"])
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        export_indices = [i for i, x in enumerate(cmd) if x == "--export"]
        assert len(export_indices) == 3
        exported_names = [cmd[i + 1] for i in export_indices]
        assert "main" in exported_names
        assert "memory" in exported_names
        assert "my_func" in exported_names

    def test_memory_layout_flags(self) -> None:
        config = WasmLinkerConfig(
            stack_size=131072,  # 128KB
            initial_memory=2097152,  # 2MB
            max_memory=4194304,  # 4MB
        )
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--stack-first" in cmd
        idx_stack = cmd.index("--stack-size")
        assert cmd[idx_stack + 1] == "131072"
        idx_init = cmd.index("--initial-memory")
        assert cmd[idx_init + 1] == "2097152"
        idx_max = cmd.index("--max-memory")
        assert cmd[idx_max + 1] == "4194304"

    def test_no_max_memory_flag_when_none(self) -> None:
        config = WasmLinkerConfig(max_memory=None)
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--max-memory" not in cmd

    def test_import_memory_browser(self) -> None:
        config = WasmLinkerConfig(import_memory=True)
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--import-memory" in cmd

    def test_shared_memory_flag(self) -> None:
        config = WasmLinkerConfig(shared_memory=True)
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--shared-memory" in cmd

    def test_import_table_flag(self) -> None:
        config = WasmLinkerConfig(import_table=True)
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--import-table" in cmd

    def test_strip_all_flag(self) -> None:
        config = WasmLinkerConfig(strip_all=True)
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--strip-all" in cmd

    def test_extra_args_passed_through(self) -> None:
        config = WasmLinkerConfig(extra_args=["--verbose", "--gc-sections"])
        cmd = _build_link_command(
            "wasm-ld",
            [Path("mod.o")],
            Path("out.wasm"),
            config,
        )
        assert "--verbose" in cmd
        assert "--gc-sections" in cmd

    def test_extra_libs(self) -> None:
        config = WasmLinkerConfig()
        cmd = _build_link_command(
            "wasm-ld",
            [Path("main.o")],
            Path("out.wasm"),
            config,
            extra_libs=[Path("libc.a")],
        )
        assert "libc.a" in cmd


# ---------------------------------------------------------------------------
# Linking tests (mocked subprocess)
# ---------------------------------------------------------------------------


class TestLinkWasmModules:
    """Test link_wasm_modules with mocked wasm-ld."""

    @patch("mapanare.wasm_linker.find_wasm_ld", return_value=None)
    def test_wasm_ld_not_found(self, mock_find: MagicMock) -> None:
        result = link_wasm_modules(
            [Path("a.o")],
            Path("out.wasm"),
        )
        assert result.success is False
        assert "wasm-ld not found" in result.stderr

    @patch("mapanare.wasm_linker.find_wasm_ld", return_value="/usr/bin/wasm-ld")
    def test_missing_object_file(self, mock_find: MagicMock, tmp_path: Path) -> None:
        result = link_wasm_modules(
            [tmp_path / "nonexistent.o"],
            tmp_path / "out.wasm",
        )
        assert result.success is False
        assert "not found" in result.stderr

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wasm_ld", return_value="/usr/bin/wasm-ld")
    def test_successful_link(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        # Create fake object files
        obj1 = tmp_path / "a.o"
        obj2 = tmp_path / "b.o"
        obj1.write_bytes(b"\x00")
        obj2.write_bytes(b"\x00")

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = link_wasm_modules(
            [obj1, obj2],
            tmp_path / "out.wasm",
        )
        assert result.success is True
        assert result.output_path == tmp_path / "out.wasm"
        assert len(result.command) > 0

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wasm_ld", return_value="/usr/bin/wasm-ld")
    def test_link_failure(self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path) -> None:
        obj = tmp_path / "bad.o"
        obj.write_bytes(b"\x00")

        mock_run.return_value = MagicMock(
            returncode=1, stderr="wasm-ld: error: bad.o: not a valid object file"
        )

        result = link_wasm_modules([obj], tmp_path / "out.wasm")
        assert result.success is False
        assert "not a valid object file" in result.stderr

    @patch("mapanare.wasm_linker.subprocess.run", side_effect=FileNotFoundError)
    @patch("mapanare.wasm_linker.find_wasm_ld", return_value="/usr/bin/wasm-ld")
    def test_link_binary_disappeared(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        obj = tmp_path / "a.o"
        obj.write_bytes(b"\x00")

        result = link_wasm_modules([obj], tmp_path / "out.wasm")
        assert result.success is False
        assert "disappeared" in result.stderr


# ---------------------------------------------------------------------------
# WASI linking tests
# ---------------------------------------------------------------------------


class TestLinkWithWasi:
    """Test WASI-specific linking."""

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wasm_ld", return_value="/usr/bin/wasm-ld")
    def test_wasi_link_with_sysroot(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        obj = tmp_path / "main.o"
        obj.write_bytes(b"\x00")
        sysroot = tmp_path / "wasi-sysroot"
        libc_dir = sysroot / "lib" / "wasm32-wasi"
        libc_dir.mkdir(parents=True)
        libc = libc_dir / "libc.a"
        libc.write_bytes(b"\x00")

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = link_with_wasi([obj], tmp_path / "out.wasm", wasi_sysroot=sysroot)
        assert result.success is True
        # Verify libc.a was included in the command
        cmd_str = " ".join(result.command)
        assert "libc.a" in cmd_str

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wasm_ld", return_value="/usr/bin/wasm-ld")
    def test_wasi_link_default_config(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        obj = tmp_path / "main.o"
        obj.write_bytes(b"\x00")

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = link_with_wasi([obj], tmp_path / "out.wasm")
        assert result.success is True
        # Default WASI config should use _start entry
        assert "--entry" in result.command
        idx = result.command.index("--entry")
        assert result.command[idx + 1] == "_start"


# ---------------------------------------------------------------------------
# WAT to object conversion tests
# ---------------------------------------------------------------------------


class TestWatToWasmObject:
    """Test WAT to WASM object file conversion."""

    @patch("mapanare.wasm_linker.find_wat2wasm", return_value=None)
    def test_wat2wasm_not_found(self, mock_find: MagicMock, tmp_path: Path) -> None:
        result = wat_to_wasm_object(
            tmp_path / "test.wat",
            tmp_path / "test.o",
        )
        assert result is False

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wat2wasm", return_value="/usr/bin/wat2wasm")
    def test_successful_conversion(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = wat_to_wasm_object(
            tmp_path / "test.wat",
            tmp_path / "test.o",
            relocatable=True,
        )
        assert result is True
        # Verify --relocatable was passed
        call_args = mock_run.call_args[0][0]
        assert "--relocatable" in call_args

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wat2wasm", return_value="/usr/bin/wat2wasm")
    def test_conversion_without_relocatable(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        result = wat_to_wasm_object(
            tmp_path / "test.wat",
            tmp_path / "test.o",
            relocatable=False,
        )
        assert result is True
        call_args = mock_run.call_args[0][0]
        assert "--relocatable" not in call_args

    @patch("mapanare.wasm_linker.subprocess.run")
    @patch("mapanare.wasm_linker.find_wat2wasm", return_value="/usr/bin/wat2wasm")
    def test_conversion_failure(
        self, mock_find: MagicMock, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="syntax error")
        result = wat_to_wasm_object(
            tmp_path / "bad.wat",
            tmp_path / "bad.o",
        )
        assert result is False


# ---------------------------------------------------------------------------
# High-level pipeline tests
# ---------------------------------------------------------------------------


class TestLinkWatFiles:
    """Test the high-level link_wat_files pipeline."""

    def test_empty_input(self) -> None:
        result = link_wat_files([], Path("out.wasm"))
        assert result.success is False
        assert "No WAT files" in result.stderr

    @patch("mapanare.wasm_linker.link_wasm_modules")
    @patch("mapanare.wasm_linker.wat_to_wasm_object", return_value=True)
    def test_pipeline_calls_wat2wasm_then_linker(
        self, mock_wat2wasm: MagicMock, mock_link: MagicMock, tmp_path: Path
    ) -> None:
        wat1 = tmp_path / "a.wat"
        wat2 = tmp_path / "b.wat"
        wat1.write_text("(module)")
        wat2.write_text("(module)")

        mock_link.return_value = WasmLinkResult(success=True, output_path=tmp_path / "out.wasm")

        result = link_wat_files([wat1, wat2], tmp_path / "out.wasm")
        assert result.success is True
        # wat2wasm called once per WAT file
        assert mock_wat2wasm.call_count == 2
        # linker called once
        assert mock_link.call_count == 1

    @patch("mapanare.wasm_linker.wat_to_wasm_object", return_value=False)
    def test_pipeline_fails_on_assembly_error(
        self, mock_wat2wasm: MagicMock, tmp_path: Path
    ) -> None:
        wat = tmp_path / "bad.wat"
        wat.write_text("(module)")

        result = link_wat_files([wat], tmp_path / "out.wasm")
        assert result.success is False
        assert "Failed to assemble" in result.stderr

    @patch("mapanare.wasm_linker.link_with_wasi")
    @patch("mapanare.wasm_linker.wat_to_wasm_object", return_value=True)
    def test_pipeline_uses_wasi_linker_for_wasi_target(
        self, mock_wat2wasm: MagicMock, mock_wasi_link: MagicMock, tmp_path: Path
    ) -> None:
        wat = tmp_path / "main.wat"
        wat.write_text("(module)")

        mock_wasi_link.return_value = WasmLinkResult(
            success=True, output_path=tmp_path / "out.wasm"
        )

        config = WasmLinkerConfig.for_wasi()
        result = link_wat_files([wat], tmp_path / "out.wasm", config=config)
        assert result.success is True
        assert mock_wasi_link.call_count == 1


# ---------------------------------------------------------------------------
# WasmModuleImport tests (emit_wasm.py integration)
# ---------------------------------------------------------------------------


class TestWasmModuleImport:
    """Test cross-module import emission in the WASM emitter."""

    def test_module_import_dataclass(self) -> None:
        from mapanare.emit_wasm import WasmModuleImport

        imp = WasmModuleImport(
            module="math_utils",
            name="add",
            params=["i64", "i64"],
            result="i64",
        )
        assert imp.module == "math_utils"
        assert imp.name == "add"
        assert imp.params == ["i64", "i64"]
        assert imp.result == "i64"

    def test_module_import_void_return(self) -> None:
        from mapanare.emit_wasm import WasmModuleImport

        imp = WasmModuleImport(
            module="logger",
            name="log_message",
            params=["i32", "i32"],
        )
        assert imp.result is None
