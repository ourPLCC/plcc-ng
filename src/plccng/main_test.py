# import pytest
# from .main import Main, __doc__
# from .scanner.main import Main as ScannerMain
# import io

# def test_help_command_short_option_prints_and_exits(capfd):
#     argv = ["-h"]
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out.strip() == __doc__.strip()

# def test_help_command_long_option_prints_and_exits(capfd):
#     argv = ["--help"]
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out.strip() == __doc__.strip()

# def test_pass_specfile_to_scanner(tmp_path):
#     specfilePath = build_specfile(tmp_path)
#     argv = ['scan', f'--spec={specfilePath}']
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     assert main.scannerMain.args == {
#         '--spec' : str(specfilePath),
#         '<file>' : ['-']
#     }

# def test_pass_file_arguments_to_scanner(tmp_path):
#     specfilePath = build_specfile(tmp_path)
#     argv = ['scan', f'--spec={specfilePath}', 'f1', '-', 'f2']
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     assert main.scannerMain.args == {
#         '--spec' : str(specfilePath),
#         '<file>' : ['f1','-','f2']
#     }

# def test_scan_missing_specfile_prints_error_and_exits(capfd):
#     argv = ['scan']
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out == "Invalid arguments, Enter 'plccng -h' for help.\n"


# def test_no_arguments_prints_error_message_and_exits(capfd):
#     argv = []
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out == "Invalid arguments, Enter 'plccng -h' for help.\n"

# def test_incorrect_arguments_prints_error_message_and_exits(capfd):
#     argv = ['blahblah']
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out == "Invalid arguments, Enter 'plccng -h' for help.\n"

# def test_help_command_prints_and_exits_before_scan(capfd, tmp_path):
#     specfile = build_specfile(tmp_path)
#     argv = ["--help", "scan", f'--spec={specfile}']
#     main = Main(ScannerMain(Scanner(Matcher(None)), Source([]), None))
#     with pytest.raises(SystemExit):
#         main.run(stdin=None, stdout=None, stderr=None, argv=argv)
#     captured = capfd.readouterr()
#     assert captured.out.strip() == __doc__.strip()
#     assert main.scannerMain.args == None

# def build_specfile(tmp_path):
#     specfile = tmp_path / "specfile.json"
#     file_content = """
#     [
#         {
#             "type": "Token",
#             "name": "MINUS",
#             "regex": "-"
#         },
#         {
#             "type": "Skip",
#             "name": "WHITESPACE",
#             "regex": "\\\\s+"
#         },
#         {
#             "type": "Token",
#             "name": "ONETWOTHREE",
#             "regex": "123"
#         },
#         {
#             "type": "Token",
#             "name": "NUMBER",
#             "regex": "\\\\d+"
#         }
#     ]
#     """
#     with open(specfile, 'w') as f:
#         f.write(file_content)

#     return specfile

# class Scanner:
#     def __init__(self, matcher):
#         self.matcher = matcher

#     def scan(self, lines):
#         self.scanned = lines

# class Matcher:
#     def __init__(self, spec):
#         self.spec = spec

# class Source:
#     def __init__(self, files):
#         self.files = files

#     def __iter__(self):
#         return iter(self.files)
