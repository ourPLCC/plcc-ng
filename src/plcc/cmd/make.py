import contextlib
import enum
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.build.staleness import (
    compute_hash, read_sentinel, write_sentinel, delete_sentinel, is_current,
)
from plcc.build.spec import read_spec, write_spec, resolve_spec_path
from plcc.cmd.spec import SPEC_OPTION
from plcc.ll1.format_conflict_message import format_conflict_message
from plcc.version import get_version
from .output import print_banner

__doc__ = """plcc-make
    Build a PLCC project from a spec file.

Usage:
    plcc-make [-v ...] [options]

Options:
""" + SPEC_OPTION + """\
    --through=<level>       Build up to this level: scan, parse, model, or all [default: all].
    -b --banner             Show the version and spec banner on stderr.
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

    banner = args["--banner"]
    verbose = VerboseContext.from_args("plcc-make", Events, args)
    explicit_spec = args['--spec']
    through = args['--through']
    build_dir = Path('build')

    stored_spec = read_spec(build_dir) if build_dir.is_dir() else None

    spec = resolve_spec_path(explicit_spec, stored_spec)

    if through not in ('scan', 'parse', 'model', 'all'):
        print(
            f"plcc-make: invalid --through value '{through}'; "
            "must be scan, parse, model, or all",
            file=sys.stderr,
        )
        sys.exit(1)

    if explicit_spec is None and stored_spec is not None and not os.path.exists(spec):
        print(f"plcc-make: spec file not found: {spec}", file=sys.stderr)
        print(
            "(the active spec was set by a previous run; "
            "use --spec to specify a different one)",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.exists(spec):
        print(f"plcc-make: spec file not found: {spec}", file=sys.stderr)
        sys.exit(1)

    if banner:
        print_banner(get_version(), os.path.abspath(spec))

    if (
        explicit_spec is not None
        and stored_spec is not None
        and explicit_spec != stored_spec
    ):
        shutil.rmtree(build_dir)
        build_dir.mkdir()

    verbose.emit(Events.STARTED, message=f"spec: {spec}")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    build_dir.mkdir(exist_ok=True)
    write_spec(build_dir, spec)

    # Run plcc-spec into a temp file to avoid corrupting build/spec.json on failure.
    # Temp file lives inside build/ so os.replace() is guaranteed atomic (same filesystem).
    verbose.emit(Events.PHASE, message="spec")
    tmp_fd, tmp_spec = tempfile.mkstemp(suffix='.json', dir=build_dir)
    os.close(tmp_fd)
    try:
        with open(tmp_spec, 'w') as spec_out:
            result = subprocess.run(
                ['plcc-spec', spec] + child_flags,
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
    tool_stages = set()  # semantics is now a single SemanticSpec | None, no tool stages

    _REQUIRED = {
        'scan':  {'scan'},
        'parse': {'scan', 'parse'},
        'model': {'scan', 'model'},
        'all':   {'scan', 'parse', 'model'} | tool_stages,
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
            _report_ll1_failure(ll1)
            sys.exit(1)

    if through in ('model', 'all'):
        verbose.emit(Events.PHASE, message="model")
        model_json = str(build_dir / 'model.json')
        _run_or_die(['plcc-model', spec_json] + child_flags, stdout_file=model_json, verbose=verbose)

    if through == 'all':
        _sem = spec_data.get('semantics')
        _sections = [_sem] if _sem is not None else []
        for section in _sections:
            tool = section.get('tool')
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

    write_sentinel(build_dir, new_hash, required_stages)
    verbose.emit(Events.FINISHED, message="done")


def validate_tool_name(name):
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _report_ll1_failure(ll1):
    print("plcc-make: error: grammar is not LL(1)", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print("", file=sys.stderr)
        print(format_conflict_message(conflict), file=sys.stderr)
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
