package main

import (
	"fmt"
	"sync"
)

func compute(n int) int {
	total := 0
	for i := 1; i <= n; i++ {
		total += i
	}
	return total
}

func main() {
	results := make([]int, 100)
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			results[idx] = compute(idx + 1)
		}(i)
	}
	wg.Wait()
	total := 0
	for _, v := range results {
		total += v
	}
	fmt.Printf("checksum = %d\n", total)
}
