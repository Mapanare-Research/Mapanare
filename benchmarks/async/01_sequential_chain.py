"""Async benchmark 1: Sequential await chain (Python asyncio baseline)."""
import asyncio

async def step(n: int) -> int:
    return n

async def chain() -> int:
    total = 0
    for i in range(1, 101):
        total += await step(i)
    return total

def main():
    result = asyncio.run(chain())
    print(f"checksum = {result}")

if __name__ == "__main__":
    main()
