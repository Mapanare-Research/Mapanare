from __future__ import annotations

import sys
from pathlib import Path

import mapanare.toolchain as toolchain


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return path


def _pyinstaller_root(monkeypatch, root: Path) -> None:
    exe = _touch(root / "mapanare.exe")
    monkeypatch.setattr(sys, "executable", str(exe))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)


def _stub_probe(monkeypatch) -> None:
    monkeypatch.setattr(toolchain, "_probe_compiler", lambda _path: True)
    monkeypatch.setattr(toolchain, "_candidate_install_paths", lambda: [])


def test_pyinstaller_sdk_clang_wins(monkeypatch, tmp_path):
    root = tmp_path / "install"
    sdk_clang = _touch(root / "sdk" / "bin" / "clang.exe")
    _touch(root / "toolchain" / "bin" / "gcc.exe")
    _pyinstaller_root(monkeypatch, root)
    _stub_probe(monkeypatch)
    monkeypatch.setattr(toolchain.shutil, "which", lambda name: f"C:/system/{name}.exe")

    detected = toolchain.detect_toolchain()

    assert detected is not None
    assert detected.name == "clang"
    assert Path(detected.compiler) == sdk_clang
    assert Path(detected.bin_dir or "") == sdk_clang.parent


def test_pyinstaller_legacy_toolchain_gcc_still_works(monkeypatch, tmp_path):
    root = tmp_path / "install"
    legacy_gcc = _touch(root / "toolchain" / "bin" / "gcc.exe")
    _pyinstaller_root(monkeypatch, root)
    _stub_probe(monkeypatch)
    monkeypatch.setattr(toolchain.shutil, "which", lambda _name: None)

    detected = toolchain.detect_toolchain()

    assert detected is not None
    assert detected.name == "gcc"
    assert Path(detected.compiler) == legacy_gcc
    assert Path(detected.bin_dir or "") == legacy_gcc.parent


def test_clang_only_sdk_does_not_fall_through_to_system_gcc(monkeypatch, tmp_path):
    root = tmp_path / "install"
    sdk_clang = _touch(root / "sdk" / "bin" / "clang.exe")
    _pyinstaller_root(monkeypatch, root)
    _stub_probe(monkeypatch)
    monkeypatch.setattr(
        toolchain.shutil,
        "which",
        lambda name: "C:/system/gcc.exe" if name == "gcc" else None,
    )

    detected = toolchain.detect_toolchain()

    assert detected is not None
    assert detected.name == "clang"
    assert Path(detected.compiler) == sdk_clang


def test_bundled_runtime_archive_is_detected(monkeypatch, tmp_path):
    root = tmp_path / "install"
    _touch(root / "sdk" / "bin" / "clang.exe")
    rt_archive = _touch(root / "sdk" / "lib" / "mapanare" / "libmapanare_rt.a")
    _pyinstaller_root(monkeypatch, root)
    _stub_probe(monkeypatch)
    monkeypatch.setattr(toolchain.shutil, "which", lambda _name: None)

    detected = toolchain.detect_toolchain()

    assert detected is not None
    assert detected.rt_archive == str(rt_archive)


def test_no_bundled_sdk_falls_back_to_path(monkeypatch, tmp_path):
    root = tmp_path / "install"
    _pyinstaller_root(monkeypatch, root)
    _stub_probe(monkeypatch)
    system_gcc = "C:/system/gcc.exe"
    monkeypatch.setattr(
        toolchain.shutil,
        "which",
        lambda name: system_gcc if name == "gcc" else None,
    )

    detected = toolchain.detect_toolchain()

    assert detected is not None
    assert detected.name == "gcc"
    assert detected.compiler == system_gcc
    assert detected.bin_dir is None
