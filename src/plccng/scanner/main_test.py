"""
Usage:
    plccng scan --spec=<specfile> [<file> ...]
"""

from .main import Main
from docopt import docopt

def test_read_specfile_builds_matcher_spec(fs):
    createFile(fs, contents= '''
        skip WHITESPACE '\\s+'
        token MINUS '-'
    ''')
    string = "scan --spec=specfile"
    args = docopt(__doc__, string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert len(main.Scanner.matcher.spec) == 2
    assert main.Scanner.matcher.spec.ruleList[0].isSkip == True
    assert main.Scanner.matcher.spec.ruleList[1].name == "MINUS"

def test_read_input_file_and_pass_to_source(fs):
    createFile(fs)
    string = "scan --spec=specfile f1 - f2"
    args = docopt(__doc__, string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert main.Source.files == ['f1','-', 'f2']

def test_scan_stdin_when_input_files_not_specified(fs):
    createFile(fs)
    string = "scan --spec=specfile"
    args = docopt(__doc__, string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert main.Source.files == ['-']

def createFile(fs, name="./specfile", contents="token MINUS '-'"):
    fs.create_file(name, contents=contents)

class ScannerSpy:
    def __init__(self, matcher):
        self.matcher = matcher
        self.scanned = None # for testing what lines are passed into Scanner.scan()

    def scan(self, lines):
        self.scanned = lines

class MatcherMock:
    def __init__(self, spec):
        self.spec = spec

    def match(string):
        pass

class SourceMock:
    def __init__(self, files):
        self.files = files

    def __iter__(self):
        return iter(self.files)

    def __next__(self):
        return 'line'
