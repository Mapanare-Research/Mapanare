"""Benchmark: Struct allocation — Python equivalent."""
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    z: int

def main():
    s = 0
    for i in range(100_000):
        p = Point(i, i * 2, i * 3)
        s += p.x + p.y + p.z
    print(f"checksum = {s}")

if __name__ == "__main__":
    main()
