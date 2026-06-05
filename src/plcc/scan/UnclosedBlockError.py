from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..lines import Line

if TYPE_CHECKING:
    from ..spec.lexical.TokenRule import TokenRule
    from ..spec.lexical.SkipRule import SkipRule


@dataclass
class UnclosedBlockError:
    line: Line
    column: int
    rule: TokenRule | SkipRule
