import enum
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram
    Generate and display a class diagram from a PLCC grammar file.

Usage:
    plcc-diagram [-v ...] [options]

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --format=FMT            Diagram format [default: plantuml].
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


_SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}


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
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    grammar_file = args['--grammar']
    fmt = args['--format']

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-diagram: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-diagram --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message="generating diagram")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ['plcc-make', '--through=model']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        sys.stderr.buffer.write(make_result.stderr)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

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
        sys.stderr.buffer.write(emit_result.stderr)
    if emit_result.returncode != 0:
        sys.exit(emit_result.returncode)

    build_result = subprocess.run(
        ['plcc-diagram-build', f'--format={fmt}',
         f'--input={diagram_source}',
         f'--output={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if build_result.stderr:
        sys.stderr.buffer.write(build_result.stderr)
    if build_result.returncode != 0:
        sys.exit(build_result.returncode)

    run_result = subprocess.run(
        ['plcc-diagram-run', f'--format={fmt}', f'--input={diagram_image}'] + child_flags,
        stderr=subprocess.PIPE,
    )
    if run_result.stderr:
        sys.stderr.buffer.write(run_result.stderr)
    if run_result.returncode != 0:
        sys.exit(run_result.returncode)

    verbose.emit(Events.FINISHED, message="done")
