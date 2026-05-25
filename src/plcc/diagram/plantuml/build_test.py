import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_missing_plantuml_lib_prints_helpful_error(tmp_path, capsys):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"

    with patch.dict('sys.modules', {'plantuml': None}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'pip install plcc-ng[diagram]' in err


def test_calls_plantuml_server_and_writes_png(tmp_path):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\nclass Foo {}\n@enduml\n")
    out = tmp_path / "diagram.png"
    fake_png = b'\x89PNG fake'

    mock_lib = MagicMock()
    mock_server = MagicMock()
    mock_server.processes.return_value = fake_png
    mock_lib.PlantUML.return_value = mock_server

    with patch.dict('sys.modules', {'plantuml': mock_lib}):
        run_main([f'--input={src}', f'--output={out}'])

    assert out.read_bytes() == fake_png
    mock_lib.PlantUML.assert_called_once_with(
        url='https://www.plantuml.com/plantuml/png/',
        request_opts={'timeout': 30},
    )
    mock_server.processes.assert_called_once_with("@startuml\nclass Foo {}\n@enduml\n")


def test_missing_input_file_exits_with_error(tmp_path, capsys):
    src = tmp_path / "nonexistent.puml"
    out = tmp_path / "diagram.png"

    mock_lib = MagicMock()
    mock_lib.PlantUML.return_value = MagicMock()

    with patch.dict('sys.modules', {'plantuml': mock_lib}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert err.strip() != ''


def test_plantuml_error_prints_message_and_exits(tmp_path, capsys):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"

    mock_lib = MagicMock()
    mock_server = MagicMock()
    mock_server.processes.side_effect = Exception("connection refused")
    mock_lib.PlantUML.return_value = mock_server

    with patch.dict('sys.modules', {'plantuml': mock_lib}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'connection refused' in err


