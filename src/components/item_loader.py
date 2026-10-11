from typing import Tuple, Mapping
from PIL import Image

from context import Context
from components import tag_loader, block_loader
from util import InternalError
from i18n import I18n

import util

CACHE = {}


def decode_item(item: Mapping[str, str] | str) -> str:
    """ Standardizes item/tag representations from {'item': 'foo'}, {'tag': 'foo'} to 'foo' and '#foo' """
    if isinstance(item, str):
        if item.startswith('tag:'):
            return '#%s' % item[4:] 
        else:
            return item
    if isinstance(item, dict):
        if 'tag' in item:
            return '#%s' % item['tag']
        elif 'item' in item:
            return item['item']
        else:
            util.error('Invalid format for an item: \'%s\'' % item)


def get_item_image(context: Context, item: str, placeholder: bool = True) -> Tuple[str, str | None]:
    """
    Loads an item image, based on a specific keyed representation of an item.
    The key may be an item ID ('foo:bar'), a tag ('#foo:bar'), or a csv list of item IDs ('foo:bar,foo:baz')
    Using a global cache, the image will be generated, and saved to the _images/ directory.
    For items that aren't render-able (for various reasons), this will use a placeholder image.
    Returns:
        src : str = The path to the item image (for use in href="", or src="")
        name : str = The translated name of the item (if a single item), or a localized generic name (if multiple items)
    """
    if item.endswith('.png'):
        # This is not an item image, it must be a image directly
        return context.convert_icon(item), None

    item = decode_item(item)

    # Patchouli icons can include data components. The static guide cannot
    # reproduce their dynamic overlays, but the underlying item model remains
    # a useful and accurate fallback icon.
    if '[' in item and item.endswith(']') and not item.startswith('#'):
        item = item.split('[', 1)[0]

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
        elif ',' in item:
            name = context.translate(I18n.ITEMS)
        return path, name
    
    util.require('{' not in item, 'Item : Item with NBT : \'%s\'' % item, True)

    name = None
    key = None  # A translation key, if this needs to be re-translated

    if item.startswith('#'):
        name = context.translate(I18n.TAG) % item
        items = tag_loader.load_item_tag(context, item[1:])
    elif ',' in item:
        name = context.translate(I18n.ITEMS)
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
        images = []
        for choice in items:
            try:
                images.append(create_item_image(context, choice))
            except InternalError as e:
                # Tags and comma-separated alternatives can contain an item whose
                # model is not renderable (for example a built-in entity model).
                # Keep the usable alternatives instead of losing the entire icon.
                if len(items) == 1:
                    raise
                e.prefix('Item Image Alternative').warning()
        util.require(images, 'Item Image(s) : No renderable alternatives : \'%s\'' % item, True)

        if len(images) == 1:
            path = context.loader.save_image(context.next_id('item'), images[0])
        else:
            # If any images are 64x64, then we need to resize them all to be 64x64 if we're saving a .gif
            if any(img.size == (64, 64) for img in images):
                images = [
                    img.resize((64, 64), resample=Image.NEAREST)
                    for img in images
                ]

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
    return create_item_model_image(context, item, model)


def create_item_model_image(context: Context, item: str, model: dict) -> Image.Image:
    if 'loader' in model:
        loader = model['loader']
        if loader in ('tfc:contained_fluid', 'tfc:fluid_container'):
            # Assume it's empty, and use a single layer item
            layer = model['textures']['base']
            img = context.loader.load_texture(layer)
            return img
        elif loader == 'tfc:trim':
            # Show the untrimmed armor item.
            return context.loader.load_texture(model['textures']['armor'])
        elif loader == 'neoforge:separate_transforms':
            # The in-game inventory uses the GUI perspective, not the held model.
            gui_model = model.get('perspectives', {}).get('gui', model.get('base'))
            util.require(gui_model is not None, 'Item Model : No GUI Perspective : \'%s\'' % item, True)
            if 'parent' in gui_model:
                gui_model = context.loader.load_model(gui_model['parent'])
            return create_item_model_image(context, item, gui_model)
        else:
            util.error('Item Model : Unknown Loader : \'%s\' at \'%s\'' % (loader, item), True)

    model, parent = resolve_item_model(context, item, model)
    if parent in (
        'minecraft:item/generated',
        'minecraft:item/handheld',
        'minecraft:item/handheld_rod',
        'tfc:item/handheld_flipped',
    ):
        # Simple single-layer item model
        layer0 = model['textures']['layer0']
        img = context.loader.load_texture(layer0)
        return img
    elif 'elements' in model:
        # A custom item can inherit elements from an item or block model.
        img = block_loader.create_block_model_image(context, item, model)
        img = img.resize((64, 64), resample=Image.NEAREST)
        return img
    else:
        util.error('Item Model : Unknown Parent \'%s\' : at \'%s\'' % (parent, item), True)


def resolve_item_model(context: Context, item: str, model: dict) -> tuple[dict, str]:
    """Follow ordinary model parents, retaining child texture overrides and elements."""
    textures = {}
    elements = None
    seen = set()
    current = model
    terminal_parents = {
        'minecraft:item/generated',
        'minecraft:item/handheld',
        'minecraft:item/handheld_rod',
        'tfc:item/handheld_flipped',
    }
    while True:
        textures = {**current.get('textures', {}), **textures}
        if elements is None and 'elements' in current:
            elements = current['elements']
        if 'parent' not in current:
            util.require(seen, 'Item Model : No Parent : \'%s\'' % item, True)
            break
        parent = util.resource_location(current['parent'])
        if parent in terminal_parents or parent.startswith('minecraft:builtin/'):
            break
        util.require(parent not in seen, 'Item Model : Cyclic Parent : \'%s\'' % item, True)
        seen.add(parent)
        try:
            current = context.loader.load_model(parent)
        except InternalError:
            break
    resolved = {**model, 'parent': parent, 'textures': textures}
    if elements is not None:
        resolved['elements'] = elements
    return resolved, parent

