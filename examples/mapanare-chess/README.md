# Cascabel — Mapanare Chess

A small native chess engine written in Mapanare. The package name is
`mapanare-chess`; Cascabel is the engine name (Spanish for rattlesnake).

Version 0.1.0 is a terminal prototype: legal moves, FEN positions, perft,
and fixed-depth alpha–beta search. The engine lives in one source file so
it is easy to study and can become a separate repository later.

## Build and play

The verified development platform is Linux, including Ubuntu under WSL,
with Mapanare 5.54.0 and clang. From the Mapanare repository root:

```bash
mkdir -p build
./mapanare/self/mnc-stage1 build examples/mapanare-chess/main.mn -o build/cascabel
./build/cascabel
```

In PowerShell, from the same repository directory:

```powershell
wsl -d Ubuntu -- ./build/cascabel
```

If the self-hosted compiler has not been built, follow the repository's
build instructions first. A reproducible alternative, also used by the
integration tests, is:

```bash
mkdir -p build
python -m mapanare emit-llvm examples/mapanare-chess/main.mn -o build/cascabel.ll
clang -O2 build/cascabel.ll runtime/native/mapanare_core.c -o build/cascabel
```

Try this session:

```text
d
play e2e4
go 2
d
quit
```

`play` makes your move. `go` searches for and plays the engine's reply.
Promotion moves include a suffix, such as `a7a8q` or `a7a8n`.

| Command | Result |
|---|---|
| `help` | Show commands |
| `startpos` | Reset to the standard initial position |
| `fen <six FEN fields>` | Load a position; reject malformed input |
| `d` | Display the board |
| `moves` | List legal moves in coordinate notation |
| `play e2e4` | Play a legal move |
| `go 2` | Search two plies and play the best move; depth 1–4 |
| `perft 3` | Count legal move paths; depth 0–4 |
| `quit` | Exit; EOF or an empty line also exits |

Use single spaces between command/FEN fields. Illegal moves and malformed
commands leave the position unchanged. `bestmove 0000` means no legal move
exists. This is a custom terminal protocol, **not UCI**.

## Rules and search

- A 120-cell mailbox board, with explicit board copies between positions.
- Legal move filtering, check, castling rights and attacked-square checks.
- All four promotions and en passant, including discovered-check filtering.
- Negamax with alpha–beta pruning, material values and pawn-advance bonuses.
- Checkmate and stalemate detection, including at the search horizon.
- A search score of zero at the fifty-move threshold, after checking for mate.

No bitboards, neural networks, external chess library, or C chess logic is used.
The linked C code is Mapanare's existing language runtime.

## Tests

```bash
python -m pytest tests/integration/test_mapanare_chess.py -q
```

The tests compile and execute the engine through both the Python bootstrap
and the self-hosted compiler. They check repeated searches and position
isolation as well as chess rules. Standard perft fixtures are also used in
[Stockfish's perft suite](https://github.com/official-stockfish/Stockfish/blob/master/tests/perft.sh).

| Position | Depth | Nodes |
|---|---:|---:|
| Initial position | 4 | 197,281 |
| Kiwipete | 3 | 97,862 |
| Rook/pawn endgame | 4 | 43,238 |
| Castling/promotion position | 3 | 9,467 |
| Promotion/check position | 3 | 62,379 |
| Middlegame | 3 | 89,890 |

## Prototype limits

This is a starting point, not a tournament engine. There is no UCI adapter,
clock management, interruption during search, repetition history,
insufficient-material adjudication, quiescence search, transposition table,
or measured playing strength. FEN validation checks representation and
required kings, not whether a position is reachable in a legal game.

Runtime stress testing found retained allocations in the current compiler's
generated ownership/cleanup paths. Search depth is capped, but repeated
commands can still grow process memory; restart between long experiments.
The initial Linux sanitizer probe reported approximately 1.7 MB retained
after two depth-two perft runs and a short play/search/reset session. This
is an open compiler/runtime investigation, not a clean leak-check result.

The published Windows v5.54.0 native compiler rejected this program's LLVM
IR with PHI/predecessor errors. Use WSL for now. The source avoids chained
string method calls and `split()` results, and reads lines without `trim()`:
early probes exposed incorrect string-list indexing and aliased-string
cleanup on those paths. These are recorded rather than silently treated as
language-wide fixes.

Next milestones: bounded memory during long searches, native Windows
execution, complete draw handling, then interruptible UCI and timed search.
