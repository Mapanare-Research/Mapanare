"""Tests for WASM and mobile cross-compilation targets (Phase v2.0.0).

Tests cover:
  1. wasm32-unknown-unknown target
  2. wasm32-wasi target
  3. aarch64-apple-ios target
  4. aarch64-linux-android target
  5. x86_64-linux-android target
  6. WASM target data layout
  7. WASM target triple format
  8. WASM target extensions (.wasm)
  9. WASM target linker (wasm-ld)
  10. iOS target triple includes version
  11. Android target triple includes API level
  12. Mobile target linkers (clang variants)
  13. WASM not returned by host_target_name() on x86
  14. All targets have valid data layouts
  15. Target resolution by name
"""

from __future__ import annotations

import pytest

from mapanare.targets import (
    TARGET_AARCH64_APPLE_IOS,
    TARGET_AARCH64_LINUX_ANDROID,
    TARGET_WASM32,
    TARGET_WASM32_WASI,
    TARGET_X86_64_LINUX_ANDROID,
    TARGETS,
    get_target,
    host_target_name,
    list_targets,
)

# ===========================================================================
# 1. wasm32-unknown-unknown target
# ===========================================================================


class TestWasm32Target:
    """Test wasm32-unknown-unknown target definition."""

    def test_wasm32_exists_in_targets(self) -> None:
        assert "wasm32" in TARGETS

    def test_wasm32_is_correct_instance(self) -> None:
        assert TARGETS["wasm32"] is TARGET_WASM32

    def test_wasm32_triple(self) -> None:
        assert TARGET_WASM32.triple == "wasm32-unknown-unknown"

    def test_wasm32_description(self) -> None:
        assert TARGET_WASM32.description
        assert "WebAssembly" in TARGET_WASM32.description or "WASM" in TARGET_WASM32.description

    def test_wasm32_is_frozen(self) -> None:
        with pytest.raises(AttributeError):
            TARGET_WASM32.triple = "changed"  # type: ignore[misc]


# ===========================================================================
# 2. wasm32-wasi target
# ===========================================================================


class TestWasm32WasiTarget:
    """Test wasm32-wasi target definition."""

    def test_wasm32_wasi_exists(self) -> None:
        assert "wasm32-wasi" in TARGETS

    def test_wasm32_wasi_is_correct_instance(self) -> None:
        assert TARGETS["wasm32-wasi"] is TARGET_WASM32_WASI

    def test_wasm32_wasi_triple(self) -> None:
        assert TARGET_WASM32_WASI.triple == "wasm32-wasi"

    def test_wasm32_wasi_description_mentions_wasi(self) -> None:
        assert "WASI" in TARGET_WASM32_WASI.description


# ===========================================================================
# 3. aarch64-apple-ios target
# ===========================================================================


class TestIOSTarget:
    """Test aarch64-apple-ios target definition."""

    def test_ios_exists(self) -> None:
        assert "aarch64-apple-ios" in TARGETS

    def test_ios_is_correct_instance(self) -> None:
        assert TARGETS["aarch64-apple-ios"] is TARGET_AARCH64_APPLE_IOS

    def test_ios_triple_format(self) -> None:
        assert TARGET_AARCH64_APPLE_IOS.triple.startswith("aarch64-apple-ios")

    def test_ios_description(self) -> None:
        assert "iOS" in TARGET_AARCH64_APPLE_IOS.description


# ===========================================================================
# 4. aarch64-linux-android target
# ===========================================================================


class TestAndroidAArch64Target:
    """Test aarch64-linux-android target definition."""

    def test_android_aarch64_exists(self) -> None:
        assert "aarch64-linux-android" in TARGETS

    def test_android_aarch64_is_correct_instance(self) -> None:
        assert TARGETS["aarch64-linux-android"] is TARGET_AARCH64_LINUX_ANDROID

    def test_android_aarch64_triple(self) -> None:
        assert "aarch64-linux-android" in TARGET_AARCH64_LINUX_ANDROID.triple

    def test_android_aarch64_description(self) -> None:
        assert "Android" in TARGET_AARCH64_LINUX_ANDROID.description


# ===========================================================================
# 5. x86_64-linux-android target
# ===========================================================================


class TestAndroidX8664Target:
    """Test x86_64-linux-android target definition."""

    def test_android_x86_64_exists(self) -> None:
        assert "x86_64-linux-android" in TARGETS

    def test_android_x86_64_is_correct_instance(self) -> None:
        assert TARGETS["x86_64-linux-android"] is TARGET_X86_64_LINUX_ANDROID

    def test_android_x86_64_triple(self) -> None:
        assert "x86_64-linux-android" in TARGET_X86_64_LINUX_ANDROID.triple

    def test_android_x86_64_description_mentions_emulator(self) -> None:
        desc = TARGET_X86_64_LINUX_ANDROID.description.lower()
        assert "emulator" in desc or "x86_64" in desc


# ===========================================================================
# 6. WASM target data layout
# ===========================================================================


class TestWASMDataLayout:
    """Test WASM target data layout strings."""

    def test_wasm32_data_layout_little_endian(self) -> None:
        assert TARGET_WASM32.data_layout.startswith("e-")

    def test_wasm32_data_layout_32bit_pointers(self) -> None:
        assert "p:32:32" in TARGET_WASM32.data_layout

    def test_wasm32_data_layout_64bit_i64(self) -> None:
        assert "i64:64" in TARGET_WASM32.data_layout

    def test_wasm32_wasi_same_data_layout(self) -> None:
        """WASM and WASI should share the same data layout."""
        assert TARGET_WASM32.data_layout == TARGET_WASM32_WASI.data_layout


# ===========================================================================
# 7. WASM target triple format
# ===========================================================================


class TestWASMTripleFormat:
    """Test that WASM target triples follow LLVM conventions."""

    def test_wasm32_triple_starts_with_wasm32(self) -> None:
        assert TARGET_WASM32.triple.startswith("wasm32")

    def test_wasm32_wasi_triple_is_wasm32_wasi(self) -> None:
        assert TARGET_WASM32_WASI.triple == "wasm32-wasi"

    def test_wasm32_triple_has_unknown_vendor_os(self) -> None:
        assert "unknown-unknown" in TARGET_WASM32.triple


# ===========================================================================
# 8. WASM target extensions
# ===========================================================================


class TestWASMExtensions:
    """Test that WASM target file extensions are correct."""

    def test_wasm32_exe_ext(self) -> None:
        assert TARGET_WASM32.exe_ext == ".wasm"

    def test_wasm32_lib_ext(self) -> None:
        assert TARGET_WASM32.lib_ext == ".wasm"

    def test_wasm32_obj_ext(self) -> None:
        assert TARGET_WASM32.obj_ext == ".o"

    def test_wasm32_wasi_exe_ext(self) -> None:
        assert TARGET_WASM32_WASI.exe_ext == ".wasm"

    def test_wasm32_wasi_lib_ext(self) -> None:
        assert TARGET_WASM32_WASI.lib_ext == ".wasm"


# ===========================================================================
# 9. WASM target linker
# ===========================================================================


class TestWASMLinker:
    """Test that WASM targets use wasm-ld."""

    def test_wasm32_linker(self) -> None:
        assert TARGET_WASM32.linker == "wasm-ld"

    def test_wasm32_wasi_linker(self) -> None:
        assert TARGET_WASM32_WASI.linker == "wasm-ld"


# ===========================================================================
# 10. iOS target triple includes version
# ===========================================================================


class TestIOSTripleVersion:
    """Test that iOS target triple encodes minimum deployment version."""

    def test_ios_triple_has_version_number(self) -> None:
        triple = TARGET_AARCH64_APPLE_IOS.triple
        # Should be like "aarch64-apple-ios17.0"
        assert "ios" in triple
        # Extract version suffix after "ios"
        ios_idx = triple.index("ios")
        version_part = triple[ios_idx + 3 :]
        assert version_part, "iOS triple should include version number"
        # Version should start with a digit
        assert version_part[0].isdigit(), f"Expected version digit, got: {version_part}"

    def test_ios_minimum_version_reasonable(self) -> None:
        triple = TARGET_AARCH64_APPLE_IOS.triple
        ios_idx = triple.index("ios")
        version_str = triple[ios_idx + 3 :].split(".")[0]
        version = int(version_str)
        assert version >= 14, f"iOS minimum version {version} seems too low"


# ===========================================================================
# 11. Android target triple includes API level
# ===========================================================================


class TestAndroidAPILevel:
    """Test that Android target triples encode API level."""

    def test_android_aarch64_has_api_level(self) -> None:
        triple = TARGET_AARCH64_LINUX_ANDROID.triple
        # Should be like "aarch64-linux-android34"
        assert "android" in triple
        android_idx = triple.index("android")
        level_str = triple[android_idx + 7 :]
        assert level_str.isdigit(), f"Expected API level digit, got: {level_str}"

    def test_android_x86_64_has_api_level(self) -> None:
        triple = TARGET_X86_64_LINUX_ANDROID.triple
        assert "android" in triple
        android_idx = triple.index("android")
        level_str = triple[android_idx + 7 :]
        assert level_str.isdigit()

    def test_android_api_level_matches(self) -> None:
        """Both Android targets should target the same API level."""
        triple_arm = TARGET_AARCH64_LINUX_ANDROID.triple
        triple_x86 = TARGET_X86_64_LINUX_ANDROID.triple
        arm_level = triple_arm[triple_arm.index("android") + 7 :]
        x86_level = triple_x86[triple_x86.index("android") + 7 :]
        assert arm_level == x86_level

    def test_android_api_level_reasonable(self) -> None:
        triple = TARGET_AARCH64_LINUX_ANDROID.triple
        level = int(triple[triple.index("android") + 7 :])
        assert level >= 21, f"Android API level {level} seems too low"


# ===========================================================================
# 12. Mobile target linkers
# ===========================================================================


class TestMobileLinkers:
    """Test that mobile targets use correct linker commands."""

    def test_ios_linker_is_clang(self) -> None:
        assert TARGET_AARCH64_APPLE_IOS.linker == "clang"

    def test_android_aarch64_linker_is_ndk_clang(self) -> None:
        linker = TARGET_AARCH64_LINUX_ANDROID.linker
        assert "clang" in linker
        assert "aarch64" in linker

    def test_android_x86_64_linker_is_ndk_clang(self) -> None:
        linker = TARGET_X86_64_LINUX_ANDROID.linker
        assert "clang" in linker
        assert "x86_64" in linker

    def test_android_linkers_include_api_level(self) -> None:
        """Android NDK clang wrappers encode the API level."""
        linker_arm = TARGET_AARCH64_LINUX_ANDROID.linker
        linker_x86 = TARGET_X86_64_LINUX_ANDROID.linker
        # e.g., "aarch64-linux-android34-clang"
        assert any(c.isdigit() for c in linker_arm)
        assert any(c.isdigit() for c in linker_x86)


# ===========================================================================
# 13. WASM not returned by host_target_name()
# ===========================================================================


class TestHostTargetExcludesWASM:
    """Test that host_target_name() never returns a WASM target."""

    def test_host_target_is_not_wasm(self) -> None:
        name = host_target_name()
        assert "wasm" not in name.lower()

    def test_host_target_is_not_mobile(self) -> None:
        name = host_target_name()
        assert "ios" not in name.lower()
        assert "android" not in name.lower()

    def test_host_target_is_native(self) -> None:
        name = host_target_name()
        # Should be one of the desktop targets
        assert name in (
            "x86_64-linux-gnu",
            "aarch64-apple-macos",
            "x86_64-windows-msvc",
            "x86_64-windows-gnu",
        )


# ===========================================================================
# 14. All targets have valid data layouts
# ===========================================================================


class TestAllTargetsValid:
    """Test that every registered target has all required fields."""

    def test_all_targets_have_triple(self) -> None:
        for name, target in TARGETS.items():
            assert target.triple, f"{name}: missing triple"

    def test_all_targets_have_data_layout(self) -> None:
        for name, target in TARGETS.items():
            assert target.data_layout, f"{name}: missing data_layout"
            # All data layouts should start with "e-" (little-endian)
            assert target.data_layout.startswith(
                "e-"
            ), f"{name}: data_layout should be little-endian"

    def test_all_targets_have_description(self) -> None:
        for name, target in TARGETS.items():
            assert target.description, f"{name}: missing description"

    def test_all_targets_have_linker(self) -> None:
        for name, target in TARGETS.items():
            assert target.linker, f"{name}: missing linker"

    def test_all_targets_have_extensions(self) -> None:
        for name, target in TARGETS.items():
            # obj_ext and lib_ext must be non-empty
            assert target.obj_ext, f"{name}: missing obj_ext"
            assert target.lib_ext, f"{name}: missing lib_ext"
            # exe_ext can be empty (ELF, Mach-O) but must be defined

    def test_all_targets_are_frozen(self) -> None:
        for name, target in TARGETS.items():
            with pytest.raises(AttributeError):
                target.triple = "hacked"  # type: ignore[misc]


# ===========================================================================
# 15. Target resolution by name
# ===========================================================================


class TestTargetResolution:
    """Test get_target() and list_targets() with new targets."""

    def test_get_wasm32_by_name(self) -> None:
        target = get_target("wasm32")
        assert target is TARGET_WASM32

    def test_get_wasm32_wasi_by_name(self) -> None:
        target = get_target("wasm32-wasi")
        assert target is TARGET_WASM32_WASI

    def test_get_ios_by_name(self) -> None:
        target = get_target("aarch64-apple-ios")
        assert target is TARGET_AARCH64_APPLE_IOS

    def test_get_android_aarch64_by_name(self) -> None:
        target = get_target("aarch64-linux-android")
        assert target is TARGET_AARCH64_LINUX_ANDROID

    def test_get_android_x86_64_by_name(self) -> None:
        target = get_target("x86_64-linux-android")
        assert target is TARGET_X86_64_LINUX_ANDROID

    def test_list_targets_includes_wasm(self) -> None:
        targets = list_targets()
        names = [name for name, _ in targets]
        assert "wasm32" in names
        assert "wasm32-wasi" in names

    def test_list_targets_includes_mobile(self) -> None:
        targets = list_targets()
        names = [name for name, _ in targets]
        assert "aarch64-apple-ios" in names
        assert "aarch64-linux-android" in names
        assert "x86_64-linux-android" in names

    def test_list_targets_sorted_alphabetically(self) -> None:
        targets = list_targets()
        names = [name for name, _ in targets]
        assert names == sorted(names)

    def test_total_target_count(self) -> None:
        """v2.0.0 should have 9 targets: 4 desktop + 2 WASM + 3 mobile."""
        assert len(TARGETS) == 9
