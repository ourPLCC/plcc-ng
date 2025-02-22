from pathlib import Path
from plccng import lineparse
from plccng.roughparse.structs import lineparse
from .parse_dividers import parse_dividers
from .parse_blocks import parse_blocks
from .parse_includes import parse_includes
from .structs import CircularIncludeError, Include


def resolve_includes(rough):
    return IncludeResolver().resolveIncludes(rough)


def from_lines_unresolved(lines):
    blocks = parse_blocks(lines)
    includes = parse_includes(blocks)
    dividers = parse_dividers(includes)
    return dividers


def from_file_unresolved(file, startLineNumber=1):
    lines = lineparse.fromFile(file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines)


class IncludeResolver():
    def __init__(self):
        self._files_seen = set()

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
        self._assert_file_has_not_been_included(include, file)
        yield from self._include_file(file)

    def _get_absolute_path_to_include_file(self, include):
        p = Path(include.file)
        if not p.is_absolute():
            p = (Path(include.line.file).parent/p).resolve()
        p = str(p)
        return p

    def _assert_file_has_not_been_included(self, include, p):
        if p in self._files_seen:
            raise CircularIncludeError(include.line)

    def _include_file(self, file):
        self._files_seen.add(file)
        rough = from_file_unresolved(file)
        yield from self.resolveIncludes(rough)
        self._files_seen.remove(file)


def from_string_unresolved(string, file=None, startLineNumber=1):
    lines = lineparse.fromString(string, file=file, startLineNumber=startLineNumber)
    return from_lines_unresolved(lines)
