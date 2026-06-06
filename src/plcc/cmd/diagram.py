import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .output import print_version_line, print_grammar_line

__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --format=FMT            Diagram format [default: plantuml].
    --no-banner             Suppress the version and grammar banner.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


_SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if "--no-banner" not in argv:
        print_version_line(get_version())
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    no_banner = args["--no-banner"]
    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    grammar_file = args['--grammar']
    fmt = args['--format']

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--through=model', '--no-banner']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if not no_banner:
        print_grammar_line(os.path.abspath(read_grammar('build')))

    source_ext = _SOURCE_EXT.get(fmt, fmt)
    build_diagram_dir = os.path.join('build', 'diagram')
    os.makedirs(build_diagram_dir, exist_ok=True)
    diagram_source = os.path.join(build_diagram_dir, f'diagram.{source_ext}')
    diagram_image = os.path.join(build_diagram_dir, 'diagram.png')
    model_json = os.path.join('build', 'model.json')

    with open(model_json) as stdin_f, open(diagram_source, 'w') as stdout_f:
        emit_result = subprocess.run(
            ['plcc-diagram-emit', f'--format={fmt}'] + child_flags,
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
