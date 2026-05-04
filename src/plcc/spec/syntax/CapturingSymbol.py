from dataclasses import dataclass, KW_ONLY


@dataclass(frozen=True)
class CapturingSymbol:
    altName: str | None = None
    _: KW_ONLY
    isCapturing: bool = True

    def getAttributeName(self):
        if self.altName is None:
            return self.name.lower()
        else:
            return self.altName.lower()
