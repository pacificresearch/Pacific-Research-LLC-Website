from . import ashby, greenhouse, lever

_REG = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}


def get(kind: str):
    return _REG[kind]
