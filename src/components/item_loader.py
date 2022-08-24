from typing import Tuple
from context import Context
from PIL import Image

import util


@util.context(lambda _, i: 'item(s) = \'%s\'' % i)
def format_items(context: Context, item: str) -> Tuple[str, str]:
    validate_item(item)
    
    if ',' in item:
        # Animated gif
        items = item.split(',')
        images = [format_item(context, i) for i in items]
        path = context.loader.save_gif(items[0], images)

        return path, None  # Don't search item names for multi-images
    else:
        # Single image
        image = format_item(context, item)
        path = context.loader.save_image(item, image)
    
        key = 'item.' + item.replace('/', '.').replace(':', '.')
        if key not in context.lang_json:
            key2 = 'block' + key[4:]
            if key2 not in context.lang_json:
                util.error('No item name found for key: %s or %s' % (key, key2))
            key = key2
        
        name = context.lang_json[key]

    return path, name


@util.context(lambda _, i: 'item = \'%s\'' % i)
def format_item(context: Context, item: str) -> Image.Image:
    validate_item(item)

    model = context.loader.load_item_model(item)
    util.require('parent' in model, 'Unsupported model without parent')
    
    parent = model['parent']
    util.require(parent == 'item/generated' or parent == 'item/handheld', 'Unsupported parent: %s' % parent)
    
    layer0 = model['textures']['layer0']
    _, img = context.loader.load_image(layer0)
    
    img = img.resize((64, 64), resample=Image.Resampling.NEAREST)
    return img


def validate_item(item: str):
    if '#' in item:
        util.error('No support for tags yet')
    if '{' in item:
        util.error('No support for items with NBT yet')
    



