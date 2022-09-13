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

    def __init__(self, reason: str, quiet: bool = False):
        self.reason = reason
        self.quiet = quiet
    
    def warning(self):
        if self.quiet:
            LOG.debug(self.reason)
        else:
            LOG.warning(self.reason)
    
    def prefix(self, other_reason: str) -> 'InternalError':
        return error('%s : %s' % (other_reason, self), self.quiet)
    
    def __repr__(self) -> str: return self.reason
    def __str__(self) -> str: return self.reason


def require(condition: bool, reason: str, quiet: bool = False):
    if not condition:
        error(reason, quiet)


def error(reason: str, quiet: bool = False):
    raise InternalError(reason, quiet)

