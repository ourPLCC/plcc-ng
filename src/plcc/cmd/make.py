"""plcc-make
    Build a PLCC project from a grammar file.

Usage:
    plcc-make GRAMMAR

Arguments:
    GRAMMAR     Path to the PLCC grammar file.

Options:
    -h --help   Show this message.
"""

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys

from docopt import docopt

_TOOL_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    grammar = args['GRAMMAR']
    build_dir = 'build'

    # 1. Clean
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    # 2. Spec
    spec_json = os.path.join(build_dir, 'spec.json')
    _run_or_die(['plcc-spec', grammar], stdout_file=spec_json)

    # 3. Model
    model_json = os.path.join(build_dir, 'model.json')
    _run_or_die(['plcc-model', spec_json], stdout_file=model_json)

    # 4 & 5. Emit and build per semantic section
    with open(spec_json) as f:
        spec = json.load(f)
    for section in spec.get('semantics', []):
        tool = section['tool']
        lang = section['language']
        try:
            validate_tool_name(tool)
        except ValueError as e:
            print(f"plcc-make: {e}", file=sys.stderr)
            sys.exit(1)
        output_dir = os.path.join(build_dir, tool)
        os.makedirs(output_dir, exist_ok=True)
        # Phase 1: --semantics is not forwarded to plcc-lang-emit.
        # See architectural spec §10.1. Phase 2 wires up --semantics.
        _run_or_die(
            ['plcc-lang-emit', f'--target={lang}', f'--output={output_dir}'],
            stdin_file=model_json,
        )
        _run_or_die(['plcc-lang-build', f'--target={lang}', f'--output={output_dir}'])


def validate_tool_name(name):
    """Raise ValueError if tool name could escape build/."""
    if not name or not _TOOL_NAME_RE.match(name):
        raise ValueError(
            f"Invalid tool name '{name}'. "
            "Tool names must match [a-zA-Z0-9_-]+ to prevent path traversal."
        )


def _run_or_die(cmd, stdout_file=None, stdin_file=None):
    with contextlib.ExitStack() as stack:
        stdin = stack.enter_context(open(stdin_file)) if stdin_file else None
        stdout = stack.enter_context(open(stdout_file, 'w')) if stdout_file else None
        # stderr passes through to terminal so the failing tool's message is visible
        result = subprocess.run(cmd, stdin=stdin, stdout=stdout)
    if result.returncode != 0:
        print(f"plcc-make: {cmd[0]} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
