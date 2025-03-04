from . import rough


def split_rough(rough_):
    rough_lex = []
    for thing in rough_:
        if isinstance(thing, rough.Divider):
            break
        rough_lex.append(thing)

    rough_syn = []
    div = None
    for thing in rough_:
        if isinstance(thing, rough.Divider):
            div = thing
            break
        rough_syn.append(thing)

    rough_sems = []
    if div is not None:
        rough_sems = [[div]]
        for thing in rough_:
            if isinstance(thing, rough.Divider):
                rough_sems.append([])
            rough_sems[-1].append(thing)

    return rough_lex, rough_syn, rough_sems
