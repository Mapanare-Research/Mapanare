// Benchmark 4: String concatenation — Go equivalent.
package main

import "fmt"

func main() {
	result := ""
	for i := 0; i < 10000; i++ {
		result += "hello"
	}
	fmt.Printf("len = %d\n", len(result))
}
