def column(model, name):
    return model.__table__.columns[name]


def foreign_key_targets(model, name):
    return {fk.target_fullname for fk in column(model, name).foreign_keys}


def constraint_names(model, kind=None):
    constraints = model.__table__.constraints
    if kind is not None:
        constraints = [constraint for constraint in constraints if isinstance(constraint, kind)]
    return {constraint.name for constraint in constraints}


def relationship_names(model):
    return set(model.__mapper__.relationships.keys())
