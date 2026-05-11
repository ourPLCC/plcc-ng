import enum
import json
import os
import subprocess
import sys
import tempfile

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
    plcc-scan [-v ...] [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help           Show this message.
    --show-skips        Show skip records in output.
    --show-line         Show source line and cursor before each token.
    --show-attempts     Show rule match attempts before each token.
    --show-regex        Show matched regex in each token line.
    -t --trace          Enable all --show-* flags.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _render_record(record, show_skips, show_line, show_regex, show_attempts):
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
    regex = record.get("regex", "")
    source_line = record.get("source_line", "")
    attempts = record.get("attempts", [])
    col = source.get("column", 1)

    if show_line and source_line:
        print(source_line)
        print(" " * (col - 1) + "^")

    if show_attempts:
        for attempt in attempts:
            prefix = "    * " if attempt.get("winner") else "      "
            a_name = attempt.get("name", "?")
            a_regex = attempt.get("regex", "?")
            a_count = attempt.get("char_count", 0)
            a_lexeme = attempt.get("lexeme", "?")
            print(f"{prefix}{a_name} '{a_regex}' {a_count} chars '{a_lexeme}'")

    if show_regex and kind == "skip":
        print(f"{loc} {name} '{regex}' '{lexeme}' SKIPPED", flush=True)
    elif show_regex:
        print(f"{loc} {name} '{regex}' '{lexeme}'", flush=True)
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
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]

    trace = args["--trace"]
    show_skips = args["--show-skips"] or trace
    show_line = args["--show-line"] or trace
    show_regex = args["--show-regex"] or trace
    show_attempts = args["--show-attempts"] or trace
    any_enrichment = show_skips or show_line or show_regex or show_attempts

    if sys.stdin.isatty() and (not sources or "-" in sources):
        print("reading from stdin — press ^D to end input", flush=True)

    verbose.emit(Events.STARTED, message=f"scanning with {grammar}")
    child_flags = verbose.child_flags()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        spec_path = f.name
    try:
        with open(spec_path, "w") as spec_out:
            result = subprocess.run(
                ["plcc-spec", grammar] + child_flags,
                stdout=spec_out,
                stderr=None,
            )
        if result.returncode != 0:
            print(f"plcc-scan: plcc-spec failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)

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
            _render_record(record, show_skips, show_line, show_regex, show_attempts)

        proc.wait()

        if proc.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
            sys.exit(proc.returncode)
    finally:
        os.unlink(spec_path)

    verbose.emit(Events.FINISHED, message="done")
