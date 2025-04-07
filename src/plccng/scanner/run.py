from .main import Main
from .scanner import Scanner
from .source import Source
from .matcher import Matcher
from .structs import HasLexErrors

def run(args):
	try:
		Main(Scanner, Source, Matcher).run(args)
	except HasLexErrors as errors:
		_printErrors(errors.lexErrors)

def _printErrors(errorList):
	for error in errorList:
		print(error)
