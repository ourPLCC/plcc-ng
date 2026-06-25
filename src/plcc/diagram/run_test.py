import pytest
from unittest.mock import patch, MagicMock

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_diagram_plantuml_run(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-plantuml-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}'])

    assert calls[0][0] == 'plcc-diagram-plantuml-run'
    assert f'--input={img}' in calls[0]


def test_custom_format_dispatches_correctly(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-mermaid-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}', '--format=mermaid'])

    assert calls[0][0] == 'plcc-diagram-mermaid-run'


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={img}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
