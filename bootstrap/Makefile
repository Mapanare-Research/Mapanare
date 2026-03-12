# Bootstrap Makefile — Build self-hosted compiler from Python bootstrap
#
# Usage:
#   make bootstrap    Build self-hosted compiler (Stage 1)
#   make verify       Three-stage bootstrap verification
#   make clean        Remove build artifacts

PYTHON ?= python
SELF_DIR := ../mapanare/self
SOURCES := $(wildcard $(SELF_DIR)/*.mn)
OUT_DIR := ../build/bootstrap

.PHONY: bootstrap verify clean

# Stage 1: Python bootstrap compiles self-hosted sources → native binary
bootstrap:
	@echo "=== Stage 1: Bootstrap compiler (Python) → self-hosted binary ==="
	@mkdir -p $(OUT_DIR)
	$(PYTHON) -m mapanare build-multi $(SOURCES) -o $(OUT_DIR)/mapanare-s1
	@echo "Stage 1 binary: $(OUT_DIR)/mapanare-s1"

# Three-stage bootstrap verification
# Stage 1: Python → Binary A
# Stage 2: Binary A → Binary B
# Stage 3: Binary B → Binary C
# Verify: Binary B == Binary C (byte-identical)
verify: bootstrap
	@echo ""
	@echo "=== Stage 2: Binary A compiles self-hosted → Binary B ==="
	$(OUT_DIR)/mapanare-s1 build-multi $(SOURCES) -o $(OUT_DIR)/mapanare-s2
	@echo ""
	@echo "=== Stage 3: Binary B compiles self-hosted → Binary C ==="
	$(OUT_DIR)/mapanare-s2 build-multi $(SOURCES) -o $(OUT_DIR)/mapanare-s3
	@echo ""
	@echo "=== Verifying fixed point: Binary B == Binary C ==="
	@if cmp -s $(OUT_DIR)/mapanare-s2 $(OUT_DIR)/mapanare-s3; then \
		echo "PASS: Three-stage bootstrap verified (Stage 2 == Stage 3)"; \
	else \
		echo "FAIL: Stage 2 and Stage 3 binaries differ"; \
		exit 1; \
	fi

clean:
	rm -rf $(OUT_DIR)
