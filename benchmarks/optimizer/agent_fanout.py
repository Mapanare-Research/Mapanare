"""Benchmark 5: Simulated agent fanout — Python equivalent."""
def worker(wid, message):
    return (message * (wid + 1)) % 1000000

total = 0
for msg in range(1000):
    for w in range(10):
        total += worker(w, msg)
print(f"total = {total}")
