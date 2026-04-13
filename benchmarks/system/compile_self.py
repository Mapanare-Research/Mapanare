"""Benchmark: Compile-self proxy — Python equivalent."""

def make_grid(w, h):
    return [(i * 7 + 13) % 256 for i in range(w * h)]

def simulate_step(grid, w, h):
    s = 0
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            center = grid[y * w + x]
            north = grid[(y - 1) * w + x]
            south = grid[(y + 1) * w + x]
            east = grid[y * w + x + 1]
            west = grid[y * w + x - 1]
            s += (center + north + south + east + west) // 5
    return s

def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n - 1) + fibonacci(n - 2)

def collatz_steps(n):
    val, steps = n, 0
    while val != 1:
        rem = val % 2
        if rem == 0:
            val = val // 2
        else:
            val = val * 3 + 1
        steps += 1
    return steps

def main():
    w, h = 50, 50
    grid = make_grid(w, h)
    sim_result = sum(simulate_step(grid, w, h) for _ in range(10))
    fib_result = fibonacci(25)
    collatz_sum = sum(collatz_steps(i) for i in range(1, 1001))
    print(f"checksum = {sim_result + fib_result + collatz_sum}")

if __name__ == "__main__":
    main()
