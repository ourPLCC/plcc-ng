import io
import json

import docopt
import pytest

from .spec_cli import run


def test_no_args_prints_usage():
    with pytest.raises(docopt.DocoptExit, match=r'Usage'):
        run(['spec'])


def test_h_prints_usage(capsys):
    with pytest.raises(SystemExit):
        run('spec -h'.split())
    assertStdoutContains(capsys, 'Usage')


def test_help_prints_usage(capsys):
    with pytest.raises(SystemExit):
        run('spec --help'.split())
    assertStdoutContains(capsys, 'Usage')


def test_spec_from_file(capsys, fs, oneRuleSpec):
    file = createFile(fs, oneRuleSpec)
    run(f'spec {file}'.split())
    out, err = capsys.readouterr()
    assert out == ''


def test_spec_json_from_file_prints_json(capsys, fs, oneRuleSpec):
    file = createFile(fs, oneRuleSpec)
    run(f'spec --json {file}'.split())
    assertStdoutContainsJsonSpec(capsys, ruleCount=1)


def test_spec_from_stdin(monkeypatch, capsys, oneRuleSpec):
    setStdin(monkeypatch, oneRuleSpec)
    run('spec --json -'.split())
    assertStdoutContainsJsonSpec(capsys, ruleCount=1)


def test_spec_with_one_error(capsys, fs, specWithNameExpectedError):
    file = createFile(fs, specWithNameExpectedError)
    run(f'spec {file}'.split())
    assertStdoutContains(capsys, 'NameExpected')


def test_spec_json_with_one_error(capsys, fs, specWithNameExpectedError):
    file = createFile(fs, specWithNameExpectedError)
    run(f'spec --json {file}'.split())
    assertStdoutContains(capsys, 'NameExpected')


def createFile(fs, oneRuleSpec):
    fs.create_file("/spec.plcc", contents=oneRuleSpec)
    return "/spec.plcc"


def setStdin(monkeypatch, string):
    monkeypatch.setattr('sys.stdin', io.StringIO(string))


def assertStdoutContains(capsys, string):
    out, err = capsys.readouterr()
    assert string in out


def assertStdoutContainsJsonSpec(capsys, ruleCount):
    out, err = capsys.readouterr()
    result = json.loads(out)
    assert len(result['lexical']['ruleList']) == ruleCount


@pytest.fixture
def oneRuleSpec():
    return '''

            A 'a'

    '''

@pytest.fixture
def specWithNameExpectedError():
    return '''

            a 'a'

    '''
