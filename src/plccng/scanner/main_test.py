from .main import Main
from docopt import docopt
import pytest
from .structs import HasLexErrors
from ..spec import LexicalSpecError

def test_read_specfile_builds_matcher_spec(fs):
    createFile(fs, contents= '''
        skip WHITESPACE '\\s+'
        token MINUS '-'
    ''')
    string = "scan --spec=specfile"
    args = docopt(getDocString(), string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert len(main.Scanner.matcher.spec) == 2
    assert main.Scanner.matcher.spec.ruleList[0].isSkip == True
    assert main.Scanner.matcher.spec.ruleList[1].name == "MINUS"

def test_read_input_file_and_pass_to_source(fs):
    createFile(fs)
    string = "scan --spec=specfile f1 - f2"
    args = docopt(getDocString(), string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert main.Source.files == ['f1','-', 'f2']

def test_Source_is_scanned(fs):
    createFile(fs)
    string = "scan --spec=specfile f1 - f2"
    args = docopt(getDocString(), string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert main.Scanner.scanned == main.Source.files

def test_scan_stdin_symbol_when_input_files_not_specified(fs):
    createFile(fs)
    string = "scan --spec=specfile"
    args = docopt(getDocString(), string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    assert main.Scanner.scanned == ['-']

def test_print_scan_results(fs, capfd):
    createFile(fs)
    string = "scan --spec=specfile f1 - f2"
    args = docopt(getDocString(), string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    main.run(args)
    captured = capfd.readouterr()
    assert captured.out == f"Output of Scanner.scan({main.Scanner.scanned})\n"

def test_raise_HasLexerros(fs):
    createFile(fs, contents="this will raise LexError\n this too")
    string = "scan --spec=specfile f1 - f2"
    args = docopt(getDocString(), string)
    main = Main(ScannerSpy, SourceMock, MatcherMock)
    with pytest.raises(HasLexErrors) as exc_info:
        main.run(args)
    assert len(exc_info.value.lexErrors) == 2
    assert isinstance(exc_info.value.lexErrors[0], LexicalSpecError)

def createFile(fs, name="specfile", contents="token MINUS '-'"):
    fs.create_file(name, contents=contents)

def getDocString():
    return "Usage: plccng scan --spec=<specfile> [<file> ...]"

class ScannerSpy:
    def __init__(self, matcher):
        self.matcher = matcher
        self.scanned = None # for testing what lines are passed into Scanner.scan()

    def scan(self, lines):
        self.scanned = lines
        yield f"Output of Scanner.scan({lines})"

class MatcherMock:
    def __init__(self, spec):
        self.spec = spec

class SourceMock:
    def __init__(self, files):
        self.files = files

    def __iter__(self):
        return iter(self.files)
