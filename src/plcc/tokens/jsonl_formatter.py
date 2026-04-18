"""JSONL formatter for plcc-tokens output."""

import json

from ..scan.Token import Token


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
