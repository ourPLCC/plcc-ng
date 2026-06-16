# src/plcc/cmd/spec.py
import os
import sys

from plcc.build.spec import DEFAULT_SPEC_FILE

SPEC_OPTION = f"""\
    -s <path> --spec=<path>
                            Spec to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_SPEC_FILE} on first use.
"""


def validate_spec_flag(cmd_name, args):
    path = args['--spec']
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: spec file not found: {path}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Run '{cmd_name} --help' for more information.", file=sys.stderr)
        sys.exit(1)


def spec_flag_for_child(args):
    path = args['--spec']
    return [f'--spec={path}'] if path is not None else []
