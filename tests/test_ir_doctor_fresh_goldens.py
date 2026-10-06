"""Golden validation must compile current sources instead of reading cached IR."""

from __future__ import annotations

import argparse
import subprocess

from scripts import ir_doctor

FRESH_IR = "define i64 @main() {\nentry:\n  ret i64 0\n}\n"


def test_golden_ignores_stale_stage1_ir(tmp_path, monkeypatch):
    source = tmp_path / "01_hello.mn"
    source.write_text('fn main():\n    print("hello")\n')
    source.with_suffix(".stage1.ll").write_text("stale, invalid cached IR")
    compiler = tmp_path / "mnc-stage1"
    compiler.touch()
    calls = []

    def compile_current(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=FRESH_IR, stderr="")

    monkeypatch.setattr(ir_doctor.subprocess, "run", compile_current)
    monkeypatch.setattr(ir_doctor, "GOLDEN_DIR", tmp_path)
    monkeypatch.setattr(ir_doctor, "BASELINE_DIR", tmp_path / "baseline")
    monkeypatch.setattr(ir_doctor, "JOURNAL_FILE", tmp_path / "journal.jsonl")
    monkeypatch.setattr(ir_doctor, "validate_ir", lambda ir: (ir == FRESH_IR, ""))
    assert ir_doctor.cmd_golden(argparse.Namespace(stage1=str(compiler))) == 0
    assert calls == [[str(compiler), "emit-llvm", str(source)]]


def test_offline_comparison_can_still_use_cached_ir(tmp_path, monkeypatch):
    source = tmp_path / "demo.mn"
    source.with_suffix(".stage1.ll").write_text(FRESH_IR)

    def unexpected_compile(*args, **kwargs):
        raise AssertionError("offline comparison should use the cached artifact")

    monkeypatch.setattr(ir_doctor.subprocess, "run", unexpected_compile)
    assert ir_doctor.stage1_compile(source, "unavailable-compiler") == FRESH_IR
