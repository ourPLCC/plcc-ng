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
    result = json.loads(out)
    assert isinstance(result, dict)


def test_output_is_tree_kind(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    assert json.loads(out)["kind"] == "tree"


def test_output_rule_is_start_symbol(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    assert json.loads(out)["rule"] == "program"


def test_output_has_source(capsys):
    _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    src = json.loads(out)["source"]
    assert "line" in src and "column" in src


def test_capturing_child_in_tree(capsys):
    _run(_CAPTURING_LL1, [_tok("NUM", "42")])
    out, _ = capsys.readouterr()
    result = json.loads(out)
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


def test_exits_nonzero_on_syntax_error(monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_tok("IDENTIFIER", "x")) + "\n"))
        with pytest.raises(SystemExit) as exc:
            run_main([f"--ll1={ll1_file.name}"])
        assert exc.value.code != 0
    finally:
        os.unlink(ll1_file.name)


def test_nothing_written_to_stdout_on_error(capsys, monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_tok("IDENTIFIER", "x")) + "\n"))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        assert out.strip() == ""
    finally:
        os.unlink(ll1_file.name)
