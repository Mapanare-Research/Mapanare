"""Experimental Mapanare modules — not part of the default build.

These modules are under active development and may change or be removed.
They are NOT imported by ``import mapanare`` and are excluded from the
default package distribution.

Modules:
  - tensor: CPU tensor runtime (shape validation, matmul, element-wise ops)
  - gpu: GPU device detection and kernel dispatch abstractions
  - model: Model loading (native .mnw, ONNX, safetensors)
"""
