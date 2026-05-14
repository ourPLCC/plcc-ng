import sys
from dataclasses import dataclass

HINT = "Enter input. Press ^D (EOF) when done."
PROMPT = ">>> "
CONTINUATION = "... "


@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False


class SourceRunner:
    def __init__(self, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
        self._hint = hint
        self._prompt = prompt
        self._continuation = continuation

    def run(self, sources, handler):
        """Run handler over sources. Returns False if any non-interactive feed
        signalled incomplete input (handler returned False); True otherwise."""
        effective = sources if sources else ["-"]
        completed = True
        for source in effective:
            if source == "-":
                if sys.stdin.isatty():
                    self._run_interactive(handler)
                else:
                    content = sys.stdin.buffer.read()
                    if handler.feed(content, "-") is False:
                        completed = False
            else:
                with open(source, "rb") as f:
                    content = f.read()
                if handler.feed(content, source) is False:
                    completed = False
        return completed

    def _run_interactive(self, handler):
        print(self._hint, file=sys.stderr)
        buffer = b""
        prompt = self._prompt
        while True:
            try:
                print(prompt, end="", flush=True, file=sys.stderr)
                line = sys.stdin.buffer.readline()
            except KeyboardInterrupt:
                print(file=sys.stderr)
                if buffer:
                    print("KeyboardInterrupt", file=sys.stderr)
                    buffer = b""
                    prompt = self._prompt
                else:
                    sys.exit(130)
                continue

            if not line:                          # ^D
                print(file=sys.stderr)
                if buffer:
                    self._evaluate(handler, buffer)
                    buffer = b""
                    prompt = self._prompt
                else:
                    break
            elif not line.strip():                # blank line
                if buffer:
                    self._evaluate(handler, buffer + line)
                    buffer = b""
                    prompt = self._prompt
            else:                                 # normal line
                buffer += line
                if self._evaluate(handler, buffer):
                    buffer = b""
                    prompt = self._prompt
                else:
                    prompt = self._continuation

    def _evaluate(self, handler, content):
        try:
            return handler.feed(content, "-")
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)

    def _is_interrupted(self, line):
        return line is None

    def _is_eof(self, line):
        return not line

    def _is_partial_eof(self, line):
        return not line.endswith(b"\n")

    def _is_blank(self, line):
        return not line.strip()
