import json

class Main:
    def __init__(self, Scanner, Source, Matcher):
        self.Scanner = Scanner
        self.Source = Source
        self.Matcher = Matcher

    def run(self, args):
        self.Matcher = self._buildMatcher(args["--spec"])
        self.Scanner = self.Scanner(self.Matcher)
        self.Source = self._buildSource(args["<file>"])

        self.Scanner.scan(list(self.Source))

    def _buildSource(self, files):
        return self.Source(files)

    def _buildMatcher(self, filePath):
        with open(filePath, "r") as file:
            data = json.load(file)
            return self.Matcher(filePath)

