"""Shared fixtures for native runtime tests."""

import pytest

from runtime.native_bridge import NATIVE_AVAILABLE

# Skip all tests in this directory if the native library is not built
pytestmark = pytest.mark.skipif(
    not NATIVE_AVAILABLE,
    reason="Native runtime not built — run: python runtime/native/build_native.py",
)
