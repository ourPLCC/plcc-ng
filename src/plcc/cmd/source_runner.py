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
            return sys.stdin.buffer.readline()
        except KeyboardInterrupt:
            return None

    def _process_line(self, handler, line, state):
        if self._is_interrupted(line):
            return self._clear_buffer_or_exit(state)
        if self._is_eof(line):
            return self._exit_or_submit_accumulated_buffer(handler, state)
        if self._is_partial_eof(line):
            return self._force_submit_including_partial_line(handler, line, state)
        if self._is_blank(line):
            return self._force_submit_accumulated_buffer(handler, line, state)
        return self._accumulate_and_evaluate(handler, line, state)

    def _is_interrupted(self, line):
        return line is None

    def _is_eof(self, line):
        return not line

    def _is_partial_eof(self, line):
        return not line.endswith(b"\n")

    def _is_blank(self, line):
        return not line.strip()

    def _clear_buffer_or_exit(self, state):
        print(file=sys.stderr)
        if state.buffer:
            print("KeyboardInterrupt", file=sys.stderr)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        sys.exit(130)

    def _exit_or_submit_accumulated_buffer(self, handler, state):
        print(file=sys.stderr)
        if state.buffer:
            self._evaluate(handler, state.buffer)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)

    def _force_submit_including_partial_line(self, handler, line, state):
        print(file=sys.stderr)
        self._evaluate(handler, state.buffer + line)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _force_submit_accumulated_buffer(self, handler, line, state):
        if state.buffer:
            self._evaluate(handler, state.buffer + line)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _accumulate_and_evaluate(self, handler, line, state):
        buffer = state.buffer + line
        if self._evaluate(handler, buffer):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=buffer, prompt=self._continuation)

    def _evaluate(self, handler, content):
        try:
            return handler.feed(content, "-")
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
