from logging import getLogger, StreamHandler, Formatter

import os

LOG = getLogger('main')
LOG.addHandler((
    h := StreamHandler(),
    h.setFormatter(Formatter('%(levelname)s: %(message)s')),
    h
)[-1])


def path_join(*parts):
    return os.path.normpath(os.path.join(*parts))


class InternalError(Exception):

    def __init__(self, reason: str):
        self.reason = reason
    
    def at(self, site: str):
        self.reason += '\n  at: ' + site
        return self
    
    def warning(self, category_id: str = None, entry_id: str = None):
        if category_id:
            self.at('entry = \'%s\'' % entry_id)
        if entry_id:
            self.at('category = \'%s\'' % category_id)
        LOG.warning(self)
    
    def __repr__(self) -> str: return self.reason
    def __str__(self) -> str: return self.reason


def require(condition: bool, reason: str):
    if not condition:
        error(reason)


def error(reason: str):
    raise InternalError(reason)


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
