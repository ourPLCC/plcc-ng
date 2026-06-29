"""Shared verbose infrastructure for the PLCC pipeline.

Every command accepts -v and --verbose-format. This module provides
the VerboseContext object and the VERBOSE_OPTIONS docopt fragment.
"""

import json
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional


VERBOSE_OPTIONS = """
    -v                      Increase verbosity (may repeat: -v, -vv, -vvv for levels 1-3).
    --verbose-format=FMT    Output format: text or json [default: text].
"""

DIAGNOSTICS_OPTIONS = """
Diagnostics:
    -v                      Increase verbosity (may repeat: -v, -vv, -vvv for levels 1-3).
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
        level = int(args.get("-v") or 0)
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

    def emit_error(self, pos, message, **fields):
        if self.fmt == "json":
            record = {
                "stage": self.stage,
                "time": time.monotonic_ns(),
                "event": "error",
                "severity": "error",
                "pos": pos,
                "message": message,
                **fields,
            }
            print(json.dumps(record), file=sys.stderr, flush=True)
        else:
            filename = pos.get("file") or "<stdin>"
            line = pos.get("line", 0)
            col = pos.get("column", 0)
            parts = [f"{self.stage}: {filename}:{line}:{col}: error: {message}"]
            source_line = fields.get("source_line")
            hint = fields.get("hint")
            if source_line is not None:
                parts.append(source_line)
                if col > 0:
                    parts.append(" " * (col - 1) + "^")
            if hint is not None:
                parts.append(hint)
            print("\n".join(parts), file=sys.stderr, flush=True)

    def child_flags(self):
        return ["-v"] * self.level + [f"--verbose-format={self.fmt}"]

    def child_flags_for_orchestrator(self, min_level=None):
        level = max(self.level, min_level or 0)
        return ["-v"] * level + ["--verbose-format=json"]

    def parse_child_events(self, stderr_text):
        events = []
        for line in stderr_text.splitlines():
            stripped = line.strip()
            if not stripped:
                print(file=sys.stderr, flush=True)
                continue
            try:
                events.append(json.loads(stripped))
            except json.JSONDecodeError:
                print(line, file=sys.stderr, flush=True)
        return events

    def reformat_child_events(self, events):
        for ev in events:
            if self.fmt == "json":
                print(json.dumps(ev), file=sys.stderr, flush=True)
                continue
            if ev.get("event") == "error":
                stage = ev.get("stage", "unknown")
                pos = ev.get("pos", {}) or {}
                file = pos.get("file") or "<stdin>"
                line = pos.get("line", 0)
                col = pos.get("column", 0)
                msg = ev.get("message", "")
                parts = [f"{stage}: {file}:{line}:{col}: error: {msg}"]
                source_line = ev.get("source_line")
                hint = ev.get("hint")
                if source_line is not None:
                    parts.append(source_line)
                    if col > 0:
                        parts.append(" " * (col - 1) + "^")
                if hint is not None:
                    parts.append(hint)
                print("\n".join(parts), file=sys.stderr, flush=True)
            else:
                stage = ev.get("stage", "unknown")
                event = ev.get("event", "unknown")
                msg = ev.get("message", "")
                print(f"{stage}: {event}: {msg}", file=sys.stderr, flush=True)


@dataclass
class PipelineResult:
    failed_stage: Optional[str]   # label of first failing stage, or None
    exit_code: int                # returncode of first failing stage, or 0
    events_to_render: List[dict] = field(default_factory=list)


def reap_pipeline(stages):
    """Wait for all pipeline stages, attribute failure upstream-first,
    and suppress downstream cascades.

    Arguments:
        stages: list of (Popen-or-dummy, label) pairs in upstream-to-downstream
                order. Each proc must have .returncode set and either
                .stderr_captured (bytes) already set, or a .stderr attribute
                that can be .read().

    Returns:
        PipelineResult with:
          - failed_stage: label of first failing stage, or None
          - exit_code: returncode of the first failing stage, or 0
          - events_to_render: JSONL events to be reformatted.
            If any stage failed, events from downstream-of-failure are dropped.
    """
    # Collect stderr bytes for every stage, parse JSONL.
    per_stage_events = []
    for proc, label in stages:
        stderr_bytes = getattr(proc, "stderr_captured", None)
        if stderr_bytes is None and getattr(proc, "stderr", None) is not None:
            stderr_bytes = proc.stderr.read()
        text = (stderr_bytes or b"").decode("utf-8", errors="replace")
        events = _parse_jsonl_events(text)
        per_stage_events.append(events)

    # Find first failing stage.
    failed_index = None
    for i, (proc, _label) in enumerate(stages):
        if proc.returncode != 0:
            failed_index = i
            break

    if failed_index is None:
        all_events = [e for stage_events in per_stage_events for e in stage_events]
        return PipelineResult(failed_stage=None, exit_code=0, events_to_render=all_events)

    # Keep events from stages 0..failed_index inclusive; drop everything downstream.
    kept = []
    for events in per_stage_events[: failed_index + 1]:
        kept.extend(events)

    return PipelineResult(
        failed_stage=stages[failed_index][1],
        exit_code=stages[failed_index][0].returncode,
        events_to_render=kept,
    )


def _parse_jsonl_events(text):
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # Non-JSON line (e.g. a child that wrote text to stderr despite
            # --verbose-format=json). Preserve it as an opaque record.
            events.append({"stage": "unknown", "event": "raw", "message": line})
    return events
