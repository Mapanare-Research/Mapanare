"""Benchmark: Enum matching — Python equivalent."""


def area(tag, a, b):
    if tag == 0:
        return a * a * 3  # Circle
    if tag == 1:
        return a * a  # Square
    if tag == 2:
        return a * b // 2  # Triangle
    if tag == 3:
        return 0  # Point
    if tag == 4:
        return a  # Line
    return a * b  # Rect


def main():
    total = 0
    for i in range(100_000):
        tag = i % 6
        a = (
            i % 50 + 1
            if tag == 0
            else (
                i % 30 + 1
                if tag == 1
                else (
                    i % 20 + 1
                    if tag == 2
                    else 0 if tag == 3 else i % 100 + 1 if tag == 4 else i % 25 + 1
                )
            )
        )
        b = 0 if tag in (0, 1, 3, 4) else i % 40 + 1 if tag == 2 else i % 35 + 1
        total += area(tag, a, b)
    print(f"checksum = {total}")


if __name__ == "__main__":
    main()
