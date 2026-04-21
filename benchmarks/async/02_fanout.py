"""Async benchmark 2: Fan-out (Python asyncio baseline)."""

import asyncio


async def compute(n: int) -> int:
    total = 0
    for i in range(1, n + 1):
        total += i
    return total


async def fanout() -> int:
    tasks = [compute(i) for i in range(1, 101)]
    results = await asyncio.gather(*tasks)
    return sum(results)


def main():
    result = asyncio.run(fanout())
    print(f"checksum = {result}")


if __name__ == "__main__":
    main()
