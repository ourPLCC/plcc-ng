import io
import json
import pytest
from unittest.mock import patch, MagicMock

from .dispatch import main as run_main


_TRIVIAL_MODEL = json.dumps({
    "start": "program",
    "classes": [
        {"name": "Program", "abstract": False, "extends": None,
         "fields": [{"name": "num", "type": "Token"}]}
    ],
    "semantic_sections": []
})


def test_missing_output_arg_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_plantuml_diagram(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--output={tmp_path}'])

    assert calls[0][0] == 'plcc-plantuml-diagram'
    assert f'--output={tmp_path}' in calls[0]


def test_default_format_is_plantuml(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--output={tmp_path}'])

    assert 'plcc-plantuml-diagram' in calls[0][0]


def test_custom_format_dispatches_to_correct_command(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-mermaid-diagram'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--output={tmp_path}', '--format=mermaid'])

    assert calls[0][0] == 'plcc-mermaid-diagram'


def test_missing_plugin_exits_nonzero(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--output={tmp_path}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
