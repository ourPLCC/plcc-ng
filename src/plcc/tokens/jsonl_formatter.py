"""JSONL formatter for plcc-tokens output."""

import json

from ..scan.Token import Token
from ..scan.LexError import LexError


def format_record(obj):
    if isinstance(obj, Token):
        return json.dumps({
            'kind': 'token',
            'name': obj.name,
            'lexeme': obj.lexeme,
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        })
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
