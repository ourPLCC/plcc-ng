from .iterate_rough import iterate_rough


def parse_rough(thing, file=None, startLineNumber=1):
    errors = []
    def collect(error):
        nonlocal errors
        errors.append(error)

    return list(iterate_rough(thing, handler=collect, file=file, startLineNumber=startLineNumber)), errors
