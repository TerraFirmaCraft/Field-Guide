from logging import getLogger, StreamHandler, Formatter
from typing import Dict, Any

import os

LOG = getLogger('main')
LOG.addHandler((
    h := StreamHandler(),
    h.setFormatter(Formatter('%(levelname)s: %(message)s')),
    h
)[-1])

Keyable = Dict[str, Any]

def path_join(*parts):
    return os.path.normpath(os.path.join(*parts))