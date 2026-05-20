import subprocess
import shutil

import pytest

from .run import main as run_main


def test_keyboard_interrupt_in_subprocess_exits_130(monkeypatch):
    def raise_ki(*a, **kw):
        raise KeyboardInterrupt()
    monkeypatch.setattr(subprocess, "run", raise_ki)
    monkeypatch.setattr(shutil, "which", lambda cmd: f"/usr/bin/{cmd}")
    exit_code = None
    try:
        run_main(["--target=Java", "--output=build/java"])
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt escaped — should be converted to sys.exit(130)")
    assert exit_code == 130
