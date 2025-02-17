import pytest
from .main import Main
from .main_help_message import helpMessage


def test_help_command(capfd):
    argv = ["-h"]
    main = Main(None, None)
    main.run(stdin=None, stdout=None, stderr=None, argv=argv)
    captured = capfd.readouterr()
    assert captured.out == helpMessage + "\n"

class StubScanner:
    pass

class StubSource:
    pass
