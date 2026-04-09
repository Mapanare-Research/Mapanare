# GPU Examples

GPU-accelerated tensor operations from Mapanare code.

## Requirements

- NVIDIA GPU (tested on RTX 4090)
- Linux or WSL2 with `libcuda.so` accessible
- No CUDA SDK installation needed (loaded via dlopen)

## Running

```bash
mnc run vector_add.mn
mnc run matmul_bench.mn
```

Programs detect GPU availability and degrade gracefully to CPU.
