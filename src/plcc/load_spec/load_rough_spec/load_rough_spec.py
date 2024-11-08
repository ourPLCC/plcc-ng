from pathlib import Path


from .parse_rough import parse_rough
from .parse_includes import Include
from .split_rough_spec import split_rough_spec


def load_rough_spec(file):
    rough_spec = load_rough_spec_without_processing_includes(file)
    rough_spec = process_includes(rough_spec)
    rough_spec = split_rough_spec(rough_spec)
    return rough_spec


def load_rough_spec_without_processing_includes(file):
    string = read_file_as_string(file)
    rough_spec = parse_rough(string, file)
    return rough_spec


def read_file_as_string(file):
    with open(file, 'r') as f:
        return f.read()


def process_includes(lines):
    return IncludeProcessor().process(lines)


class IncludeProcessor():
    def __init__(self):
        self._files_seen = set()

    def process(self, lines):
        if lines is None:
            return []
        for line in lines:
            yield from self._process_line(line)

    def _process_line(self, line):
        if isinstance(line, Include):
            yield from self._process_include_line(line)
        else:
            yield line

    def _process_include_line(self, include):
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
        rough_spec = load_rough_spec_without_processing_includes(file)
        yield from self.process(rough_spec)
        self._files_seen.remove(file)


class CircularIncludeError(Exception):
    def __init__(self, line):
        self.line = line
