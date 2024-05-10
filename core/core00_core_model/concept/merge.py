from ..utils.naming import classname_for


def merge_concepts(*concepts):
    return type(classname_for(*concepts), concepts, {})
