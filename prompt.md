We are building Mapanare — an open-source AI-native compiled programming language.
Repo: github.com/Mapanare-Research/mapanare

DO NOT USE THE GSD PLUGIN OR ANY TASK MANAGEMENT PLUGIN.

---

Start Phase [X.X]

Read ROADMAP.md.
Complete every task in that section top to bottom.
Write tests for each task before moving to the next one.
When all tasks are done run: make test && mypy mapa/ runtime/ && black . && ruff check .
Tell me what was completed and flag anything that was skipped and why.

---

## Status Tracking

ROADMAP.md is the single source of truth for progress.
Every task table has a **Status** column. Update it as you work:

| Icon | Meaning |
|------|---------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Skipped (add reason in Notes) |

When a sub-phase is fully complete, update its parent phase in the Phase Overview table:
- `🔲 Not Started` — no tasks done
- `🔶 In Progress` — some tasks done
- `✅ Complete` — all tasks done

Always update ROADMAP.md status **after** completing each task, not in bulk at the end.
