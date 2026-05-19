import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
from .source_runner import SourceRunner, SubmitOn

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    --grammar-file=<path>   Path to the PLCC grammar file [default: grammar.plcc].
    --tool=NAME             Semantic section to run (inferred if only one exists).
    -h --help               Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def _location_str(source):
    """Return 'file:line:col' for real files, '-:line:col' for stdin, or None if no location."""
    file = source.get("file", "")
    line = source.get("line")
    col = source.get("column")
    if line is None or col is None:
        return None
    if file and file not in ("-", "<stdin>", ""):
        return f"{file}:{line}:{col}"
    return f"-:{line}:{col}"


class RepHandler:
    def __init__(self, spec_path, ll1_path, interpreter, verbose_format,
                 child_flags=None):
        self._spec_path = spec_path
        self._ll1_path = ll1_path
        self._interpreter = interpreter
        self._verbose_format = verbose_format
        self._child_flags = child_flags or []

    def feed(self, content, source, eof=False):
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tree_proc = subprocess.Popen(
            ["plcc-trees", f"--ll1={self._ll1_path}"] + self._child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(content)
        tokens_proc.stdin.close()
        tree_out, _ = tree_proc.communicate()
        tokens_proc.wait()

        records = []
        raw_lines = []
        for raw in tree_out.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            records.append(json.loads(raw))
            raw_lines.append(raw)

        if not records:
            return False

        any_tree = any(r.get("kind") == "tree" for r in records)
        any_genuine_error = any(
            r.get("kind") == "error" and r.get("found") != "eof"
            for r in records
        )
        only_eof_errors = not any_tree and not any_genuine_error

        if only_eof_errors and not eof:
            return False

        for record, raw in zip(records, raw_lines):
            if record.get("kind") == "error":
                src = record.get("source", {})
                message = record.get("message", "error")
                loc = _location_str(src)
                if loc:
                    print(f"{loc}: error: {message}", file=sys.stderr)
                else:
                    stage = record.get("stage", "plcc-rep")
                    print(f"{stage}: error: {message}", file=sys.stderr)
            elif record.get("kind") == "tree":
                try:
                    self._interpreter.stdin.write(raw + b'\n')
                    self._interpreter.stdin.flush()
                except BrokenPipeError:
                    print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
                    sys.exit(1)
                _read_response(self._interpreter.stdout, self._verbose_format)
        return True


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = docopt(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    grammar_file = args['--grammar-file']
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    if not os.path.exists(grammar_file):
        print(f"plcc-rep: grammar file not found: {grammar_file}", file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)

    verbose.emit(Events.STARTED, message=f'starting rep with {grammar_file}')
    child_flags = verbose.child_flags_for_orchestrator(min_level=0)

    make_result = subprocess.run(
        ['plcc-make', f'--grammar-file={grammar_file}'] + child_flags,
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


def _read_response(stdout, verbose_format):
    while True:
        raw = stdout.readline()
        if not raw:
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
        print(f"error: {record.get('type')}: {record.get('message')}", file=sys.stderr)
