import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_missing_mmdc_prints_helpful_error(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch.dict('sys.modules', {'mmdc': None}):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'pip install plcc[diagram]' in err


def test_calls_mmdc_converter(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Foo {}\n")
    out = tmp_path / "diagram.png"

    mock_converter = MagicMock()
    mock_converter.to_png.return_value = b'\x89PNG\r\n'
    mock_mmdc = MagicMock()
    mock_mmdc.MermaidConverter.return_value = mock_converter

    with patch.dict('sys.modules', {'mmdc': mock_mmdc}):
        run_main([f'--input={src}', f'--output={out}'])

    mock_converter.to_png.assert_called_once_with("classDiagram\n    class Foo {}\n")
    assert out.read_bytes() == b'\x89PNG\r\n'
