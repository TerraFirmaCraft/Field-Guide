from typing import Tuple
from PIL import Image

from context import Context
from components import tag_loader, block_loader

import util

CACHE = {}


def get_item_image(context: Context, item: str) -> Tuple[str, str]:
    """
    Loads an item image, based on a specific keyed representation of an item.
    The key may be an item ID ('foo:bar'), a tag ('#foo:bar'), or a csv list of item IDs ('foo:bar,foo:baz')
    Using a global cache, the image will be generated, and saved to the _images/ directory.
    Returns:
        src : str = The path to the item image (for use in href="", or src="")
        name : str = The translated name of the item (if a single item), or a best guess (if a tag), or None (if csv)
    """

    util.require('{' not in item, 'Item : Item with NBT : \'%s\'' % item)

    if item in CACHE:
        return CACHE[item]
    
    name = None

    if item.startswith('#'):
        # Guess the name based on the tag
        name = item.split(':')[1].replace('_', ' ').replace('/', ', ').title()
        items = tag_loader.load_item_tag(context, item[1:])
    elif ',' in item:
        items = item.split(',')
    else:
        items = [item]
    
    # Create images for each item.
    images = [create_item_image(context, i) for i in items]
    
    if len(images) == 1:
        path = context.loader.save_image(context.next_id('item'), images[0])
        name = items[0].replace('/', '.').replace(':', '.')
        name = context.translate(
            'item.' + name,
            'block.' + name
        )
    else:
        path = context.loader.save_gif(context.next_id('item'), images)

    CACHE[item] = path, name
    return path, name


def create_item_image(context: Context, item: str) -> Image.Image:

    model = context.loader.load_item_model(item)
    util.require('parent' in model, 'Item Model : No Parent : \'%s\'' % item)
    
    if 'loader' in model:
        loader = model['loader']
        if loader == 'tfc:contained_fluid':
            # Assume it's empty, and use a single layer item
            layer = model['textures']['base']
            img = context.loader.load_texture(layer)
            img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
            return img
        else:
            util.error('Item Model : Unknown Loader : \'%s\' at \'%s\'' % (loader, item))

    parent = util.resource_location(model['parent'])
    if parent in (
        'minecraft:item/generated',
        'minecraft:item/handheld',
        'minecraft:item/handheld_rod',
        'tfc:item/handheld_flipped',
    ):
        # Simple single-layer item model
        layer0 = model['textures']['layer0']
        img = context.loader.load_texture(layer0)
        img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
        return img
    elif parent.startswith('tfc:block/') or parent.startswith('minecraft:block/'):
        # Block model
        block_model = context.loader.load_model(parent)
        img = block_loader.create_block_model_image(context, item, block_model)
        img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
        return img
    else:
        util.error('Item Model : Unknown Parent \'%s\' : at \'%s\'' % (parent, item))

