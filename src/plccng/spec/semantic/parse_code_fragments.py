from plccng.spec.structs import CodeFragment
from plccng.spec.structs import TargetLocator
from plccng.lineparse.Line import Line
from plccng.roughparse.Block import Block
from .parse_target_locator import parse_target_locator

def parse_code_fragments(lines_and_blocks):
    locators_and_blocks = parse_locators(lines_and_blocks)
    return list(parse_fragments(locators_and_blocks))

def parse_locators(lines_and_blocks):
    for locatorOrBlock in lines_and_blocks:
        if not isEmpty(locatorOrBlock):
            yield parse_target_locator(locatorOrBlock) if isinstance(locatorOrBlock, Line) else locatorOrBlock

def parse_fragments(locatorsOrBlocks):
    locatorsOrBlocks = list(locatorsOrBlocks)
    i = 0
    while i < len(locatorsOrBlocks):
        if isLocator(locatorsOrBlocks, i) and isBlock(locatorsOrBlocks, i+1):
            yield CodeFragment(locatorsOrBlocks[i], locatorsOrBlocks[i+1])
            i += 2
        elif isLocator(locatorsOrBlocks, i) and isLocator(locatorsOrBlocks, i+1):
            yield CodeFragment(locatorsOrBlocks[i], None)
            i += 1
        elif isBlock(locatorsOrBlocks, i) and isBlock(locatorsOrBlocks, i+1):
            yield CodeFragment(None, locatorsOrBlocks[i])
            i += 1
        elif isBlock(locatorsOrBlocks, i) and isLocator(locatorsOrBlocks, i+1):
            yield CodeFragment(None, locatorsOrBlocks[i])
            i += 1
        elif isLocator(locatorsOrBlocks, i):
            yield CodeFragment(locatorsOrBlocks[i], None)
            i += 1
        elif isBlock(locatorsOrBlocks, i):
            yield CodeFragment(None, locatorsOrBlocks[i])
            i += 1
        else:
            raise TypeError(f'{type(locatorsOrBlocks[i])}')

def isBlock(locatorsOrBlocks, i):
    return isType(locatorsOrBlocks, i, Block)

def isLocator(locatorsOrBlocks, i):
    return isType(locatorsOrBlocks, i, TargetLocator)

def isType(locatorsOrBlocks, i, Type):
    return i < len(locatorsOrBlocks) and isinstance(locatorsOrBlocks[i], Type)

def isEmpty(locatorOrBlock):
    if locatorOrBlock is None:
        return True
    if isinstance(locatorOrBlock, Line):
        s = locatorOrBlock.string
        return s is None or s.strip() == ''
    return False
