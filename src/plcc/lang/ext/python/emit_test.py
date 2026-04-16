import os
import pytest

from .emit import main as run_main


def test_no_args_prints_usage():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_copies_main_py(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'main.py').exists()


def test_verbose_flag_accepted(tmp_path, monkeypatch):
    import io
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    # Should not raise
    run_main([f'--output={tmp_path}', '--verbose=1'])


def test_main_py_is_runnable(tmp_path, monkeypatch):
    import io
    import subprocess
    import sys
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    run_main([f'--output={tmp_path}'])
    main_py = tmp_path / 'main.py'
    result = subprocess.run(
        [sys.executable, str(main_py)],
        input='',
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
