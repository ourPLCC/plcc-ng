from dataclasses import dataclass, KW_ONLY


@dataclass(frozen=True)
class CapturingSymbol:
    altName: str | None = None
    _: KW_ONLY
    isCapturing: bool = True

    def getAttributeName(self):
        if self.altName is not None:
            return self.altName
        if self.isTerminal:
            return self.name.lower()
        return self.name[:1].lower() + self.name[1:]
