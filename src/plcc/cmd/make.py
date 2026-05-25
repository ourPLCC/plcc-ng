import contextlib
import enum
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.build.staleness import (
    compute_hash, read_sentinel, write_sentinel, delete_sentinel, is_current,
)

__doc__ = """plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make [-v ...] [options]

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --through=<level>       Build up to this level: scan, parse, diagram, or all [default: all].
    --diagram-format=FMT    Diagram format when using --through=diagram or --through=all [default: plantuml].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


class Events(enum.Enum):
    STARTED = "started"
    PHASE = "phase"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-make --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-make", Events, args)
    grammar = args['--grammar-file']
    through = args['--through']
    diagram_fmt = args['--diagram-format'] or 'plantuml'
    build_dir = Path('build')

    if through not in ('scan', 'parse', 'diagram', 'all'):
        print(
            f"plcc-make: invalid --through value '{through}'; "
            "must be scan, parse, diagram, or all",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(grammar):
        print(f"plcc-make: grammar file not found: {grammar}", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f"building {grammar}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    build_dir.mkdir(exist_ok=True)

    # Run plcc-spec into a temp file to avoid corrupting build/spec.json on failure.
    # Temp file lives inside build/ so os.replace() is guaranteed atomic (same filesystem).
    verbose.emit(Events.PHASE, message="spec")
    tmp_fd, tmp_spec = tempfile.mkstemp(suffix='.json', dir=build_dir)
    os.close(tmp_fd)
    try:
        with open(tmp_spec, 'w') as spec_out:
            result = subprocess.run(
                ['plcc-spec', grammar] + child_flags,
                stdout=spec_out,
                stderr=subprocess.PIPE,
            )
        if result.stderr:
            events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
            verbose.reformat_child_events(events)
        if result.returncode != 0:
            os.unlink(tmp_spec)
            delete_sentinel(build_dir)
            print(f"plcc-make: plcc-spec failed (exit {result.returncode})", file=sys.stderr)
            sys.exit(result.returncode)
    except Exception:
        if os.path.exists(tmp_spec):
            os.unlink(tmp_spec)
        delete_sentinel(build_dir)
        raise

    new_hash = compute_hash(tmp_spec)
    sentinel = read_sentinel(build_dir)

    with open(tmp_spec) as f:
        spec_data = json.load(f)
    tool_stages = {s['tool'] for s in spec_data.get('semantics', [])}

    _REQUIRED = {
        'scan':    {'scan'},
        'parse':   {'scan', 'parse'},
        'diagram': {'scan', 'model', 'diagram'},
        'all':     {'scan', 'parse', 'model'} | tool_stages,
    }
    required_stages = _REQUIRED[through]

    if is_current(sentinel, new_hash, required_stages):
        os.unlink(tmp_spec)
        verbose.emit(Events.FINISHED, message="build is current")
        return

    # Slow path: replace spec atomically, delete sentinel, run downstream steps
    os.replace(tmp_spec, build_dir / 'spec.json')
    spec_json = str(build_dir / 'spec.json')
    model_json = None
    delete_sentinel(build_dir)  # absent until final success write below

    if through in ('parse', 'all'):
        verbose.emit(Events.PHASE, message="ll1")
        ll1_json = str(build_dir / 'll1.json')
        _run_or_die(['plcc-ll1'] + child_flags, stdin_file=spec_json, stdout_file=ll1_json, verbose=verbose)
        with open(ll1_json) as f:
            ll1 = json.load(f)
        if not ll1.get("is_ll1", True):
            _report_ll1_failure(ll1, ll1_json)
            sys.exit(1)

    if through in ('diagram', 'all'):
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)

    if through == 'all':
        for section in spec_data.get('semantics', []):
            tool = section['tool']
            lang = section['language']
            try:
                validate_tool_name(tool)
            except ValueError as e:
                print(f"plcc-make: {e}", file=sys.stderr)
                delete_sentinel(build_dir)
                sys.exit(1)
            output_dir = str(build_dir / tool)
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

    if through in ('diagram', 'all'):
        verbose.emit(Events.PHASE, message="diagram emit")
        (build_dir / 'diagram').mkdir(exist_ok=True)
        required = (through == 'diagram')
        diagram_ok = _run_or_die(
            ['plcc-diagram-emit', f'--format={diagram_fmt}'] + child_flags,
            stdin_file=model_json,
            stdout_file=str(build_dir / 'diagram' / 'diagram.mmd'),
            verbose=verbose,
            required=required,
        )
        if diagram_ok:
            verbose.emit(Events.PHASE, message="diagram build")
            diagram_ok = _run_or_die(
                ['plcc-diagram-build', f'--format={diagram_fmt}',
                 f'--input={build_dir / "diagram" / "diagram.mmd"}',
                 f'--output={build_dir / "diagram" / "diagram.png"}'] + child_flags,
                verbose=verbose,
                required=required,
            )
        if diagram_ok:
            required_stages = required_stages | {'diagram'}
        else:
            print("plcc-make: diagram generation skipped", file=sys.stderr)

    write_sentinel(build_dir, new_hash, required_stages)
    verbose.emit(Events.FINISHED, message="done")


def validate_tool_name(name):
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _report_ll1_failure(ll1, path):
    print(f"plcc-make: error: grammar is not LL(1); see {path}", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print(
            f"plcc-make: error: conflict at "
            f"{conflict.get('nonterminal', '?')} on "
            f"{conflict.get('lookahead', '?')}: "
            f"{conflict.get('productions', [])}",
            file=sys.stderr,
        )
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)


def _run_or_die(cmd, stdout_file=None, stdin_file=None, verbose=None, required=True):
    with contextlib.ExitStack() as stack:
        stdin = stack.enter_context(open(stdin_file)) if stdin_file else None
        stdout = stack.enter_context(open(stdout_file, 'w')) if stdout_file else None
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=subprocess.PIPE)
    if verbose and result.stderr:
        events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if result.returncode != 0:
        print(f"plcc-make: {cmd[0]} failed (exit {result.returncode})", file=sys.stderr)
        if required:
            sys.exit(result.returncode)
        return False
    return True
