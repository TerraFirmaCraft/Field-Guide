from typing import List, Any

from context import Context
from components import crafting_recipe, item_loader
from util import InternalError

import util


def format_misc_recipe(context: Context, buffer: List[str], identifier: str):
    data = context.loader.load_recipe(identifier)
    recipe_type = data['type']
    if recipe_type == 'tfc:quern' or recipe_type == 'firmalife:drying':
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
        # 1.18 uses an ingredient with 'input_count' parameter
        # 1.20 uses an item stack ingredient with 'ingredient' and 'count' fields
        # 1.21 changed the 'ingredient' field to 'item'
        if 'ingredient' in data:
            count = data['input_count'] if 'input_count' in data else data['ingredient']['count'] if 'count' in data['ingredient'] else 1
            format_misc_recipe_from_data(context, buffer, identifier, data, in_count=count)
        elif 'ingredient' in data and 'ingredient' in data['ingredient'] and 'count' in data['ingredient']:
            ing = data['ingredient']
            format_misc_recipe_from_data(context, buffer, identifier, data, ingredient=ing['ingredient'], in_count=ing['count'])
        else:
            util.error('Unrecognized loom recipe format: %s' % repr(data))
    elif recipe_type == 'tfc:anvil':
        if 'input' in data:
            format_misc_recipe_from_data(context, buffer, identifier, data, ingredient=data['input'])
        elif 'ingredient' in data:
            format_misc_recipe_from_data(context, buffer, identifier, data, ingredient=data['ingredient'])
        else:
            util.error('Unrecognized anvil recipe format: %s' % repr(data))
        tooltip = get_tier(context, data['tier'] if 'tier' in data else 0)
        buffer.append("""
        <div style="text-align: center;" class="minecraft-text minecraft-gray">
            <p>%s</p>
        </div>
        """ % tooltip)
    elif recipe_type == 'tfc:glassworking':
        format_misc_recipe_from_data(context, buffer, identifier, data, ingredient=data['batch'])
        buffer.append('<h4>Steps</h4><ol>')

        for key in data['operations']:
            # Item Images
            op_name = context.translate('tfc.enum.glassoperation.' + key, 'glass_operation.' + key.replace(':', '.'))
            key = key.replace('tfc:', '')
            util.require(key in GLASS_ITEMS, 'Missing item for glass op: %s' % key.replace)
            op_item = GLASS_ITEMS[key]
            try:
                item_src, item_name = item_loader.get_item_image(context, op_item, False)
                buffer.append('<li>')
                context.format_title_with_icon(buffer, item_src, op_name, data, tag='p', tooltip=item_name)
                buffer.append('</li>')
                context.items_passed += 1
            except InternalError as e:
                e.warning()
                buffer.append('<li><p>%s</p></li>' % op_name)
        buffer.append('</ol>')
    else:
        util.error('Cannot handle as a misc recipe: %s' % recipe_type)


def format_misc_recipe_from_data(context: Context, buffer: List[str], identifier: str, data: Any, ingredient: Any = None, result: str = 'result', in_count: Any = None):
    util.require(result in data, 'Missing \'%s\' field for recipe: %s' % (result, identifier))

    if ingredient is None:
        ingredient = data['ingredient']
    if in_count is None:
        in_count = 1

    in_path, in_name = crafting_recipe.format_ingredient(context, ingredient)
    out_path, out_name, out_count = crafting_recipe.format_item_stack(context, data[result])

    buffer.append("""
    <div class="d-flex align-items-center justify-content-center">
        <div class="crafting-recipe">
            <img src="../../_images/1to1.png" />
            <div class="crafting-recipe-item misc-recipe-pos-in">
                <span href="#" data-bs-toggle="tooltip" title="%s" class="crafting-recipe-item-tooltip"></span>
                %s
                <img class="recipe-item" src="%s" />
            </div>
            <div class="crafting-recipe-item misc-recipe-pos-out">
                <span href="#" data-bs-toggle="tooltip" title="%s" class="crafting-recipe-item-tooltip"></span>
                %s
                <img class="recipe-item" src="%s" />
            </div>
        </div>
    </div>
    """ % (
        in_name,
        crafting_recipe.format_count(in_count),
        in_path,
        out_name,
        crafting_recipe.format_count(out_count),
        out_path
    ))


def get_temperature(context: Context, temperature: int) -> tuple[str, str]:
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
    return context.translate(
        'tfc.enum.tier.tier_%s' % ['0', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'][tier],
        'tfc.tooltip.tier_%s' % [0, 1, 2, 3, 4, 5, 6, 7][tier]
        )


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

GLASS_ITEMS = {
    'saw': 'tfc:gem_saw',
    'roll': 'tfc:wool_cloth',
    'stretch': 'tfc:blowpipe_with_glass',
    'blow': 'tfc:blowpipe_with_glass',
    'table_pour': 'tfc:blowpipe_with_glass',
    'basin_pour': 'tfc:blowpipe_with_glass',
    'flatten': 'tfc:paddle',
    'pinch': 'tfc:jacks',
}
