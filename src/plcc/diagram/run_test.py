import pytest
from unittest.mock import patch, MagicMock

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_mermaid_diagram_run(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-mermaid-diagram-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}'])

    assert calls[0][0] == 'plcc-mermaid-diagram-run'
    assert f'--input={img}' in calls[0]


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={img}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
