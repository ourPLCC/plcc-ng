"""JSONL formatter for plcc-tokens output."""

import json

from ..scan.Token import Token
from ..scan.LexError import LexError


def format_record(obj):
    """Return a single-line JSON string for a token or lex error."""
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
    elif isinstance(obj, LexError):
        return json.dumps({
            'kind': 'error',
            'stage': 'plcc-tokens',
            'source': {
                'file': obj.line.file,
                'line': obj.line.number,
                'column': obj.column,
            },
        })
    else:
        raise TypeError(f'Unexpected type: {type(obj)}')
