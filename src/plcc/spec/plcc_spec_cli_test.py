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
