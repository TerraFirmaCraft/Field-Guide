from typing import Dict, Any
from context import Context
from PIL import Image

import util


Keyable = Dict[str, Any]


KNAPPING_RECIPE_TYPES = {
    'tfc:rock_knapping': (
        'textures/gui/knapping/rock/loose/granite.png',
        None,
    ),
    'tfc:clay_knapping': (
        'textures/gui/knapping/clay_ball.png',
        'textures/gui/knapping/clay_ball_disabled.png',
    ),
    'tfc:fire_clay_knapping': (
        'textures/gui/knapping/fire_clay.png',
        'textures/gui/knapping/fire_clay_disabled.png',
    ),
    'tfc:leather_knapping': (
        'textures/gui/knapping/leather.png',
        None,
    ),
}

KNAPPING_RECIPE_OUTLINE = 'textures/gui/book/icons.png'


@util.context(lambda _, d: 'knapping_recipe = \'%s\'' % d)
def format_knapping_recipe(context: Context, data: Keyable):
    recipe_id = data['recipe'] if 'recipe' in data else data['recipes'][0]
    recipe_data = context.loader.load_recipe(recipe_id)

    img = Image.new('RGBA', (90, 90), (0, 0, 0, 0))

    # Background
    _, bg = context.loader.load_image(KNAPPING_RECIPE_OUTLINE)
    bg = bg.crop((0, 0, 90, 90))
    img.paste(bg)

    low_texture, hi_texture = KNAPPING_RECIPE_TYPES[recipe_data['type']]
    low = hi = None

    if low_texture:
        _, low = context.loader.load_image(low_texture)
    if hi_texture:
        _, hi = context.loader.load_image(hi_texture)

    # Pattern
    pattern = recipe_data['pattern']
    outside_slot = recipe_data['outside_slot_required'] if 'outside_slot_required' in recipe_data else True

    # If the pattern is < 5 wide in any direction, we offset it so it appears centered, rounding down
    offset_y = (5 - len(pattern)) // 2
    offset_x = (5 - len(pattern[0])) // 2

    for x in range(5):
        for y in range(5):
            if 0 <= y - offset_y < len(pattern) and 0 <= x - offset_x < len(pattern[y - offset_y]):  # in bounds
                if tile := (hi if pattern[y - offset_y][x - offset_x] == ' ' else low):
                    img.paste(tile, (5 + 16 * x, 5 + 16 * y))
            else:  # out of bounds
                if tile := (low if outside_slot else hi):
                    img.paste(tile, (5 + 16 * x, 5 + 16 * y))
    
    img = img.resize((3 * 90, 3 * 90), Image.Resampling.NEAREST)

    return recipe_id, context.loader.save_image(recipe_id, img)
