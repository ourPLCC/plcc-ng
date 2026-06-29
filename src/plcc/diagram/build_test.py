import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_diagram_plantuml_build(tmp_path):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-plantuml-build'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={src}', f'--output={out}'])

    assert calls[0][0] == 'plcc-diagram-plantuml-build'
    assert f'--input={src}' in calls[0]
    assert f'--output={out}' in calls[0]


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
