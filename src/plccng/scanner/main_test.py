import pytest
from .main import Main
from .main_help_message import helpMessage
import io

def test_help_command(capfd):
    argv = ["-h"]
    main = Main(build_scanner(), None)
    main.run(stdin=None, stdout=None, stderr=None, argv=argv)
    captured = capfd.readouterr()
    assert captured.out == helpMessage + "\n"

def test_read_specfile_and_build_matcher_spec(tmp_path):
    specfile = build_specfile(tmp_path)
    argv = [f'--specfile={specfile}']

    main = Main(build_scanner(), None)
    main.run(stdin=None, stdout=None, stderr=None, argv=argv)

    assert len(main.scanner.matcher.spec) == 4
    assert main.scanner.matcher.spec[0]['type'] == 'Token'
    assert main.scanner.matcher.spec[1]['regex'] == '\\s+'
    assert main.scanner.matcher.spec[2]['name'] == 'ONETWOTHREE'

def test_read_input_file_and_pass_to_source(tmp_path):
    specfile = build_specfile(tmp_path)
    argv = [f'--specfile={specfile}', 'input1', 'input2']

    main = Main(build_scanner(), Source([]))
    main.run(stdin=None, stdout=None, stderr=None, argv=argv)
    assert main.source.files == ["input1", "input2"]

def test_stdin_pass_to_source(tmp_path):
    specfile = build_specfile(tmp_path)
    argv = [f'--specfile={specfile}']
    stdin = io.StringIO('123      45')
    main = Main(build_scanner(), Source([]))
    main.run(stdin, stdout=None, stderr=None, argv=argv)
    assert main.source.files == ['-']

def test_stdin_pass_to_source_after_input_file(tmp_path):
    specfile = build_specfile(tmp_path)
    argv = [f'--specfile={specfile}', 'input1', 'input2']
    stdin = io.StringIO('123      45')
    main = Main(build_scanner(), Source([]))
    main.run(stdin, stdout=None, stderr=None, argv=argv)
    assert main.source.files == ["input1", "input2", '-']

def build_specfile(tmp_path):
    specfile = tmp_path / "specfile.json"
    file_content = """
    [
        {
            "type": "Token",
            "name": "MINUS",
            "regex": "-"
        },
        {
            "type": "Skip",
            "name": "WHITESPACE",
            "regex": "\\\\s+"
        },
        {
            "type": "Token",
            "name": "ONETWOTHREE",
            "regex": "123"
        },
        {
            "type": "Token",
            "name": "NUMBER",
            "regex": "\\\\d+"
        }
    ]
    """
    with open(specfile, 'w') as f:
        f.write(file_content)

    return specfile

def build_scanner():
    matcher = Matcher(None)
    return Scanner(matcher)


class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher
        self.scanned = False

    def scan(self, lines):
        self.scanned = True

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(string):
        pass

class Source:
    def __init__(self, files):
        self.files = files
