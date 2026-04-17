import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-lang-emit
    Dispatch to the appropriate plcc-<lang>-emit command.

Usage:
    plcc-lang-emit [options] --target=LANG --output=DIR

Options:
    --target=LANG   Target language (e.g. PlantUML, Java, Python).
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-lang-emit", Events, args)
    lang = args['--target']
    output = args['--output']
    cmd = resolve_emit_command(lang)
    if not shutil.which(cmd):
        print(
            f"No emitter found for '{lang}'. Is {cmd} installed?\n"
            f"Run plcc-lang-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--output={output}'] + verbose.child_flags(),
        stdin=sys.stdin,
    )
    sys.exit(result.returncode)


def resolve_emit_command(lang):
    return f'plcc-{lang.lower()}-emit'
