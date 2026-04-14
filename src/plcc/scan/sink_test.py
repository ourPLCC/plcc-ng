import json

from ..lines import Line
from .LexError import LexError
from .sink import Sink
from .Skip import Skip
from .Token import Token


def formatJson(obj):
    """Format Token, Skip, or LexError as JSON."""
    if isinstance(obj, Token):
        return json.dumps({
            "Type": "Token",
            "Name": obj.name,
            "Lexeme": obj.lexeme,
            "File": obj.line.file,
            "Line": obj.line.number,
            "Column": obj.column,
        })
    elif isinstance(obj, Skip):
        return json.dumps({
            "Type": "Skip",
            "Name": obj.name,
            "Lexeme": obj.lexeme,
            "File": obj.line.file,
            "Line": obj.line.number,
            "Column": obj.column,
        })
    elif isinstance(obj, LexError):
        return json.dumps({
            "Type": "LexError",
            "File": obj.line.file,
            "Line": obj.line.number,
            "Column": obj.column,
        })
    else:
        raise TypeError(f"Cannot format {type(obj)}")


def formatText(obj):
    """Format Token, Skip, or LexError as text."""
    if isinstance(obj, Token):
        return f"{obj.line.file}:{obj.line.number}:{obj.column}:Token {obj.name} '{obj.lexeme}'"
    elif isinstance(obj, Skip):
        return f"{obj.line.file}:{obj.line.number}:{obj.column}:Skip {obj.name} '{obj.lexeme}'"
    elif isinstance(obj, LexError):
        return f"{obj.line.file}:{obj.line.number}:{obj.column}:LexError 't'"
    else:
        raise TypeError(f"Cannot format {type(obj)}")


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
