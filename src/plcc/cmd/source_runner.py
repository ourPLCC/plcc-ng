import sys

HINT = "Enter input. Press ^D (EOF) when done."
PROMPT = ">>> "
CONTINUATION = "... "


class SourceRunner:
    def __init__(self, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
        self._hint = hint
        self._prompt = prompt
        self._continuation = continuation

    def run(self, sources, handler):
        effective = sources if sources else ["-"]
        for source in effective:
            if source == "-":
                if sys.stdin.isatty():
                    self._run_interactive(handler)
                else:
                    content = sys.stdin.buffer.read()
                    handler.feed(content, "-")
            else:
                with open(source, "rb") as f:
                    content = f.read()
                handler.feed(content, source)

    def _run_interactive(self, handler):
        print(self._hint, file=sys.stderr)
        buffer = b""
        prompt = self._prompt
        while True:
            try:
                print(prompt, end="", flush=True, file=sys.stderr)
                line = sys.stdin.buffer.readline()
                if not line:  # EOF (^D)
                    if buffer:
                        handler.feed(buffer, "-")
                    break
                if not line.strip() and not buffer:
                    # Empty line on a fresh prompt: skip silently
                    continue
                buffer += line
                result = handler.feed(buffer, "-")
                if result:
                    buffer = b""
                    prompt = self._prompt
                else:
                    prompt = self._continuation
            except KeyboardInterrupt:
                print(file=sys.stderr)
                buffer = b""
                prompt = self._prompt
