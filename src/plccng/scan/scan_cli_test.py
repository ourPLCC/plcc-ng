import json

import docopt
import pytest

from .scan_cli import run


def test_no_args_prints_usage():
    with pytest.raises(docopt.DocoptExit, match=r'Usage'):
        run(['scan'])


def test_h_prints_usage(capsys):
    with pytest.raises(SystemExit):
        run('scan -h'.split())
    assertStdoutContains(capsys, 'Usage')


def test_help_prints_usage(capsys):
    with pytest.raises(SystemExit):
        run('scan --help'.split())
    assertStdoutContains(capsys, 'Usage')


def test_happy_path(capsys, fs):
    fs.create_file('/spec', contents='''
                                A 'a'
                          ''')
    fs.create_file('/code', contents='a')
    run('scan /spec /code'.split())
    out, err = capsys.readouterr()
    result = json.loads(out)
    assert result == {
        'Type': 'Token',
        'Name': 'A',
        'Lexeme': 'a',
        'File': '/code',
        'Line': 1,
        'Column': 1,
    }


def test_spec_with_error(capsys, fs):
    fs.create_file('/spec', contents='''
                                a 'a'
                          ''')
    fs.create_file('/code', contents='a')
    run('scan /spec /code'.split())
    out, err = capsys.readouterr()
    assert 'NameExpected' in out


def assertStdoutContains(capsys, string):
    out, err = capsys.readouterr()
    assert string in out
