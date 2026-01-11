from typing import Tuple, Mapping
from PIL import Image, ImageColor

from context import Context
from components import tag_loader, colorization
from util import InternalError
from i18n import I18n

import util

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

def get_fluid_bucket_image(context: Context, fluid_in: str | dict, placeholder: bool = True) -> Tuple[str, str]:
    """
    Creates a fluid bucket image with the fluid colorized.
    Returns:
        src : str = The path to the bucket image
        name : str = The translated name with amount
    """
    fluid, amount = decode_fluid(fluid_in)

    cache_key = f'bucket_{fluid}'
    if cache_key in CACHE:
        path, name, key = CACHE[cache_key]
        if key is not None:
            try:
                name = context.translate('fluid.' + key, 'block.' + key)
            except InternalError as e:
                e.warning()
        if amount > 0:
            name = '%s mB %s' % (str(amount), name)
        return path, name

    # Get fluid info
    name = None
    key = None
    if fluid.startswith('#'):
        name = context.translate(I18n.TAG) % fluid
        fluids = tag_loader.load_fluid_tag(context, fluid[1:])
        if fluids:
            fluid = fluids[0]  # Use first fluid in tag

    if not fluid.startswith('#'):
        key = fluid.replace('/', '.').replace(':', '.')
        try:
            name = context.translate('fluid.' + key, 'block.' + key)
        except InternalError as e:
            e.warning()
            name = fluid

    try:
        img = create_fluid_bucket_image(context, fluid)
        path = context.loader.save_image(context.next_id('fluid'), img)
    except InternalError as e:
        e.prefix('Fluid Bucket Image').warning()
        if placeholder:
            path = '../../_images/placeholder_64.png'
        else:
            raise e

    CACHE[cache_key] = path, name, key
    if amount > 0:
        name = '%s mB %s' % (str(amount), name)
    return path, name

def create_fluid_bucket_image(context: Context, fluid: str) -> Image.Image:
    """Creates a wooden bucket image with colorized fluid overlay"""
    try:
        # Load base bucket texture
        base = context.loader.load_texture('tfc:item/bucket/wooden_bucket_empty')

        # Load fluid overlay (grayscale)
        overlay = context.loader.load_texture('tfc:item/bucket/wooden_bucket_overlay')

        # Get fluid color
        fluid_path = fluid
        if ':' in fluid_path:
            _, fluid_path = fluid.split(':', 1)

        if fluid_path in FLUID_COLORS:
            color = ImageColor.getrgb(FLUID_COLORS[fluid_path])
            # Colorize the overlay
            overlay = colorization.colorize_grayscale_texture(overlay, color)

        # Composite base and overlay
        base = base.convert('RGBA')
        overlay = overlay.convert('RGBA')
        base.paste(overlay, (0, 0), overlay)

        return base
    except Exception as e:
        util.error('Failed to create fluid bucket image for \'%s\': %s' % (fluid, e), True)

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
        base = colorization.put_on_all_pixels(base, clr)
        return base

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

    # dyes (Minecraft standard colors)
    'white_dye': '#F0F0F0',
    'light_gray_dye': '#9D9D97',
    'gray_dye': '#474F52',
    'black_dye': '#1D1D21',
    'brown_dye': '#835432',
    'red_dye': '#B02E26',
    'orange_dye': '#F9801D',
    'yellow_dye': '#FED83D',
    'lime_dye': '#80C71F',
    'green_dye': '#5E7C16',
    'cyan_dye': '#169C9C',
    'light_blue_dye': '#3AB3DA',
    'blue_dye': '#3C44AA',
    'purple_dye': '#8932B8',
    'magenta_dye': '#C74EBD',
    'pink_dye': '#F38BAA',

    # addons - firmalife
    'yak_milk': '#E8E8E8',
    'goat_milk': '#E8E8E8',
    'chocolate': '#756745',
    'yeast_starter': '#F5E6D3',
}