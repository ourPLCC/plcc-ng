import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .source_runner import SourceRunner, SubmitOn

__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
    --grammar-file=<path>       Path to the PLCC grammar file [default: grammar.plcc].
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _location_str(source):
    file = source.get("file")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file != "<stdin>":
        return f"{file}:{line}:{col}"
    return f"{line}:{col}"


class ParseHandler:
    def __init__(self, spec_path, ll1_path, child_flags):
        self._spec_path = spec_path
        self._ll1_path = ll1_path
        self._child_flags = child_flags
        self.had_error = False

    def feed(self, content, source):
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tree_proc = subprocess.Popen(
            ["plcc-tree", f"--ll1={self._ll1_path}"] + self._child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(content)
        tokens_proc.stdin.close()
        tree_out, _ = tree_proc.communicate()
        tokens_proc.wait()

        tree_out = tree_out.strip()
        if not tree_out:
            return False

        record = json.loads(tree_out)
        if record.get("kind") == "error":
            stage = record.get("stage", "plcc-parse")
            message = record.get("message", "error")
            print(f"{stage}: error: {message}", file=sys.stderr)
            self.had_error = True
            return True

        _print_tree(record, indent=0)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)
    verbose = VerboseContext.from_args("plcc-parse", Events, args)
    grammar_file = args["--grammar-file"]
    sources = args["SOURCE"]

    if not os.path.exists(grammar_file):
        print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"parsing with {grammar_file}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    # Ensure build/ is current for the parse level
    make_result = subprocess.run(
        ['plcc-make', '--through=parse', f'--grammar-file={grammar_file}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                           child_flags=child_flags)
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    completed = runner.run(sources, handler)

    if not completed or handler.had_error:
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="done")


def _print_tree(node, indent):
    prefix = "  " * indent
    kind = node.get("kind", "?")
    if kind == "tree":
        rule = node.get("rule", "?")
        print(f"{prefix}{rule}")
        for _field, child in node.get("children", []):
            _print_tree(child, indent + 1)
    elif kind == "token":
        name = node.get("name", "?")
        lexeme = node.get("lexeme", "?")
        source = node.get("source", {})
        loc = _location_str(source)
        print(f"{prefix}{name} '{lexeme}' [{loc}]")
    # forward-looking: plcc-tree may emit error records inline in a future protocol
    elif kind == "error":
        source = node.get("source", {})
        loc = _location_str(source)
        message = node.get("message", "unknown error")
        print(f"{prefix}{loc}: error: {message}")
