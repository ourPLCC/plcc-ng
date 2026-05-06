import enum
import json
import os
import subprocess
import sys

from docopt import docopt, DocoptExit

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file (build/ is resolved from the current directory).
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    --tool=NAME         Semantic section to run (inferred if only one exists).
    -h --help           Show this message.
""" + VERBOSE_OPTIONS


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
        print("\nRun 'plcc-rep --help' for more information.", file=sys.stderr)
        sys.exit(1)
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    verbose.emit(Events.STARTED, message='starting rep')

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    if not os.path.exists(spec_path) or not os.path.exists(ll1_path):
        print('plcc-rep: build/ not found. Run plcc-make first.', file=sys.stderr)
        sys.exit(1)

    with open(spec_path) as f:
        spec = json.load(f)

    tool_name, language = _resolve_tool(spec, tool_name)
    tool_dir = os.path.join('build', tool_name)

    if not os.path.exists(tool_dir):
        print(f'plcc-rep: build/{tool_name}/ not found. Run plcc-make first.', file=sys.stderr)
        sys.exit(1)

    interpreter = subprocess.Popen(
        ['plcc-lang-run', f'--target={language}', f'--output={tool_dir}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    try:
        for src in sources:
            with open(src, 'rb') as f:
                chunk = f.read()
            _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)

        if not sources:
            interactive = sys.stdin.isatty()
            if interactive:
                while True:
                    try:
                        print('>>> ', end='', flush=True, file=sys.stderr)
                        line = sys.stdin.readline()
                        if not line:
                            break
                        chunk = line.encode()
                        _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)
                    except KeyboardInterrupt:
                        print(file=sys.stderr)
                        break
            else:
                chunk = sys.stdin.buffer.read()
                _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)
    finally:
        try:
            interpreter.stdin.close()
        except BrokenPipeError:
            pass
        interpreter.wait()

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
        print("plcc-rep: no semantic sections found. Run plcc-make first.", file=sys.stderr)
        sys.exit(1)

    if len(sections) == 1:
        return sections[0]['tool'], sections[0]['language']

    names = [s['tool'] for s in sections]
    print(f"plcc-rep: multiple semantic sections: {names}. Use --tool=NAME.", file=sys.stderr)
    sys.exit(1)


def _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format):
    tokens_proc = subprocess.Popen(
        ['plcc-tokens', spec_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tree_proc = subprocess.Popen(
        ['plcc-tree', f'--ll1={ll1_path}'],
        stdin=tokens_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tokens_proc.stdout.close()
    tokens_proc.stdin.write(chunk)
    tokens_proc.stdin.close()

    tree_out, tree_err = tree_proc.communicate()
    tokens_err = tokens_proc.stderr.read()
    tokens_proc.wait()

    if tokens_proc.returncode != 0 or tree_proc.returncode != 0:
        for msg in [tokens_err, tree_err]:
            if msg:
                sys.stderr.buffer.write(msg)
        return

    tree_line = tree_out.strip()
    if not tree_line:
        return

    try:
        interpreter.stdin.write(tree_line + b'\n')
        interpreter.stdin.flush()
    except BrokenPipeError:
        print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
        sys.exit(1)

    _read_response(interpreter.stdout, verbose_format)


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
        if 'kind' not in record:
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
