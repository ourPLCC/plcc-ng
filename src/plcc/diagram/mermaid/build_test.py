import urllib.error
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_renders_png_via_kroki(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Foo {}\n")
    out = tmp_path / "diagram.png"

    fake_png = b'\x89PNG fake'
    mock_response = MagicMock()
    mock_response.read.return_value = fake_png
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        run_main([f'--input={src}', f'--output={out}'])

    assert out.read_bytes() == fake_png


def test_http_error_prints_message_and_exits(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('urllib.request.urlopen', side_effect=urllib.error.URLError('connection refused')):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'plcc-diagram-mermaid-build' in err


def test_encodes_source_in_url(tmp_path):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n    class Bar {}\n")
    out = tmp_path / "diagram.png"

    captured_urls = []

    def fake_urlopen(req, timeout=None):
        captured_urls.append(req.full_url)
        mock_response = MagicMock()
        mock_response.read.return_value = b'\x89PNG'
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    with patch('urllib.request.urlopen', side_effect=fake_urlopen):
        run_main([f'--input={src}', f'--output={out}'])

    assert len(captured_urls) == 1
    url = captured_urls[0]
    assert url.startswith('https://kroki.io/mermaid/png/')
    payload = url[len('https://kroki.io/mermaid/png/'):]
    assert len(payload) > 0
