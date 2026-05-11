import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS, reap_pipeline

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

    # Build input
    chunks = []
    for src in sources:
        if src == '-':
            chunks.append(sys.stdin.buffer.read())
        else:
            with open(src, "rb") as sf:
                chunks.append(sf.read())
    if not sources:
        chunks.append(sys.stdin.buffer.read())
    input_data = b"".join(chunks)

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
        if tree.get("kind") == "error":
            verbose.reformat_child_events([{
                "stage": tree.get("stage", "plcc-tokens"),
                "event": "error",
                "severity": "error",
                "pos": tree.get("pos", {}),
                "message": tree.get("message", "error"),
            }])
            sys.exit(1)
        _print_tree(tree, indent=0)

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
