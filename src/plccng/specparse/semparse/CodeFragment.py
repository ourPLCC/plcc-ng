from dataclasses import dataclass

from ..roughparse import Block
from .TargetLocator import TargetLocator


@dataclass
class CodeFragment:
    targetLocator: TargetLocator
    block: Block
