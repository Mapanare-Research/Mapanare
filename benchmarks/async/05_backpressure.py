"""Async benchmark 5: Backpressure chain (Python asyncio baseline)."""
import asyncio

async def stage_a(n: int) -> int:
    return n + 1

async def stage_b(n: int) -> int:
    return n * 2

async def stage_c(n: int) -> int:
    return n - 1

async def pipeline() -> int:
    total = 0
    for i in range(50):
        a = await stage_a(i)
        b = await stage_b(a)
        c = await stage_c(b)
        total += c
    return total

def main():
    result = asyncio.run(pipeline())
    print(f"checksum = {result}")

if __name__ == "__main__":
    main()
