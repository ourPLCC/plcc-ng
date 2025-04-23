import sys

import docopt
import pytest

from .cli import cli, main


def test_no_args_displays_usage(monkeypatch):
    with pytest.raises(docopt.DocoptExit, match='Usage:'):
        run(monkeypatch, 'plccng')


def test_h_displays_usage(capsys, monkeypatch):
    with pytest.raises(SystemExit):
        run(monkeypatch, 'plccng -h')
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_help_displays_usage(capsys, monkeypatch):
    with pytest.raises(SystemExit):
        run(monkeypatch, 'plccng --help')
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_unrecognized_command_displays_usage(capsys, monkeypatch):
    run(monkeypatch, 'plccng UNRECOGNIZED_COMMAND')
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_spec(capsys, monkeypatch):
    with pytest.raises(docopt.DocoptExit, match=r'plccng spec'):
        run(monkeypatch, 'plccng spec')
    out, err = capsys.readouterr()


def run(monkeypatch, commandLine):
    setCommandLine(monkeypatch, commandLine)
    main()


def setCommandLine(monkeypatch, commandLine):
    monkeypatch.setattr(sys, 'argv', commandLine.split())
