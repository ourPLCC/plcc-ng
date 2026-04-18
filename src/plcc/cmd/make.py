import contextlib
import enum
import json
import os
import re
import shutil
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [options] GRAMMAR

Arguments:
    GRAMMAR     Path to the PLCC grammar file.

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


class Events(enum.Enum):
    STARTED = "started"
    PHASE = "phase"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-make", Events, args)
    grammar = args['GRAMMAR']
    build_dir = 'build'

    verbose.emit(Events.STARTED, message=f"building {grammar}")

    # 1. Clean
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    # 2. Spec
    verbose.emit(Events.PHASE, message="spec")
    spec_json = os.path.join(build_dir, 'spec.json')
    _run_or_die(['plcc-spec', grammar] + child_flags, stdout_file=spec_json, verbose=verbose)

    # 3. LL(1)
    verbose.emit(Events.PHASE, message="ll1")
    ll1_json = os.path.join(build_dir, 'll1.json')
    _run_or_die(['plcc-ll1', spec_json] + child_flags, stdout_file=ll1_json, verbose=verbose)
    with open(ll1_json) as f:
        ll1 = json.load(f)
    if not ll1.get("is_ll1", True):
        _report_ll1_failure(ll1, ll1_json, verbose)
        sys.exit(1)

    # 4. Model
    verbose.emit(Events.PHASE, message="model")
    model_json = os.path.join(build_dir, 'model.json')
    _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)

    # 5 & 6. Emit and build per semantic section
    with open(spec_json) as f:
        spec = json.load(f)
    for section in spec.get('semantics', []):
        tool = section['tool']
        lang = section['language']
        try:
            validate_tool_name(tool)
        except ValueError as e:
            print(f"plcc-make: {e}", file=sys.stderr)
            sys.exit(1)
        output_dir = os.path.join(build_dir, tool)
        os.makedirs(output_dir, exist_ok=True)
        verbose.emit(Events.PHASE, message=f"emit {lang} -> {tool}")
        _run_or_die(
            ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'] + child_flags,
            stdin_file=model_json,
            verbose=verbose,
        )
        verbose.emit(Events.PHASE, message=f"build {lang} -> {tool}")
        _run_or_die(
            ['plcc-lang-build', f'--target={lang}', f'--output={output_dir}'] + child_flags,
            verbose=verbose,
        )

    verbose.emit(Events.FINISHED, message="done")


def validate_tool_name(name):
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _report_ll1_failure(ll1, path, verbose):
    print(
        f"plcc-make: error: grammar is not LL(1); see {path}",
        file=sys.stderr,
    )
    for conflict in ll1.get("conflicts", []):
        print(
            f"plcc-make: error: conflict at "
            f"{conflict.get('nonterminal', '?')} on "
            f"{conflict.get('lookahead', '?')}: "
            f"{conflict.get('competing', [])}",
            file=sys.stderr,
        )
    for cycle in ll1.get("left_recursion", []):
        print(
            f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}",
            file=sys.stderr,
        )


def _run_or_die(cmd, stdout_file=None, stdin_file=None, verbose=None):
    with contextlib.ExitStack() as stack:
        stdin = stack.enter_context(open(stdin_file)) if stdin_file else None
        stdout = stack.enter_context(open(stdout_file, 'w')) if stdout_file else None
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=subprocess.PIPE)
    if verbose and result.stderr:
        events = verbose.parse_child_events(result.stderr.decode("utf-8", errors="replace"))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-make: {cmd[0]} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
