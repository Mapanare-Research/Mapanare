"""mapanare.log -- structured logging with agent context."""

from __future__ import annotations

import enum
import json
import sys
import time
from typing import Any, TextIO

# ---------------------------------------------------------------------------
# Log levels
# ---------------------------------------------------------------------------


class LogLevel(enum.IntEnum):
    """Severity levels for log messages."""

    TRACE = 0
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    FATAL = 50


# ---------------------------------------------------------------------------
# Log record
# ---------------------------------------------------------------------------


class LogRecord:
    """A single structured log entry."""

    __slots__ = ("level", "message", "timestamp", "agent_id", "agent_name", "fields")

    def __init__(
        self,
        level: LogLevel,
        message: str,
        *,
        agent_id: str = "",
        agent_name: str = "",
        fields: dict[str, Any] | None = None,
    ) -> None:
        self.level = level
        self.message = message
        self.timestamp = time.time()
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.fields = fields or {}

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "level": self.level.name,
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.agent_id:
            d["agent_id"] = self.agent_id
        if self.agent_name:
            d["agent_name"] = self.agent_name
        if self.fields:
            d.update(self.fields)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_text(self) -> str:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        parts = [f"[{ts}]", f"[{self.level.name}]"]
        if self.agent_name:
            parts.append(f"[{self.agent_name}]")
        elif self.agent_id:
            parts.append(f"[{self.agent_id}]")
        parts.append(self.message)
        if self.fields:
            kv = " ".join(f"{k}={v}" for k, v in self.fields.items())
            parts.append(kv)
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


class Logger:
    """Structured logger with optional agent context.

    Usage::

        log = Logger("MyAgent", agent_id="abc123")
        log.info("started", port=8080)
        log.error("failed", reason="timeout")
    """

    def __init__(
        self,
        name: str = "",
        *,
        agent_id: str = "",
        level: LogLevel = LogLevel.INFO,
        output: TextIO | None = None,
        json_format: bool = False,
    ) -> None:
        self._name = name
        self._agent_id = agent_id
        self._level = level
        self._output = output or sys.stderr
        self._json_format = json_format
        self._records: list[LogRecord] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def level(self) -> LogLevel:
        return self._level

    @level.setter
    def level(self, value: LogLevel) -> None:
        self._level = value

    @property
    def records(self) -> list[LogRecord]:
        """Return all recorded log entries."""
        return list(self._records)

    def _emit(self, level: LogLevel, message: str, **fields: Any) -> None:
        if level < self._level:
            return
        record = LogRecord(
            level=level,
            message=message,
            agent_id=self._agent_id,
            agent_name=self._name,
            fields=fields if fields else None,
        )
        self._records.append(record)
        line = record.to_json() if self._json_format else record.to_text()
        self._output.write(line + "\n")
        self._output.flush()

    def trace(self, message: str, **fields: Any) -> None:
        self._emit(LogLevel.TRACE, message, **fields)

    def debug(self, message: str, **fields: Any) -> None:
        self._emit(LogLevel.DEBUG, message, **fields)

    def info(self, message: str, **fields: Any) -> None:
        self._emit(LogLevel.INFO, message, **fields)

    def warn(self, message: str, **fields: Any) -> None:
        self._emit(LogLevel.WARN, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._emit(LogLevel.ERROR, message, **fields)

    def fatal(self, message: str, **fields: Any) -> None:
        self._emit(LogLevel.FATAL, message, **fields)

    def child(self, name: str, **extra_fields: Any) -> Logger:
        """Create a child logger with additional context."""
        child_name = f"{self._name}.{name}" if self._name else name
        child_logger = Logger(
            child_name,
            agent_id=self._agent_id,
            level=self._level,
            output=self._output,
            json_format=self._json_format,
        )
        return child_logger


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_logger = Logger("mapanare")


def set_level(level: LogLevel) -> None:
    """Set the default logger's level."""
    _default_logger.level = level


def trace(message: str, **fields: Any) -> None:
    _default_logger.trace(message, **fields)


def debug(message: str, **fields: Any) -> None:
    _default_logger.debug(message, **fields)


def info(message: str, **fields: Any) -> None:
    _default_logger.info(message, **fields)


def warn(message: str, **fields: Any) -> None:
    _default_logger.warn(message, **fields)


def error(message: str, **fields: Any) -> None:
    _default_logger.error(message, **fields)


def fatal(message: str, **fields: Any) -> None:
    _default_logger.fatal(message, **fields)
