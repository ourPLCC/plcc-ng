from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    name: str | None
