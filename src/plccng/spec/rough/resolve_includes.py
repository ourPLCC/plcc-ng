from pathlib import Path

from .. import lines
from .CircularIncludeError import CircularIncludeError
from .Include import Include
from .parse_blocks import parse_blocks
from .parse_dividers import parse_dividers
from .parse_includes import parse_includes
from .raise_handler import raise_handler


def resolve_includes(rough, handler=raise_handler):
    return IncludeResolver(handler=handler).resolveIncludes(rough)


def from_lines_unresolved(lines):
    blocks = parse_blocks(lines)
    includes = parse_includes(blocks)
    dividers = parse_dividers(includes)
    return dividers


def from_file_unresolved(file, startLineNumber=1):
    lines_ = lines.parse_from_file(file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines_)


class IncludeResolver():
    def __init__(self, handler=raise_handler):
        self._files_seen = set()
        self._handler = handler

    def resolveIncludes(self, rough):
        if rough is None:
            return []
        for part in parse_includes(rough):
            yield from self._process_part(part)

    def _process_part(self, part):
        if isinstance(part, Include):
            yield from self._resolve_include(part)
        else:
            yield part

    def _resolve_include(self, include):
        file = self._get_absolute_path_to_include_file(include)
        if file in self._files_seen:
            self._handler(CircularIncludeError(include.line))
            # Don't yield anything, and let processing continue to next line.
        else:
            self._files_seen.add(file)
            yield from self._include_file(file)

    def _get_absolute_path_to_include_file(self, include):
        p = Path(include.file)
        if not p.is_absolute():
            p = (Path(include.line.file).parent/p).resolve()
        p = str(p)
        return p

    def _include_file(self, file):
        rough = from_file_unresolved(file)
        yield from self.resolveIncludes(rough)
        self._files_seen.remove(file)


def from_string_unresolved(string, file=None, startLineNumber=1):
    lines_ = lines.parse_from_string(string, file=file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines_)
