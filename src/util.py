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

def anyof(dict, *args):
    for arg in args:
        if arg in dict:
            return dict[arg]
    error('None of %s in %s' % (str(args), str(dict)))
    return None

def walk(path: str):
    if os.path.isfile(path):
        yield path
    elif os.path.isdir(path):
        for sub in os.listdir(path):
            yield from walk(os.path.join(path, sub))

def load_html(template_name: str) -> str:
    with open(path_join('assets/templates', template_name + '.html'), 'r', encoding='utf-8') as f:
        return f.read()

def write_html(*path_parts: str, html: str):
    path = path_join(*path_parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def path_join(*parts):
    return os.path.normpath(os.path.join(*parts))


class InternalError(Exception):

    def __init__(self, reason: str, quiet: bool = False):
        self.reason = reason
        self.quiet = quiet
    
    def warning(self, loud: bool = False):
        if self.quiet and not loud:
            LOG.debug(self.reason)
        else:
            LOG.warning(self.reason)
    
    def prefix(self, other_reason: str) -> 'InternalError':
        return InternalError('%s : %s' % (other_reason, self), self.quiet)
    
    def __repr__(self) -> str: return self.reason
    def __str__(self) -> str: return self.reason


def require(condition: bool, reason: str, quiet: bool = False):
    if not condition:
        error(reason, quiet)


def error(reason: str, quiet: bool = False):
    raise InternalError(reason, quiet)

