"""Async benchmark 4: Mixed CPU + I/O simulation (Python asyncio baseline)."""
import asyncio

async def cpu_task(n: int) -> int:
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

async def io_task(id: int) -> int:
    return id

async def mixed() -> int:
    total = 0
    for i in range(1, 51):
        if i % 2 == 0:
            total += await cpu_task(i)
        else:
            total += await io_task(i)
    return total

def main():
    result = asyncio.run(mixed())
    print(f"checksum = {result}")

if __name__ == "__main__":
    main()
