import subprocess

import pytest

from .run import main as run_main


def test_run_invokes_cabal_run_interpreter(monkeypatch, tmp_path):
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(subprocess, 'run', fake_run)
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit:
        pass
    assert calls[0] == ['cabal', 'run', 'interpreter']


def test_run_exits_with_process_return_code(monkeypatch, tmp_path):
    class FakeResult:
        returncode = 42
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: FakeResult())
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 42


def test_run_exits_130_on_keyboard_interrupt(monkeypatch, tmp_path):
    def raise_ki(*a, **kw):
        raise KeyboardInterrupt()
    monkeypatch.setattr(subprocess, 'run', raise_ki)
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt should be converted to sys.exit(130)")
    assert exit_code == 130
