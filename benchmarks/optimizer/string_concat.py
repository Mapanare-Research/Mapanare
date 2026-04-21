"""Benchmark 4: String concatenation — Python equivalent."""

result = ""
for _ in range(10000):
    result += "hello"
print(f"len = {len(result)}")
