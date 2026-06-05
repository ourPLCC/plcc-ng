import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.grammar import read_grammar
from .pipeline import TreePipeline, print_parse_error
from .output import print_version_line, print_grammar_line, print_user_error
from .source_runner import SourceRunner, SubmitOn

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to grammar.plcc on first use.
    --tool=NAME             Semantic section to run (inferred if only one exists).
    --no-banner             Suppress the version and grammar banner.
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


class RepHandler:
    def __init__(self, spec_path, ll1_path, interpreter, verbose_format,
                 child_flags=None, verbose=None):
        self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, verbose=verbose)
        self._interpreter = interpreter
        self._verbose_format = verbose_format

    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return False
        for record, raw in items:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-rep")
                break
            elif record.get("kind") == "tree":
                try:
                    self._interpreter.stdin.write(raw + b'\n')
                    self._interpreter.stdin.flush()
                except BrokenPipeError:
                    print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
                    sys.exit(1)
                _read_response(self._interpreter.stdout, self._interpreter, self._verbose_format)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    _opts = argv[:argv.index("--")] if "--" in argv else argv
    if "--no-banner" not in _opts:
        print_version_line(get_version())
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)
    no_banner = args["--no-banner"]
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    grammar_file = args['--grammar']
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    if grammar_file is not None and not os.path.exists(grammar_file):
        print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message='starting')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', '--no-banner']
        + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
        + child_flags,
        stderr=subprocess.PIPE,
    )
    if make_result.stderr:
        events = verbose.parse_child_events(make_result.stderr.decode('utf-8', errors='replace'))
        verbose.reformat_child_events(events)
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    with open(spec_path) as f:
        spec = json.load(f)

    tool_name, language = _resolve_tool(spec, tool_name)
    if not no_banner:
        print_grammar_line(
            os.path.abspath(read_grammar('build')),
            tool=tool_name,
            language=language,
        )
    tool_dir = os.path.join('build', tool_name)

    interpreter = subprocess.Popen(
        ['plcc-lang-run', f'--target={language}', f'--output={tool_dir}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    completed = True
    try:
        handler = RepHandler(
            spec_path=spec_path,
            ll1_path=ll1_path,
            interpreter=interpreter,
            verbose_format=verbose_format,
            child_flags=child_flags,
            verbose=verbose,
        )
        runner = SourceRunner(submit_on=SubmitOn.EOF)
        completed = runner.run(sources, handler)
    finally:
        try:
            interpreter.stdin.close()
        except BrokenPipeError:
            pass
        interpreter.wait()

    if not completed:
        sys.exit(1)
    verbose.emit(Events.FINISHED, message='done')


def _resolve_tool(spec, tool_name):
    sections = spec.get('semantics', [])
    if tool_name:
        for s in sections:
            if s['tool'] == tool_name:
                return s['tool'], s['language']
        print(f"plcc-rep: no semantic section with tool '{tool_name}'", file=sys.stderr)
        sys.exit(1)

    if len(sections) == 0:
        print("plcc-rep: no semantic sections found in grammar.", file=sys.stderr)
        sys.exit(1)

    if len(sections) == 1:
        return sections[0]['tool'], sections[0]['language']

    names = [s['tool'] for s in sections]
    print(f"plcc-rep: multiple semantic sections: {names}. Use --tool=NAME.", file=sys.stderr)
    sys.exit(1)


def _read_response(stdout, interpreter, verbose_format):
    while True:
        raw = stdout.readline()
        if not raw:
            rc = interpreter.poll()
            if rc is not None and (rc < 0 or rc == 130):
                sys.exit(130)
            print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
            sys.exit(1)
        line = raw.decode('utf-8', errors='replace').rstrip('\n')
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(line)
            continue
        if not isinstance(record, dict) or 'kind' not in record:
            print(line)
            continue
        _render_record(record, verbose_format)
        return


def _render_record(record, verbose_format):
    if verbose_format == 'json':
        print(json.dumps(record))
        return
    if record['kind'] == 'result':
        value = record.get('value')
        if value is not None:
            print(value)
    elif record['kind'] == 'error':
        print_user_error(f"error: {record.get('type')}: {record.get('message')}")
