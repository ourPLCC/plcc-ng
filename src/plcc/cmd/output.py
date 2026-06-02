def print_user_error(message):
    print(message, flush=True)


def print_startup_banner(grammar_path, version, tool=None, language=None):
    print(f"plcc-ng {version}  grammar: {grammar_path}", flush=True)
    if tool is not None and language is not None:
        print(f"Running {tool} with {language}.", flush=True)
