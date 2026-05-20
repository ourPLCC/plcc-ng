import json
import pytest
from ..lines import Line
from ..scan.Token import Token
from ..scan.LexError import LexError
from ..scan.Skip import Skip
from .jsonl_formatter import format_record, format_error_record


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


def test_formats_error_record():
    line = Line(string='hello@world', number=3, file='src.txt')
    lex_error = LexError(line=line, column=6)  # '@' is at index 5, column 6
    result = json.loads(format_error_record(lex_error))
    assert result['kind'] == 'error'
    assert result['stage'] == 'plcc-tokens'
    assert result['severity'] == 'error'
    assert result['source'] == {'file': 'src.txt', 'line': 3, 'column': 6}
    assert result['lexeme'] == '@'
    assert result['message'] == "unrecognized character '@'"


def test_format_error_record_rejects_token():
    token = Token(name='NUM', lexeme='42', line=Line(string='42', number=1, file='f'), column=1)
    with pytest.raises(TypeError):
        format_error_record(token)


def _skip(lexeme=' ', name='WS', line=None, column=3):
    l = line or _line(s='42 99', n=1, f='test.txt')
    s = Skip(lexeme=lexeme, name=name, line=l, column=column, pattern=r'\s+')
    return s


def _token_enriched():
    t = Token(lexeme='42', name='NUM', line=_line(s='hello 42', n=2, f='src.txt'), column=7, pattern=r'\d+')
    return t


def test_lean_record_omits_regex_source_line_attempts():
    t = Token(lexeme='42', name='NUM', line=_line(), column=1)
    record = json.loads(format_record(t))
    assert 'regex' not in record
    assert 'source_line' not in record
    assert 'attempts' not in record


def test_show_all_token_includes_regex_and_source_line():
    t = _token_enriched()
    record = json.loads(format_record(t, show_all=True))
    assert record['kind'] == 'token'
    assert record['regex'] == r'\d+'
    assert record['source_line'] == 'hello 42'


def test_show_all_token_omits_attempts_when_empty():
    t = _token_enriched()
    record = json.loads(format_record(t, show_all=True))
    assert 'attempts' not in record


def test_show_all_token_includes_attempts_when_present():
    t = _token_enriched()
    t.attempts = [
        {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
         'char_count': 2, 'is_skip': False, 'winner': True},
    ]
    record = json.loads(format_record(t, show_all=True))
    assert len(record['attempts']) == 1
    assert record['attempts'][0]['winner'] is True


def test_skip_record_has_kind_skip():
    s = _skip()
    record = json.loads(format_record(s, show_all=True))
    assert record['kind'] == 'skip'
    assert record['name'] == 'WS'
    assert record['lexeme'] == ' '


def test_skip_record_show_all_includes_regex_and_source_line():
    s = _skip()
    record = json.loads(format_record(s, show_all=True))
    assert record['regex'] == r'\s+'
    assert record['source_line'] == '42 99'


def test_skip_record_lean_not_emitted_without_show_all():
    # format_record on a Skip without show_all should still work structurally
    # (tokens_cli decides whether to print it, not the formatter)
    s = _skip()
    record = json.loads(format_record(s))
    assert record['kind'] == 'skip'
    assert 'regex' not in record


def test_exactly_one_winner_in_attempts():
    t = _token_enriched()
    t.attempts = [
        {'name': 'ONE', 'regex': r'\d', 'lexeme': '4',
         'char_count': 1, 'is_skip': False, 'winner': False},
        {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
         'char_count': 2, 'is_skip': False, 'winner': True},
    ]
    record = json.loads(format_record(t, show_all=True))
    winners = [a for a in record['attempts'] if a['winner']]
    assert len(winners) == 1
