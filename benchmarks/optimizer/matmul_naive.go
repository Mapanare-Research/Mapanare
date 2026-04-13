// Benchmark 3: Naive matrix multiply — Go equivalent.
package main

import "fmt"

func main() {
	n := 64
	n2 := n * n
	a := make([]int, n2)
	b := make([]int, n2)
	c := make([]int, n2)
	for i := 0; i < n2; i++ {
		a[i] = (i*3 + 7) % 100
		b[i] = (i*5 + 13) % 100
	}
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			s := 0
			for k := 0; k < n; k++ {
				s += a[i*n+k] * b[k*n+j]
			}
			c[i*n+j] = s
		}
	}
	cs := c[0] + c[n-1] + c[(n-1)*n] + c[n2-1]
	fmt.Printf("checksum = %d\n", cs)
}
