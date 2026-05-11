"""JSONL formatter for plcc-tokens output."""

import json

from ..scan.Token import Token
from ..scan.Skip import Skip
from ..scan.LexError import LexError


def format_record(obj, show_all=False):
    if isinstance(obj, (Token, Skip)):
        kind = 'skip' if isinstance(obj, Skip) else 'token'
        record = {
            'kind': kind,
            'name': obj.name,
            'lexeme': obj.lexeme,
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        }
        if show_all:
            record['regex'] = obj.pattern
            record['source_line'] = obj.line.string
            if obj.attempts:
                record['attempts'] = obj.attempts
        return json.dumps(record)
    raise TypeError(f'Unexpected type: {type(obj)}')


def format_error_record(obj):
    if not isinstance(obj, LexError):
        raise TypeError(f'Unexpected type: {type(obj)}')
    return json.dumps({
        'kind': 'error',
        'stage': 'plcc-tokens',
        'severity': 'error',
        'pos': {
            'file': obj.line.file,
            'line': obj.line.number,
            'column': obj.column,
        },
        'lexeme': obj.line.string[obj.column - 1],
        'message': 'unrecognized character',
    })
