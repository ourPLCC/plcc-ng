import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


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
    --grammar-file=<path>       Path to the PLCC grammar file [default: grammar.plcc].
    -t --trace                  Show detailed scanning output.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("pos", {}))
        lexeme = record.get("lexeme", "?")
        message = record.get("message", "unrecognized character")
        print(f"{loc}: error: {message} '{lexeme}'", flush=True)
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

    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    grammar_file = args["--grammar-file"]
    sources = args["SOURCE"]

    trace = args["--trace"]
    any_enrichment = trace

    if not os.path.exists(grammar_file):
        print(f"plcc-scan: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"scanning with {grammar_file}")
    child_flags = verbose.child_flags()

    # Ensure build/ is current for the scan level
    make_result = subprocess.run(
        ['plcc-make', '--through=scan', f'--grammar-file={grammar_file}'] + child_flags,
        stderr=None,
    )
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    spec_path = os.path.join('build', 'spec.json')

    token_sources = sources if sources else ["-"]
    tokens_flags = child_flags + (["--trace"] if any_enrichment else [])

    proc = subprocess.Popen(
        ["plcc-tokens", spec_path] + token_sources + tokens_flags,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    for raw in proc.stdout:
        line = raw.decode("utf-8").strip()
        if not line:
            continue
        record = json.loads(line)
        _render_record(record, trace, trace, trace)

    proc.wait()

    if proc.returncode != 0:
        print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
        sys.exit(proc.returncode)

    verbose.emit(Events.FINISHED, message="done")
