import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.version import get_version
from plcc.build.grammar import read_grammar
from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .pipeline import TreePipeline, print_parse_error, location_str
from .output import print_startup_banner
from .source_runner import SourceRunner, SubmitOn

__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
    -t --trace                  Show step-by-step trace of the parse algorithm.
    -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                commands until changed. Defaults to grammar.plcc on first use.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


class ParseHandler:
    def __init__(self, spec_path, ll1_path, child_flags, trees_flags=None, verbose=None):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, trees_flags=trees_flags, verbose=verbose)
        self.had_error = False

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, _ in items:
            if record.get("kind") == "parse-step":
                _print_parse_step(record)
            elif record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-parse")
                self.had_error = True
                break
            elif record.get("kind") == "tree":
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
    grammar_file = args["--grammar"]
    trace = args["--trace"]
    sources = args["SOURCE"]

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-parse: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="parsing")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)
    trees_flags = child_flags + (["--trace"] if trace else [])

    # Ensure build/ is current for the parse level
    make_result = subprocess.run(
        ['plcc-make', '--through=parse']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    print_startup_banner(os.path.abspath(read_grammar('build')), get_version())

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                           child_flags=child_flags, trees_flags=trees_flags, verbose=verbose)
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    completed = runner.run(sources, handler)

    if not completed or handler.had_error:
        sys.exit(1)
    verbose.emit(Events.FINISHED, message="done")


def _print_tree(node, indent):
    if isinstance(node, list):
        for item in node:
            _print_tree(item, indent)
        return
    prefix = "  " * indent
    kind = node.get("kind", "?")
    if kind == "tree":
        rule = node.get("rule", "?")
        children = node.get("children", [])
        suffix = " (empty)" if not children else ""
        print(f"{prefix}{rule}{suffix}")
        for _field, child in children:
            _print_tree(child, indent + 1)
    elif kind == "token":
        name = node.get("name", "?")
        lexeme = node.get("lexeme", "?")
        source = node.get("source", {})
        loc = location_str(source)
        print(f"{prefix}{name} '{lexeme}' [{loc}]")
    # plcc-trees may emit error records inline in the current protocol
    elif kind == "error":
        source = node.get("source", {})
        loc = location_str(source)
        message = node.get("message", "unknown error")
        print(f"{prefix}{loc}: error: {message}")


def _print_parse_step(record):
    depth = record.get("depth", 0)
    indent = "  " * depth
    event = record.get("event", "?")
    if event == "predict":
        sym = record.get("sym", "?")
        lookahead = record.get("lookahead", "?")
        production = record.get("production")
        if production is None:
            print(f"{indent}{'predict':<9}{sym}  lookahead={lookahead} → (iteration)", flush=True)
        else:
            print(f"{indent}{'predict':<9}{sym}  lookahead={lookahead} → {production}", flush=True)
    elif event == "shift":
        name = record.get("name", "?")
        lexeme = record.get("lexeme", "?")
        source = record.get("source", {})
        loc = location_str(source)
        loc_str = f" [{loc}]" if loc else ""
        print(f"{indent}{'shift':<9}{name} '{lexeme}'{loc_str}", flush=True)
    elif event == "complete":
        rule = record.get("rule", "?")
        print(f"{indent}{'complete':<9}{rule}", flush=True)
