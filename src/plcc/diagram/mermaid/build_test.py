import subprocess
import pytest
from unittest.mock import patch

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_missing_mmdc_cli_prints_helpful_error(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'npm install -g @mermaid-js/mermaid-cli' in err


def test_calls_mmdc_with_correct_args(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Foo {}\n")
    out = tmp_path / "diagram.png"

    with patch('shutil.which', return_value='/usr/bin/mmdc'):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0)
            run_main([f'--input={src}', f'--output={out}'])

    mock_run.assert_called_once_with(
        ['mmdc', '-i', str(src), '-o', str(out)],
        stderr=subprocess.PIPE,
    )


def test_mmdc_nonzero_exit_prints_error_and_exits(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('shutil.which', return_value='/usr/bin/mmdc'):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                [], 1, stderr=b'mmdc: error rendering diagram\n'
            )
            with pytest.raises(SystemExit) as exc:
                run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'mmdc' in err
