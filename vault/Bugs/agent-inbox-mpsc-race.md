---
severity: high
found: "[[v4.26.0]]"
fixed: "[[v4.28.0]]"
status: fixed
tags: [bug, high, concurrency, agents, ring-buffer]
---

# Agent Inbox MPSC Race

The agent inbox used an SPSC (single-producer, single-consumer) lock-free ring buffer, but multiple agents could send messages to the same target agent concurrently, creating a de facto MPSC pattern. Without a producer-side lock, concurrent `send()` calls could corrupt the write index and overwrite in-flight messages.

## Root Cause
The ring buffer in `runtime/native/` was designed for SPSC use (one sender, one receiver). The agent runtime allowed any agent to send to any other agent, meaning multiple producers could race on the same ring buffer's write pointer. The SPSC algorithm's single-producer invariant was silently violated.

## Fix
Added a lightweight spinlock on the producer side of agent inboxes, converting the ring buffer to safe MPSC operation. The consumer side remains lock-free. Benchmarked the overhead at <2% for typical agent message rates. Fixed in v4.28.0.
