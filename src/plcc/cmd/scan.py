import enum
import json
import os
import subprocess
import sys
import tempfile
import threading

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS


def _location_str(source):
    file = source.get("file", "?")
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

        token_sources = sources if sources else ["-"]
        proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + token_sources + child_flags,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stderr_chunks = []

        def _drain_stderr():
            stderr_chunks.append(proc.stderr.read())

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        for raw in proc.stdout:
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("kind") == "token":
                name = record.get("name", "?")
                lexeme = record.get("lexeme", "?")
                source = record.get("source", {})
                loc = _location_str(source)
                print(f"{loc} {name} '{lexeme}'", flush=True)
            elif record.get("kind") == "error":
                loc = _location_str(record.get("pos", {}))
                lexeme = record.get("lexeme", "?")
                message = record.get("message", "unrecognized character")
                print(f"{loc}: error: {message} '{lexeme}'", flush=True)

        stderr_thread.join()
        proc.wait()

        stderr_data = b"".join(stderr_chunks)
        if stderr_data:
            events = verbose.parse_child_events(stderr_data.decode("utf-8", errors="replace"))
            verbose.reformat_child_events(events)

        if proc.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})", file=sys.stderr)
            sys.exit(proc.returncode)
    finally:
        os.unlink(spec_path)

    verbose.emit(Events.FINISHED, message="done")
