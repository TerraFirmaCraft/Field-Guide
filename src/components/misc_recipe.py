from typing import List, Any

from context import Context
from components import crafting_recipe

import util

def format_misc_recipe(context: Context, buffer: List[str], identifier: str):
    data = context.loader.load_recipe(identifier)
    recipe_type = data['type']
    if recipe_type == 'tfc:quern':
        format_misc_recipe_from_data(context, buffer, identifier, data)
    elif recipe_type == 'tfc:heating':
        format_misc_recipe_from_data(context, buffer, identifier, data, result='result_item')
        key, tooltip = get_temperature(context, data['temperature'])
        buffer.append("""
        <div style="text-align: center;" class="minecraft-text minecraft-%s">
            <p>%s</p>
        </div>
        """ % (key, tooltip))
    elif recipe_type == 'tfc:loom':
        format_misc_recipe_from_data(context, buffer, identifier, data, in_count='input_count')
    elif recipe_type == 'tfc:anvil':
        format_misc_recipe_from_data(context, buffer, identifier, data, ingredient='input')
        tooltip = get_tier(context, data['tier'])
        buffer.append("""
        <div style="text-align: center;" class="minecraft-text minecraft-gray">
            <p>%s</p>
        </div>
        """ % tooltip)
    else:
        util.error('Cannot handle as a misc recipe: %s' % recipe_type)


def format_misc_recipe_from_data(context: Context, buffer: List[str], identifier: str, data: Any, ingredient: str = 'ingredient', result: str = 'result', in_count: str = None):
    util.require(result in data, 'Missing \'%s\' field for recipe: %s' % (result, identifier))
    
    in_path, in_name = crafting_recipe.format_ingredient(context, data[ingredient])
    in_count = 1 if in_count is None else data[in_count]
    out_path, out_name, out_count = crafting_recipe.format_item_stack(context, data[result])

    buffer.append("""
    <div class="d-flex align-items-center justify-content-center">
        <div class="crafting-recipe">
            <img src="../../_images/1to1.png" />
            <div class="crafting-recipe-item misc-recipe-pos-in">
                <span href="#" data-toggle="tooltip" title="%s" class="crafting-recipe-item-tooltip"></span>
                %s
                <img src="%s" />
            </div>
            <div class="crafting-recipe-item misc-recipe-pos-out">
                <span href="#" data-toggle="tooltip" title="%s" class="crafting-recipe-item-tooltip"></span>
                %s
                <img src="%s" />
            </div>
        </div>
    </div>
    """% (
        in_name,
        crafting_recipe.format_count(in_count),
        in_path,
        out_name,
        crafting_recipe.format_count(out_count),
        out_path
    ))


def get_temperature(context: Context, temperature: int) -> str:
    for i, (key, css, value) in enumerate(HEAT[:-1]):
        if temperature <= value:
            _, _, next_value = HEAT[i + 1]
            tooltip = context.translate('tfc.enum.heat.%s' % key)
            for t in (0.2, 0.4, 0.6, 0.8):
                if temperature < value + (next_value - value) * t:
                    tooltip += '*'
            return css, tooltip
    return 'brilliant-white', context.translate('tfc.enum.heat.brilliant_white')

def get_tier(context: Context, tier: int) -> str:
    return context.translate('tfc.enum.tier.tier_%s' % ['0', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'][tier])


HEAT = (
    ('warming', 'gray', 80),
    ('hot', 'gray', 210),
    ('very_hot', 'gray', 480),
    ('faint_red', 'dark-red', 580),
    ('dark_red', 'dark-red', 730),
    ('bright_red', 'red', 930),
    ('orange', 'gold', 1100),
    ('yellow', 'yellow', 1300),
    ('yellow_white', 'yellow', 1400),
    ('white', 'white', 1500),
    ('brilliant_white', 'white', 1600)
)