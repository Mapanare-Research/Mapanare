"""Tests for mapanare.io -- file and stdin/stdout agents."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from stdlib.io import (
    FileReaderAgent,
    FileWriterAgent,
    StdoutAgent,
    read_file,
    write_file,
)

# ---------------------------------------------------------------------------
# Convenience function tests
# ---------------------------------------------------------------------------


class TestReadFile:
    async def test_read_file(self, tmp_path: Path) -> None:
        f = tmp_path / "hello.txt"
        f.write_text("Hello, Mapanare!", encoding="utf-8")
        content = await read_file(str(f))
        assert content == "Hello, Mapanare!"

    async def test_read_file_utf8(self, tmp_path: Path) -> None:
        f = tmp_path / "unicode.txt"
        f.write_text("café ñ 日本語", encoding="utf-8")
        content = await read_file(str(f))
        assert "café" in content

    async def test_read_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            await read_file(str(tmp_path / "nope.txt"))


class TestWriteFile:
    async def test_write_file_new(self, tmp_path: Path) -> None:
        f = tmp_path / "out.txt"
        await write_file(str(f), "written")
        assert f.read_text() == "written"

    async def test_write_file_overwrite(self, tmp_path: Path) -> None:
        f = tmp_path / "out.txt"
        f.write_text("old")
        await write_file(str(f), "new")
        assert f.read_text() == "new"

    async def test_write_file_append(self, tmp_path: Path) -> None:
        f = tmp_path / "out.txt"
        f.write_text("a")
        await write_file(str(f), "b", append=True)
        assert f.read_text() == "ab"

    async def test_write_file_creates_dirs(self, tmp_path: Path) -> None:
        f = tmp_path / "sub" / "dir" / "file.txt"
        await write_file(str(f), "deep")
        assert f.read_text() == "deep"


# ---------------------------------------------------------------------------
# FileReaderAgent tests
# ---------------------------------------------------------------------------


class TestFileReaderAgent:
    async def test_read_full_content(self, tmp_path: Path) -> None:
        f = tmp_path / "data.txt"
        f.write_text("line1\nline2\nline3")

        handle = await FileReaderAgent.spawn()
        await handle._agent._inputs["inp"].send(str(f))
        await asyncio.sleep(0.15)

        out_ch = handle._agent._outputs["out"]
        content = await asyncio.wait_for(out_ch.receive(), timeout=1.0)
        assert content == "line1\nline2\nline3"
        await handle.stop()

    async def test_read_line_mode(self, tmp_path: Path) -> None:
        f = tmp_path / "lines.txt"
        f.write_text("alpha\nbeta\ngamma")

        handle = await FileReaderAgent.spawn(line_mode=True)
        await handle._agent._inputs["inp"].send(str(f))
        await asyncio.sleep(0.15)

        out_ch = handle._agent._outputs["out"]
        lines = []
        for _ in range(3):
            line = await asyncio.wait_for(out_ch.receive(), timeout=1.0)
            lines.append(line)
        assert lines == ["alpha", "beta", "gamma"]
        await handle.stop()


# ---------------------------------------------------------------------------
# FileWriterAgent tests
# ---------------------------------------------------------------------------


class TestFileWriterAgent:
    async def test_write_fixed_path(self, tmp_path: Path) -> None:
        f = tmp_path / "fixed.txt"
        handle = await FileWriterAgent.spawn(path=str(f), append=False)
        await handle._agent._inputs["inp"].send("hello")
        await asyncio.sleep(0.15)
        await handle.stop()
        assert f.read_text() == "hello"

    async def test_write_tuple_input(self, tmp_path: Path) -> None:
        f = tmp_path / "tuple.txt"
        handle = await FileWriterAgent.spawn()
        await handle._agent._inputs["inp"].send((str(f), "tuple-content"))
        await asyncio.sleep(0.15)
        await handle.stop()
        assert f.read_text() == "tuple-content"

    async def test_write_append_mode(self, tmp_path: Path) -> None:
        f = tmp_path / "append.txt"
        f.write_text("start")
        handle = await FileWriterAgent.spawn(path=str(f), append=True)
        await handle._agent._inputs["inp"].send("-end")
        await asyncio.sleep(0.15)
        await handle.stop()
        assert f.read_text() == "start-end"


# ---------------------------------------------------------------------------
# StdoutAgent tests
# ---------------------------------------------------------------------------


class TestStdoutAgent:
    async def test_stdout_agent_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        handle = await StdoutAgent.spawn()
        await handle._agent._inputs["inp"].send("hello stdout")
        await asyncio.sleep(0.15)
        await handle.stop()
        captured = capsys.readouterr()
        assert "hello stdout" in captured.out
