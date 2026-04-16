"""Shared verbose infrastructure for the PLCC pipeline.

Every command accepts --verbose and --verbose-format. This module provides
the VerboseContext object and the VERBOSE_OPTIONS docopt fragment.
"""

import json
import sys
import time


VERBOSE_OPTIONS = """
    --verbose=LEVEL         Verbosity level 0-3 [default: 0].
    --verbose-format=FMT    Output format: text or json [default: text].
"""


class VerboseContext:
    """Holds verbosity settings for one command invocation."""

    def __init__(self, stage, events_enum, level=0, fmt="text"):
        self.stage = stage
        self.events_enum = events_enum
        self.level = level
        self.fmt = fmt

    @classmethod
    def from_args(cls, stage, events_enum, args):
        level = int(args.get("--verbose") or 0)
        fmt = args.get("--verbose-format") or "text"
        return cls(stage, events_enum, level, fmt)

    def emit(self, event, level=1, **payload):
        if self.level < level:
            return
        if self.fmt == "json":
            record = {
                "stage": self.stage,
                "time": time.monotonic_ns(),
                "event": event.value,
                **payload,
            }
            print(json.dumps(record), file=sys.stderr, flush=True)
        else:
            msg = payload.get("message", "")
            print(f"{self.stage}: {event.value}: {msg}", file=sys.stderr, flush=True)

    def child_flags(self):
        return [f"--verbose={self.level}", f"--verbose-format={self.fmt}"]

    def child_flags_for_orchestrator(self, min_level=None):
        level = max(self.level, min_level or 0)
        return [f"--verbose={level}", "--verbose-format=json"]

    def parse_child_events(self, stderr_text):
        events = []
        for line in stderr_text.splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
        return events

    def reformat_child_events(self, events):
        for ev in events:
            if self.fmt == "json":
                print(json.dumps(ev), file=sys.stderr, flush=True)
            else:
                stage = ev.get("stage", "unknown")
                event = ev.get("event", "unknown")
                msg = ev.get("message", "")
                print(f"{stage}: {event}: {msg}", file=sys.stderr, flush=True)
