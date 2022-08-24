from typing import Tuple
from PIL import Image

from context import Context
from components import tag_loader, block_loader

import util

CACHE = {}


@util.context(lambda _, i: 'item(s) = \'%s\'' % i)
def get_item_image(context: Context, item: str) -> Tuple[str, str]:
    util.require('{' not in item, 'No support for items with NBT yet', muted=True)

    if item in CACHE:
        return CACHE[item]
    
    name = None

    if item.startswith('#'):
        # Guess the name based on the tag
        name = item.split(':')[1].replace('_', ' ').replace('/', ',').title()
        items = tag_loader.load_item_tag(context, item[1:])
    elif ',' in item:
        items = item.split(',')
    else:
        items = [item]
    
    # Create images for each item. Discard items we can't create images for
    images = []
    errors = []
    for i in items:
        try:
            images.append(create_item_image(context, i))
        except util.InternalError as e:
            errors.append(e)
    
    util.require(images, 'Error(s) building item images:\n%s' % '\n'.join(map(str, errors)), muted=any(e.muted for e in errors))

    if len(images) == 1:
        path = context.loader.save_image(context.next_id('item_'), images[0])

        # Inspect the lang.json for a single item's name
        key = 'item.' + item.replace('/', '.').replace(':', '.')
        if key in context.lang_json:
            name = context.lang_json[key]
        else:
            key = 'block' + key[4:]
            if key in context.lang_json:
                name = context.lang_json[key]

    else:
        path = context.loader.save_gif(context.next_id('item_'), images)

    CACHE[item] = path, name

    return path, name


@util.context(lambda _, i: 'item = \'%s\'' % i)
def create_item_image(context: Context, item: str) -> Image.Image:

    model = context.loader.load_item_model(item)
    util.require('parent' in model, 'Unsupported model without parent')
    
    if 'loader' in model:
        loader = model['loader']
        if loader == 'tfc:contained_fluid':
            # Assume it's empty, and use a single layer item
            layer = model['textures']['base']
            _, img = context.loader.load_image(layer)
            img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
            return img
        else:
            util.error('Unsupported loader: %s' % loader)

    parent = model['parent']
    if parent in (
        'item/generated',
        'item/handheld',
        'minecraft:item/handheld_rod',
        'tfc:item/handheld_flipped',
    ):
        # Simple single-layer item model
        layer0 = model['textures']['layer0']
        _, img = context.loader.load_image(layer0)
        img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
        return img
    elif parent.startswith('tfc:block/'):
        # Block model
        block_model = context.loader.load_model(parent)
        img = block_loader.create_block_model_image(context, block_model)
        img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
        return img
    else:
        util.error('Unsupported parent: %s' % parent, muted=True)

