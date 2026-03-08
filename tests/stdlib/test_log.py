"""Tests for mapanare.log -- structured logging with agent context."""

from __future__ import annotations

import io
import json

from stdlib.log import Logger, LogLevel, LogRecord

# ---------------------------------------------------------------------------
# LogRecord tests
# ---------------------------------------------------------------------------


class TestLogRecord:
    def test_record_fields(self) -> None:
        record = LogRecord(LogLevel.INFO, "hello")
        assert record.level == LogLevel.INFO
        assert record.message == "hello"
        assert record.timestamp > 0

    def test_record_with_agent(self) -> None:
        record = LogRecord(
            LogLevel.DEBUG,
            "msg",
            agent_id="abc123",
            agent_name="MyAgent",
        )
        assert record.agent_id == "abc123"
        assert record.agent_name == "MyAgent"

    def test_record_to_dict(self) -> None:
        record = LogRecord(LogLevel.WARN, "warning", agent_name="Agent1")
        d = record.to_dict()
        assert d["level"] == "WARN"
        assert d["message"] == "warning"
        assert d["agent_name"] == "Agent1"
        assert "timestamp" in d

    def test_record_to_dict_with_fields(self) -> None:
        record = LogRecord(LogLevel.INFO, "msg", fields={"port": 8080})
        d = record.to_dict()
        assert d["port"] == 8080

    def test_record_to_json(self) -> None:
        record = LogRecord(LogLevel.ERROR, "fail")
        j = record.to_json()
        parsed = json.loads(j)
        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "fail"

    def test_record_to_text(self) -> None:
        record = LogRecord(LogLevel.INFO, "started", agent_name="Server")
        text = record.to_text()
        assert "[INFO]" in text
        assert "[Server]" in text
        assert "started" in text

    def test_record_to_text_with_fields(self) -> None:
        record = LogRecord(LogLevel.INFO, "req", fields={"method": "GET"})
        text = record.to_text()
        assert "method=GET" in text


# ---------------------------------------------------------------------------
# Logger tests
# ---------------------------------------------------------------------------


class TestLogger:
    def test_logger_info(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out)
        log.info("hello")
        output = out.getvalue()
        assert "[INFO]" in output
        assert "hello" in output

    def test_logger_level_filter(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out, level=LogLevel.WARN)
        log.debug("should not appear")
        log.info("should not appear")
        log.warn("visible")
        output = out.getvalue()
        assert "should not appear" not in output
        assert "visible" in output

    def test_logger_all_levels(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out, level=LogLevel.TRACE)
        log.trace("t")
        log.debug("d")
        log.info("i")
        log.warn("w")
        log.error("e")
        log.fatal("f")
        assert len(log.records) == 6

    def test_logger_json_format(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out, json_format=True)
        log.info("structured", port=8080)
        line = out.getvalue().strip()
        parsed = json.loads(line)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "structured"
        assert parsed["port"] == 8080

    def test_logger_agent_context(self) -> None:
        out = io.StringIO()
        log = Logger("MyAgent", agent_id="abc123", output=out)
        log.info("started")
        text = out.getvalue()
        assert "[MyAgent]" in text

    def test_logger_records(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out)
        log.info("one")
        log.warn("two")
        records = log.records
        assert len(records) == 2
        assert records[0].message == "one"
        assert records[1].message == "two"

    def test_logger_extra_fields(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out, json_format=True)
        log.info("request", method="GET", path="/api")
        parsed = json.loads(out.getvalue().strip())
        assert parsed["method"] == "GET"
        assert parsed["path"] == "/api"

    def test_logger_child(self) -> None:
        out = io.StringIO()
        parent = Logger("app", output=out)
        child = parent.child("http")
        child.info("listening")
        text = out.getvalue()
        assert "[app.http]" in text

    def test_logger_name_and_level(self) -> None:
        log = Logger("mylog", level=LogLevel.DEBUG)
        assert log.name == "mylog"
        assert log.level == LogLevel.DEBUG

    def test_logger_set_level(self) -> None:
        out = io.StringIO()
        log = Logger("test", output=out, level=LogLevel.ERROR)
        log.info("hidden")
        assert out.getvalue() == ""
        log.level = LogLevel.INFO
        log.info("visible")
        assert "visible" in out.getvalue()


# ---------------------------------------------------------------------------
# LogLevel ordering
# ---------------------------------------------------------------------------


class TestLogLevel:
    def test_ordering(self) -> None:
        assert LogLevel.TRACE < LogLevel.DEBUG
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARN
        assert LogLevel.WARN < LogLevel.ERROR
        assert LogLevel.ERROR < LogLevel.FATAL

    def test_names(self) -> None:
        assert LogLevel.TRACE.name == "TRACE"
        assert LogLevel.FATAL.name == "FATAL"
