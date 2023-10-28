from typing import Any, NamedTuple
from context import Context
from PIL import Image


class KnappingType(NamedTuple):
    type_1_18: str
    type_1_20: str
    low: str | None
    hi: str | None

KNAPPING_TYPES = (
    KnappingType('tfc:rock_knapping', 'tfc:rock', 'tfc:textures/gui/knapping/rock/loose/granite.png', None),
    KnappingType('tfc:clay_knapping', 'tfc:clay', 'tfc:textures/gui/knapping/clay_ball.png', 'tfc:textures/gui/knapping/clay_ball_disabled.png'),
    KnappingType('tfc:fire_clay_knapping', 'tfc:fire_clay', 'tfc:textures/gui/knapping/fire_clay.png', 'tfc:textures/gui/knapping/fire_clay_disabled.png'),
    KnappingType('tfc:leather_knapping', 'tfc:leather', 'tfc:textures/gui/knapping/leather.png', None),
)

KNAPPING_RECIPE_OUTLINE = 'tfc:textures/gui/book/icons.png'
CACHE = {}


def format_knapping_recipe(context: Context, data: Any):
    recipe_id = data['recipe'] if 'recipe' in data else data['recipes'][0]

    if recipe_id in CACHE:
        return CACHE[recipe_id]

    recipe_data = context.loader.load_recipe(recipe_id)

    img = Image.new('RGBA', (90, 90), (0, 0, 0, 0))

    # Background
    bg = context.loader.load_explicit_texture(KNAPPING_RECIPE_OUTLINE)
    bg = bg.crop((0, 0, 90, 90))
    img.paste(bg)

    # 1.18 has the 'type' field indicating the knapping type
    # 1.20 has the 'type' field only be 'tfc:knapping' with the 'knapping_type' field indicating the type
    if 'knapping_type' in recipe_data:
        type_data = next(t for t in KNAPPING_TYPES if t.type_1_20 == recipe_data['knapping_type'])
    else:
        type_data = next(t for t in KNAPPING_TYPES if t.type_1_18 == recipe_data['type'])

    low = hi = None

    if type_data.low:
        low = context.loader.load_explicit_texture(type_data.low)
    if type_data.hi:
        hi = context.loader.load_explicit_texture(type_data.hi)

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
    path = context.loader.save_image(context.next_id('image'), img)

    CACHE[recipe_id] = recipe_id, path
    return recipe_id, path
