def collatz_length(start: int) -> int:
    n = start
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps


max_len = 0
max_n = 0
i = 1
while i < 1000000:
    length = collatz_length(i)
    if length > max_len:
        max_len = length
        max_n = i
    i += 1
print(max_n)
print(max_len)
