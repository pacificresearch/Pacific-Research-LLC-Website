from . import ashby, greenhouse, lever, oracle, workday

_REG = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby, "workday": workday, "oracle": oracle}


def get(kind: str):
    return _REG[kind]
