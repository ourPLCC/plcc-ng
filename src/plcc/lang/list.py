import enum
import os
import re
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-lang-list
    List installed language emitter plugins.

Usage:
    plcc-lang-list [-v ...] [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

_EMIT_PATTERN = re.compile(r'^plcc-(.+)-emit$')


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-lang-list", Events, args)
    for lang in sorted(find_languages()):
        print(lang)


def find_languages():
    """Scan PATH for plcc-*-emit commands; return list of language names."""
    languages = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = extract_language_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    languages.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return languages


def extract_language_name(command_name):
    """Return the language name from a plcc-<lang>-emit command name, or None."""
    m = _EMIT_PATTERN.match(command_name)
    if m:
        lang = m.group(1)
        # Exclude the dispatcher itself
        if lang != 'lang':
            return lang
    return None


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
