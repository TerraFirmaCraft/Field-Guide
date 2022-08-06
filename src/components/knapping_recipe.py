from typing import List, Dict, Any
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

KNAPPING_RECIPE_OUTLINE = 'src/main/resources/assets/tfc/textures/gui/book/icons.png'


def format_knapping_recipe(context: Context, data: Keyable):
    recipe_id = data['recipe'] if 'recipe' in data else data['recipes'][0]
    path = context.convert_identifier(recipe_id)
    recipe_data = context.find_recipe(recipe_id)

    img = Image.new('RGBA', (270, 270), (0, 0, 0, 0))

    # Background
    bg = Image.open(util.path_join(context.tfc_dir, KNAPPING_RECIPE_OUTLINE)).convert('RGBA')
    bg = bg.crop((0, 0, 90, 90))
    bg = bg.resize((270, 270))
    img.paste(bg)

    low_texture, hi_texture = KNAPPING_RECIPE_TYPES[recipe_data['type']]
    low = hi = None

    if low_texture:
        low = Image.open(util.path_join(context.tfc_dir, 'src/main/resources/assets/tfc/', low_texture)).convert('RGBA')
        low = low.resize((48, 48), Image.Resampling.NEAREST)

    if hi_texture:
        hi = Image.open(util.path_join(context.tfc_dir, 'src/main/resources/assets/tfc/', hi_texture)).convert('RGBA')
        hi = hi.resize((48, 48), Image.Resampling.NEAREST)

    # Pattern
    pattern = recipe_data['pattern']
    outside_slot = data['outside_slot_required'] if 'outside_slot_required' in data else True

    for x in range(5):
        for y in range(5):
            in_bounds = y < len(pattern) and x < len(pattern[y])
            if (in_bounds and pattern[y][x] == ' ') or (not in_bounds and outside_slot):
                if hi:
                    img.paste(hi, (15 + 48 * x, 15 + 48 * y))
            else:
                if low:
                    img.paste(low, (15 + 48 * x, 15 + 48 * y))
    
    rel = util.path_join('_images', path.replace('/', '_') + '.png')
    dest = util.path_join(context.output_dir, '../', rel)  # Images are saved one level up, in lang-independent location
    
    img.save(dest)

    return recipe_id, '../../' + rel
