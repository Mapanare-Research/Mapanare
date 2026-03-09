"""Tests for mapa.model — Phase 5.3: Model Loading.

Tests cover:
  1. Native .mnw model format and loader
  2. ONNX import
  3. Safetensors / HuggingFace import
  4. Standard model interface: predict, encode, generate
  5. Model registry: mapanare://models/
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from mapanare.model import (
    DType,
    MapanareModel,
    MNWHeader,
    ModelFormatError,
    ModelRegistry,
    ModelRegistryEntry,
    ONNXTensorInfo,
    TensorInfo,
    _build_onnx_field,
    _build_onnx_varint,
    _compute_file_sha256,
    _decode_bf16,
    _decode_f16,
    _deserialize_tensor_data,
    _onnx_tensor_to_mapanare,
    _read_varint,
    _serialize_tensor_data,
    get_model_registry,
    load_huggingface_config,
    load_huggingface_model,
    load_mnw,
    load_onnx,
    load_safetensors,
    save_mnw,
    save_onnx_simple,
    save_safetensors,
)
from mapanare.tensor import Tensor

# ===================================================================
# Task 1: Native .mnw model format and loader
# ===================================================================


class TestDType:
    """Test DType enum properties."""

    def test_byte_sizes(self) -> None:
        assert DType.FLOAT32.byte_size == 4
        assert DType.FLOAT64.byte_size == 8
        assert DType.INT32.byte_size == 4
        assert DType.INT64.byte_size == 8
        assert DType.BOOL.byte_size == 1

    def test_struct_formats(self) -> None:
        assert DType.FLOAT32.struct_format == "f"
        assert DType.FLOAT64.struct_format == "d"
        assert DType.INT32.struct_format == "i"
        assert DType.INT64.struct_format == "q"
        assert DType.BOOL.struct_format == "?"

    def test_all_dtypes_have_byte_size(self) -> None:
        for dt in DType:
            assert dt.byte_size > 0

    def test_all_dtypes_have_struct_format(self) -> None:
        for dt in DType:
            assert len(dt.struct_format) == 1


class TestTensorInfo:
    """Test TensorInfo dataclass."""

    def test_to_dict(self) -> None:
        info = TensorInfo(name="w1", dtype="FLOAT64", shape=(3, 4), offset=0, byte_size=96)
        d = info.to_dict()
        assert d["name"] == "w1"
        assert d["dtype"] == "FLOAT64"
        assert d["shape"] == [3, 4]
        assert d["offset"] == 0
        assert d["byte_size"] == 96

    def test_from_dict(self) -> None:
        d = {"name": "b1", "dtype": "FLOAT32", "shape": [5], "offset": 96, "byte_size": 20}
        info = TensorInfo.from_dict(d)
        assert info.name == "b1"
        assert info.dtype == "FLOAT32"
        assert info.shape == (5,)
        assert info.offset == 96
        assert info.byte_size == 20

    def test_roundtrip(self) -> None:
        info = TensorInfo(name="test", dtype="INT64", shape=(2, 3, 4), offset=100, byte_size=192)
        d = info.to_dict()
        info2 = TensorInfo.from_dict(d)
        assert info == info2


class TestMNWHeader:
    """Test MNWHeader dataclass."""

    def test_to_dict(self) -> None:
        header = MNWHeader(
            model_name="test_model",
            model_version="2.0.0",
            architecture="transformer",
            metadata={"layers": 12},
        )
        d = header.to_dict()
        assert d["model_name"] == "test_model"
        assert d["model_version"] == "2.0.0"
        assert d["architecture"] == "transformer"
        assert d["metadata"]["layers"] == 12

    def test_from_dict(self) -> None:
        d = {
            "model_name": "my_model",
            "model_version": "1.0.0",
            "architecture": "mlp",
            "metadata": {},
            "tensors": [],
        }
        header = MNWHeader.from_dict(d)
        assert header.model_name == "my_model"
        assert header.architecture == "mlp"

    def test_defaults(self) -> None:
        header = MNWHeader(model_name="minimal")
        assert header.model_version == "1.0.0"
        assert header.architecture == ""
        assert header.metadata == {}
        assert header.tensors == []


class TestSerializeDeserialize:
    """Test tensor data serialization."""

    def test_float64_roundtrip(self) -> None:
        t = Tensor([1.0, 2.5, 3.14], (3,))
        raw = _serialize_tensor_data(t, DType.FLOAT64)
        assert len(raw) == 3 * 8
        values = _deserialize_tensor_data(raw, DType.FLOAT64, 3)
        assert values == pytest.approx([1.0, 2.5, 3.14])

    def test_float32_roundtrip(self) -> None:
        t = Tensor([1.0, -2.0, 0.0], (3,))
        raw = _serialize_tensor_data(t, DType.FLOAT32)
        assert len(raw) == 3 * 4
        values = _deserialize_tensor_data(raw, DType.FLOAT32, 3)
        assert values == pytest.approx([1.0, -2.0, 0.0], abs=1e-6)

    def test_int32_roundtrip(self) -> None:
        t = Tensor([10, 20, 30], (3,))
        raw = _serialize_tensor_data(t, DType.INT32)
        assert len(raw) == 3 * 4
        values = _deserialize_tensor_data(raw, DType.INT32, 3)
        assert values == [10, 20, 30]

    def test_int64_roundtrip(self) -> None:
        t = Tensor([100, 200], (2,))
        raw = _serialize_tensor_data(t, DType.INT64)
        assert len(raw) == 2 * 8
        values = _deserialize_tensor_data(raw, DType.INT64, 2)
        assert values == [100, 200]

    def test_bool_roundtrip(self) -> None:
        t = Tensor([1, 0, 1, 1], (4,))
        raw = _serialize_tensor_data(t, DType.BOOL)
        assert len(raw) == 4
        values = _deserialize_tensor_data(raw, DType.BOOL, 4)
        assert values == [1, 0, 1, 1]


class TestMNWFormat:
    """Test .mnw file save and load."""

    def test_save_load_single_tensor(self, tmp_path: Path) -> None:
        path = tmp_path / "model.mnw"
        t = Tensor([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], (2, 3))
        save_mnw(path, {"weight": t}, model_name="test")
        header, tensors = load_mnw(path)
        assert header.model_name == "test"
        assert "weight" in tensors
        assert tensors["weight"].shape == (2, 3)
        assert tensors["weight"].data == pytest.approx([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

    def test_save_load_multiple_tensors(self, tmp_path: Path) -> None:
        path = tmp_path / "model.mnw"
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        b = Tensor([0.5, -0.5], (2,))
        save_mnw(path, {"weight": w, "bias": b}, model_name="mlp")
        header, tensors = load_mnw(path)
        assert header.model_name == "mlp"
        assert len(tensors) == 2
        assert tensors["weight"].shape == (2, 2)
        assert tensors["bias"].shape == (2,)

    def test_save_load_with_metadata(self, tmp_path: Path) -> None:
        path = tmp_path / "model.mnw"
        t = Tensor([0.0], (1,))
        save_mnw(
            path,
            {"x": t},
            model_name="meta_model",
            model_version="3.0.0",
            architecture="cnn",
            metadata={"hidden_size": 768, "layers": 12},
        )
        header, _ = load_mnw(path)
        assert header.model_version == "3.0.0"
        assert header.architecture == "cnn"
        assert header.metadata["hidden_size"] == 768

    def test_save_load_float32(self, tmp_path: Path) -> None:
        path = tmp_path / "model.mnw"
        t = Tensor([1.0, 2.0, 3.0], (3,))
        save_mnw(path, {"data": t}, model_name="f32", dtype=DType.FLOAT32)
        header, tensors = load_mnw(path)
        assert tensors["data"].data == pytest.approx([1.0, 2.0, 3.0], abs=1e-6)

    def test_load_nonexistent(self) -> None:
        with pytest.raises(ModelFormatError, match="File not found"):
            load_mnw("/nonexistent/path/model.mnw")

    def test_load_invalid_magic(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.mnw"
        path.write_bytes(b"BAAD" + b"\x00" * 100)
        with pytest.raises(ModelFormatError, match="Invalid magic"):
            load_mnw(path)

    def test_load_invalid_version(self, tmp_path: Path) -> None:
        path = tmp_path / "bad_ver.mnw"
        data = b"MNW\x00" + struct.pack("<I", 999) + b"\x00" * 100
        path.write_bytes(data)
        with pytest.raises(ModelFormatError, match="Unsupported MNW version"):
            load_mnw(path)

    def test_empty_tensors_dict(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.mnw"
        save_mnw(path, {}, model_name="empty")
        header, tensors = load_mnw(path)
        assert header.model_name == "empty"
        assert len(tensors) == 0

    def test_large_tensor(self, tmp_path: Path) -> None:
        path = tmp_path / "large.mnw"
        data = [float(i) for i in range(1000)]
        t = Tensor(data, (10, 100))
        save_mnw(path, {"big": t}, model_name="large")
        _, tensors = load_mnw(path)
        assert tensors["big"].shape == (10, 100)
        assert tensors["big"].size == 1000


# ===================================================================
# Task 2: ONNX import
# ===================================================================


class TestProtobufHelpers:
    """Test low-level protobuf parsing helpers."""

    def test_read_varint_single_byte(self) -> None:
        data = bytes([42])
        val, pos = _read_varint(data, 0)
        assert val == 42
        assert pos == 1

    def test_read_varint_multi_byte(self) -> None:
        # 300 = 0b100101100 → varint bytes: 0xAC 0x02
        data = bytes([0xAC, 0x02])
        val, pos = _read_varint(data, 0)
        assert val == 300
        assert pos == 2

    def test_build_varint(self) -> None:
        raw = _build_onnx_varint(300)
        val, _ = _read_varint(raw, 0)
        assert val == 300

    def test_build_field_varint(self) -> None:
        field_bytes = _build_onnx_field(1, 0, 9)
        assert len(field_bytes) > 0

    def test_build_field_length_delimited(self) -> None:
        field_bytes = _build_onnx_field(2, 2, b"hello")
        assert len(field_bytes) > 0


class TestONNXTensorConversion:
    """Test ONNX tensor to Mapanare tensor conversion."""

    def test_float_data(self) -> None:
        info = ONNXTensorInfo(
            name="w",
            data_type=1,
            shape=(2, 2),
            float_data=[1.0, 2.0, 3.0, 4.0],
        )
        t = _onnx_tensor_to_mapanare(info)
        assert t.shape == (2, 2)
        assert t.data == pytest.approx([1.0, 2.0, 3.0, 4.0])

    def test_double_data(self) -> None:
        info = ONNXTensorInfo(
            name="w",
            data_type=11,
            shape=(3,),
            double_data=[1.5, 2.5, 3.5],
        )
        t = _onnx_tensor_to_mapanare(info)
        assert t.shape == (3,)
        assert t.data == pytest.approx([1.5, 2.5, 3.5])

    def test_int32_data(self) -> None:
        info = ONNXTensorInfo(
            name="idx",
            data_type=6,
            shape=(2,),
            int32_data=[10, 20],
        )
        t = _onnx_tensor_to_mapanare(info)
        assert t.data == pytest.approx([10.0, 20.0])

    def test_int64_data(self) -> None:
        info = ONNXTensorInfo(
            name="idx",
            data_type=7,
            shape=(2,),
            int64_data=[100, 200],
        )
        t = _onnx_tensor_to_mapanare(info)
        assert t.data == pytest.approx([100.0, 200.0])

    def test_raw_data_float32(self) -> None:
        raw = struct.pack("<3f", 1.0, 2.0, 3.0)
        info = ONNXTensorInfo(name="w", data_type=1, shape=(3,), raw_data=raw)
        t = _onnx_tensor_to_mapanare(info)
        assert t.data == pytest.approx([1.0, 2.0, 3.0], abs=1e-5)

    def test_empty_tensor(self) -> None:
        info = ONNXTensorInfo(name="empty", data_type=1, shape=(0,))
        t = _onnx_tensor_to_mapanare(info)
        assert t.size == 0

    def test_zero_fill_on_missing_data(self) -> None:
        info = ONNXTensorInfo(name="zeros", data_type=1, shape=(3,))
        t = _onnx_tensor_to_mapanare(info)
        assert t.data == [0.0, 0.0, 0.0]


class TestONNXSaveLoad:
    """Test ONNX file save and load roundtrip."""

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "model.onnx"
        w = Tensor([1.0, 2.0, 3.0, 4.0], (2, 2))
        save_onnx_simple(path, {"weight": w}, model_name="test_model")

        info, tensors = load_onnx(path)
        assert info.ir_version == 9
        assert info.producer_name == "mapanare"
        assert "weight" in tensors
        assert tensors["weight"].shape == (2, 2)
        assert tensors["weight"].data == pytest.approx([1.0, 2.0, 3.0, 4.0])

    def test_save_load_multiple(self, tmp_path: Path) -> None:
        path = tmp_path / "multi.onnx"
        t1 = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        t2 = Tensor([0.5, -0.5], (2,))
        save_onnx_simple(path, {"w": t1, "b": t2})
        info, tensors = load_onnx(path)
        assert len(tensors) == 2
        assert tensors["w"].shape == (2, 2)
        assert tensors["b"].shape == (2,)

    def test_load_nonexistent(self) -> None:
        with pytest.raises(ModelFormatError, match="File not found"):
            load_onnx("/no/such/file.onnx")

    def test_opset_version(self, tmp_path: Path) -> None:
        path = tmp_path / "opset.onnx"
        save_onnx_simple(path, {"x": Tensor([1.0], (1,))})
        info, _ = load_onnx(path)
        assert info.opset_version == 19

    def test_graph_name(self, tmp_path: Path) -> None:
        path = tmp_path / "named.onnx"
        save_onnx_simple(path, {"x": Tensor([1.0], (1,))}, model_name="my_graph")
        info, _ = load_onnx(path)
        assert info.graph_name == "my_graph"


# ===================================================================
# Task 3: Safetensors / HuggingFace import
# ===================================================================


class TestF16BF16Decoding:
    """Test half-precision float decoding."""

    def test_decode_f16(self) -> None:
        # Pack known f16 values
        raw = struct.pack("<3e", 1.0, 2.0, 0.5)
        values = _decode_f16(raw, 3)
        assert values == pytest.approx([1.0, 2.0, 0.5], abs=1e-3)

    def test_decode_bf16_ones(self) -> None:
        # bfloat16 of 1.0: upper 16 bits of float32 1.0
        # float32 1.0 = 0x3F800000 → bf16 = 0x3F80
        raw = struct.pack("<H", 0x3F80)
        values = _decode_bf16(raw, 1)
        assert values == pytest.approx([1.0])

    def test_decode_bf16_zero(self) -> None:
        raw = struct.pack("<H", 0x0000)
        values = _decode_bf16(raw, 1)
        assert values == pytest.approx([0.0])


class TestSafetensorsFormat:
    """Test safetensors save and load."""

    def test_save_load_roundtrip_f64(self, tmp_path: Path) -> None:
        path = tmp_path / "model.safetensors"
        t = Tensor([1.0, 2.0, 3.0], (3,))
        save_safetensors(path, {"weight": t}, dtype="F64")
        meta, tensors = load_safetensors(path)
        assert "weight" in tensors
        assert tensors["weight"].data == pytest.approx([1.0, 2.0, 3.0])
        assert meta.tensor_dtypes["weight"] == "F64"

    def test_save_load_roundtrip_f32(self, tmp_path: Path) -> None:
        path = tmp_path / "model.safetensors"
        t = Tensor([1.0, -2.0, 0.0, 3.14], (2, 2))
        save_safetensors(path, {"data": t}, dtype="F32")
        _, tensors = load_safetensors(path)
        assert tensors["data"].shape == (2, 2)
        assert tensors["data"].data == pytest.approx([1.0, -2.0, 0.0, 3.14], abs=1e-5)

    def test_save_load_with_metadata(self, tmp_path: Path) -> None:
        path = tmp_path / "meta.safetensors"
        t = Tensor([0.0], (1,))
        save_safetensors(path, {"x": t}, metadata={"format": "pt", "model_name": "test"})
        meta, _ = load_safetensors(path)
        assert meta.metadata["model_name"] == "test"
        assert meta.metadata["format"] == "pt"

    def test_multiple_tensors(self, tmp_path: Path) -> None:
        path = tmp_path / "multi.safetensors"
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        b = Tensor([0.1, 0.2], (2,))
        save_safetensors(path, {"weight": w, "bias": b})
        _, tensors = load_safetensors(path)
        assert len(tensors) == 2
        assert tensors["weight"].shape == (2, 2)
        assert tensors["bias"].shape == (2,)

    def test_tensor_names_tracked(self, tmp_path: Path) -> None:
        path = tmp_path / "names.safetensors"
        save_safetensors(path, {"a": Tensor([1.0], (1,)), "b": Tensor([2.0], (1,))})
        meta, _ = load_safetensors(path)
        assert set(meta.tensor_names) == {"a", "b"}

    def test_tensor_shapes_tracked(self, tmp_path: Path) -> None:
        path = tmp_path / "shapes.safetensors"
        save_safetensors(path, {"w": Tensor([0.0] * 6, (2, 3))})
        meta, _ = load_safetensors(path)
        assert meta.tensor_shapes["w"] == (2, 3)

    def test_load_nonexistent(self) -> None:
        with pytest.raises(ModelFormatError, match="File not found"):
            load_safetensors("/no/file.safetensors")

    def test_load_truncated_header(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.safetensors"
        path.write_bytes(b"\x01\x00")  # Too short
        with pytest.raises(ModelFormatError, match="cannot read header size"):
            load_safetensors(path)

    def test_save_load_int_types(self, tmp_path: Path) -> None:
        path = tmp_path / "ints.safetensors"
        t = Tensor([1, 2, 3], (3,))
        save_safetensors(path, {"idx": t}, dtype="I32")
        _, tensors = load_safetensors(path)
        assert tensors["idx"].data == pytest.approx([1.0, 2.0, 3.0])


class TestHuggingFaceConfig:
    """Test HuggingFace config loading."""

    def test_load_config(self, tmp_path: Path) -> None:
        config_data = {
            "model_type": "llama",
            "architectures": ["LlamaForCausalLM"],
            "hidden_size": 4096,
            "num_hidden_layers": 32,
            "num_attention_heads": 32,
            "intermediate_size": 11008,
            "vocab_size": 32000,
            "max_position_embeddings": 2048,
            "custom_field": True,
        }
        (tmp_path / "config.json").write_text(json.dumps(config_data))

        config = load_huggingface_config(tmp_path)
        assert config.model_type == "llama"
        assert config.architectures == ["LlamaForCausalLM"]
        assert config.hidden_size == 4096
        assert config.num_hidden_layers == 32
        assert config.num_attention_heads == 32
        assert config.vocab_size == 32000
        assert config.extra["custom_field"] is True

    def test_load_config_from_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps({"model_type": "gpt2", "hidden_size": 768}))
        config = load_huggingface_config(config_path)
        assert config.model_type == "gpt2"
        assert config.hidden_size == 768

    def test_config_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(ModelFormatError, match="Config not found"):
            load_huggingface_config(tmp_path / "no_config")

    def test_config_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("not json")
        with pytest.raises(ModelFormatError, match="Failed to load config"):
            load_huggingface_config(tmp_path)

    def test_config_defaults(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text("{}")
        config = load_huggingface_config(tmp_path)
        assert config.model_type == ""
        assert config.hidden_size == 0
        assert config.architectures == []


class TestHuggingFaceModel:
    """Test HuggingFace model directory loading."""

    def test_load_model_with_safetensors(self, tmp_path: Path) -> None:
        # Write config
        (tmp_path / "config.json").write_text(json.dumps({"model_type": "bert", "hidden_size": 4}))
        # Write safetensors
        t = Tensor([1.0, 2.0, 3.0, 4.0], (2, 2))
        save_safetensors(tmp_path / "model.safetensors", {"embeddings": t})

        config, tensors = load_huggingface_model(tmp_path)
        assert config.model_type == "bert"
        assert "embeddings" in tensors
        assert tensors["embeddings"].shape == (2, 2)

    def test_load_model_not_directory(self) -> None:
        with pytest.raises(ModelFormatError, match="Not a directory"):
            load_huggingface_model("/nonexistent/dir")

    def test_load_model_no_weights(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text(json.dumps({"model_type": "test"}))
        with pytest.raises(ModelFormatError, match="No model weights found"):
            load_huggingface_model(tmp_path)

    def test_load_model_pytorch_unsupported(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text(json.dumps({"model_type": "test"}))
        (tmp_path / "pytorch_model.bin").write_bytes(b"fake")
        with pytest.raises(ModelFormatError, match="PyTorch .bin format not supported"):
            load_huggingface_model(tmp_path)

    def test_load_sharded_model(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text(json.dumps({"model_type": "sharded"}))
        # Create two shard files
        save_safetensors(
            tmp_path / "model-00001-of-00002.safetensors",
            {"layer0.weight": Tensor([1.0, 2.0], (2,))},
        )
        save_safetensors(
            tmp_path / "model-00002-of-00002.safetensors",
            {"layer1.weight": Tensor([3.0, 4.0], (2,))},
        )
        config, tensors = load_huggingface_model(tmp_path)
        assert "layer0.weight" in tensors
        assert "layer1.weight" in tensors


# ===================================================================
# Task 4: Standard model interface: predict, encode, generate
# ===================================================================


class TestModelInterface:
    """Test MapanareModel implements the standard interface."""

    def test_create_model(self) -> None:
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        assert model.name == "test"
        assert model.version == "1.0.0"
        assert "w" in model.weights

    def test_model_properties(self) -> None:
        model = MapanareModel(
            name="my_model",
            weights={},
            version="2.0.0",
            architecture="transformer",
            metadata={"layers": 6},
        )
        assert model.name == "my_model"
        assert model.version == "2.0.0"
        assert model.architecture == "transformer"
        assert model.metadata["layers"] == 6

    def test_weight_access(self) -> None:
        w = Tensor([1.0, 2.0], (2,))
        model = MapanareModel(name="test", weights={"layer.weight": w})
        result = model.weight("layer.weight")
        assert result.data == pytest.approx([1.0, 2.0])

    def test_weight_not_found(self) -> None:
        model = MapanareModel(name="test", weights={})
        with pytest.raises(KeyError, match="not found"):
            model.weight("missing")

    def test_predict_default_matmul(self) -> None:
        # Identity matrix weight → predict returns input
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        inp = Tensor([3.0, 4.0], (2,))
        out = model.predict(inp)
        assert out.data == pytest.approx([3.0, 4.0])

    def test_predict_custom_fn(self) -> None:
        model = MapanareModel(name="test", weights={"w": Tensor([2.0], (1,))})

        def my_predict(inp: Tensor, weights: dict[str, Tensor]) -> Tensor:
            scale = weights["w"].data[0]
            return Tensor([v * scale for v in inp.data], inp.shape)

        model.set_predict_fn(my_predict)
        out = model.predict(Tensor([1.0, 2.0, 3.0], (3,)))
        assert out.data == pytest.approx([2.0, 4.0, 6.0])

    def test_encode_defaults_to_predict(self) -> None:
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        inp = Tensor([5.0, 6.0], (2,))
        encoded = model.encode(inp)
        predicted = model.predict(inp)
        assert encoded.data == pytest.approx(predicted.data)

    def test_encode_custom_fn(self) -> None:
        model = MapanareModel(name="test", weights={})

        def my_encode(inp: Tensor, weights: dict[str, Tensor]) -> Tensor:
            return Tensor([v / 2.0 for v in inp.data], inp.shape)

        model.set_encode_fn(my_encode)
        out = model.encode(Tensor([4.0, 6.0], (2,)))
        assert out.data == pytest.approx([2.0, 3.0])

    def test_generate_defaults_to_predict(self) -> None:
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        inp = Tensor([1.0, 2.0], (2,))
        generated = model.generate(inp)
        predicted = model.predict(inp)
        assert generated.data == pytest.approx(predicted.data)

    def test_generate_custom_fn(self) -> None:
        model = MapanareModel(name="test", weights={})

        def my_generate(
            inp: Tensor, weights: dict[str, Tensor], max_len: int, temp: float
        ) -> Tensor:
            # Just repeat the input max_len times
            return Tensor(list(inp.data) * min(max_len, 3), (len(inp.data) * min(max_len, 3),))

        model.set_generate_fn(my_generate)
        out = model.generate(Tensor([1.0, 2.0], (2,)), max_length=2)
        assert out.data == pytest.approx([1.0, 2.0, 1.0, 2.0])

    def test_generate_temperature_parameter(self) -> None:
        model = MapanareModel(name="test", weights={})
        temps: list[float] = []

        def capture_temp(
            inp: Tensor, weights: dict[str, Tensor], max_len: int, temp: float
        ) -> Tensor:
            temps.append(temp)
            return inp

        model.set_generate_fn(capture_temp)
        model.generate(Tensor([1.0], (1,)), temperature=0.7)
        assert temps[0] == pytest.approx(0.7)

    def test_predict_no_compatible_weight(self) -> None:
        # 3D weight — no default matmul possible
        w = Tensor([0.0] * 8, (2, 2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        inp = Tensor([1.0, 2.0], (2,))
        # Should return input unchanged
        out = model.predict(inp)
        assert out.data == pytest.approx([1.0, 2.0])

    def test_predict_2d_input(self) -> None:
        w = Tensor([1.0, 0.0, 0.0, 1.0], (2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        inp = Tensor([1.0, 2.0, 3.0, 4.0], (2, 2))
        out = model.predict(inp)
        assert out.shape == (2, 2)


class TestModelSaveFormats:
    """Test MapanareModel save to different formats."""

    def test_save_mnw(self, tmp_path: Path) -> None:
        w = Tensor([1.0, 2.0, 3.0], (3,))
        model = MapanareModel(name="test", weights={"w": w})
        path = tmp_path / "model.mnw"
        model.save(path, fmt="mnw")
        loaded = MapanareModel.from_mnw(path)
        assert loaded.name == "test"
        assert loaded.weights["w"].data == pytest.approx([1.0, 2.0, 3.0])

    def test_save_safetensors(self, tmp_path: Path) -> None:
        w = Tensor([1.0, 2.0], (2,))
        model = MapanareModel(name="test", weights={"w": w})
        path = tmp_path / "model.safetensors"
        model.save(path, fmt="safetensors")
        loaded = MapanareModel.from_safetensors(path)
        assert "w" in loaded.weights

    def test_save_onnx(self, tmp_path: Path) -> None:
        w = Tensor([1.0, 2.0, 3.0, 4.0], (2, 2))
        model = MapanareModel(name="test", weights={"w": w})
        path = tmp_path / "model.onnx"
        model.save(path, fmt="onnx")
        loaded = MapanareModel.from_onnx(path)
        assert "w" in loaded.weights

    def test_save_unsupported_format(self) -> None:
        model = MapanareModel(name="test", weights={})
        with pytest.raises(ValueError, match="Unsupported format"):
            model.save("/tmp/model.xyz", fmt="xyz")

    def test_from_huggingface(self, tmp_path: Path) -> None:
        (tmp_path / "config.json").write_text(
            json.dumps(
                {
                    "model_type": "gpt2",
                    "architectures": ["GPT2LMHeadModel"],
                    "hidden_size": 2,
                }
            )
        )
        save_safetensors(
            tmp_path / "model.safetensors",
            {"wte.weight": Tensor([1.0, 2.0, 3.0, 4.0], (2, 2))},
        )
        model = MapanareModel.from_huggingface(tmp_path)
        assert model.name == "gpt2"
        assert model.architecture == "GPT2LMHeadModel"
        assert "wte.weight" in model.weights


# ===================================================================
# Task 5: Model registry: mapanare://models/
# ===================================================================


class TestModelRegistryEntry:
    """Test ModelRegistryEntry dataclass."""

    def test_uri(self) -> None:
        entry = ModelRegistryEntry(
            name="llama", version="2.0.0", path="/models/llama", format="mnw"
        )
        assert entry.uri == "mapanare://models/llama/2.0.0"

    def test_to_dict(self) -> None:
        entry = ModelRegistryEntry(
            name="test", version="1.0.0", path="/path", format="onnx", description="A test model"
        )
        d = entry.to_dict()
        assert d["name"] == "test"
        assert d["format"] == "onnx"
        assert d["description"] == "A test model"

    def test_from_dict(self) -> None:
        d = {"name": "m", "version": "1.0.0", "path": "/p", "format": "mnw"}
        entry = ModelRegistryEntry.from_dict(d)
        assert entry.name == "m"
        assert entry.format == "mnw"

    def test_roundtrip(self) -> None:
        entry = ModelRegistryEntry(
            name="roundtrip",
            version="3.0.0",
            path="/some/path",
            format="safetensors",
            architecture="bert",
            sha256="abc123",
        )
        d = entry.to_dict()
        entry2 = ModelRegistryEntry.from_dict(d)
        assert entry.name == entry2.name
        assert entry.version == entry2.version
        assert entry.format == entry2.format


class TestModelRegistry:
    """Test ModelRegistry functionality."""

    def test_register_and_get(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        # Create a dummy model file
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        entry = registry.register("test_model", model_path, version="1.0.0", fmt="mnw")
        assert entry.name == "test_model"
        assert entry.version == "1.0.0"

        found = registry.get("test_model", "1.0.0")
        assert found is not None
        assert found.name == "test_model"

    def test_get_latest_version(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("model", model_path, version="1.0.0")
        registry.register("model", model_path, version="2.0.0")
        registry.register("model", model_path, version="1.5.0")

        latest = registry.get("model")
        assert latest is not None
        assert latest.version == "2.0.0"

    def test_get_nonexistent(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        assert registry.get("nonexistent") is None

    def test_list_models(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("alpha", model_path, version="1.0.0")
        registry.register("beta", model_path, version="1.0.0")
        registry.register("alpha", model_path, version="2.0.0")

        models = registry.list_models()
        assert len(models) == 3
        # Sorted by name then version
        assert models[0].name == "alpha"
        assert models[0].version == "1.0.0"
        assert models[1].name == "alpha"
        assert models[1].version == "2.0.0"
        assert models[2].name == "beta"

    def test_list_names(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("z_model", model_path)
        registry.register("a_model", model_path)
        names = registry.list_names()
        assert names == ["a_model", "z_model"]

    def test_list_versions(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("model", model_path, version="1.0.0")
        registry.register("model", model_path, version="3.0.0")
        registry.register("model", model_path, version="2.0.0")

        versions = registry.list_versions("model")
        assert versions == ["1.0.0", "2.0.0", "3.0.0"]

    def test_list_versions_nonexistent(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        assert registry.list_versions("nope") == []

    def test_remove_specific_version(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("model", model_path, version="1.0.0")
        registry.register("model", model_path, version="2.0.0")

        removed = registry.remove("model", "1.0.0")
        assert removed is True
        assert registry.get("model", "1.0.0") is None
        assert registry.get("model", "2.0.0") is not None

    def test_remove_all_versions(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("model", model_path, version="1.0.0")
        registry.register("model", model_path, version="2.0.0")

        removed = registry.remove("model")
        assert removed is True
        assert registry.get("model") is None

    def test_remove_nonexistent(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        assert registry.remove("nope") is False

    def test_remove_nonexistent_version(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")
        registry.register("model", model_path, version="1.0.0")
        assert registry.remove("model", "9.9.9") is False

    def test_resolve_uri(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("llama", model_path, version="2.0.0")

        entry = registry.resolve_uri("mapanare://models/llama/2.0.0")
        assert entry is not None
        assert entry.name == "llama"

    def test_resolve_uri_no_version(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        registry.register("llama", model_path, version="1.0.0")
        entry = registry.resolve_uri("mapanare://models/llama")
        assert entry is not None
        assert entry.name == "llama"

    def test_resolve_uri_invalid_prefix(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        with pytest.raises(ValueError, match="Invalid model URI"):
            registry.resolve_uri("http://example.com/model")

    def test_resolve_uri_not_found(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        result = registry.resolve_uri("mapanare://models/nonexistent")
        assert result is None

    def test_load_model_from_registry(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        w = Tensor([1.0, 2.0, 3.0], (3,))
        save_mnw(model_path, {"w": w}, model_name="loadable")

        registry.register("loadable", model_path, fmt="mnw")
        model = registry.load_model("loadable")
        assert model.name == "loadable"
        assert model.weights["w"].data == pytest.approx([1.0, 2.0, 3.0])

    def test_load_model_via_uri(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([5.0], (1,))}, model_name="uri_model")

        registry.register("uri_model", model_path, fmt="mnw")
        model = registry.load_model("mapanare://models/uri_model")
        assert model.name == "uri_model"

    def test_load_model_not_found(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        with pytest.raises(ModelFormatError, match="Model not found"):
            registry.load_model("nonexistent")

    def test_load_model_file_missing(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        # Register with a path that doesn't exist
        registry.register("ghost", "/nonexistent/model.mnw", fmt="mnw")
        with pytest.raises(ModelFormatError, match="Model file not found"):
            registry.load_model("ghost")

    def test_persistence(self, tmp_path: Path) -> None:
        registry_dir = tmp_path / "registry"
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        # Register in first instance
        reg1 = ModelRegistry(registry_dir=registry_dir)
        reg1.register("persistent", model_path, version="1.0.0")

        # Load in new instance
        reg2 = ModelRegistry(registry_dir=registry_dir)
        entry = reg2.get("persistent", "1.0.0")
        assert entry is not None
        assert entry.name == "persistent"

    def test_sha256_computed(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.mnw"
        save_mnw(model_path, {"w": Tensor([1.0], (1,))}, model_name="test")

        entry = registry.register("hashed", model_path)
        assert len(entry.sha256) == 64  # SHA-256 hex digest

    def test_load_onnx_from_registry(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.onnx"
        save_onnx_simple(model_path, {"w": Tensor([1.0, 2.0], (2,))})

        registry.register("onnx_model", model_path, fmt="onnx")
        model = registry.load_model("onnx_model")
        assert "w" in model.weights

    def test_load_safetensors_from_registry(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.safetensors"
        save_safetensors(model_path, {"w": Tensor([1.0, 2.0], (2,))})

        registry.register("st_model", model_path, fmt="safetensors")
        model = registry.load_model("st_model")
        assert "w" in model.weights

    def test_unsupported_format_in_registry(self, tmp_path: Path) -> None:
        registry = ModelRegistry(registry_dir=tmp_path / "registry")
        model_path = tmp_path / "model.xyz"
        model_path.write_bytes(b"fake")

        registry.register("bad", model_path, fmt="xyz_format")
        with pytest.raises(ModelFormatError, match="Unsupported format"):
            registry.load_model("bad")


class TestComputeFileSha256:
    """Test file hashing utility."""

    def test_known_hash(self, tmp_path: Path) -> None:
        path = tmp_path / "test.bin"
        path.write_bytes(b"hello world")
        sha = _compute_file_sha256(path)
        assert len(sha) == 64
        # Known SHA-256 of "hello world"
        assert sha == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "empty.bin"
        path.write_bytes(b"")
        sha = _compute_file_sha256(path)
        assert len(sha) == 64


class TestGetModelRegistry:
    """Test the singleton registry accessor."""

    def test_get_with_custom_dir(self, tmp_path: Path) -> None:
        registry = get_model_registry(tmp_path / "custom_registry")
        assert registry.registry_dir == tmp_path / "custom_registry"
