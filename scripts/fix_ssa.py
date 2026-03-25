#!/usr/bin/env python3
"""Fix duplicate SSA value names in LLVM IR (stub — not yet working).

The self-hosted compiler's relaxed SSA can produce duplicate value definitions.
This script is a placeholder for a future SSA fixup pass.

Currently does nothing (passes IR through unchanged).
"""

import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: fix_ssa.py input.ll [-o output.ll]", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        ir = f.read()

    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        with open(sys.argv[idx + 1], "w") as f:
            f.write(ir)
    else:
        print(ir)


if __name__ == "__main__":
    main()
