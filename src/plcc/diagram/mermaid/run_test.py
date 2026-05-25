import pytest
from unittest.mock import patch

from .run import main as run_main, _open_file


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_open_file_calls_open_on_macos(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    with patch('platform.system', return_value='Darwin'):
        with patch('subprocess.run', side_effect=lambda cmd, **kw: calls.append(cmd)):
            _open_file(str(img))

    assert calls[0] == ['open', str(img)]


def test_open_file_calls_xdg_open_on_linux(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    calls = []

    with patch('platform.system', return_value='Linux'):
        with patch('subprocess.run', side_effect=lambda cmd, **kw: calls.append(cmd)):
            _open_file(str(img))

    assert calls[0] == ['xdg-open', str(img)]


def test_open_file_calls_startfile_on_windows(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('platform.system', return_value='Windows'):
        with patch('plcc.diagram.mermaid.run.os.startfile', create=True) as mock_startfile:
            _open_file(str(img))

    mock_startfile.assert_called_once_with(str(img))


def test_main_calls_open_file(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('plcc.diagram.mermaid.run._open_file') as mock_open:
        run_main([f'--input={img}'])

    mock_open.assert_called_once_with(str(img))


def test_viewer_not_found_prints_error_and_exits(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")

    with patch('plcc.diagram.mermaid.run._open_file',
               side_effect=FileNotFoundError(2, 'No such file or directory', 'xdg-open')):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={img}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'xdg-open' in err
