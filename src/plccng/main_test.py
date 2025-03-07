import pytest
from .main import Main, __doc__
from .scanner.main import Main as ScannerMain
import io

def test_help_command_short_option_prints_and_exits(capfd):
    argv = ["-h"]
    main = Main(Scanner(Matcher(None)), Source([]))
    with pytest.raises(SystemExit):
        main.run(stdin=None, stdout=None, stderr=None, argv=argv)
    captured = capfd.readouterr()
    assert captured.out.strip() == __doc__.strip()

def test_help_command_long_option_prints_and_exits(capfd):
    argv = ["--help"]
    main = Main(Scanner(Matcher(None)), Source([]))
    with pytest.raises(SystemExit):
        main.run(stdin=None, stdout=None, stderr=None, argv=argv)
    captured = capfd.readouterr()
    assert captured.out.strip() == __doc__.strip()

def test_specfile_argument_pass_to_scanner(tmp_path):
    specfilePath = str(tmp_path / "specfile.json")
    argv = ['scan', f'--spec={specfilePath}']
    main = Main(Scanner(Matcher(None)), Source([]))
    main.run(stdin=None, stdout=None, stderr=None, argv=argv)
    assert main.scannerMain.args == {
        '--spec' : specfilePath,
        '<file>' : []
    }

# def test_file_argument_pass_to_scanner(tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = ['scan', f'--spec={specfile}', 'f1', 'f2']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     assert main.scannerMain.args == {
#         '--spec' : tmp_path,
#         '<file>' : ['f1', 'f2']
#     }



# def test_read_specfile_adds_stdin_file_path_to_source(tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = [f'--spec={specfile}']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     assert main.source.files == ["-"]

# def test_missing_specfile_argument_prints_error_message_and_exits(capfd):
#     argv = ['f1', 'f2']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out == "Missing --spec argument\n"

# def test_no_arguments_prints_error_message_and_exits(capfd):
#     argv = []
#     main = Main(Scanner(Matcher(None)), Source([]))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out == "Missing --spec argument\n"

# def test_read_input_file_and_pass_to_source(tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = [f'--spec={specfile}', 'f1', 'f2']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     assert main.source.files == ['f1', 'f2']

# def test_stdin_pass_to_source(tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = [f'--spec={specfile}', '-']
#     stdin = io.StringIO('123      45')
#     main = Main(Scanner(Matcher(None)), Source([]))
#     main.run(stdin, stdout=None, stderr=None, argv=argv)
#     assert main.source.files == ['-']

# def test_stdin_pass_to_source_after_input_file(tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = [f'--spec={specfile}', 'f1', 'f2', '-']
#     stdin = io.StringIO('123      45')
#     main = Main(Scanner(Matcher(None)), Source([]))
#     main.run(stdin=stdin, stdout=None, stderr=None, argv=argv)
#     assert main.source.files == ['f1', 'f2', '-']

# def test_help_command_prints_and_exits_before_matcher_spec_is_built(capfd, tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = ["--help", f'--spec={specfile}']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out.strip() == __doc__.strip()
#     assert main.scanner.matcher.spec == None

# def test_help_command_prints_and_exits_before_source_files_added(capfd):
#     argv = ["--help", 'f1']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out.strip() == __doc__.strip()
#     assert main.source.files == []

# def test_scan_source_stdin(tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = [f'--spec={specfile}']
#     main = Main(Scanner(Matcher(None)), Source([]))
#     main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     assert main.scanner.scanned == ["-"]

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

class Scanner:
    def __init__(self, matcher):
        self.matcher = matcher
        self.scanned = None # for testing what is passed into Scanner.scan()

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
