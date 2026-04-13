// Benchmark 5: Simulated agent fanout — Go equivalent.
package main

import "fmt"

func worker(id, message int) int {
	return (message * (id + 1)) % 1000000
}

func main() {
	total := 0
	for msg := 0; msg < 1000; msg++ {
		for w := 0; w < 10; w++ {
			total += worker(w, msg)
		}
	}
	fmt.Printf("total = %d\n", total)
}
