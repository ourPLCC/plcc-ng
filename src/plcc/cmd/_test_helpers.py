import io
import json
from types import SimpleNamespace


def _proc(stdout=b"", returncode=0, stderr=b""):
    p = SimpleNamespace(returncode=returncode)
    p.communicate = lambda: (stdout, stderr)
    p.wait = lambda: None
    p.stdin = io.BytesIO()
    p.stdout = io.BytesIO(stdout)
    p.stderr = io.BytesIO(stderr)
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


def _parse_step_record(event="predict", sym="program", lookahead="NUM",
                        production="program", depth=0):
    return json.dumps({
        "kind": "parse-step",
        "event": event,
        "sym": sym,
        "lookahead": lookahead,
        "production": production,
        "depth": depth,
    }).encode() + b"\n"


def _shift_step_record(name="NUM", lexeme="42", file="-", line=1, col=1, depth=1):
    return json.dumps({
        "kind": "parse-step",
        "event": "shift",
        "name": name,
        "lexeme": lexeme,
        "source": {"file": file, "line": line, "column": col},
        "depth": depth,
    }).encode() + b"\n"


def _complete_step_record(rule="program", depth=0):
    return json.dumps({
        "kind": "parse-step",
        "event": "complete",
        "rule": rule,
        "depth": depth,
    }).encode() + b"\n"


def _hold_record(line=1, col=1, file="-"):
    return json.dumps({
        "kind": "hold",
        "source": {"file": file, "line": line, "column": col},
    }).encode() + b"\n"


def _ready_record():
    return json.dumps({"kind": "ready"}).encode() + b"\n"


def _specification_error_record(msg="stack underflow", type_="ValueError"):
    return json.dumps({"kind": "specification_error", "type": type_, "message": msg}).encode() + b"\n"
