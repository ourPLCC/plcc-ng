from .main import Main
from .main_test import ScannerSpy, SourceMock, MatcherMock # TODO: replace with real classes when merged

def run(args):
	Main(ScannerSpy, SourceMock, MatcherMock).run(args)
