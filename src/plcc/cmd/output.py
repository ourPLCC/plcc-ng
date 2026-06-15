import sys


def print_user_error(message):
    print(message, flush=True)


def print_version_line(version):
    print(f"plcc-ng {version}", flush=True)


def print_grammar_line(grammar_path, tool=None, language=None):
    print(f"grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)


def print_banner(version, grammar_path, tool=None, language=None):
    print(f"plcc-ng {version}", file=sys.stderr, flush=True)
    print(f"grammar: {grammar_path}", file=sys.stderr, flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", file=sys.stderr, flush=True)
