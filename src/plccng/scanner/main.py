import json

class Main:
    def __init__(self, scanner, source, args):
        self.scanner = scanner
        self.source = source
        self.args = args

    def run(self):
        if self.args["--spec"]:
            self._buildMatcherSpecFromSpecfile(self.args["--spec"])

            self._configureSourceFiles(self.args["<file>"])

        self.scanner.scan(list(self.source))

    def _buildMatcherSpecFromSpecfile(self, filePath):
        with open(filePath, "r") as file:
            data = json.load(file)
            self.scanner.matcher.spec = data

    def _configureSourceFiles(self, filePaths):
        if filePaths:
            self._appendSourceFiles(filePaths)
        else:
            self.source.files.append("-")

    def _appendSourceFiles(self, filePaths):
        for filePath in filePaths:
            self.source.files.append(filePath)
