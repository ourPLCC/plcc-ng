import enum
import shutil
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-trees
    Dispatch to a parser plugin. Reads token JSONL, emits a parse tree.

Usage:
    plcc-trees [-v ...] [options] --ll1=LL1_JSON

Options:
    --ll1=LL1_JSON          Path to LL(1) analysis JSON (required).
    --parser=KIND           Parser plugin to use [default: table].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-trees", Events, args)
    ll1_path = args["--ll1"]
    parser_kind = args["--parser"]
    cmd = f"plcc-parser-{parser_kind}"
    if not shutil.which(cmd):
        print(
            f"plcc-trees: parser plugin '{cmd}' not found on PATH.\n"
            f"Run plcc-parser-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    verbose.emit(Events.STARTED, message=f"dispatching to {cmd}")
    child_cmd = [cmd, f"--ll1={ll1_path}"] + verbose.child_flags()
    result = subprocess.run(child_cmd, stdin=sys.stdin)
    verbose.emit(Events.FINISHED, message=f"exit {result.returncode}")
    sys.exit(result.returncode)
