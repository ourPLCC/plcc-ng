import json

class Main:
    def __init__(self, Scanner, Source):
        self.Scanner = Scanner
        self.Source = Source

    def run(self, args):
        self.Scanner = self._buildScanner(args["--spec"])
        self.Source = self._buildSource(args["<file>"])

        self.Scanner.scan(list(self.Source))

    def _buildScanner(self, filePath):
        with open(filePath, "r") as file:
            data = json.load(file)
            return self.Scanner(data)

    def _buildSource(self, files):
        return self.Source(files)

    # def _addSourceFiles(self, filePaths):
    #     return self.Source(filePaths)
        # for filePath in filePaths:
        #     self.source.files.append(filePath)
