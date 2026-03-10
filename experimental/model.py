"""Model loading for Mapanare — native format, ONNX, safetensors, registry.

Phase 5.3: Model Loading
  - Native .mnw model format and loader
  - ONNX import
  - Safetensors / HuggingFace import
  - Standard model interface: predict, encode, generate
  - Model registry: mapanare://models/
"""

from __future__ import annotations

import hashlib
import json
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable

from experimental.tensor import Numeric, Tensor

# ---------------------------------------------------------------------------
# Tensor data types for serialization
# ---------------------------------------------------------------------------


class DType(Enum):
    """Supported tensor element types for serialization."""

    FLOAT32 = auto()
    FLOAT64 = auto()
    INT32 = auto()
    INT64 = auto()
    BOOL = auto()

    @property
    def byte_size(self) -> int:
        """Number of bytes per element."""
        sizes = {
            DType.FLOAT32: 4,
            DType.FLOAT64: 8,
            DType.INT32: 4,
            DType.INT64: 8,
            DType.BOOL: 1,
        }
        return sizes[self]

    @property
    def struct_format(self) -> str:
        """Python struct format character for this dtype."""
        formats = {
            DType.FLOAT32: "f",
            DType.FLOAT64: "d",
            DType.INT32: "i",
            DType.INT64: "q",
            DType.BOOL: "?",
        }
        return formats[self]


# ---------------------------------------------------------------------------
# Task 1: Native .mnw model format and loader
# ---------------------------------------------------------------------------

# MNW format layout:
#   [magic: 4 bytes "MNW\x00"]
#   [version: 4 bytes uint32]
#   [header_size: 8 bytes uint64]
#   [header: JSON bytes, header_size long]
#   [tensor data: contiguous binary blocks]
#
# Header JSON contains:
#   - model_name: str
#   - model_version: str
#   - architecture: str
#   - metadata: dict
#   - tensors: list of {name, dtype, shape, offset, byte_size}

MNW_MAGIC = b"MNW\x00"
MNW_VERSION = 1


@dataclass
class TensorInfo:
    """Metadata about a tensor stored in a model file."""

    name: str
    dtype: str  # DType name (e.g., "FLOAT64")
    shape: tuple[int, ...]
    offset: int  # byte offset from start of tensor data section
    byte_size: int  # total bytes for this tensor's data

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "shape": list(self.shape),
            "offset": self.offset,
            "byte_size": self.byte_size,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> TensorInfo:
        return TensorInfo(
            name=d["name"],
            dtype=d["dtype"],
            shape=tuple(d["shape"]),
            offset=d["offset"],
            byte_size=d["byte_size"],
        )


@dataclass
class MNWHeader:
    """Header for the native .mnw model format."""

    model_name: str
    model_version: str = "1.0.0"
    architecture: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    tensors: list[TensorInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "architecture": self.architecture,
            "metadata": self.metadata,
            "tensors": [t.to_dict() for t in self.tensors],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> MNWHeader:
        return MNWHeader(
            model_name=d["model_name"],
            model_version=d.get("model_version", "1.0.0"),
            architecture=d.get("architecture", ""),
            metadata=d.get("metadata", {}),
            tensors=[TensorInfo.from_dict(t) for t in d.get("tensors", [])],
        )


class ModelFormatError(Exception):
    """Raised when a model file has an invalid format."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def _serialize_tensor_data(tensor: Tensor, dtype: DType) -> bytes:
    """Serialize tensor data to raw bytes."""
    fmt = f"<{tensor.size}{dtype.struct_format}"
    values: list[Any] = list(tensor.data)
    if dtype == DType.BOOL:
        values = [bool(v) for v in values]
    return struct.pack(fmt, *values)


def _deserialize_tensor_data(raw: bytes, dtype: DType, size: int) -> list[Numeric]:
    """Deserialize raw bytes to tensor data."""
    fmt = f"<{size}{dtype.struct_format}"
    values = list(struct.unpack(fmt, raw))
    if dtype == DType.BOOL:
        values = [int(v) for v in values]
    return values


def save_mnw(
    path: str | Path,
    tensors: dict[str, Tensor],
    model_name: str,
    model_version: str = "1.0.0",
    architecture: str = "",
    metadata: dict[str, Any] | None = None,
    dtype: DType = DType.FLOAT64,
) -> None:
    """Save tensors to a .mnw file.

    Args:
        path: Output file path.
        tensors: Dict mapping tensor names to Tensor objects.
        model_name: Name of the model.
        model_version: Version string.
        architecture: Architecture description.
        metadata: Optional extra metadata dict.
        dtype: Data type for serialization.
    """
    path = Path(path)
    tensor_infos: list[TensorInfo] = []
    tensor_data_parts: list[bytes] = []
    offset = 0

    for name, tensor in tensors.items():
        raw = _serialize_tensor_data(tensor, dtype)
        tensor_infos.append(
            TensorInfo(
                name=name,
                dtype=dtype.name,
                shape=tensor.shape,
                offset=offset,
                byte_size=len(raw),
            )
        )
        tensor_data_parts.append(raw)
        offset += len(raw)

    header = MNWHeader(
        model_name=model_name,
        model_version=model_version,
        architecture=architecture,
        metadata=metadata or {},
        tensors=tensor_infos,
    )

    header_json = json.dumps(header.to_dict(), separators=(",", ":")).encode("utf-8")
    header_size = len(header_json)

    with open(path, "wb") as f:
        f.write(MNW_MAGIC)
        f.write(struct.pack("<I", MNW_VERSION))
        f.write(struct.pack("<Q", header_size))
        f.write(header_json)
        for part in tensor_data_parts:
            f.write(part)


def load_mnw(path: str | Path) -> tuple[MNWHeader, dict[str, Tensor]]:
    """Load tensors from a .mnw file.

    Args:
        path: Path to the .mnw file.

    Returns:
        Tuple of (header, dict of tensor name → Tensor).

    Raises:
        ModelFormatError: If the file is not a valid .mnw file.
    """
    path = Path(path)
    if not path.exists():
        raise ModelFormatError(f"File not found: {path}")

    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != MNW_MAGIC:
            raise ModelFormatError(f"Invalid magic bytes: expected {MNW_MAGIC!r}, got {magic!r}")

        (version,) = struct.unpack("<I", f.read(4))
        if version != MNW_VERSION:
            raise ModelFormatError(f"Unsupported MNW version: {version}")

        (header_size,) = struct.unpack("<Q", f.read(8))
        header_json = f.read(header_size)

        try:
            header_dict = json.loads(header_json.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ModelFormatError(f"Invalid header JSON: {exc}") from exc

        header = MNWHeader.from_dict(header_dict)

        # Read tensor data section
        tensor_data_start = f.tell()
        tensors: dict[str, Tensor] = {}

        for info in header.tensors:
            f.seek(tensor_data_start + info.offset)
            raw = f.read(info.byte_size)
            if len(raw) != info.byte_size:
                raise ModelFormatError(
                    f"Truncated tensor data for '{info.name}': "
                    f"expected {info.byte_size} bytes, got {len(raw)}"
                )

            dtype = DType[info.dtype]
            size = 1
            for d in info.shape:
                size *= d

            data = _deserialize_tensor_data(raw, dtype, size)
            tensors[info.name] = Tensor(data, info.shape)

    return header, tensors


# ---------------------------------------------------------------------------
# Task 2: ONNX import
# ---------------------------------------------------------------------------

# ONNX uses protobuf, but we implement a lightweight parser that reads
# the binary protobuf wire format directly — no external dependency needed.
# This supports the minimal subset needed for model weight extraction.

# ONNX tensor data type enum values (from onnx.TensorProto.DataType)
ONNX_DTYPE_MAP: dict[int, DType] = {
    1: DType.FLOAT32,  # FLOAT
    2: DType.FLOAT64,  # DOUBLE (uint8 in ONNX but we map to supported)
    5: DType.INT32,  # INT16 → INT32
    6: DType.INT32,  # INT32
    7: DType.INT64,  # INT64
    9: DType.BOOL,  # BOOL
    10: DType.FLOAT32,  # FLOAT16 → FLOAT32 (upcast)
    11: DType.FLOAT64,  # DOUBLE
}


@dataclass
class ONNXTensorInfo:
    """Information about an ONNX tensor (initializer)."""

    name: str
    data_type: int  # ONNX DataType enum value
    shape: tuple[int, ...]
    raw_data: bytes = b""
    float_data: list[float] = field(default_factory=list)
    int32_data: list[int] = field(default_factory=list)
    int64_data: list[int] = field(default_factory=list)
    double_data: list[float] = field(default_factory=list)


@dataclass
class ONNXModelInfo:
    """Parsed ONNX model metadata."""

    ir_version: int = 0
    producer_name: str = ""
    producer_version: str = ""
    domain: str = ""
    model_version: int = 0
    doc_string: str = ""
    opset_version: int = 0
    graph_name: str = ""
    initializers: list[ONNXTensorInfo] = field(default_factory=list)


def _onnx_tensor_to_mapanare(info: ONNXTensorInfo) -> Tensor:
    """Convert an ONNX tensor to a Mapanare Tensor."""
    size = 1
    for d in info.shape:
        size *= d

    if size == 0:
        return Tensor([], (0,))

    dtype = ONNX_DTYPE_MAP.get(info.data_type, DType.FLOAT32)

    # Try raw_data first, then typed arrays
    if info.raw_data:
        fmt = f"<{size}{dtype.struct_format}"
        expected_bytes = size * dtype.byte_size
        raw = info.raw_data[:expected_bytes]
        if len(raw) == expected_bytes:
            values = list(struct.unpack(fmt, raw))
            return Tensor([float(v) for v in values], info.shape)

    # Fall back to typed data fields
    if info.float_data:
        return Tensor([float(v) for v in info.float_data[:size]], info.shape)
    if info.double_data:
        return Tensor([float(v) for v in info.double_data[:size]], info.shape)
    if info.int32_data:
        return Tensor([float(v) for v in info.int32_data[:size]], info.shape)
    if info.int64_data:
        return Tensor([float(v) for v in info.int64_data[:size]], info.shape)

    # Empty/unknown — return zeros
    return Tensor([0.0] * size, info.shape)


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read a protobuf varint from data at pos. Returns (value, new_pos)."""
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, pos


def _read_protobuf_field(data: bytes, pos: int) -> tuple[int, int, Any, int]:
    """Read one protobuf field. Returns (field_number, wire_type, value, new_pos)."""
    tag, pos = _read_varint(data, pos)
    field_number = tag >> 3
    wire_type = tag & 0x07

    result: Any
    if wire_type == 0:  # Varint
        result, pos = _read_varint(data, pos)
        return field_number, wire_type, result, pos
    elif wire_type == 1:  # 64-bit
        result = struct.unpack("<d", data[pos : pos + 8])[0]
        return field_number, wire_type, result, pos + 8
    elif wire_type == 2:  # Length-delimited
        length, pos = _read_varint(data, pos)
        result = data[pos : pos + length]
        return field_number, wire_type, result, pos + length
    elif wire_type == 5:  # 32-bit
        result = struct.unpack("<f", data[pos : pos + 4])[0]
        return field_number, wire_type, result, pos + 4
    else:
        raise ModelFormatError(f"Unsupported protobuf wire type: {wire_type}")


def _parse_onnx_tensor(data: bytes) -> ONNXTensorInfo:
    """Parse an ONNX TensorProto from protobuf bytes."""
    info = ONNXTensorInfo(name="", data_type=1, shape=())
    dims: list[int] = []
    float_data: list[float] = []
    int32_data: list[int] = []
    int64_data: list[int] = []
    double_data: list[float] = []

    pos = 0
    while pos < len(data):
        field_num, wire_type, value, pos = _read_protobuf_field(data, pos)

        if field_num == 1 and wire_type == 0:  # dims (repeated int64, packed)
            dims.append(int(value))
        elif field_num == 1 and wire_type == 2:  # dims (packed)
            inner_pos = 0
            while inner_pos < len(value):
                dim, inner_pos = _read_varint(value, inner_pos)
                dims.append(dim)
        elif field_num == 2 and wire_type == 0:  # data_type
            info = ONNXTensorInfo(
                name=info.name,
                data_type=int(value),
                shape=info.shape,
                raw_data=info.raw_data,
            )
        elif field_num == 4 and wire_type == 2:  # float_data (packed)
            count = len(value) // 4
            float_data.extend(struct.unpack(f"<{count}f", value[: count * 4]))
        elif field_num == 5 and wire_type == 2:  # int32_data (packed)
            count = len(value) // 4
            int32_data.extend(struct.unpack(f"<{count}i", value[: count * 4]))
        elif field_num == 7 and wire_type == 2:  # int64_data (packed)
            count = len(value) // 8
            int64_data.extend(struct.unpack(f"<{count}q", value[: count * 8]))
        elif field_num == 8 and wire_type == 2:  # name (string)
            info = ONNXTensorInfo(
                name=value.decode("utf-8") if isinstance(value, bytes) else str(value),
                data_type=info.data_type,
                shape=info.shape,
                raw_data=info.raw_data,
            )
        elif field_num == 13 and wire_type == 2:  # raw_data
            info = ONNXTensorInfo(
                name=info.name,
                data_type=info.data_type,
                shape=info.shape,
                raw_data=bytes(value) if isinstance(value, (bytes, bytearray)) else b"",
            )
        elif field_num == 10 and wire_type == 2:  # double_data (packed)
            count = len(value) // 8
            double_data.extend(struct.unpack(f"<{count}d", value[: count * 8]))

    shape = tuple(dims) if dims else (0,)
    return ONNXTensorInfo(
        name=info.name,
        data_type=info.data_type,
        shape=shape,
        raw_data=info.raw_data,
        float_data=float_data,
        int32_data=int32_data,
        int64_data=int64_data,
        double_data=double_data,
    )


def _parse_onnx_graph(data: bytes) -> tuple[str, list[ONNXTensorInfo]]:
    """Parse an ONNX GraphProto, extracting name and initializers."""
    graph_name = ""
    initializers: list[ONNXTensorInfo] = []

    pos = 0
    while pos < len(data):
        field_num, wire_type, value, pos = _read_protobuf_field(data, pos)

        if field_num == 5 and wire_type == 2:  # initializer (TensorProto)
            initializers.append(_parse_onnx_tensor(value))
        elif field_num == 12 and wire_type == 2:  # name
            graph_name = value.decode("utf-8") if isinstance(value, bytes) else str(value)

    return graph_name, initializers


def load_onnx(path: str | Path) -> tuple[ONNXModelInfo, dict[str, Tensor]]:
    """Load model weights from an ONNX file.

    Parses the ONNX protobuf format directly (no onnx package needed).
    Extracts initializer tensors (model weights).

    Args:
        path: Path to the .onnx file.

    Returns:
        Tuple of (model info, dict of tensor name → Tensor).

    Raises:
        ModelFormatError: If the file cannot be parsed.
    """
    path = Path(path)
    if not path.exists():
        raise ModelFormatError(f"File not found: {path}")

    with open(path, "rb") as f:
        data = f.read()

    model_info = ONNXModelInfo()
    pos = 0

    try:
        while pos < len(data):
            field_num, wire_type, value, pos = _read_protobuf_field(data, pos)

            if field_num == 1 and wire_type == 0:  # ir_version
                model_info.ir_version = int(value)
            elif field_num == 2 and wire_type == 2:  # producer_name
                model_info.producer_name = (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
            elif field_num == 3 and wire_type == 2:  # producer_version
                model_info.producer_version = (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
            elif field_num == 4 and wire_type == 2:  # domain
                model_info.domain = (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
            elif field_num == 5 and wire_type == 0:  # model_version
                model_info.model_version = int(value)
            elif field_num == 6 and wire_type == 2:  # doc_string
                model_info.doc_string = (
                    value.decode("utf-8") if isinstance(value, bytes) else str(value)
                )
            elif field_num == 7 and wire_type == 2:  # graph
                graph_name, initializers = _parse_onnx_graph(value)
                model_info.graph_name = graph_name
                model_info.initializers = initializers
            elif field_num == 8 and wire_type == 2:  # opset_import
                # Parse opset version from OpSetIdProto
                inner_pos = 0
                while inner_pos < len(value):
                    fn, wt, v, inner_pos = _read_protobuf_field(value, inner_pos)
                    if fn == 2 and wt == 0:  # version
                        model_info.opset_version = int(v)
    except Exception as exc:
        raise ModelFormatError(f"Failed to parse ONNX file: {exc}") from exc

    # Convert initializers to Tensors
    tensors: dict[str, Tensor] = {}
    for init in model_info.initializers:
        if init.name:
            tensors[init.name] = _onnx_tensor_to_mapanare(init)

    return model_info, tensors


def _build_onnx_varint(value: int) -> bytes:
    """Encode an integer as a protobuf varint."""
    result = bytearray()
    while value > 0x7F:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value & 0x7F)
    return bytes(result)


def _build_onnx_field(field_number: int, wire_type: int, value: bytes | int) -> bytes:
    """Build a protobuf field."""
    tag = _build_onnx_varint((field_number << 3) | wire_type)
    if wire_type == 0:  # varint
        return tag + _build_onnx_varint(int(value))
    elif wire_type == 2:  # length-delimited
        assert isinstance(value, bytes)
        return tag + _build_onnx_varint(len(value)) + value
    return tag


def save_onnx_simple(
    path: str | Path,
    tensors: dict[str, Tensor],
    model_name: str = "mapanare_model",
) -> None:
    """Save tensors to a minimal ONNX-compatible file.

    This writes a valid ONNX ModelProto with the tensors as graph initializers.
    Useful for interop with ONNX-consuming tools.
    """
    path = Path(path)

    # Build TensorProto messages for each tensor
    initializer_data = b""
    for name, tensor in tensors.items():
        tensor_msg = b""
        # dims (field 1, packed varint)
        dims_packed = b""
        for d in tensor.shape:
            dims_packed += _build_onnx_varint(d)
        tensor_msg += _build_onnx_field(1, 2, dims_packed)
        # data_type = DOUBLE (11) (field 2)
        tensor_msg += _build_onnx_field(2, 0, 11)
        # name (field 8)
        tensor_msg += _build_onnx_field(8, 2, name.encode("utf-8"))
        # raw_data (field 13)
        raw = struct.pack(f"<{tensor.size}d", *tensor.data)
        tensor_msg += _build_onnx_field(13, 2, raw)

        initializer_data += _build_onnx_field(5, 2, tensor_msg)

    # Build GraphProto
    graph_msg = initializer_data
    # graph name (field 12)
    graph_msg += _build_onnx_field(12, 2, model_name.encode("utf-8"))

    # Build ModelProto
    model_msg = b""
    # ir_version = 9 (field 1)
    model_msg += _build_onnx_field(1, 0, 9)
    # producer_name (field 2)
    model_msg += _build_onnx_field(2, 2, b"mapanare")
    # graph (field 7)
    model_msg += _build_onnx_field(7, 2, graph_msg)
    # opset_import (field 8) — version = 19
    opset = _build_onnx_field(2, 0, 19)
    model_msg += _build_onnx_field(8, 2, opset)

    with open(path, "wb") as f:
        f.write(model_msg)


# ---------------------------------------------------------------------------
# Task 3: Safetensors / HuggingFace import
# ---------------------------------------------------------------------------

# Safetensors format:
#   [header_size: 8 bytes uint64 LE]
#   [header: JSON, header_size bytes]
#   [tensor data: contiguous, aligned]
#
# Header JSON: { tensor_name: { dtype, shape, data_offsets: [start, end] }, "__metadata__": {...} }

SAFETENSORS_DTYPE_MAP: dict[str, DType] = {
    "F16": DType.FLOAT32,  # upcast to f32
    "BF16": DType.FLOAT32,  # upcast to f32
    "F32": DType.FLOAT32,
    "F64": DType.FLOAT64,
    "I32": DType.INT32,
    "I64": DType.INT64,
    "BOOL": DType.BOOL,
}

# Byte sizes for safetensors dtypes (original sizes for reading raw data)
_ST_DTYPE_SIZES: dict[str, int] = {
    "F16": 2,
    "BF16": 2,
    "F32": 4,
    "F64": 8,
    "I32": 4,
    "I64": 8,
    "BOOL": 1,
}


@dataclass
class SafetensorsMetadata:
    """Metadata from a safetensors file."""

    metadata: dict[str, str] = field(default_factory=dict)
    tensor_names: list[str] = field(default_factory=list)
    tensor_dtypes: dict[str, str] = field(default_factory=dict)
    tensor_shapes: dict[str, tuple[int, ...]] = field(default_factory=dict)


def _decode_f16(raw: bytes, count: int) -> list[float]:
    """Decode IEEE 754 half-precision floats to Python floats."""
    # Use struct with 'e' format (Python 3.6+)
    return list(struct.unpack(f"<{count}e", raw[: count * 2]))


def _decode_bf16(raw: bytes, count: int) -> list[float]:
    """Decode bfloat16 values to Python floats.

    bfloat16 is the upper 16 bits of a float32.
    """
    values: list[float] = []
    for i in range(count):
        bf16_bits = struct.unpack_from("<H", raw, i * 2)[0]
        # Expand to float32 by shifting left 16 bits
        f32_bits = bf16_bits << 16
        (f32_val,) = struct.unpack("<f", struct.pack("<I", f32_bits))
        values.append(f32_val)
    return values


def load_safetensors(path: str | Path) -> tuple[SafetensorsMetadata, dict[str, Tensor]]:
    """Load tensors from a safetensors file.

    Args:
        path: Path to the .safetensors file.

    Returns:
        Tuple of (metadata, dict of tensor name → Tensor).

    Raises:
        ModelFormatError: If the file format is invalid.
    """
    path = Path(path)
    if not path.exists():
        raise ModelFormatError(f"File not found: {path}")

    with open(path, "rb") as f:
        # Read header size (8 bytes, uint64 LE)
        header_size_raw = f.read(8)
        if len(header_size_raw) < 8:
            raise ModelFormatError("File too short: cannot read header size")

        (header_size,) = struct.unpack("<Q", header_size_raw)

        if header_size > 100 * 1024 * 1024:  # 100MB header limit
            raise ModelFormatError(f"Header size too large: {header_size}")

        header_raw = f.read(header_size)
        if len(header_raw) < header_size:
            raise ModelFormatError("Truncated header")

        try:
            header = json.loads(header_raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ModelFormatError(f"Invalid header JSON: {exc}") from exc

        if not isinstance(header, dict):
            raise ModelFormatError("Header must be a JSON object")

        # Parse metadata and tensor info
        st_meta = SafetensorsMetadata()
        if "__metadata__" in header:
            meta = header.pop("__metadata__")
            if isinstance(meta, dict):
                st_meta.metadata = {str(k): str(v) for k, v in meta.items()}

        tensor_data_start = 8 + header_size
        tensors: dict[str, Tensor] = {}

        for name, info in header.items():
            if not isinstance(info, dict):
                continue

            st_dtype = info.get("dtype", "F32")
            shape = tuple(info.get("shape", []))
            offsets = info.get("data_offsets", [0, 0])

            st_meta.tensor_names.append(name)
            st_meta.tensor_dtypes[name] = st_dtype
            st_meta.tensor_shapes[name] = shape

            start_offset, end_offset = offsets[0], offsets[1]
            data_len = end_offset - start_offset

            f.seek(tensor_data_start + start_offset)
            raw = f.read(data_len)

            if len(raw) < data_len:
                raise ModelFormatError(f"Truncated tensor data for '{name}'")

            size = 1
            for d in shape:
                size *= d

            if size == 0:
                tensors[name] = Tensor([], (0,))
                continue

            # Decode based on dtype
            if st_dtype == "F16":
                values = _decode_f16(raw, size)
            elif st_dtype == "BF16":
                values = _decode_bf16(raw, size)
            elif st_dtype == "F32":
                values = list(struct.unpack(f"<{size}f", raw[: size * 4]))
            elif st_dtype == "F64":
                values = list(struct.unpack(f"<{size}d", raw[: size * 8]))
            elif st_dtype == "I32":
                values = [float(v) for v in struct.unpack(f"<{size}i", raw[: size * 4])]
            elif st_dtype == "I64":
                values = [float(v) for v in struct.unpack(f"<{size}q", raw[: size * 8])]
            elif st_dtype == "BOOL":
                values = [float(v) for v in struct.unpack(f"<{size}?", raw[:size])]
            else:
                raise ModelFormatError(f"Unsupported safetensors dtype: {st_dtype}")

            tensors[name] = Tensor([float(v) for v in values], shape)

    return st_meta, tensors


def save_safetensors(
    path: str | Path,
    tensors: dict[str, Tensor],
    metadata: dict[str, str] | None = None,
    dtype: str = "F64",
) -> None:
    """Save tensors to a safetensors file.

    Args:
        path: Output file path.
        tensors: Dict mapping tensor names to Tensor objects.
        metadata: Optional metadata dict (string → string).
        dtype: Safetensors dtype string (e.g., "F32", "F64").
    """
    path = Path(path)

    # Build tensor data and header
    header: dict[str, Any] = {}
    if metadata:
        header["__metadata__"] = metadata

    data_parts: list[bytes] = []
    offset = 0

    for name, tensor in tensors.items():
        if dtype == "F64":
            raw = struct.pack(f"<{tensor.size}d", *tensor.data)
        elif dtype == "F32":
            raw = struct.pack(f"<{tensor.size}f", *tensor.data)
        elif dtype == "I32":
            raw = struct.pack(f"<{tensor.size}i", *[int(v) for v in tensor.data])
        elif dtype == "I64":
            raw = struct.pack(f"<{tensor.size}q", *[int(v) for v in tensor.data])
        else:
            raw = struct.pack(f"<{tensor.size}d", *tensor.data)

        header[name] = {
            "dtype": dtype,
            "shape": list(tensor.shape),
            "data_offsets": [offset, offset + len(raw)],
        }
        data_parts.append(raw)
        offset += len(raw)

    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")

    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(header_json)))
        f.write(header_json)
        for part in data_parts:
            f.write(part)


@dataclass
class HuggingFaceModelConfig:
    """Parsed HuggingFace model config.json."""

    model_type: str = ""
    architectures: list[str] = field(default_factory=list)
    hidden_size: int = 0
    num_hidden_layers: int = 0
    num_attention_heads: int = 0
    intermediate_size: int = 0
    vocab_size: int = 0
    max_position_embeddings: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


def load_huggingface_config(path: str | Path) -> HuggingFaceModelConfig:
    """Load and parse a HuggingFace model config.json.

    Args:
        path: Path to config.json or directory containing it.

    Returns:
        Parsed HuggingFaceModelConfig.

    Raises:
        ModelFormatError: If the config cannot be loaded.
    """
    path = Path(path)
    if path.is_dir():
        path = path / "config.json"

    if not path.exists():
        raise ModelFormatError(f"Config not found: {path}")

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise ModelFormatError(f"Failed to load config: {exc}") from exc

    if not isinstance(data, dict):
        raise ModelFormatError("Config must be a JSON object")

    known_keys = {
        "model_type",
        "architectures",
        "hidden_size",
        "num_hidden_layers",
        "num_attention_heads",
        "intermediate_size",
        "vocab_size",
        "max_position_embeddings",
    }

    config = HuggingFaceModelConfig(
        model_type=data.get("model_type", ""),
        architectures=data.get("architectures", []),
        hidden_size=data.get("hidden_size", 0),
        num_hidden_layers=data.get("num_hidden_layers", 0),
        num_attention_heads=data.get("num_attention_heads", 0),
        intermediate_size=data.get("intermediate_size", 0),
        vocab_size=data.get("vocab_size", 0),
        max_position_embeddings=data.get("max_position_embeddings", 0),
        extra={k: v for k, v in data.items() if k not in known_keys},
    )

    return config


def load_huggingface_model(
    model_dir: str | Path,
) -> tuple[HuggingFaceModelConfig, dict[str, Tensor]]:
    """Load a HuggingFace model from a local directory.

    Expects:
      - config.json — model configuration
      - model.safetensors — model weights (safetensors format)
      - OR pytorch_model.bin — not supported, raises error

    Args:
        model_dir: Path to the model directory.

    Returns:
        Tuple of (config, tensors dict).

    Raises:
        ModelFormatError: If the model cannot be loaded.
    """
    model_dir = Path(model_dir)
    if not model_dir.is_dir():
        raise ModelFormatError(f"Not a directory: {model_dir}")

    config = load_huggingface_config(model_dir)

    # Look for safetensors weights
    st_path = model_dir / "model.safetensors"
    if not st_path.exists():
        # Check for sharded safetensors
        st_files = sorted(model_dir.glob("model-*.safetensors"))
        if st_files:
            # Load all shards
            all_tensors: dict[str, Tensor] = {}
            for shard in st_files:
                _, shard_tensors = load_safetensors(shard)
                all_tensors.update(shard_tensors)
            return config, all_tensors

        # Check for pytorch format (unsupported)
        if (model_dir / "pytorch_model.bin").exists():
            raise ModelFormatError(
                "PyTorch .bin format not supported. Convert to safetensors first: "
                "https://huggingface.co/docs/safetensors"
            )

        raise ModelFormatError(
            f"No model weights found in {model_dir}. "
            "Expected model.safetensors or model-*.safetensors"
        )

    _, tensors = load_safetensors(st_path)
    return config, tensors


# ---------------------------------------------------------------------------
# Task 4: Standard model interface: predict, encode, generate
# ---------------------------------------------------------------------------


class ModelInterface(ABC):
    """Standard interface for all Mapanare models.

    Every model loaded in Mapanare must implement this interface,
    providing a consistent API for inference regardless of the
    model's origin format (MNW, ONNX, safetensors).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Model name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Model version string."""
        ...

    @property
    @abstractmethod
    def weights(self) -> dict[str, Tensor]:
        """All model weight tensors."""
        ...

    @abstractmethod
    def predict(self, input_tensor: Tensor) -> Tensor:
        """Run forward pass on input tensor.

        Args:
            input_tensor: Input data tensor.

        Returns:
            Output prediction tensor.
        """
        ...

    @abstractmethod
    def encode(self, input_tensor: Tensor) -> Tensor:
        """Encode input to latent representation.

        Args:
            input_tensor: Input data tensor.

        Returns:
            Encoded representation tensor.
        """
        ...

    @abstractmethod
    def generate(
        self,
        input_tensor: Tensor,
        max_length: int = 128,
        temperature: float = 1.0,
    ) -> Tensor:
        """Generate output autoregressively.

        Args:
            input_tensor: Seed/prompt tensor.
            max_length: Maximum output length.
            temperature: Sampling temperature (1.0 = no scaling).

        Returns:
            Generated output tensor.
        """
        ...


class MapanareModel(ModelInterface):
    """Concrete model implementation backed by Mapanare tensors.

    Provides the standard predict/encode/generate interface with
    configurable forward functions. Users can set custom forward
    logic via set_predict_fn, set_encode_fn, set_generate_fn.
    """

    def __init__(
        self,
        name: str,
        weights: dict[str, Tensor],
        version: str = "1.0.0",
        architecture: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._architecture = architecture
        self._metadata = metadata or {}
        self._weights = dict(weights)
        self._predict_fn: Callable[[Tensor, dict[str, Tensor]], Tensor] | None = None
        self._encode_fn: Callable[[Tensor, dict[str, Tensor]], Tensor] | None = None
        self._generate_fn: Callable[[Tensor, dict[str, Tensor], int, float], Tensor] | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def architecture(self) -> str:
        return self._architecture

    @property
    def metadata(self) -> dict[str, Any]:
        return dict(self._metadata)

    @property
    def weights(self) -> dict[str, Tensor]:
        return dict(self._weights)

    def weight(self, name: str) -> Tensor:
        """Get a specific weight tensor by name.

        Raises:
            KeyError: If the weight does not exist.
        """
        if name not in self._weights:
            raise KeyError(f"Weight '{name}' not found. Available: {list(self._weights.keys())}")
        return self._weights[name]

    def set_predict_fn(self, fn: Callable[[Tensor, dict[str, Tensor]], Tensor]) -> None:
        """Set custom predict function: fn(input, weights) → output."""
        self._predict_fn = fn

    def set_encode_fn(self, fn: Callable[[Tensor, dict[str, Tensor]], Tensor]) -> None:
        """Set custom encode function: fn(input, weights) → encoded."""
        self._encode_fn = fn

    def set_generate_fn(
        self, fn: Callable[[Tensor, dict[str, Tensor], int, float], Tensor]
    ) -> None:
        """Set custom generate function: fn(input, weights, max_len, temp) → output."""
        self._generate_fn = fn

    def predict(self, input_tensor: Tensor) -> Tensor:
        """Run forward pass.

        If a custom predict_fn is set, uses that.
        Otherwise, performs a simple linear transform: output = input @ weight
        using the first 2D weight tensor found, or returns input unchanged.
        """
        if self._predict_fn is not None:
            return self._predict_fn(input_tensor, self._weights)

        # Default: find a compatible weight and do matmul
        for w in self._weights.values():
            if w.ndim == 2 and input_tensor.ndim <= 2:
                if input_tensor.ndim == 1 and input_tensor.shape[0] == w.shape[0]:
                    return input_tensor @ w
                if input_tensor.ndim == 2 and input_tensor.shape[1] == w.shape[0]:
                    return input_tensor @ w
        return input_tensor

    def encode(self, input_tensor: Tensor) -> Tensor:
        """Encode input to latent space.

        If a custom encode_fn is set, uses that.
        Otherwise, delegates to predict().
        """
        if self._encode_fn is not None:
            return self._encode_fn(input_tensor, self._weights)
        return self.predict(input_tensor)

    def generate(
        self,
        input_tensor: Tensor,
        max_length: int = 128,
        temperature: float = 1.0,
    ) -> Tensor:
        """Generate output autoregressively.

        If a custom generate_fn is set, uses that.
        Otherwise, runs predict() once and returns the result.
        """
        if self._generate_fn is not None:
            return self._generate_fn(input_tensor, self._weights, max_length, temperature)
        return self.predict(input_tensor)

    def save(self, path: str | Path, fmt: str = "mnw") -> None:
        """Save model to file.

        Args:
            path: Output file path.
            fmt: Format — "mnw", "safetensors", or "onnx".
        """
        if fmt == "mnw":
            save_mnw(
                path,
                self._weights,
                model_name=self._name,
                model_version=self._version,
                architecture=self._architecture,
                metadata=self._metadata,
            )
        elif fmt == "safetensors":
            save_safetensors(path, self._weights, metadata={"model_name": self._name})
        elif fmt == "onnx":
            save_onnx_simple(path, self._weights, model_name=self._name)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    @staticmethod
    def from_mnw(path: str | Path) -> MapanareModel:
        """Load a model from a .mnw file."""
        header, tensors = load_mnw(path)
        return MapanareModel(
            name=header.model_name,
            weights=tensors,
            version=header.model_version,
            architecture=header.architecture,
            metadata=header.metadata,
        )

    @staticmethod
    def from_onnx(path: str | Path) -> MapanareModel:
        """Load a model from an ONNX file."""
        info, tensors = load_onnx(path)
        return MapanareModel(
            name=info.graph_name or info.producer_name or "onnx_model",
            weights=tensors,
            version=str(info.model_version),
            architecture=f"onnx_ir_v{info.ir_version}",
            metadata={
                "producer": info.producer_name,
                "producer_version": info.producer_version,
                "opset": info.opset_version,
            },
        )

    @staticmethod
    def from_safetensors(path: str | Path, name: str = "safetensors_model") -> MapanareModel:
        """Load a model from a safetensors file."""
        meta, tensors = load_safetensors(path)
        model_name = meta.metadata.get("model_name", name)
        return MapanareModel(
            name=model_name,
            weights=tensors,
            metadata={"safetensors_metadata": meta.metadata},
        )

    @staticmethod
    def from_huggingface(model_dir: str | Path) -> MapanareModel:
        """Load a model from a HuggingFace local directory."""
        config, tensors = load_huggingface_model(model_dir)
        return MapanareModel(
            name=config.model_type or "hf_model",
            weights=tensors,
            architecture=", ".join(config.architectures) if config.architectures else "",
            metadata={
                "hidden_size": config.hidden_size,
                "num_layers": config.num_hidden_layers,
                "num_heads": config.num_attention_heads,
                "vocab_size": config.vocab_size,
            },
        )


# ---------------------------------------------------------------------------
# Task 5: Model registry: mapanare://models/
# ---------------------------------------------------------------------------


@dataclass
class ModelRegistryEntry:
    """Entry in the model registry."""

    name: str
    version: str
    path: str  # local file path or URL
    format: str  # "mnw", "onnx", "safetensors", "huggingface"
    architecture: str = ""
    description: str = ""
    sha256: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def uri(self) -> str:
        """Mapanare model URI."""
        return f"mapanare://models/{self.name}/{self.version}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "path": self.path,
            "format": self.format,
            "architecture": self.architecture,
            "description": self.description,
            "sha256": self.sha256,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> ModelRegistryEntry:
        return ModelRegistryEntry(
            name=d["name"],
            version=d.get("version", "1.0.0"),
            path=d.get("path", ""),
            format=d.get("format", "mnw"),
            architecture=d.get("architecture", ""),
            description=d.get("description", ""),
            sha256=d.get("sha256", ""),
            metadata=d.get("metadata", {}),
        )


class ModelRegistry:
    """Registry for Mapanare models.

    Manages model registration, lookup, and loading via
    the mapanare://models/ URI scheme.

    Models are indexed by name and version. The registry
    persists to a JSON file in the Mapanare data directory.
    """

    def __init__(self, registry_dir: str | Path | None = None) -> None:
        if registry_dir is None:
            home = Path.home()
            registry_dir = home / ".mapanare" / "models"
        self._dir = Path(registry_dir)
        self._entries: dict[str, dict[str, ModelRegistryEntry]] = {}
        self._loaded = False

    @property
    def registry_dir(self) -> Path:
        return self._dir

    @property
    def registry_file(self) -> Path:
        return self._dir / "registry.json"

    def _ensure_dir(self) -> None:
        """Create registry directory if needed."""
        self._dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load registry from disk."""
        if self._loaded:
            return
        if self.registry_file.exists():
            try:
                with open(self.registry_file) as f:
                    data = json.load(f)
                for entry_dict in data.get("models", []):
                    entry = ModelRegistryEntry.from_dict(entry_dict)
                    if entry.name not in self._entries:
                        self._entries[entry.name] = {}
                    self._entries[entry.name][entry.version] = entry
            except (json.JSONDecodeError, OSError, KeyError):
                pass
        self._loaded = True

    def _save(self) -> None:
        """Persist registry to disk."""
        self._ensure_dir()
        all_entries: list[dict[str, Any]] = []
        for versions in self._entries.values():
            for entry in versions.values():
                all_entries.append(entry.to_dict())
        with open(self.registry_file, "w") as f:
            json.dump({"models": all_entries}, f, indent=2)

    def register(
        self,
        name: str,
        path: str | Path,
        version: str = "1.0.0",
        fmt: str = "mnw",
        architecture: str = "",
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ModelRegistryEntry:
        """Register a model in the registry.

        Args:
            name: Model name (used in mapanare://models/{name}/{version}).
            path: Path to the model file or directory.
            version: Version string.
            fmt: Model format ("mnw", "onnx", "safetensors", "huggingface").
            architecture: Architecture description.
            description: Human-readable description.
            metadata: Optional extra metadata.

        Returns:
            The created registry entry.
        """
        self._load()

        path_str = str(Path(path).resolve())
        sha = ""
        resolved = Path(path_str)
        if resolved.is_file():
            sha = _compute_file_sha256(resolved)

        entry = ModelRegistryEntry(
            name=name,
            version=version,
            path=path_str,
            format=fmt,
            architecture=architecture,
            description=description,
            sha256=sha,
            metadata=metadata or {},
        )

        if name not in self._entries:
            self._entries[name] = {}
        self._entries[name][version] = entry
        self._save()
        return entry

    def get(self, name: str, version: str | None = None) -> ModelRegistryEntry | None:
        """Look up a model by name and optional version.

        If version is None, returns the latest registered version.
        """
        self._load()
        versions = self._entries.get(name)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        # Return latest version (lexicographic sort)
        latest = sorted(versions.keys())[-1]
        return versions[latest]

    def resolve_uri(self, uri: str) -> ModelRegistryEntry | None:
        """Resolve a mapanare://models/ URI to a registry entry.

        URI format: mapanare://models/{name}[/{version}]

        Args:
            uri: The model URI.

        Returns:
            The matching entry, or None if not found.

        Raises:
            ValueError: If the URI format is invalid.
        """
        prefix = "mapanare://models/"
        if not uri.startswith(prefix):
            raise ValueError(f"Invalid model URI: {uri}. Must start with '{prefix}'")

        remainder = uri[len(prefix) :].strip("/")
        parts = remainder.split("/")

        if len(parts) == 1:
            return self.get(parts[0])
        elif len(parts) == 2:
            return self.get(parts[0], parts[1])
        else:
            raise ValueError(f"Invalid model URI format: {uri}")

    def load_model(self, name_or_uri: str, version: str | None = None) -> MapanareModel:
        """Load a model from the registry.

        Args:
            name_or_uri: Model name or mapanare://models/ URI.
            version: Version (ignored if name_or_uri is a URI).

        Returns:
            Loaded MapanareModel.

        Raises:
            ModelFormatError: If the model cannot be found or loaded.
        """
        if name_or_uri.startswith("mapanare://"):
            entry = self.resolve_uri(name_or_uri)
        else:
            entry = self.get(name_or_uri, version)

        if entry is None:
            raise ModelFormatError(f"Model not found: {name_or_uri}")

        path = Path(entry.path)
        if not path.exists():
            raise ModelFormatError(f"Model file not found: {path}")

        if entry.format == "mnw":
            return MapanareModel.from_mnw(path)
        elif entry.format == "onnx":
            return MapanareModel.from_onnx(path)
        elif entry.format == "safetensors":
            return MapanareModel.from_safetensors(path, name=entry.name)
        elif entry.format == "huggingface":
            return MapanareModel.from_huggingface(path)
        else:
            raise ModelFormatError(f"Unsupported format: {entry.format}")

    def list_models(self) -> list[ModelRegistryEntry]:
        """List all registered models (all versions)."""
        self._load()
        result: list[ModelRegistryEntry] = []
        for versions in self._entries.values():
            for entry in versions.values():
                result.append(entry)
        return sorted(result, key=lambda e: (e.name, e.version))

    def list_names(self) -> list[str]:
        """List all registered model names."""
        self._load()
        return sorted(self._entries.keys())

    def list_versions(self, name: str) -> list[str]:
        """List all versions of a model."""
        self._load()
        versions = self._entries.get(name)
        if not versions:
            return []
        return sorted(versions.keys())

    def remove(self, name: str, version: str | None = None) -> bool:
        """Remove a model from the registry.

        If version is None, removes all versions.
        Returns True if anything was removed.
        """
        self._load()
        if name not in self._entries:
            return False

        if version is None:
            del self._entries[name]
            self._save()
            return True

        if version in self._entries[name]:
            del self._entries[name][version]
            if not self._entries[name]:
                del self._entries[name]
            self._save()
            return True

        return False


def _compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


# Singleton registry
_model_registry: ModelRegistry | None = None


def get_model_registry(registry_dir: str | Path | None = None) -> ModelRegistry:
    """Get the global model registry singleton."""
    global _model_registry
    if _model_registry is None or registry_dir is not None:
        _model_registry = ModelRegistry(registry_dir)
    return _model_registry
