import subprocess

import pytest

from .run import main as run_main


def test_keyboard_interrupt_exits_130(monkeypatch, tmp_path):
    def raise_ki(*a, **kw):
        raise KeyboardInterrupt()
    monkeypatch.setattr(subprocess, 'run', raise_ki)
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt escaped — should be converted to sys.exit(130)")
    assert exit_code == 130


def test_run_exits_with_node_return_code(monkeypatch, tmp_path):
    class FakeResult:
        returncode = 42
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: FakeResult())
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 42
