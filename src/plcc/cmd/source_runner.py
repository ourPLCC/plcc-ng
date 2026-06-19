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
        """Run handler over sources. Interactive stdin parses incrementally;
        files and piped stdin are fed whole with eof=True."""
        effective = sources if sources else ["-"]
        for source in effective:
            if source == "-":
                if sys.stdin.isatty():
                    self._run_interactive(handler)
                else:
                    content = sys.stdin.buffer.read()
                    handler.feed(content, "-", eof=True)
            else:
                with open(source, "rb") as f:
                    content = f.read()
                handler.feed(content, source, eof=True)

    def _run_interactive(self, handler):
        self._print_hint()
        state = _InteractiveState(buffer=b"", prompt=self._prompt)
        while not state.done:
            line = self._read_line(state.prompt)
            state = self._process_line(handler, line, state)

    def _print_hint(self):
        print(self._hint, file=sys.stderr)

    def _read_line(self, prompt):
        try:
            print(prompt, end="", flush=True, file=sys.stderr)
            return sys.stdin.buffer.read1(65536)
        except KeyboardInterrupt:
            return None

    def _process_line(self, handler, line, state):
        if line is None:
            return self._clear_buffer_or_exit(state)
        if line == b"":
            return self._ctrl_d(handler, state)
        if not line.endswith(b"\n"):
            return self._force_submit(handler, state.buffer + line)
        return self._incremental(handler, state.buffer + line)

    def _ctrl_d(self, handler, state):
        print(file=sys.stderr)
        if state.buffer:
            return self._force_submit(handler, state.buffer)
        return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)

    def _force_submit(self, handler, content):
        remainder = self._evaluate(handler, content, eof=True)
        if remainder:
            print("PLCC internal error: forced submission left unconsumed input.",
                  file=sys.stderr)
            sys.exit(1)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _incremental(self, handler, content):
        remainder = self._evaluate(handler, content, eof=False)
        prompt = self._prompt if not remainder else self._continuation
        return _InteractiveState(buffer=remainder, prompt=prompt)

    def _clear_buffer_or_exit(self, state):
        print(file=sys.stderr)
        if state.buffer:
            print("KeyboardInterrupt", file=sys.stderr)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        sys.exit(130)

    def _evaluate(self, handler, content, eof):
        try:
            return handler.feed(content, "-", eof=eof)
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
