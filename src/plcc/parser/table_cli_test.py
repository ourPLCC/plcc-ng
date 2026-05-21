import io
import json
import os
import sys
import tempfile
import pytest
from plcc.parser.table_cli import main as run_main


_TRIVIAL_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": [{"symbol": "NUM", "field": None}]
        }
    },
}

_NON_LL1 = {
    "is_ll1": False,
    "start_symbol": "program",
    "parse_table": {},
    "conflicts": [{"nonterminal": "program", "lookahead": "NUM", "productions": []}],
    "left_recursion": [],
}

_CAPTURING_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {"NUM": [{"symbol": "NUM", "field": "num"}]}
    },
}

_ADDITION_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": [
                {"symbol": "NUM", "field": None},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": None},
            ]
        }
    },
}

def _tok(name, lexeme, line=1, col=1, file="<stdin>"):
    return {"kind": "token", "name": name, "lexeme": lexeme,
            "source": {"file": file, "line": line, "column": col}}

def _run(ll1_dict, tokens, extra_args=None):
    """Run table_cli.main with the given ll1 and tokens. Returns exit_code (int)."""
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(ll1_dict, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        argv = [f"--ll1={ll1_file.name}"] + (extra_args or [])
        exit_code = 0
        try:
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr("sys.stdin", io.StringIO(stdin_data))
                run_main(argv)
        except SystemExit as e:
            exit_code = e.code or 0
        return exit_code
    finally:
        os.unlink(ll1_file.name)


def test_exits_zero_for_valid_input(capsys):
    code = _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert code == 0


def test_stdout_is_valid_json(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    result = json.loads(out.strip().splitlines()[0])
    assert isinstance(result, dict)


def test_output_is_tree_kind(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    assert json.loads(out.strip().splitlines()[0])["kind"] == "tree"


def test_output_rule_is_start_symbol(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    assert json.loads(out.strip().splitlines()[0])["rule"] == "program"


def test_output_has_source(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    src = json.loads(out.strip().splitlines()[0])["source"]
    assert "line" in src and "column" in src


def test_capturing_child_in_tree(capsys):
    _run(_CAPTURING_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    result = json.loads(out.strip().splitlines()[0])
    fields = [c[0] for c in result["children"]]
    assert "num" in fields


def test_exits_nonzero_for_non_ll1_grammar(monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_NON_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        with pytest.raises(SystemExit) as exc:
            run_main([f"--ll1={ll1_file.name}"])
        assert exc.value.code != 0
    finally:
        os.unlink(ll1_file.name)


def test_exits_zero_for_parse_error_but_emits_record(monkeypatch, capsys):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_tok("IDENTIFIER", "x")) + "\n"))
        exit_code = 0
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit as e:
            exit_code = e.code or 0
        assert exit_code == 0
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        assert any(r.get("kind") == "error" for r in records)
    finally:
        os.unlink(ll1_file.name)


def test_error_record_passes_through(capsys, monkeypatch):
    error_record = {"kind": "error", "stage": "plcc-tokens",
                    "source": {"file": None, "line": 1, "column": 1}}
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(error_record) + "\n"))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit as e:
            assert e.code == 0
        out, _ = capsys.readouterr()
        assert json.loads(out.strip().splitlines()[0])["kind"] == "error"
    finally:
        os.unlink(ll1_file.name)


def test_parse_error_emits_error_record_to_stdout(capsys, monkeypatch):
    """A real parse error (wrong token) emits {"kind":"error"} to stdout."""
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        # PLUS is not valid for program → NUM
        bad_tokens = [_tok("PLUS", "+")]
        stdin_data = "\n".join(json.dumps(t) for t in bad_tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        assert any(r.get("kind") == "error" for r in records)
    finally:
        os.unlink(ll1_file.name)


# Grammar: exp → NUM exp2 ; exp2 → OP exp | ε
# Demonstrates incomplete input: "23 +" hits eof where NUM was expected.
_EXP_LL1 = {
    "is_ll1": True,
    "start_symbol": "exp",
    "parse_table": {
        "exp": {
            "NUM": [
                {"symbol": "NUM", "field": None},
                {"symbol": "exp2", "field": None},
            ]
        },
        "exp2": {
            "OP": [
                {"symbol": "OP", "field": None},
                {"symbol": "exp", "field": None},
            ],
            "eof": [],
        },
    },
}


def _sentinel(line=1, col=1, file="-"):
    return {"kind": "token", "name": "eof", "lexeme": "",
            "source": {"file": file, "line": line, "column": col}}


def test_exits_zero_on_syntax_error(monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        bad = [_tok("PLUS", "+"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in bad) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        exit_code = 0
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit as e:
            exit_code = e.code or 0
        assert exit_code == 0
    finally:
        os.unlink(ll1_file.name)


def test_syntax_error_emits_error_record_with_source(capsys, monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        bad = [_tok("PLUS", "+", line=2, col=5), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in bad) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        err_records = [r for r in records if r.get("kind") == "error"]
        assert len(err_records) >= 1
        assert err_records[0].get("source", {}).get("line") == 2
        assert err_records[0].get("source", {}).get("column") == 5
    finally:
        os.unlink(ll1_file.name)


def test_non_eof_error_stops_loop(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [PLUS, NUM, eof]
    # PLUS is not a valid start token. With the cascade removed, the loop breaks
    # immediately on the PLUS error and never attempts to parse NUM.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("PLUS", "+"), _tok("NUM", "42"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        trees  = [r for r in records if r.get("kind") == "tree"]
        assert len(errors) == 1
        assert len(trees) == 0
    finally:
        os.unlink(ll1_file.name)


def test_two_programs_in_one_input_emits_two_trees(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [NUM, NUM, $] → two trees
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _tok("NUM", "2"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        trees = [r for r in records if r.get("kind") == "tree"]
        assert len(trees) == 2
    finally:
        os.unlink(ll1_file.name)


def test_incomplete_input_error_record_has_found_eof(capsys, monkeypatch):
    # Grammar: program → NUM PLUS NUM; tokens: [NUM, eof] — incomplete input
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        err_records = [r for r in records if r.get("kind") == "error"]
        assert len(err_records) >= 1
        assert err_records[0].get("found") == "eof"
    finally:
        os.unlink(ll1_file.name)


def test_incomplete_input_emits_error_record(capsys, monkeypatch):
    # Grammar: program → NUM PLUS NUM; tokens: [NUM, $] — incomplete
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        assert any(r.get("kind") == "error" for r in records)
    finally:
        os.unlink(ll1_file.name)


def test_incomplete_input_emits_only_one_error_no_cascade(capsys, monkeypatch):
    # Tokens: [NUM("23"), OP("+"), eof] — incomplete, nothing after the operator.
    # The parser fails with found="eof". Without the fix, cursor advances to OP
    # and a second error with found="OP" is emitted (cascade). With the fix,
    # the loop breaks immediately, leaving exactly one error record.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_EXP_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "23"), _tok("OP", "+"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        err_records = [r for r in records if r.get("kind") == "error"]
        assert len(err_records) == 1
        assert err_records[0].get("found") == "eof"
    finally:
        os.unlink(ll1_file.name)


def test_parse_error_does_not_write_to_stderr(capsys, monkeypatch):
    # Grammar: program → NUM; token: PLUS → parse error.
    # Parse errors are results (stdout JSONL), not diagnostics (stderr).
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        bad_tokens = [_tok("PLUS", "+"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in bad_tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        _, err = capsys.readouterr()
        assert err == ""
    finally:
        os.unlink(ll1_file.name)


def test_three_invalid_tokens_emit_one_error(capsys, monkeypatch):
    # Grammar: program → NUM PLUS NUM; tokens: [NUM(3), NUM(2), NUM(1), eof]
    # cursor=0: parse NUM(3), expect PLUS, find NUM(2) → error (found="NUM").
    # With cascade: cursor advances, two more errors follow. Without cascade: one error.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "3"), _tok("NUM", "2"), _tok("NUM", "1"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        trees  = [r for r in records if r.get("kind") == "tree"]
        assert len(errors) == 1
        assert len(trees) == 0
        assert errors[0].get("found") != "eof"
    finally:
        os.unlink(ll1_file.name)


def test_error_after_success_stops_further_parsing(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [NUM(1), PLUS(+), NUM(2), eof]
    # cursor=0: parse NUM(1) → tree, cursor=1.
    # cursor=1: parse PLUS → error (found="PLUS"). Without cascade: stop.
    # With cascade: cursor=2, parse NUM(2) → second tree.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _tok("PLUS", "+"), _tok("NUM", "2"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        errors = [r for r in records if r.get("kind") == "error"]
        trees  = [r for r in records if r.get("kind") == "tree"]
        assert len(trees) == 1
        assert len(errors) == 1
        assert records[0]["kind"] == "tree"
        assert records[1]["kind"] == "error"
    finally:
        os.unlink(ll1_file.name)
