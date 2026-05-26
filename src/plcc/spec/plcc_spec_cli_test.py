import json
import pytest
import docopt

from .plcc_spec_cli import main as run_main


def test_no_args_prints_usage():
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_help(capsys):
    with pytest.raises(SystemExit):
        run_main(['--help'])
    out, err = capsys.readouterr()
    assert 'Usage' in out


def test_outputs_spec_json(capsys, fs):
    fs.create_file('/trivial.plcc', contents="""
token NUM '\\d+'
%
<program> ::= NUM
%
% diagram PlantUML
""")
    run_main(['/trivial.plcc'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert 'lexical' in data
    assert 'syntax' in data
    assert 'semantics' in data


def test_lexical_rules_present(capsys, fs):
    fs.create_file('/trivial.plcc', contents="NUM '\\d+'\n")
    run_main(['/trivial.plcc'])
    out, err = capsys.readouterr()
    data = json.loads(out)
    names = [r['name'] for r in data['lexical']['ruleList']]
    assert 'NUM' in names


def test_exits_nonzero_on_spec_error(capsys, fs):
    fs.create_file('/bad.plcc', contents="num 'bad'\n")  # lowercase = invalid
    with pytest.raises(SystemExit) as exc:
        run_main(['/bad.plcc'])
    assert exc.value.code != 0


def test_malformed_syntactic_rule_prints_error_and_exits_nonzero(capsys, fs):
    fs.create_file('/bad.plcc', contents=(
        "token NUM '\\d+'\n"
        "%\n"
        "<program>IfStmt ::= NUM\n"
    ))
    with pytest.raises(SystemExit) as exc:
        run_main(['/bad.plcc'])
    out, err = capsys.readouterr()
    assert exc.value.code != 0
    assert "bad.plcc" in err
    assert "syntax error" in err
    assert "Examples:" in err


def test_malformed_syntactic_rule_stderr_includes_source_line(capsys, fs):
    fs.create_file('/bad.plcc', contents=(
        "token NUM '\\d+'\n"
        "%\n"
        "<program>IfStmt ::= NUM\n"
    ))
    with pytest.raises(SystemExit):
        run_main(['/bad.plcc'])
    _, err = capsys.readouterr()
    assert "<program>IfStmt ::= NUM" in err


def test_malformed_syntactic_rule_stderr_includes_caret_at_correct_column(capsys, fs):
    # <program> is 9 chars, so lhs ends at index 8 (0-based), column 10 (1-based).
    # Caret line must be 9 spaces + ^.
    fs.create_file('/bad.plcc', contents=(
        "token NUM '\\d+'\n"
        "%\n"
        "<program>IfStmt ::= NUM\n"
    ))
    with pytest.raises(SystemExit):
        run_main(['/bad.plcc'])
    _, err = capsys.readouterr()
    assert "         ^" in err


def test_lexical_error_stderr_includes_source_line(capsys, fs):
    # "num 'bad'" is invalid (lowercase token name triggers NameExpected)
    fs.create_file('/bad.plcc', contents="num 'bad'\n")
    with pytest.raises(SystemExit):
        run_main(['/bad.plcc'])
    _, err = capsys.readouterr()
    assert "num 'bad'" in err
