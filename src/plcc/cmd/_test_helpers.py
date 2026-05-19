import io
import json
from types import SimpleNamespace


def _proc(stdout=b"", returncode=0):
    p = SimpleNamespace(returncode=returncode)
    p.communicate = lambda: (stdout, b"")
    p.wait = lambda: None
    p.stdin = io.BytesIO()
    p.stdout = io.BytesIO(stdout)
    return p


def _tree_record():
    return json.dumps({
        "kind": "tree", "rule": "program",
        "source": {}, "children": []
    }).encode() + b"\n"


def _error_record(msg="bad", stage="plcc-tokens"):
    return json.dumps({"kind": "error", "message": msg, "stage": stage}).encode() + b"\n"


def _error_record_with_source(msg="bad", stage="plcc-parser-table",
                               file="-", line=2, col=5):
    return json.dumps({
        "kind": "error", "message": msg, "stage": stage,
        "source": {"file": file, "line": line, "column": col},
    }).encode() + b"\n"


def _eof_error_record(msg="unexpected end of input", stage="plcc-parser-table",
                      line=1, col=1):
    return json.dumps({
        "kind": "error", "message": msg, "stage": stage,
        "found": "eof",
        "source": {"file": "-", "line": line, "column": col},
    }).encode() + b"\n"
