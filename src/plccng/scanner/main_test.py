import pytest
from .main import Main
from .main import __doc__ as helpMessage
import io

def test_read_specfile_builds_matcher_spec(tmp_path):
    specfile = build_specfile(tmp_path)
    args = {
        '--spec' : specfile,
        '<file>' : ['-']
    }
    main = Main(Scanner(Matcher(None)), Source([]), args)
    main.run()

    assert len(main.scanner.matcher.spec) == 4
    assert main.scanner.matcher.spec[0]['type'] == 'Token'
    assert main.scanner.matcher.spec[1]['regex'] == '\\s+'
    assert main.scanner.matcher.spec[2]['name'] == 'ONETWOTHREE'

def test_read_input_file_and_pass_to_source(tmp_path):
    specfile = build_specfile(tmp_path)
    args = {
        '--spec' : specfile,
        '<file>' : ['f1','-','f2']
    }
    main = Main(Scanner(Matcher(None)), Source([]), args)
    main.run()
    assert main.source.files == ['f1','-', 'f2']

def test_scan_source_stdin(tmp_path):
    specfile = build_specfile(tmp_path)
    args = {
        '--spec' : specfile,
        '<file>' : ['-']
    }
    main = Main(Scanner(Matcher(None)), Source([]), args)
    main.run()
    assert main.scanner.scanned == ["-"]

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

    return str(specfile)

class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher
        self.scanned = None # for testing what lines are passed into Scanner.scan()

    def scan(self, lines):
        self.scanned = lines

class Matcher:
    def __init__(self, spec):
        self.spec = spec

    def match(string):
        pass

class Source:
    def __init__(self, files):
        self.files = files

    def __iter__(self):
        return iter(self.files)
