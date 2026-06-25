import io
import sys
import pytest
from .scan import _render_record


def _capture(record, show_skips=True, show_line=True, show_attempts=True):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _render_record(record, show_skips, show_line, show_attempts)
    finally:
        sys.stdout = old
    return buf.getvalue()


def _base_record(kind='token'):
    return {
        'kind': kind,
        'name': 'NUM',
        'lexeme': '42',
        'regex': r'\d+',
        'source': {'file': '-', 'line': 1, 'column': 1},
        'source_line': '42',
        'attempts': [
            {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
             'char_count': 2, 'is_skip': False, 'winner': True, 'rule_index': 1},
        ],
    }


def test_trace_header():
    out = _capture(_base_record())
    assert 'Scanning -:1:1:' in out


def test_trace_source_line_with_newline_marker():
    r = _base_record()
    r['source_line'] = '42'
    r['source'] = {'file': '-', 'line': 1, 'column': 3}
    out = _capture(r)
    assert '42↵' in out


def test_trace_source_line_no_newline_marker_when_col_within_line():
    r = _base_record()
    r['source_line'] = '42'
    r['source'] = {'file': '-', 'line': 1, 'column': 1}
    out = _capture(r)
    lines = out.splitlines()
    source_line = [l for l in lines if l.startswith('42')][0]
    assert source_line == '42'


def test_trace_tab_replaced_with_arrow():
    r = _base_record()
    r['source_line'] = '\t42'
    r['source'] = {'file': '-', 'line': 1, 'column': 1}
    out = _capture(r)
    assert '→42' in out


def test_trace_caret_at_column():
    r = _base_record()
    r['source_line'] = '42'
    r['source'] = {'file': '-', 'line': 1, 'column': 2}
    out = _capture(r)
    lines = out.splitlines()
    caret_line = [l for l in lines if '^' in l][0]
    assert caret_line == ' ^'


def test_trace_candidates_heading():
    out = _capture(_base_record())
    assert 'Candidates:' in out


def test_trace_table_header_row():
    out = _capture(_base_record())
    assert '#' in out
    assert 'Type' in out
    assert 'Name' in out
    assert 'Pattern' in out
    assert 'Len' in out
    assert 'Match' in out


def test_trace_winner_marked_on_len_when_no_tie():
    r = _base_record()
    r['attempts'] = [
        {'name': 'ONE', 'regex': r'\d', 'lexeme': '4',
         'char_count': 1, 'is_skip': False, 'winner': False, 'rule_index': 1},
        {'name': 'NUM', 'regex': r'\d+', 'lexeme': '42',
         'char_count': 2, 'is_skip': False, 'winner': True, 'rule_index': 2},
    ]
    out = _capture(r)
    assert '2*' in out
    assert '1*' not in out


def test_trace_winner_marked_on_rule_index_when_tie():
    r = _base_record()
    r['name'] = 'PLUS'
    r['lexeme'] = '+'
    r['regex'] = r'\+'
    r['attempts'] = [
        {'name': 'PLUS', 'regex': r'\+', 'lexeme': '+',
         'char_count': 1, 'is_skip': False, 'winner': True, 'rule_index': 1},
        {'name': 'OP', 'regex': r'\+', 'lexeme': '+',
         'char_count': 1, 'is_skip': False, 'winner': False, 'rule_index': 2},
    ]
    out = _capture(r)
    assert '1*' in out
    assert '2*' not in out


def test_trace_legend():
    out = _capture(_base_record())
    assert '* longest match wins; ties broken by earliest rule (#)' in out


def test_trace_result_heading():
    out = _capture(_base_record())
    assert 'Result:' in out


def test_trace_result_line():
    out = _capture(_base_record())
    lines = out.splitlines()
    result_idx = next(i for i, l in enumerate(lines) if l == 'Result:')
    assert lines[result_idx + 1] == r"token NUM '\d+' '42'"


def test_trace_result_line_skip():
    r = _base_record(kind='skip')
    r['name'] = 'WS'
    r['lexeme'] = '\n'
    r['regex'] = r'\s+'
    r['attempts'] = [
        {'name': 'WS', 'regex': r'\s+', 'lexeme': '\n',
         'char_count': 1, 'is_skip': True, 'winner': True, 'rule_index': 1},
    ]
    out = _capture(r)
    lines = out.splitlines()
    result_idx = next(i for i, l in enumerate(lines) if l == 'Result:')
    assert lines[result_idx + 1] == r"skip WS '\s+' '\n'"


def test_non_trace_token_format_unchanged():
    r = _base_record()
    out = _capture(r, show_skips=False, show_line=False, show_attempts=False)
    assert out.strip() == "-:1:1 NUM '42'"


def test_non_trace_skip_format_unchanged():
    r = _base_record(kind='skip')
    r['name'] = 'WS'
    r['lexeme'] = ' '
    out = _capture(r, show_skips=True, show_line=False, show_attempts=False)
    assert out.strip() == "-:1:1 WS ' ' SKIPPED"
