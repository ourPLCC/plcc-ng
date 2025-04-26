from ..lines import Line
from .LexError import LexError
from .sink import Sink
from .Skip import Skip
from .Token import Token
from .json_formatter import format as formatJson
from .text_formatter import format as formatText


def test_json_token(capfd):
    sink = Sink(printSkips=False, format_fn=formatJson)
    sink.write(makeToken())
    out, err = capfd.readouterr()
    assert '"Type": "Token"' in out
    assert err == ''


def test_text_token(capfd):
    sink = Sink(printSkips=False, format_fn=formatText)
    sink.write(makeToken())
    out, err = capfd.readouterr()
    assert "Token" in out
    assert err == ''


def test_json_lexError(capfd):
    sink = Sink(printSkips=False, format_fn=formatJson)
    sink.write(makeLexError())
    out, err = capfd.readouterr()
    assert '"Type": "LexError"' in out
    assert err == ''


def test_print_json_skip(capfd):
    sink = Sink(printSkips=True, format_fn=formatJson)
    sink.write(makeSkip())
    out, err = capfd.readouterr()
    assert '"Type": "Skip"' in out
    assert err == ''


def test_do_not_print_skip_json(capfd):
    sink = Sink(printSkips=False, format_fn=formatJson)
    sink.write(makeSkip())
    out, err = capfd.readouterr()
    assert out == ''
    assert err == ''


def test_consecutive_json(capfd):
    sink = Sink(printSkips=False, format_fn=formatJson)
    sink.write(makeToken())
    out, err = capfd.readouterr()
    assert '"Type": "Token"' in out
    assert '"Type": "LexError"' not in out
    sink.write(makeLexError())
    out, err = capfd.readouterr()
    assert '"Type": "LexError"' in out
    assert '"Type": "Token"' not in out


def makeToken(lexeme="lexeme", name="NAME", column=3):
    return Token(lexeme, name, makeLine(), column)


def makeLexError(column=3):
    return LexError(makeLine(), column)


def makeLine(string="string", number=1, file="fileName"):
    return Line(string, number, file)


def makeSkip(lexeme="lexeme", name="name", line=makeLine(), column=2):
    return Skip(lexeme, name, line, column)
