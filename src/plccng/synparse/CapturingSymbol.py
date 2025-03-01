from dataclasses import dataclass


@dataclass(frozen=True)
class CapturingSymbol:
    altName: str | None = None
    pass

    def getAttributeName(self):
        if self.altName == None:
            return self.name.lower()
        else:
            return self.altName.lower()
