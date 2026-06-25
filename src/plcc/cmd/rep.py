import enum
import json
import os
import subprocess
import sys

from docopt import DocoptExit
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from plcc.version import get_version
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
from .pipeline import TreePipeline, print_parse_error, split_committed
from .output import print_banner, print_user_error
from .source_runner import SourceRunner

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC spec.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
""" + SPEC_OPTION + """\
    -b --banner             Show the version and spec banner on stderr.
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
            return b"" if eof else content
        dispatch, remainder = split_committed(items, content, eof)
        for record, raw in dispatch:
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
        return remainder


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_args(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)
    banner = args["--banner"]
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    sources = args['SOURCE']
    verbose_format = args['--verbose-format'] or 'text'

    validate_spec_flag('plcc-rep', args)

    verbose.emit(Events.STARTED, message='starting')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make']
        + spec_flag_for_child(args)
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

    language = _resolve_language(spec)
    try:
        _validate_language_name(language)
    except ValueError as e:
        print(f"plcc-rep: {e}", file=sys.stderr)
        sys.exit(1)
    if banner:
        print_banner(
            get_version(),
            os.path.abspath(read_spec('build')),
            language=language,
        )
    output_dir = os.path.join('build', language)

    interpreter = subprocess.Popen(
        ['plcc-lang-run', f'--target={language}', f'--output={output_dir}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    try:
        handler = RepHandler(
            spec_path=spec_path,
            ll1_path=ll1_path,
            interpreter=interpreter,
            verbose_format=verbose_format,
            child_flags=child_flags,
            verbose=verbose,
        )
        runner = SourceRunner()
        runner.run(sources, handler)
    finally:
        try:
            interpreter.stdin.close()
        except BrokenPipeError:
            pass
        interpreter.wait()

    verbose.emit(Events.FINISHED, message='done')


def _validate_language_name(name):
    if not name or '..' in name or '/' in name or '\\' in name:
        raise ValueError(
            f"Invalid language name '{name}'. "
            "Language names must not contain path separators."
        )


def _resolve_language(spec):
    section = spec.get('semantics')
    if not section:
        print("plcc-rep: no semantic section found in spec.", file=sys.stderr)
        sys.exit(1)
    return section['language']


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
