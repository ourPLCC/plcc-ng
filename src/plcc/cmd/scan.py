import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from plcc.cmd.grammar import GRAMMAR_OPTION, validate_grammar_flag, grammar_flag_for_child
from .output import print_banner, print_user_error
from .source_runner import SourceRunner, SubmitOn


def _location_str(source):
    file = source.get("file", "-")
    line = source.get("line", "?")
    col = source.get("column", "?")
    return f"{file}:{line}:{col}"


__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + GRAMMAR_OPTION + """\
    -t --trace                  Show detailed scanning output.
    -b --banner                 Show the version and spec banner on stderr.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("source", {}))
        message = record.get("message", "unrecognized character")
        print_user_error(f"{loc}: error: {message}")
        return

    if kind == "skip" and not show_skips:
        return

    if kind not in ("token", "skip"):
        return

    source = record.get("source", {})
    loc = _location_str(source)
    name = record.get("name", "?")
    lexeme = record.get("lexeme", "?")
    source_line = record.get("source_line", "")
    attempts = record.get("attempts", [])
    col = source.get("column", 1)

    if show_line and source_line:
        print(source_line, flush=True)
        print(" " * (col - 1) + "^", flush=True)

    if show_attempts:
        print("Candidates:", flush=True)
        for attempt in attempts:
            if attempt.get("char_count", 0) == 0:
                continue
            prefix = "-> " if attempt.get("winner") else "   "
            a_name = attempt.get("name", "?")
            a_regex = attempt.get("regex", "?")
            a_count = attempt.get("char_count", 0)
            a_lexeme = attempt.get("lexeme", "?")
            print(f"{prefix}{a_name} '{a_regex}' {a_count} chars '{a_lexeme}'", flush=True)

    if show_attempts:
        if kind == "skip":
            print(f"{loc}: skip: {name} '{lexeme}'", flush=True)
        else:
            print(f"{loc}: token: {name} '{lexeme}'", flush=True)
        print(flush=True)
    elif kind == "skip":
        print(f"{loc} {name} '{lexeme}' SKIPPED", flush=True)
    else:
        print(f"{loc} {name} '{lexeme}'", flush=True)


class ScanHandler:
    def __init__(self, spec_path, tokens_flags):
        self._spec_path = spec_path
        self._tokens_flags = tokens_flags

    def feed(self, content, source, eof=False):
        proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path,
             f"--source-name={source}", "-"] + self._tokens_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        stdout, _ = proc.communicate(content)
        trace = "--trace" in self._tokens_flags
        for raw in stdout.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if record.get("name") == "eof":
                continue
            _render_record(record, trace, trace, trace)
        if proc.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})",
                  file=sys.stderr)
            sys.exit(proc.returncode)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    banner = args["--banner"]
    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    sources = args["SOURCE"]
    trace = args["--trace"]

    validate_grammar_flag('plcc-scan', args)

    verbose.emit(Events.STARTED, message="scanning")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ["plcc-make", "--through=scan"]
        + grammar_flag_for_child(args)
        + child_flags,
        stderr=None,
    )
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(read_grammar("build")))

    spec_path = os.path.join("build", "spec.json")
    tokens_flags = child_flags + (["--trace"] if trace else [])

    handler = ScanHandler(spec_path=spec_path, tokens_flags=tokens_flags)
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    runner.run(sources, handler)

    verbose.emit(Events.FINISHED, message="done")
