import enum
import json
import os
import subprocess
import sys

from docopt import DocoptExit
from plcc.cli import parse_args

from plcc.verbose import VerboseContext, DIAGNOSTICS_OPTIONS
from plcc.version import get_version
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
from plcc.cmd.spec import SPEC_OPTION, validate_spec_flag, spec_flag_for_child
from .output import print_banner, print_user_error
from .source_runner import SourceRunner


def _location_str(source):
    file = source.get("file", "-")
    line = source.get("line", "?")
    col = source.get("column", "?")
    return f"{file}:{line}:{col}"


def _escape(s):
    return (s
            .replace('\\', '\\\\')
            .replace('\n', '\\n')
            .replace('\t', '\\t')
            .replace('\r', '\\r'))


def _print_candidates_table(attempts):
    if not attempts:
        return
    winner = next((a for a in attempts if a.get('winner')), None)
    if winner is None:
        return

    winner_len = winner['char_count']
    is_tie = sum(1 for a in attempts if a['char_count'] == winner_len) > 1

    rows = []
    for a in attempts:
        if a['char_count'] == 0:
            continue
        is_winner = a.get('winner', False)
        index_marker = '*' if (is_tie and is_winner) else ''
        len_marker = '*' if (not is_tie and is_winner) else ''
        rows.append({
            '#': str(a.get('rule_index', '?')) + index_marker,
            'Type': 'skip' if a.get('is_skip') else 'token',
            'Name': a['name'],
            'Pattern': f"'{a['regex']}'",
            'Len': str(a['char_count']) + len_marker,
            'Match': f"'{_escape(a['lexeme'])}'",
        })

    cols = ['#', 'Type', 'Name', 'Pattern', 'Len', 'Match']
    header = {c: c for c in cols}
    all_rows = [header] + rows
    widths = {c: max(len(r[c]) for r in all_rows) for c in cols}

    for r in all_rows:
        print('  '.join(r[c].ljust(widths[c]) for c in cols).rstrip(), flush=True)

    print('* longest match wins; ties broken by earliest rule (#)', flush=True)


def _render_record(record, show_skips, show_line, show_attempts):
    kind = record.get("kind")

    if kind == "error":
        loc = _location_str(record.get("source", {}))
        message = record.get("message", "unrecognized character")
        print_user_error(f"{loc}: error: {message}")
        return

    if kind == "skip" and not show_skips:
        return

    if kind not in ("token", "skip"):
        return

    source = record.get("source", {})
    loc = _location_str(source)
    name = record.get("name", "?")
    lexeme = record.get("lexeme", "?")
    pattern = record.get("regex", "?")
    source_line = record.get("source_line", "")
    attempts = record.get("attempts", [])
    col = source.get("column", 1)

    if not show_attempts:
        if kind == "skip":
            print(f"{loc} {name} '{lexeme}' SKIPPED", flush=True)
        else:
            print(f"{loc} {name} '{lexeme}'", flush=True)
        return

    print(f"Scanning {loc}:", flush=True)

    display_line = source_line.replace('\t', '→')
    if col - 1 >= len(display_line):
        display_line += '↵'
    print(display_line, flush=True)
    print(' ' * (col - 1) + '^', flush=True)

    print(flush=True)
    print("Candidates:", flush=True)
    _print_candidates_table(attempts)

    print(flush=True)
    print("Result:", flush=True)
    print(f"{kind} {name} '{pattern}' '{_escape(lexeme)}'", flush=True)
    print(flush=True)


__doc__ = """plcc-scan
    Tokenize source input and print tokens in human-readable format.

Usage:
    plcc-scan [-v ...] [options] [SOURCE ...]

Arguments:
    SOURCE      Source files to tokenize. Reads stdin if none given.

Options:
    -h --help                   Show this message.
""" + SPEC_OPTION + """\

Output:
    -t --trace                  Show detailed scanning output.
    -b --banner                 Show the version and spec banner on stderr.
""" + DIAGNOSTICS_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


class ScanHandler:
    def __init__(self, spec_path, tokens_flags):
        self._spec_path = spec_path
        self._tokens_flags = tokens_flags

    def feed(self, content, source, eof=False):
        proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path,
             f"--source-name={source}", "-"] + self._tokens_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        stdout, _ = proc.communicate(content)
        trace = "--trace" in self._tokens_flags
        for raw in stdout.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            if record.get("name") == "eof":
                continue
            _render_record(record, trace, trace, trace)
        if proc.returncode != 0:
            print(f"plcc-scan: plcc-tokens failed (exit {proc.returncode})",
                  file=sys.stderr)
            sys.exit(proc.returncode)
        return b""


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    try:
        args = parse_args(__doc__, argv)
    except DocoptExit as e:
        print(str(e), file=sys.stderr)
        print(file=sys.stderr)
        print("Run 'plcc-scan --help' for more information.", file=sys.stderr)
        sys.exit(1)

    banner = args["--banner"]
    verbose = VerboseContext.from_args("plcc-scan", Events, args)
    sources = args["SOURCE"]
    trace = args["--trace"]

    validate_spec_flag('plcc-scan', args)

    verbose.emit(Events.STARTED, message="scanning")
    child_flags = verbose.child_flags()

    make_result = subprocess.run(
        ["plcc-make", "--through=scan"]
        + spec_flag_for_child(args)
        + child_flags,
        stderr=None,
    )
    if make_result.returncode != 0:
        sys.exit(make_result.returncode)

    if banner:
        print_banner(get_version(), os.path.abspath(read_spec(OUTPUT_DIR)))

    spec_path = os.path.join(OUTPUT_DIR, "spec.json")
    tokens_flags = child_flags + (["--trace"] if trace else [])

    handler = ScanHandler(spec_path=spec_path, tokens_flags=tokens_flags)
    runner = SourceRunner()
    runner.run(sources, handler)

    verbose.emit(Events.FINISHED, message="done")
