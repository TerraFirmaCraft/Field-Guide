from typing import Tuple
from PIL import Image

from context import Context
from components import tag_loader, block_loader
from util import InternalError

import util
import i18n

CACHE = {}


def get_item_image(context: Context, item: str, placeholder: bool = True) -> Tuple[str, str]:
    """
    Loads an item image, based on a specific keyed representation of an item.
    The key may be an item ID ('foo:bar'), a tag ('#foo:bar'), or a csv list of item IDs ('foo:bar,foo:baz')
    Using a global cache, the image will be generated, and saved to the _images/ directory.
    For items that aren't render-able (for various reasons), this will use a placeholder image.
    Returns:
        src : str = The path to the item image (for use in href="", or src="")
        name : str = The translated name of the item (if a single item), or a best guess (if a tag), or None (if csv)
    """

    if item in CACHE:
        path, name, key = CACHE[item]
        if key is not None:
            try:
                # Must re-translate the item each time, as the same image will be asked for in different localizations
                name = context.translate(
                    'item.' + key,
                    'block.' + key
                )
            except InternalError as e:
                e.warning()
        return path, name
    
    util.require('{' not in item, 'Item : Item with NBT : \'%s\'' % item, True)

    name = None
    key = None  # A translation key, if this needs to be re-translated

    if item.startswith('#'):
        try:
            # Use a special translation key for the tag, if one exists.
            name = context.translate(i18n.key('tag.%s' % item))
        except InternalError as e:
            e.prefix('Tag \'%s\'' % item).warning()

            # Use a fallback name
            name = item.split(':')[1].replace('_', ' ').replace('/', ', ').title()
        items = tag_loader.load_item_tag(context, item[1:])
    elif ',' in item:
        items = item.split(',')
    else:
        items = [item]
    
    if len(items) == 1:
        key = items[0].replace('/', '.').replace(':', '.')
        name = context.translate(
            'item.' + key,
            'block.' + key
        )
    
    try:
        # Create images for each item.
        images = [create_item_image(context, i) for i in items]

        if len(images) == 1:
            path = context.loader.save_image(context.next_id('item'), images[0])
        else:
            path = context.loader.save_gif(context.next_id('item'), images)
    except InternalError as e:
        e.prefix('Item Image(s)').warning()

        if placeholder:
            # Fallback to using the placeholder image
            path = '../../_images/placeholder_64.png'
        else:
            raise e

    CACHE[item] = path, name, key
    return path, name    


def create_item_image(context: Context, item: str) -> Image.Image:

    model = context.loader.load_item_model(item)
    util.require('parent' in model, 'Item Model : No Parent : \'%s\'' % item, True)
    
    if 'loader' in model:
        loader = model['loader']
        if loader == 'tfc:contained_fluid':
            # Assume it's empty, and use a single layer item
            layer = model['textures']['base']
            img = context.loader.load_texture(layer)
            img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
            return img
        else:
            util.error('Item Model : Unknown Loader : \'%s\' at \'%s\'' % (loader, item), True)

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
        util.error('Item Model : Unknown Parent \'%s\' : at \'%s\'' % (parent, item), True)

