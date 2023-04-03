from typing import Tuple, Mapping
from PIL import Image

from context import Context
from components import tag_loader, block_loader
from util import InternalError

import util
import i18n
import colorsys

CACHE = {}

def decode_fluid(context: Context, item: Mapping[str, str] | str) -> Tuple[str, int]:
    """ Assumes a FluidStackIngredient or FluidIngredient """
    amount = -1
    if isinstance(item, dict):
        ingredient = None
        if 'ingredient' in item:
            ingredient = decode_fluid_ingredient(item['ingredient'])
            if 'amount' in item:
                amount = item['amount']
        elif 'fluid' in item or 'tag' in item:
            ingredient = decode_fluid_ingredient(item)
    elif isinstance(item, str):
        ingredient = decode_fluid_ingredient({'fluid': item})
    
    if ingredient is None:
        util.error('Invalid format for an item: \'%s\'' % item)
    else:
        path, name = get_fluid_image(context, ingredient, True)
        if amount > 0:
            name = '%s %s' % (str(amount), name)
        return path, name

def decode_fluid_ingredient(item: Mapping[str, str]) -> str:
    if 'fluid' in item:
        return item['fluid']
    elif 'tag' in item:
        return '#' + item['tag']

def get_fluid_image(context: Context, fluid: str, placeholder: bool = True) -> Tuple[str, str]:
    """
    Loads an fluid image, based on a specific keyed representation of an fluid.
    The key may be an fluid ID ('foo:bar') or a tag ('#foo:bar'), or a csv list of fluid IDs ('foo:bar,foo:baz')
    Using a global cache, the image will be generated, and saved to the _images/ directory.
    For items that aren't render-able (for various reasons), this will use a placeholder image.
    Returns:
        src : str = The path to the fluid image (for use in href="", or src="")
        name : str = The translated name of the fluid (if a single fluid), or a best guess (if a tag), or None (if csv)
    """
    fluid = decode_fluid(fluid)

    if fluid in CACHE:
        path, name, key = CACHE[fluid]
        if key is not None:
            try:
                # Must re-translate the item each time, as the same image will be asked for in different localizations
                name = context.translate('fluid.' + key)
            except InternalError as e:
                e.warning()
        return path, name

    name = None
    key = None

    if fluid.startswith('#'):
        try:
            name = context.translate(i18n.key('tag.%s' % fluid))
        except InternalError as e:
            e.prefix('Tag \'%s\'' % fluid).warning()

            # Use a fallback name
            name = fluid.split(':')[1].replace('_', ' ').replace('/', ', ').title()
        fluids = tag_loader.load_fluid_tag(context, fluid[1:])
    elif ',' in fluid:
        items = fluid.split(',')
    else:
        items = [fluid]
    if len(items) == 1:
        key = items[0].replace('/', '.').replace(':', '.')
        name = context.translate('fluid.' + key)
    
    try:
        images = [create_fluid_image(context, i) for i in fluids]
        if len(images) == 1:
            path = context.loader.save_image(context.next_id('fluid'), images[0])
        else:
            path = context.loader.save_gif(context.next_id('fluid'), images)
    except InternalError as e:
        e.prefix('Fluid Image(s)').warning()

        if placeholder:
            # Fallback to using the placeholder image
            path = '../../_images/fluid.png'
        else:
            raise e

    CACHE[fluid] = path, name, key
    return path, name

def create_fluid_image(context: Context, fluid: str) -> Image.Image:
    _, path = fluid.split(',', 1)
    if path not in FLUID_COLORS:
        util.error('Fluid %s has no color specified.' % path)
    else:
        base = context.loader.load_explicit_texture('fluid.png')
        base = put_on_all_pixels(base, FLUID_COLORS[path])
        return base
    

def put_on_all_pixels(img: Image, color: Tuple[int, int, int], dark_threshold: int = 50) -> Image:
    img = img.convert('RGBA')
    _, _, _, alpha = img.split()
    img = img.convert('HSV')
    hue, sat, val = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    for x in range(0, img.width):
        for y in range(0, img.height):
            dat = img.getpixel((x, y))
            tup = (int(hue * 255), int(sat * 255), int(dat[2] if val > dark_threshold else dat[2] * 0.5))
            img.putpixel((x, y), tup)
    img = img.convert('RGBA')
    img.putalpha(alpha)
    return img

FLUID_COLORS = {
    'water': (0, 0, 230),
    'salt_water': (47, 73, 168),
    'spring_water': (145, 145, 255),
    'limewater': (201, 203, 172),
    'milk': (231, 231, 231),
    'curdled_milk': (224, 226, 197),
}