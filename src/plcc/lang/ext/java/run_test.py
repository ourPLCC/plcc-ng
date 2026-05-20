import subprocess
from pathlib import Path

import pytest

from .run import main as run_main


def test_keyboard_interrupt_in_subprocess_exits_130(monkeypatch, tmp_path):
    (tmp_path / "runtime").mkdir()
    (tmp_path / "runtime" / "org.json-1.0.jar").touch()

    def raise_ki(*a, **kw):
        raise KeyboardInterrupt()
    monkeypatch.setattr(subprocess, "run", raise_ki)
    exit_code = None
    try:
        run_main([f"--output={tmp_path}"])
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt escaped — should be converted to sys.exit(130)")
    assert exit_code == 130
