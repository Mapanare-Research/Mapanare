"""Async benchmark 3: I/O-bound simulation (Python asyncio baseline)."""
import asyncio

async def io_task(id: int) -> int:
    return 1

async def io_fanout() -> int:
    tasks = [io_task(i) for i in range(1000)]
    results = await asyncio.gather(*tasks)
    return sum(results)

def main():
    result = asyncio.run(io_fanout())
    print(f"checksum = {result}")

if __name__ == "__main__":
    main()
