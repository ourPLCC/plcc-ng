from plccng.roughparse import Block
from .TargetLocator import TargetLocator


from dataclasses import dataclass


@dataclass
class CodeFragment:
    targetLocator: TargetLocator
    block: Block
