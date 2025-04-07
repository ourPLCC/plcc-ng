from plccng.spec import parseSpec
import sys
from .structs import HasLexErrors

class Main:
    def __init__(self, Scanner, Source, Matcher):
        self.Scanner = Scanner
        self.Source = Source
        self.Matcher = Matcher

    def run(self, args):
        self.Matcher = self._buildMatcher(args["--spec"])
        self.Scanner = self.Scanner(self.Matcher)
        self.Source = self._buildSource(args)
        results = list(self.Scanner.scan(list(self.Source)))
        self._printResults(results)

    def _printResults(self, results):
        for result in results:
            print(result)

    def _buildSource(self, args):
        files = args['<file>'] if len(args['<file>']) > 0 else ['-']
        return self.Source(files)

    def _buildMatcher(self, filePath):
        fileContents = self._loadSpec(filePath)
        spec, errors = parseSpec(fileContents)
        if errors:
            raise HasLexErrors(lexErrors=errors)
        return self.Matcher(spec.lexical)

    def _loadSpec(self, filePath):
        with open(filePath, "r") as f:
            return f.read()
