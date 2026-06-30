import enum
import os
import subprocess
import sys

from docopt import DocoptExit
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
from plcc.cmd.output import print_banner

__doc__ = """plcc-diagram-class
    Generate and display a class diagram from a PLCC spec file.

Usage:
    plcc-diagram-class [-v ...] [options]

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
        print("Run 'plcc-diagram-class --help' for more information.", file=sys.stderr)
        sys.exit(1)

    banner = args["--banner"]
    fmt = args['--format']

    validate_spec_flag('plcc-diagram-class', args)

    verbose = VerboseContext.from_args("plcc-diagram-class", Events, args)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--through=model']
        + spec_flag_for_child(args)
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(read_spec(OUTPUT_DIR)))

    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join(OUTPUT_DIR, 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'class.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'class.png')
    model_json = os.path.join(OUTPUT_DIR, 'model.json')

    with open(model_json) as stdin_f, open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', '--type=class', f'--format={fmt}'] + child_flags,
            stdin=stdin_f, stdout=stdout_f, stderr=subprocess.PIPE,
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
