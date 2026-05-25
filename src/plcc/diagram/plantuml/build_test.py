import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main, _encode


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


_PLANTUML_ALPHABET = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_')


def test_encode_known_good():
    assert _encode("@startuml\nclass Foo {}\n@enduml\n") == 'SoWkIImgAStDuKhEIImkLd3BprUehkLoICrB0Ga200'


def test_encode_no_padding():
    assert '=' not in _encode("@startuml\n@enduml\n")


def test_encode_only_plantuml_alphabet():
    result = _encode("@startuml\nclass Foo {}\n@enduml\n")
    assert all(c in _PLANTUML_ALPHABET for c in result)


def test_calls_plantuml_server_and_writes_png(tmp_path):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\nclass Foo {}\n@enduml\n")
    out = tmp_path / "diagram.png"
    fake_png = b'\x89PNG fake'

    mock_response = MagicMock()
    mock_response.__enter__.return_value.read.return_value = fake_png

    with patch('urllib.request.urlopen', return_value=mock_response) as mock_urlopen:
        run_main([f'--input={src}', f'--output={out}'])

    assert out.read_bytes() == fake_png
    url_called, = mock_urlopen.call_args.args
    assert url_called.startswith('https://www.plantuml.com/plantuml/png/')
    assert mock_urlopen.call_args.kwargs == {'timeout': 30}


def test_missing_input_file_exits_with_error(tmp_path, capsys):
    src = tmp_path / "nonexistent.puml"
    out = tmp_path / "diagram.png"

    with pytest.raises(SystemExit) as exc:
        run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert err.strip() != ''


def test_server_error_prints_message_and_exits(tmp_path, capsys):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"

    with patch('urllib.request.urlopen', side_effect=Exception("connection refused")):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'connection refused' in err
