import enum
import json
import os
import subprocess
import sys
import tempfile

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS, reap_pipeline

__doc__ = """plcc-parse
    Parse source input and print parse tree in human-readable format.

Usage:
    plcc-parse [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to parse. Reads stdin if none given.

Options:
    -h --help   Show this message.
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


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-parse", Events, args)
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]

    verbose.emit(Events.STARTED, message=f"parsing with {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    spec_path = tempfile.mktemp(suffix=".json")
    ll1_path = tempfile.mktemp(suffix=".json")
    try:
        # plcc-spec
        _run_child(["plcc-spec", grammar] + child_flags, stdout_file=spec_path, verbose=verbose, label="plcc-spec")
        # plcc-ll1
        _run_child(["plcc-ll1"] + child_flags, stdin_file=spec_path, stdout_file=ll1_path, verbose=verbose, label="plcc-ll1")

        # Build input
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens | plcc-tree
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", spec_path] + child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tree_proc = subprocess.Popen(
            ["plcc-tree", f"--ll1={ll1_path}"] + child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(input_data)
        tokens_proc.stdin.close()

        tree_out, tree_err = tree_proc.communicate()
        tokens_err = tokens_proc.stderr.read()
        tokens_proc.wait()
        tokens_proc.stderr_captured = tokens_err
        tree_proc.stderr_captured = tree_err

        result = reap_pipeline([
            (tokens_proc, "plcc-tokens"),
            (tree_proc, "plcc-tree"),
        ])
        verbose.reformat_child_events(result.events_to_render)
        if result.failed_stage:
            sys.exit(result.exit_code)

        # Print tree in human-readable format
        for line in tree_out.decode("utf-8").splitlines():
            if not line.strip():
                continue
            tree = json.loads(line)
            _print_tree(tree, indent=0)
    finally:
        for p in (spec_path, ll1_path):
            if os.path.exists(p):
                os.unlink(p)

    verbose.emit(Events.FINISHED, message="done")


def _run_child(cmd, stdout_file, verbose, label, stdin_file=None):
    with open(stdout_file, "w") as out:
        stdin = open(stdin_file) if stdin_file else None
        result = subprocess.run(cmd, stdin=stdin, stdout=out, stderr=subprocess.PIPE)
        if stdin:
            stdin.close()
    if result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-parse: {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


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
