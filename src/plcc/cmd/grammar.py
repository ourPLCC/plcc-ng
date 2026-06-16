import os
import sys

from plcc.build.grammar import DEFAULT_GRAMMAR_FILE

GRAMMAR_OPTION = f"""\
    -g <path> --grammar=<path>
                            Grammar to build from. Once set, remembered for subsequent
                            commands until changed. Defaults to {DEFAULT_GRAMMAR_FILE} on first use.
"""


def validate_grammar_flag(cmd_name, args):
    path = args['--grammar']
    if path is not None and not os.path.exists(path):
        print(f"{cmd_name}: grammar file not found: {path}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Run '{cmd_name} --help' for more information.", file=sys.stderr)
        sys.exit(1)


def grammar_flag_for_child(args):
    path = args['--grammar']
    return [f'--grammar={path}'] if path is not None else []
