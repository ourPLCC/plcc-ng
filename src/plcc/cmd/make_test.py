import pytest
import docopt

from .make import main as run_main, validate_tool_name, _report_ll1_failure


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_grammar_file_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code != 0


def test_grammar_file_not_found_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main([])
    _, err = capsys.readouterr()
    assert "grammar file not found" in err


def test_grammar_file_flag_not_found_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--grammar-file=nonexistent.plcc'])
    assert exc.value.code != 0


def test_invalid_through_value_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        run_main(['--through=typo'])
    assert exc.value.code != 0


def test_invalid_through_value_prints_error(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=typo'])
    _, err = capsys.readouterr()
    assert "invalid --through" in err


def test_validate_tool_name_accepts_valid():
    validate_tool_name('diagram')
    validate_tool_name('Java')
    validate_tool_name('my-tool')
    validate_tool_name('tool_123')


def test_validate_tool_name_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_tool_name('../etc')
    with pytest.raises(ValueError):
        validate_tool_name('foo/bar')
    with pytest.raises(ValueError):
        validate_tool_name('/absolute')


def test_validate_tool_name_rejects_empty():
    with pytest.raises(ValueError):
        validate_tool_name('')


def test_report_ll1_failure_prints_error_and_conflicts(capsys):
    ll1 = {
        "is_ll1": False,
        "conflicts": [
            {"nonterminal": "E", "lookahead": "+", "competing": ["E + T", "E"]}
        ],
        "left_recursion": [],
    }
    _report_ll1_failure(ll1, "build/ll1.json")
    _, err = capsys.readouterr()
    assert "plcc-make: error:" in err
    assert "build/ll1.json" in err
    assert "E" in err
    assert "+" in err


def test_report_left_recursion_cycle(capsys):
    ll1 = {
        "conflicts": [],
        "left_recursion": [{"cycle": ["A", "B", "A"]}],
    }
    _report_ll1_failure(ll1, "build/ll1.json")
    _, err = capsys.readouterr()
    assert "A -> B -> A" in err



def test_through_model_is_valid(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=model'])
    _, err = capsys.readouterr()
    assert "invalid --through" not in err


def test_through_diagram_is_rejected(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=diagram'])
    _, err = capsys.readouterr()
    assert "invalid --through" in err


def test_invalid_through_error_message_includes_model(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        run_main(['--through=typo'])
    _, err = capsys.readouterr()
    assert "model" in err
