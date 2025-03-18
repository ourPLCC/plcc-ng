from dataclasses import dataclass

from ..rough import Block
from .TargetLocator import TargetLocator


@dataclass
class CodeFragment:
    targetLocator: TargetLocator
    block: Block
