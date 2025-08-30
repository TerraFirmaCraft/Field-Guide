from context import Context
from loader import Loader
from typing import List

def load_fluid_tag(context: Context, identifier: str) -> List[str]:
    return sort_tag_elements(context, identifier, Loader.load_fluid_tag)

def load_item_tag(context: Context, identifier: str) -> List[str]:
    return sort_tag_elements(context, identifier, Loader.load_item_tag)

def load_block_tag(context: Context, identifier: str) -> List[str]:
    return sort_tag_elements(context, identifier, Loader.load_block_tag)

def sort_tag_elements(context: Context, identifier: str, load_func):
    tag = []
    for e in load_tag_elements(context, identifier, load_func):
        if e not in tag:
            tag.append(e)
    return tag

def load_tag_elements(context: Context, identifier: str, load_func):
    json = load_func(context.loader, identifier)
    for e in json['values']:
        if isinstance(e, dict):
            yield e['id']
        elif e.startswith('#'):
            yield from load_tag_elements(context, e[1:], load_func)
        else:
            yield e
