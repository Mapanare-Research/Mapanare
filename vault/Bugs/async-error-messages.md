---
docket: 11
severity: low
found: "[[v4.99.0]]"
fixed: "[[v4.113.0]]"
status: open
tags: [bug, low, open, async, dx]
---

# Async Error Messages Cryptic

**Docket #11** from [[v4.99.0]] panel.

Error messages for common async failures are cryptic. Need user-friendly diagnostics for: await outside async fn, missing block_on, scheduler not initialized.

Flagged by [[Boa]].
