from dataclasses import dataclass

@dataclass(frozen=True)
class S:
    name: str
    isCapturing: bool = True
    altName: str | None = None
    isTerminal: bool = False
    isLhs: bool = False

    def getAttributeName(self):
        if self.altName is None:
            if self.isTerminal:
                return self.name.lower()
            else:
                return self.name
        else:
            return self.altName.lower()

    def getClassName(self):
        if self.isLhs:
            if self.altName is None:
                return self.name.capitalize()
            else:
                return self.altName
        else:
            if self.isTerminal:
                return 'Token'
            else:
                return self.name.capitalize()
