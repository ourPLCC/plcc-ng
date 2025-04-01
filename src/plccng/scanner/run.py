from .main import Main
from .main_test import ScannerSpy, SourceMock, MatcherMock # TODO: replace with real classes when merged
from .structs import HasLexErrors

def run(args):
	try:
		Main(ScannerSpy, SourceMock, MatcherMock).run(args)
	except HasLexErrors as errors:
		_printErrors(errors.lexErrors)

def _printErrors(errorList):
	for error in errorList:
		print(error)
