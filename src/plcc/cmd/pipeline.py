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

    def __init__(self, spec_path, ll1_path, child_flags=None):
        self._spec_path = spec_path
        self._ll1_path = ll1_path
        self._child_flags = child_flags or []

    def run(self, content, eof=False):
        """Run the pipeline.

        Returns None  — need more input (no records, or only EOF errors with eof=False).
        Returns list  — list of (record_dict, raw_bytes) pairs ready to dispatch.
        """
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # inherit parent stderr so errors surface to the terminal
        )
        tree_proc = subprocess.Popen(
            ["plcc-trees", f"--ll1={self._ll1_path}"] + self._child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=None,  # same: inherit
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(content)
        tokens_proc.stdin.close()
        tree_out, _ = tree_proc.communicate()
        tokens_proc.wait()

        records = []
        raws = []
        for raw in tree_out.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            records.append(json.loads(raw))
            raws.append(raw)

        if not records:
            return None

        any_tree = any(r.get("kind") == "tree" for r in records)
        any_genuine_error = any(
            r.get("kind") == "error" and r.get("found") != "eof"
            for r in records
        )
        only_eof_errors = not any_tree and not any_genuine_error

        if only_eof_errors and not eof:
            return None

        return list(zip(records, raws))
