import json
import pytest
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


def test_format_record_rejects_lex_error():
    err = LexError(line=Line(string="abc", number=1, file=None), column=1)
    with pytest.raises(TypeError):
        format_record(err)


def test_output_is_single_line():
    t = Token(lexeme='x', name='A', line=_line(), column=1)
    output = format_record(t)
    assert '\n' not in output
