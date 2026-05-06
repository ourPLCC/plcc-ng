import enum
import json
import os
import subprocess
import sys
import tempfile

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


def _location_str(source):
    file = source.get("file")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file != "<stdin>":
        return f"{file}:{line}:{col}"
    return f"{line}:{col}"


__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


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

    verbose.emit(Events.STARTED, message=f"scanning with {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        spec_path = f.name
    try:
        # plcc-spec grammar > spec.json
        with open(spec_path, "w") as spec_out:
            result = subprocess.run(
                ["plcc-spec", grammar] + child_flags,
                stdout=spec_out,
                stderr=subprocess.PIPE,
            )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            print(f"plcc-scan: plcc-spec failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)

        # Build input: concatenate source files, then stdin
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens spec.json < input
        result = subprocess.run(
            ["plcc-tokens", spec_path] + child_flags,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            # lex error: plcc-tokens already emitted the error to stderr via verbose;
            # treat as non-fatal — pipeline completed with an error in-band
            pass
        else:
            for line in result.stdout.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("kind") == "token":
                    name = record.get("name", "?")
                    lexeme = record.get("lexeme", "?")
                    source = record.get("source", {})
                    loc = _location_str(source)
                    print(f"{loc} {name} '{lexeme}'")
                # forward-looking: plcc-tokens may emit error records inline in a future protocol
                elif record.get("kind") == "error":
                    source = record.get("source", {})
                    loc = _location_str(source)
                    message = record.get("message", "unknown error")
                    print(f"{loc}: error: {message}")
    finally:
        os.unlink(spec_path)

    verbose.emit(Events.FINISHED, message="done")
