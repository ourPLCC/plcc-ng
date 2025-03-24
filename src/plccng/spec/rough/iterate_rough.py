from .parse_from_lines import parse_from_lines
from .parse_from_string import parse_from_string
from .raise_handler import raise_handler


def iterate_rough(thing, file=None, startLineNumber=1, handler=raise_handler):
    if thing is None:
        return []
    if isinstance(thing, str):
        return parse_from_string(thing, file=file, startLineNumber=startLineNumber, handler=handler)
    if isinstance(thing, list):
        if not thing:
            return []
        else:
            return parse_from_lines(thing, handler=handler)
    raise TypeError(f'Unexpected type: {type(thing)}')
