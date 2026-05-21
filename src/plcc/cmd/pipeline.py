import json
import subprocess
import sys


def location_str(source):
    file = source.get("file", "")
    line = source.get("line")
    col = source.get("column")
    if line is None or col is None:
        return None
    if file and file not in ("-", "<stdin>", ""):
        return f"{file}:{line}:{col}"
    return f"-:{line}:{col}"


def print_parse_error(record, default_stage):
    src = record.get("source", {})
    message = record.get("message", "error")
    stage = record.get("stage", default_stage)
    loc = location_str(src)
    prefix = f"{stage}: {loc}" if loc else stage
    print(f"{prefix}: error: {message}", file=sys.stderr)


class TreePipeline:
    """Runs plcc-tokens | plcc-trees and classifies the output."""

    def __init__(self, spec_path, ll1_path, child_flags=None, verbose=None):
        self._spec_path = spec_path
        self._ll1_path = ll1_path
        self._child_flags = child_flags or []
        self._verbose = verbose

    def run(self, content, eof=False):
        """Run the pipeline.

        Returns None  — need more input (no records, or only EOF errors with eof=False).
        Returns list  — list of (record_dict, raw_bytes) pairs ready to dispatch.
        """
        stderr_mode = subprocess.PIPE if self._verbose else None
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_mode,
        )
        tree_proc = subprocess.Popen(
            ["plcc-trees", f"--ll1={self._ll1_path}"] + self._child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=stderr_mode,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(content)
        tokens_proc.stdin.close()
        tree_out, tree_err = tree_proc.communicate()
        tokens_proc.wait()
        if self._verbose:
            # Note: if tokens_proc wrote >64 KB to stderr before tree_proc.communicate()
            # drained it, this read could deadlock. Verbose output is a handful of JSON
            # lines (~300 bytes per run), so this is not a practical risk.
            tokens_err = tokens_proc.stderr.read()

        records = []
        raws = []
        for raw in tree_out.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            records.append(json.loads(raw))
            raws.append(raw)

        if not records:
            return None  # suppress events: pipeline will re-run with more input

        any_tree = any(r.get("kind") == "tree" for r in records)
        any_genuine_error = any(
            r.get("kind") == "error" and r.get("found") != "eof"
            for r in records
        )
        only_eof_errors = not any_tree and not any_genuine_error

        if only_eof_errors and not eof:
            return None  # suppress events: pipeline will re-run with more input

        if self._verbose:
            # tokens runs upstream; concatenate in pipeline order for roughly
            # chronological display
            combined = tokens_err + tree_err
            events = self._verbose.parse_child_events(
                combined.decode("utf-8", errors="replace")
            )
            self._verbose.reformat_child_events(events)

        return list(zip(records, raws))
