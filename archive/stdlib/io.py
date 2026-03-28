"""mapanare.io -- file and stdin/stdout agents."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from runtime.agent import AgentBase

# ---------------------------------------------------------------------------
# Stdin agent -- reads lines from stdin and sends them downstream
# ---------------------------------------------------------------------------


class StdinAgent(AgentBase):
    """Agent that reads lines from stdin and sends them as messages.

    Each line (stripped of trailing newline) is sent to the output channel.
    Stops when EOF is reached.
    """

    def __init__(self, prompt: str = "") -> None:
        super().__init__()
        self._prompt = prompt
        self._register_output("out")

    async def _run(self) -> None:
        self._running = True
        from runtime.agent import AgentState

        self._state = AgentState.RUNNING
        await self.on_init()

        loop = asyncio.get_event_loop()
        output_names = list(self._outputs.keys())

        while self._running:
            try:
                await self._pause_event.wait()
                if not self._running:
                    break

                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break  # EOF
                stripped = line.rstrip("\n").rstrip("\r")
                if output_names:
                    await self._outputs[output_names[0]].send(stripped)
            except asyncio.CancelledError:
                break

        from runtime.agent import AgentState

        if self._state != AgentState.FAILED:
            self._state = AgentState.STOPPED
        await self.on_stop()


# ---------------------------------------------------------------------------
# Stdout agent -- receives messages and prints them to stdout
# ---------------------------------------------------------------------------


class StdoutAgent(AgentBase):
    """Agent that receives messages and prints them to stdout."""

    def __init__(self, end: str = "\n", flush: bool = True) -> None:
        super().__init__()
        self._end = end
        self._flush = flush
        self._register_input("inp")

    async def handle(self, value: Any) -> Any:
        print(value, end=self._end, flush=self._flush)
        return None


# ---------------------------------------------------------------------------
# File reader agent -- reads a file and sends lines or full content
# ---------------------------------------------------------------------------


class FileReaderAgent(AgentBase):
    """Agent that reads file paths from input and sends file contents to output.

    Receives a file path string, reads the file, and sends its content.
    If ``line_mode`` is True, sends each line separately; otherwise sends the
    full content as a single message.
    """

    def __init__(self, line_mode: bool = False, encoding: str = "utf-8") -> None:
        super().__init__()
        self._line_mode = line_mode
        self._encoding = encoding
        self._register_input("inp")
        self._register_output("out")

    async def handle(self, value: Any) -> Any:
        path = Path(str(value))
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(None, path.read_text, self._encoding)

        output_names = list(self._outputs.keys())
        if self._line_mode:
            for line in content.splitlines():
                if output_names:
                    await self._outputs[output_names[0]].send(line)
            return None
        else:
            return content


# ---------------------------------------------------------------------------
# File writer agent -- receives content and writes to a file
# ---------------------------------------------------------------------------


class FileWriterAgent(AgentBase):
    """Agent that writes received messages to a file.

    Receives ``(path, content)`` tuples or just content strings.
    If constructed with a fixed ``path``, all messages are appended there.
    """

    def __init__(
        self,
        path: str | Path | None = None,
        append: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        super().__init__()
        self._path = Path(path) if path is not None else None
        self._append = append
        self._encoding = encoding
        self._register_input("inp")

    async def handle(self, value: Any) -> Any:
        loop = asyncio.get_event_loop()

        if self._path is not None:
            target = self._path
            content = str(value)
        elif isinstance(value, (list, tuple)) and len(value) >= 2:
            target = Path(str(value[0]))
            content = str(value[1])
        else:
            raise ValueError(
                f"FileWriterAgent expects (path, content) tuple or fixed path, got {type(value)}"
            )

        mode = "a" if self._append else "w"

        def _write() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, mode, encoding=self._encoding) as f:
                f.write(content)

        await loop.run_in_executor(None, _write)
        return None


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


async def read_file(path: str | Path, encoding: str = "utf-8") -> str:
    """Read a file asynchronously and return its contents."""
    p = Path(path)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, p.read_text, encoding)


async def write_file(
    path: str | Path, content: str, append: bool = False, encoding: str = "utf-8"
) -> None:
    """Write content to a file asynchronously."""
    p = Path(path)

    def _write() -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding=encoding) as f:
            f.write(content)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _write)
