from . import ashby, greenhouse, lever, workday

_REG = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "workday": workday}


def get(kind: str):
    return _REG[kind]
