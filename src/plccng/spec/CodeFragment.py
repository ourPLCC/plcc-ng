from plccng.roughparse.Block import Block
from plccng.spec.TargetLocator import TargetLocator


from dataclasses import dataclass


@dataclass
class CodeFragment:
    targetLocator: TargetLocator
    block: Block
