import enum
import os
import subprocess
import sys

from docopt import DocoptExit
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.spec import read_spec, resolve_spec_path
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag
from plcc.cmd.output import print_banner

__doc__ = """plcc-diagram-syntax
    Generate and display a syntax grammar diagram from a PLCC spec file.

Usage:
    plcc-diagram-syntax [-v ...] [options]

Options:
""" + SPEC_OPTION + """\
    --format=FMT            Diagram format [default: plantuml].
    -b --banner             Show the version and spec banner on stderr.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


_SOURCE_EXT = {'plantuml': 'puml'}


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_args(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram-syntax --help' for more information.", file=sys.stderr)
        sys.exit(1)

    banner = args["--banner"]
    fmt = args['--format']

    validate_spec_flag('plcc-diagram-syntax', args)

    spec_path = resolve_spec_path(args['--spec'], read_spec('build'))
    if not os.path.exists(spec_path):
        print(f"plcc-diagram-syntax: spec file not found: {spec_path}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram-syntax --help' for more information.", file=sys.stderr)
        sys.exit(1)

    spec_path = os.path.abspath(spec_path)

    verbose = VerboseContext.from_args("plcc-diagram-syntax", Events, args)
    verbose.emit(Events.STARTED, message="generating syntax diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    spec_result = subprocess.run(
        ['plcc-spec', spec_path] + child_flags,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if spec_result.stderr:
        events = verbose.parse_child_events(spec_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if spec_result.returncode != 0:
        sys.exit(spec_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(spec_path))

    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'syntax.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'syntax.png')

    with open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', '--type=syntax', f'--format={fmt}'] + child_flags,
            input=spec_result.stdout, stdout=stdout_f, stderr=subprocess.PIPE,
        )
    if emit_result.stderr:
        events = verbose.parse_child_events(emit_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if emit_result.returncode != 0:
        sys.exit(emit_result.returncode)

    build_result = subprocess.run(
        ['plcc-diagram-build', f'--format={fmt}',
         f'--input={diagram_source}',
         f'--output={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if build_result.stderr:
        events = verbose.parse_child_events(build_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if build_result.returncode != 0:
        sys.exit(build_result.returncode)

    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}', f'--input={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.stderr:
        events = verbose.parse_child_events(run_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
