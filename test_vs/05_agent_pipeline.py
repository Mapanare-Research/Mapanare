"""Benchmark: Agent Pipeline Processing Messages — Python asyncio baseline."""

import asyncio
import time


async def parser(inbox: asyncio.Queue, outbox: asyncio.Queue, stop: asyncio.Event):
    while not stop.is_set():
        try:
            raw = await asyncio.wait_for(inbox.get(), timeout=0.1)
            await outbox.put(len(raw))
        except asyncio.TimeoutError:
            continue


async def validator(inbox: asyncio.Queue, outbox: asyncio.Queue, stop: asyncio.Event):
    while not stop.is_set():
        try:
            value = await asyncio.wait_for(inbox.get(), timeout=0.1)
            await outbox.put(value if value > 0 else 0)
        except asyncio.TimeoutError:
            continue


async def transformer(inbox: asyncio.Queue, outbox: asyncio.Queue, stop: asyncio.Event):
    while not stop.is_set():
        try:
            value = await asyncio.wait_for(inbox.get(), timeout=0.1)
            await outbox.put(value * 3 + 7)
        except asyncio.TimeoutError:
            continue


async def main():
    p_in: asyncio.Queue = asyncio.Queue(maxsize=1024)
    p_out: asyncio.Queue = asyncio.Queue(maxsize=1024)
    v_out: asyncio.Queue = asyncio.Queue(maxsize=1024)
    t_out: asyncio.Queue = asyncio.Queue(maxsize=1024)

    stop = asyncio.Event()

    t1 = asyncio.create_task(parser(p_in, p_out, stop))
    t2 = asyncio.create_task(validator(p_out, v_out, stop))
    t3 = asyncio.create_task(transformer(v_out, t_out, stop))

    start = time.perf_counter()
    total = 0
    for i in range(1000):
        msg = "message_payload_data_" + str(i)
        await p_in.put(msg)
        result = await t_out.get()
        total += result
    elapsed = time.perf_counter() - start

    stop.set()
    t1.cancel()
    t2.cancel()
    t3.cancel()

    print(f"sum = {total}")
    print(f"Time: {elapsed:.4f}s")


if __name__ == "__main__":
    asyncio.run(main())
