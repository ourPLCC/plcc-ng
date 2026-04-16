import io

import pytest

from .emit import main as run_main


def test_no_args_prints_usage():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_copies_main_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'Main.java').exists()


def test_verbose_flag_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(''))
    run_main([f'--output={tmp_path}', '--verbose=1'])
