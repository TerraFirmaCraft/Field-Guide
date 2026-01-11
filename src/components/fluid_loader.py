from typing import Tuple, Mapping
from PIL import Image, ImageColor

from context import Context
from components import tag_loader
from util import InternalError
from i18n import I18n

import util
import colorsys

CACHE = {}

def decode_fluid(item: Mapping[str, str] | str) -> Tuple[str, int]:
    """ Assumes a FluidStackIngredient or FluidIngredient """
    amount = 0
    ingredient = None
    
    if isinstance(item, dict):
        if 'id' in item:
            ingredient = decode_fluid_ingredient(item['id'])
        elif 'ingredient' in item:
            ingredient = decode_fluid_ingredient(item['ingredient'])
        elif 'fluid' in item or 'tag' in item:
            ingredient = decode_fluid_ingredient(item)
        amount = 1000 if 'amount' not in item else item['amount']
    elif isinstance(item, str):
        ingredient = item
    
    if ingredient is None:
        util.error('Invalid format for a fluid: \'%s\'' % item)
    else:
        return ingredient, amount

def decode_fluid_ingredient(item: Mapping[str, str] | str) -> str:
    if isinstance(item, str):
        return item
    elif 'fluid' in item:
        return item['fluid']
    elif 'tag' in item:
        return '#' + item['tag']
    util.error('Could not decode fluid ingredient: %s' % item)

def get_fluid_image(context: Context, fluid_in: str, placeholder: bool = True) -> Tuple[str, str]:
    """
    Loads an fluid image, based on a specific keyed representation of an fluid.
    The key may be an fluid ID ('foo:bar') or a tag ('#foo:bar'), or a csv list of fluid IDs ('foo:bar,foo:baz')
    Using a global cache, the image will be generated, and saved to the _images/ directory.
    For items that aren't render-able (for various reasons), this will use a placeholder image.
    Returns:
        src : str = The path to the fluid image (for use in href="", or src="")
        name : str = The translated name of the fluid (if a single fluid), or a best guess (if a tag), or None (if csv)
    """
    fluid, amount = decode_fluid(fluid_in)

    if fluid in CACHE:
        path, name, key = CACHE[fluid]
        if key is not None:
            try:
                # Must re-translate the item each time, as the same image will be asked for in different localizations
                name = context.translate('fluid.' + key, 'block.' + key)
            except InternalError as e:
                e.warning()
        return path, name

    name = None
    key = None

    if fluid.startswith('#'):
        name = context.translate(I18n.TAG) % fluid
        fluids = tag_loader.load_fluid_tag(context, fluid[1:])
    elif ',' in fluid:
        fluids = fluid.split(',')
    else:
        fluids = [fluid]
    if len(fluids) == 1:
        key = fluids[0].replace('/', '.').replace(':', '.')
        try:
            name = context.translate('fluid.' + key, 'block.' + key)
        except InternalError as e:
            e.warning()

    try:
        images = [create_fluid_image(i) for i in fluids]
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
    if amount > 0:
        name = '%s mB %s' % (str(amount), name)
    return path, name

def create_fluid_image(fluid: str) -> Image.Image:
    path = fluid
    if ':' in path:
        _, path = fluid.split(':', 1)
    base = Image.open('assets/textures/fluid.png')
    base = base.resize((64, 64), resample=Image.NEAREST)
    if path not in FLUID_COLORS:
        util.LOG.debug('Fluid %s has no color specified.' % path)
        return base
    else:
        clr = ImageColor.getrgb(FLUID_COLORS[path])
        base = put_on_all_pixels(base, clr)
        return base
    

def put_on_all_pixels(img: Image, color: Tuple[int, int, int], dark_threshold: int = 50) -> Image:
    img = img.convert('HSV')
    hue, sat, val = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    for x in range(0, img.width):
        for y in range(0, img.height):
            dat = img.getpixel((x, y))
            tup = (int(hue * 255), int(sat * 255), int(dat[2] if val > dark_threshold else dat[2] * 0.5))
            img.putpixel((x, y), tup)
    img = img.convert('RGBA')
    return img

FLUID_COLORS = {
    # tfc fluids
    'brine': '#DCD3C9',
    'curdled_milk': '#FFFBE8',
    'limewater': '#B4B4B4',
    'lye': '#feffde',
    'milk_vinegar': '#FFFBE8',
    'olive_oil': '#6A7537',
    'olive_oil_water': '#4A4702',
    'tannin': '#63594E',
    'tallow': '#EDE9CF',
    'vinegar': '#C7C2AA',
    
    # alc
    'beer': '#C39E37',
    'cider': '#B0AE32',
    'rum': '#6E0123',
    'sake': '#B7D9BC',
    'vodka': '#DCDCDC',
    'whiskey': '#583719',
    'corn_whiskey': '#D9C7B7',
    'rye_whiskey': '#C77D51',

    # water
    'water': '#2245CB',
    'salt_water': '##4E63B9',
    'spring_water': '#8AA3FF',

    # addons
    'yak_milk': '#E8E8E8',
    'goat_milk': '#E8E8E8',
    'chocolate': '#756745',
}