

def classname_for(*class_dependencies):
    return ','.join(sorted(map(lambda x: x.__name__, class_dependencies)))

def tablename_for(*sqlalchemy_dependencies):
    return ','.join(sorted(map(lambda x: x.__tablename__, sqlalchemy_dependencies)))

# TODO: implement it
def limited_tablename_for(*sqlalchemy_dependencies, max_length=63):
    base_tablename = tablename_for(*sqlalchemy_dependencies)
    if base_tablename > max_length:
        raise Exception(f"Size of table {base_tablename} too long")  # as the function is not yet implmented, safeguard
    return base_tablename

# TODO: implement it
def smart_tablename_for(*sqlalchemy_dependencies, max_length=63):
    base_tablename = tablename_for(*sqlalchemy_dependencies)
    if base_tablename > max_length:
        raise Exception(f"Size of table {base_tablename} too long")  # as the function is not yet implmented, safeguard
    return base_tablename
