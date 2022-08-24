from logging import getLogger, StreamHandler, Formatter

import os

LOG = getLogger('main')
LOG.addHandler((
    h := StreamHandler(),
    h.setFormatter(Formatter('%(levelname)s: %(message)s')),
    h
)[-1])


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

    def __init__(self, reason: str, muted):
        self.reason = reason
        self.muted = muted
    
    def at(self, site: str):
        self.reason += '\n  at: ' + site
        return self
    
    def warning(self, category_id: str = None, entry_id: str = None):
        if category_id:
            self.at('entry = \'%s\'' % entry_id)
        if entry_id:
            self.at('category = \'%s\'' % category_id)
        if self.muted:
            LOG.debug(self)
        else:
            LOG.warning(self)
    
    def __repr__(self) -> str: return self.reason
    def __str__(self) -> str: return self.reason


def require(condition: bool, reason: str, muted: bool = False):
    if not condition:
        error(reason, muted)


def error(reason: str, muted: bool = False):
    raise InternalError(reason, muted)


def context(formatter):
    def decorate(f):
        l_formatter = formatter
        def apply(*args):
            try:
                return f(*args)
            except InternalError as e:
                raise e.at(l_formatter(*args))
        return apply
    return decorate
