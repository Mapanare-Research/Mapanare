"""Benchmark: Concurrent Message Passing — Python asyncio baseline."""

import asyncio
import time


async def worker(inbox: asyncio.Queue, outbox: asyncio.Queue, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            val = await asyncio.wait_for(inbox.get(), timeout=0.1)
            await outbox.put(val * 2 + 1)
        except asyncio.TimeoutError:
            continue


async def main():
    inbox: asyncio.Queue[int] = asyncio.Queue(maxsize=1024)
    outbox: asyncio.Queue[int] = asyncio.Queue(maxsize=1024)
    stop = asyncio.Event()

    task = asyncio.create_task(worker(inbox, outbox, stop))

    start = time.perf_counter()
    total = 0
    for i in range(10_000):
        await inbox.put(i)
        result = await outbox.get()
        total += result
    elapsed = time.perf_counter() - start

    stop.set()
    await task

    print(f"sum = {total}")
    print(f"Time: {elapsed:.4f}s")


if __name__ == "__main__":
    asyncio.run(main())
