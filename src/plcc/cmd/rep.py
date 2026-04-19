import enum
import json
import os
import shutil
import subprocess
import sys
import tempfile

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file.
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    --tool=NAME     Semantic section to run [default: Java].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    grammar = args["GRAMMAR"]
    sources = args["SOURCE"]
    tool_name = args["--tool"]

    verbose.emit(Events.STARTED, message=f"rep with {grammar}, tool={tool_name}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        spec_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        ll1_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        model_path = f.name
    build_dir = tempfile.mkdtemp(prefix="plcc-rep-build-")
    try:
        # plcc-spec
        _run_child(["plcc-spec", grammar] + child_flags, stdout_file=spec_path, verbose=verbose, label="plcc-spec")
        # plcc-ll1
        _run_child_with_stdin(["plcc-ll1"] + child_flags, stdin_file=spec_path, verbose=verbose, label="plcc-ll1", stdout_file=ll1_path)
        # plcc-model
        _run_child(["plcc-model", spec_path] + child_flags, stdout_file=model_path, verbose=verbose, label="plcc-model")

        # Resolve tool -> language
        with open(spec_path) as f:
            spec = json.load(f)
        lang, tool_dir = _resolve_tool(spec, tool_name, build_dir)

        # Emit and build
        os.makedirs(tool_dir, exist_ok=True)
        _run_child_with_stdin(
            ["plcc-lang-emit", f"--target={lang}", f"--output={tool_dir}"] + child_flags,
            stdin_file=model_path, verbose=verbose, label="plcc-lang-emit",
        )
        _run_child(
            ["plcc-lang-build", f"--target={lang}", f"--output={tool_dir}"] + child_flags,
            stdout_file=None, verbose=verbose, label="plcc-lang-build",
        )

        # Build input
        input_data = b""
        for src in sources:
            with open(src, "rb") as sf:
                input_data += sf.read()
        if not sources:
            input_data = sys.stdin.buffer.read()

        # plcc-tokens | plcc-tree | plcc-lang-run
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
        run_proc = subprocess.Popen(
            ["plcc-lang-run", f"--target={lang}", f"--output={tool_dir}"] + child_flags,
            stdin=tree_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tree_proc.stdout.close()

        tokens_proc.stdin.write(input_data)
        tokens_proc.stdin.close()

        run_out, run_err = run_proc.communicate()
        tree_out, tree_err = tree_proc.communicate()
        tokens_out, tokens_err = tokens_proc.communicate()

        # Reformat child verbose output
        for stderr_bytes in (tokens_err, tree_err, run_err):
            if stderr_bytes:
                events = verbose.parse_child_events(stderr_bytes.decode("utf-8", errors="replace"))
                verbose.reformat_child_events(events)

        if tokens_proc.returncode != 0:
            print(f"plcc-rep: plcc-tokens failed (exit {tokens_proc.returncode})", file=sys.stderr)
            sys.exit(tokens_proc.returncode)
        if tree_proc.returncode != 0:
            print(f"plcc-rep: plcc-tree failed (exit {tree_proc.returncode})", file=sys.stderr)
            sys.exit(tree_proc.returncode)
        if run_proc.returncode != 0:
            print(f"plcc-rep: plcc-lang-run failed (exit {run_proc.returncode})", file=sys.stderr)
            sys.exit(run_proc.returncode)

        sys.stdout.buffer.write(run_out)
        sys.stdout.flush()

    finally:
        for p in (spec_path, ll1_path, model_path):
            if os.path.exists(p):
                os.unlink(p)
        shutil.rmtree(build_dir, ignore_errors=True)

    verbose.emit(Events.FINISHED, message="done")


def _run_child(cmd, stdout_file, verbose, label):
    if stdout_file is not None:
        with open(stdout_file, "w") as out:
            result = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE)
    else:
        result = subprocess.run(cmd, stderr=subprocess.PIPE)
    if result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-rep: {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _run_child_with_stdin(cmd, stdin_file, verbose, label, stdout_file=None):
    with open(stdin_file) as f:
        if stdout_file is not None:
            with open(stdout_file, "w") as out:
                result = subprocess.run(cmd, stdin=f, stdout=out, stderr=subprocess.PIPE)
        else:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE)
    if result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-rep: {label} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _resolve_tool(spec, tool_name, build_dir):
    for section in spec.get("semantics", []):
        if section["tool"] == tool_name:
            return section["language"], os.path.join(build_dir, tool_name)
    print(f"plcc-rep: no semantic section with tool '{tool_name}' found", file=sys.stderr)
    sys.exit(1)
