from logging import getLogger, StreamHandler, Formatter

import os

LOG = getLogger('main')
LOG.addHandler((
    h := StreamHandler(),
    h.setFormatter(Formatter('%(levelname)s: %(message)s')),
    h
)[-1])

def resource_location(path: str) -> str:
    if ':' not in path:
        return 'minecraft:%s' % path
    return path

def walk(path: str):
    if os.path.isfile(path):
        yield path
    elif os.path.isdir(path):
        for sub in os.listdir(path):
            yield from walk(os.path.join(path, sub))


def prepare(root: str, path: str) -> str:
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def path_join(*parts):
    return os.path.normpath(os.path.join(*parts))


class InternalError(Exception):

    def __init__(self, reason: str):
        self.reason = reason
    
    def at(self, site: str):
        self.reason += '\n  at: ' + site
        return self
    
    def warning(self):
        LOG.warning(self)
    
    def __repr__(self) -> str: return self.reason
    def __str__(self) -> str: return self.reason


def require(condition: bool, reason: str):
    if not condition:
        error(reason)


def error(reason: str):
    raise InternalError(reason)

