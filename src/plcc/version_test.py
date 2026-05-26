from unittest.mock import patch
from importlib.metadata import PackageNotFoundError

from plcc.version import get_version, main


def test_get_version_returns_string_from_metadata():
    with patch("plcc.version.importlib.metadata.version", return_value="1.2.3"):
        assert get_version() == "1.2.3"


def test_get_version_returns_unknown_when_not_found():
    with patch(
        "plcc.version.importlib.metadata.version",
        side_effect=PackageNotFoundError("plcc-ng"),
    ):
        assert get_version() == "unknown"


def test_main_prints_version_to_stdout(capsys):
    with patch("plcc.version.importlib.metadata.version", return_value="1.2.3"):
        main()
    captured = capsys.readouterr()
    assert captured.out == "plcc-ng 1.2.3\n"
    assert captured.err == ""
