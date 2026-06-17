import sys


def print_user_error(message):
    print(message, flush=True)


def print_banner(version, grammar_path, language=None):
    print(f"plcc-ng {version}", file=sys.stderr, flush=True)
    print(f"spec: {grammar_path}", file=sys.stderr, flush=True)
    if language is not None:
        print(f"Running {language}.", file=sys.stderr, flush=True)
