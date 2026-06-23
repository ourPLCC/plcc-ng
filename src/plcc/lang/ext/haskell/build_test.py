import subprocess

import pytest

from .build import main as build_main


def test_build_invokes_cabal_build(monkeypatch, tmp_path):
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(subprocess, 'run', fake_run)
    try:
        build_main([f'--output={tmp_path}'])
    except SystemExit:
        pass
    assert calls[0] == ['cabal', 'build']


def test_build_exits_with_cabal_return_code(monkeypatch, tmp_path):
    class FakeResult:
        returncode = 2
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: FakeResult())
    exit_code = None
    try:
        build_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 2


def test_build_uses_output_dir_as_cwd(monkeypatch, tmp_path):
    cwds = []
    def fake_run(cmd, cwd=None, **kwargs):
        cwds.append(cwd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(subprocess, 'run', fake_run)
    try:
        build_main([f'--output={tmp_path}'])
    except SystemExit:
        pass
    assert cwds[0] == str(tmp_path)
