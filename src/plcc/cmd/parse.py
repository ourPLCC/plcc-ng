import enum
import os
import subprocess
import sys

from docopt import DocoptExit
from plcc.cli import parse_args

from plcc.version import get_version
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
from .pipeline import TreePipeline, print_parse_error, location_str, split_committed
from .output import print_banner
from .source_runner import SourceRunner

__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + SPEC_OPTION + """\

Output:
    -b --banner                 Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


class ParseHandler:
    def __init__(self, spec_path, ll1_path, child_flags, verbose=None):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, verbose=verbose)
        self.had_error = False

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return b"" if eof else content
        dispatch, remainder = split_committed(items, content, eof)
        buffered_steps = []
        for record, _ in dispatch:
            if record.get("kind") == "parse-step":
                buffered_steps.append(record)
            elif record.get("kind") == "error":
                _render_trace(buffered_steps)
                print_parse_error(record, default_stage="plcc-parse")
                self.had_error = True
                break
            elif record.get("kind") == "tree":
                buffered_steps.clear()
                _print_tree(record, indent=0)
        return remainder


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_args(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-parse --help' for more information.", file=sys.stderr)
        sys.exit(1)
    banner = args["--banner"]
    verbose = VerboseContext.from_args("plcc-parse", Events, args)
    sources = args["SOURCE"]

    validate_spec_flag('plcc-parse', args)

    verbose.emit(Events.STARTED, message="parsing")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ["plcc-make", "--through=parse"]
        + spec_flag_for_child(args)
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(read_spec(OUTPUT_DIR)))

    spec_path = os.path.join(OUTPUT_DIR, "spec.json")
    ll1_path = os.path.join(OUTPUT_DIR, "ll1.json")

    handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                           child_flags=child_flags, verbose=verbose)
    runner = SourceRunner()
    runner.run(sources, handler)

    if handler.had_error:
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
    elif kind == "error":
        source = node.get("source", {})
        loc = location_str(source)
        message = node.get("message", "unknown error")
        print(f"{prefix}{loc}: error: {message}")



def _render_trace(steps):
    stack = []  # dicts: {"rule": str, "depth": int, "printed": bool}
    for step in steps:
        event = step.get("event")
        depth = step.get("depth", 0)
        if event == "predict":
            rule = step.get("production") or step.get("sym", "?")
            stack.append({"rule": rule, "depth": depth, "printed": False})
        elif event == "shift":
            for frame in stack:
                if not frame["printed"]:
                    print("  " * frame["depth"] + frame["rule"])
                    frame["printed"] = True
            name = step.get("name", "?")
            lexeme = step.get("lexeme", "?")
            source = step.get("source", {})
            loc = location_str(source)
            loc_str = f" [{loc}]" if loc else ""
            print(f"{'  ' * depth}{name} '{lexeme}'{loc_str}")
        elif event == "complete":
            if stack:
                frame = stack[-1]
                if not frame["printed"]:
                    print(f"{'  ' * frame['depth']}{frame['rule']} (empty)")
                stack.pop()
    for frame in stack:
        if not frame["printed"]:
            print("  " * frame["depth"] + frame["rule"])
