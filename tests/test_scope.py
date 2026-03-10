"""Tests for Phase 1.1 — Scope Reduction.

Verifies that experimental modules are isolated from the core compiler
and that `import mapanare` doesn't pull in heavy dependencies.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ── Task 1-3: Experimental modules moved out of mapanare/ ──


class TestExperimentalIsolation:
    """Verify gpu.py, model.py, tensor.py are in experimental/, not mapanare/."""

    def test_gpu_not_in_core(self) -> None:
        assert not (ROOT / "mapanare" / "gpu.py").exists()
        assert (ROOT / "experimental" / "gpu.py").exists()

    def test_model_not_in_core(self) -> None:
        assert not (ROOT / "mapanare" / "model.py").exists()
        assert (ROOT / "experimental" / "model.py").exists()

    def test_tensor_not_in_core(self) -> None:
        assert not (ROOT / "mapanare" / "tensor.py").exists()
        assert (ROOT / "experimental" / "tensor.py").exists()

    def test_experimental_has_init(self) -> None:
        assert (ROOT / "experimental" / "__init__.py").exists()


# ── Task 6: import mapanare doesn't pull in torch/numpy/onnx ──


class TestNoDependencyLeakage:
    """Verify that importing the core compiler doesn't load experimental deps."""

    def test_import_mapanare_no_torch(self) -> None:
        # Force re-import to be safe
        importlib.import_module("mapanare")
        assert "torch" not in sys.modules

    def test_import_mapanare_no_numpy(self) -> None:
        importlib.import_module("mapanare")
        assert "numpy" not in sys.modules

    def test_import_mapanare_no_onnx(self) -> None:
        importlib.import_module("mapanare")
        assert "onnx" not in sys.modules

    def test_import_mapanare_no_tensorflow(self) -> None:
        importlib.import_module("mapanare")
        assert "tensorflow" not in sys.modules

    def test_semantic_no_toplevel_experimental_import(self) -> None:
        """The semantic module should not have top-level imports from experimental."""
        import mapanare.semantic as sem

        source = Path(sem.__file__).read_text()  # type: ignore[arg-type]
        # Ensure no top-level (non-lazy) imports from experimental
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""'):
                continue
            # Top-level imports are at indent 0
            if line and not line[0].isspace():
                assert (
                    "experimental." not in line
                ), f"Top-level import from experimental found: {line}"


# ── Tasks 1-3: Validation utilities moved to types.py ──


class TestValidationInTypes:
    """Verify that shape validation and device annotations are in types.py."""

    def test_device_annotations_in_types(self) -> None:
        from mapanare.types import DEVICE_ANNOTATIONS

        assert "gpu" in DEVICE_ANNOTATIONS
        assert "cpu" in DEVICE_ANNOTATIONS
        assert "cuda" in DEVICE_ANNOTATIONS

    def test_resolve_shape_in_types(self) -> None:
        from mapanare.types import resolve_shape_from_type

        assert callable(resolve_shape_from_type)

    def test_validate_matmul_in_types(self) -> None:
        from mapanare.types import validate_matmul_shapes

        assert validate_matmul_shapes((2, 3), (3, 4)) == (2, 4)
        assert validate_matmul_shapes((2, 3), (4, 5)) is None
