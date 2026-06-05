def print_user_error(message):
    print(message, flush=True)


def print_version_line(version):
    print(f"plcc-ng {version}", flush=True)


def print_grammar_line(grammar_path, tool=None, language=None):
    print(f"grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)
