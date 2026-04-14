import json
from ..lines import Line
from ..scan.Token import Token
from ..scan.LexError import LexError
from .jsonl_formatter import format_record


def _line(s='hello', n=1, f='test.txt'):
    return Line(string=s, number=n, file=f)


def test_formats_token():
    t = Token(lexeme='42', name='NUM', line=_line(), column=3)
    record = json.loads(format_record(t))
    assert record['kind'] == 'token'
    assert record['name'] == 'NUM'
    assert record['lexeme'] == '42'
    assert record['source']['line'] == 1
    assert record['source']['column'] == 3
    assert record['source']['file'] == 'test.txt'


def test_formats_lex_error():
    e = LexError(line=_line(), column=5)
    record = json.loads(format_record(e))
    assert record['kind'] == 'error'
    assert record['stage'] == 'plcc-tokens'
    assert record['source']['column'] == 5


def test_output_is_single_line():
    t = Token(lexeme='x', name='A', line=_line(), column=1)
    output = format_record(t)
    assert '\n' not in output
