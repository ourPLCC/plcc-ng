from plccng.spec.Symbol import Symbol


from dataclasses import dataclass


@dataclass(frozen=True)
class Terminal(Symbol):
    pass
