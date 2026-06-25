import io
import json
import pytest
from unittest.mock import patch, MagicMock

from .emit import main as run_main

_TRIVIAL_MODEL = json.dumps({
    "start": "program",
    "classes": [{"name": "Program", "abstract": False, "extends": None,
                 "fields": [{"name": "num", "type": "Token"}]}],
    "semantic_sections": []
})


def test_dispatches_to_class_plantuml_emit_by_default(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-class-plantuml-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main(['--type=class'])

    assert calls[0][0] == 'plcc-diagram-class-plantuml-emit'


def test_explicit_type_and_format(monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-class-plantuml-emit'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main(['--type=class', '--format=plantuml'])

    assert calls[0][0] == 'plcc-diagram-class-plantuml-emit'


def test_missing_type_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    import docopt as _docopt
    with pytest.raises((SystemExit, _docopt.DocoptExit)):
        run_main([])


def test_missing_plugin_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main(['--type=class', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
