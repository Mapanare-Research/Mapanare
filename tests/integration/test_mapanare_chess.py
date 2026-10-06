"""Execute Cascabel on both compiler paths; exercise chess rules and state isolation.

Perft fixtures are the standard positions also used by Stockfish's tests/perft.sh.
https://www.chessprogramming.org/Perft_Results
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "examples" / "mapanare-chess" / "main.mn"


@pytest.fixture(scope="module", params=["bootstrap", "self-hosted"])
def chess_engine(request, tmp_path_factory):
    clang = shutil.which("clang") or shutil.which("clang-18")
    if not clang:
        # Cascabel v0.1.0: native execution requires an installed LLVM toolchain.
        pytest.skip("clang is required for native chess tests")
    destination = tmp_path_factory.mktemp(f"chess-{request.param}")
    ir = destination / "cascabel.ll"
    binary = destination / ("cascabel.exe" if os.name == "nt" else "cascabel")
    if request.param == "bootstrap":
        command = [sys.executable, "-m", "mapanare", "emit-llvm"]
    else:
        compiler = (
            ROOT / "mapanare" / "self" / ("mnc-stage1.exe" if os.name == "nt" else "mnc-stage1")
        )
        if not compiler.exists():
            # Cascabel v0.1.0: CI builds stage1 before pytest; bare clones may not.
            pytest.skip("build mnc-stage1 to exercise the self-hosted compiler")
        command = [str(compiler), "emit-llvm"]
    compile_result = subprocess.run(
        [*command, str(SOURCE), "-o", str(ir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    linked = subprocess.run(
        [
            clang,
            "-O2",
            str(ir),
            str(ROOT / "runtime" / "native" / "mapanare_core.c"),
            "-o",
            str(binary),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert linked.returncode == 0, linked.stderr
    return binary


def session(binary, commands):
    result = subprocess.run(
        [str(binary)],
        input="\n".join([*commands, "quit", ""]),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert not result.stderr, result.stderr
    return result.stdout.splitlines()[1:]


def test_start_position_and_repeated_search_are_pure(chess_engine):
    assert (
        session(chess_engine, ["perft 0", "perft 1", "perft 2", "perft 3", "perft 4"] * 2)
        == [
            "nodes 1",
            "nodes 20",
            "nodes 400",
            "nodes 8902",
            "nodes 197281",
        ]
        * 2
    )


@pytest.mark.parametrize(
    "fen,depth,nodes",
    [
        ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238),
        ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 3, 9467),
        ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 3, 62379),
        ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3, 89890),
    ],
)
def test_standard_perft_positions(chess_engine, fen, depth, nodes):
    assert session(chess_engine, [f"fen {fen}", f"perft {depth}"]) == ["ok", f"nodes {nodes}"]


def test_en_passant_and_pin(chess_engine):
    allowed = session(chess_engine, ["fen k7/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "moves"])
    pinned = session(chess_engine, ["fen k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "moves"])
    assert "e5d6" in allowed[1].split()
    assert "e5d6" not in pinned[1].split()


def test_all_four_promotions(chess_engine):
    lines = session(chess_engine, ["fen 7k/P7/8/8/8/8/8/4K3 w - - 0 1", "moves", "play a7a8n", "d"])
    assert {"a7a8n", "a7a8b", "a7a8r", "a7a8q"} <= set(lines[1].split())
    assert lines[2] == "ok"
    assert lines[3].startswith("8 N ")


def test_castling_cannot_cross_attacked_square(chess_engine):
    lines = session(chess_engine, ["fen k4r2/8/8/8/8/8/8/R3K2R w KQ - 0 1", "moves"])
    assert "e1g1" not in lines[1].split()
    assert "e1c1" in lines[1].split()


def test_play_search_and_reset(chess_engine):
    lines = session(chess_engine, ["play e2e4", "moves", "go 2", "startpos", "perft 2"])
    legal = set(lines[1].split()[1:])
    assert lines[0] == "ok"
    assert lines[2].startswith("bestmove ")
    assert lines[2].split()[1] in legal
    assert lines[-2:] == ["ok", "nodes 400"]


@pytest.mark.parametrize(
    "fen", ["7k/6Q1/5K2/8/8/8/8/8 b - - 0 1", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"]
)
def test_checkmate_and_stalemate(chess_engine, fen):
    assert session(chess_engine, [f"fen {fen}", "perft 1", "go 2"]) == [
        "ok",
        "nodes 0",
        "bestmove 0000",
    ]


@pytest.mark.parametrize(
    "command",
    [
        "fen 8/8/8/8/8/8/8/8 w - - 0 1",
        "fen 7k/8/8/8/8/8/8/4K3 x - - 0 1",
        "fen 7k/8/8/8/8/8/8/4K3 w KK - 0 1",
        "fen 7k/8/8/8/8/8/8/4K3 w - d6 0 1",
        "fen 9/8/8/8/8/8/8/4K2k w - - 0 1",
        "fen 7k/8/8/8/8/8/8/4K3 w - - nope 1",
        "play e2e5",
        "play a1a8",
        "go 0",
        "go 9999999999999999999999",
        "perft -1",
        "perft 5",
        "unknown",
    ],
)
def test_invalid_commands_preserve_position(chess_engine, command):
    lines = session(chess_engine, [command, "perft 1"])
    assert lines[0].startswith("error ")
    assert lines[1] == "nodes 20"


def test_eof_exits_cleanly(chess_engine):
    result = subprocess.run(
        [str(chess_engine)], input="", capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
