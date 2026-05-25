import pytest

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_prints_path_to_stdout(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b"PNG")
    run_main([f'--input={img}'])
    out, _ = capsys.readouterr()
    assert str(img) in out
