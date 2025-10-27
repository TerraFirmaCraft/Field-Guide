from typing import List, Tuple, Any

from context import Context
from components import item_loader

import util


def format_crafting_recipe(context: Context, buffer: List[str], identifier: str):
    recipe = context.loader.load_recipe(identifier)
    format_crafting_recipe_from_data(context, buffer, identifier, recipe)


def format_crafting_recipe_from_data(context: Context, buffer: List[str], identifier: str, data: Any):
    recipe_type = data['type']

    if recipe_type == 'minecraft:crafting_shaped':
        recipe = CraftingRecipe()
        for y, row in enumerate(data['pattern']):
            for x, key in enumerate(row):
                if key != ' ':
                    recipe.grid[x + 3 * y] = data['key'][key]
        recipe.output = format_item_stack(context, data['result'])
        recipe.shapeless = False
    elif recipe_type == 'minecraft:crafting_shapeless':
        recipe = CraftingRecipe()
        for i, key in enumerate(data['ingredients']):
            recipe.grid[i] = key
        recipe.output = format_item_stack(context, data['result'])
        recipe.shapeless = True
    elif recipe_type in (
        'tfc:damage_inputs_shaped_crafting',
        'tfc:damage_inputs_shapeless_crafting',
        'tfc:extra_products_shapeless_crafting',
        'tfc:no_remainder_shapeless_crafting'
    ):
        return format_crafting_recipe_from_data(context, buffer, identifier, data['recipe'])
    elif recipe_type == 'tfc:advanced_shaped_crafting':
        data['type'] = 'minecraft:crafting_shaped'
        stack = util.anyof(data['result'], 'stack', 'id')
        util.require(stack is not None, 'Advanced shaped crafting with complex modifiers: \'%s\'' % data['result'])
        data['result'] = stack  # Discard modifiers
        return format_crafting_recipe_from_data(context, buffer, identifier, data)
    elif recipe_type == 'tfc:advanced_shapeless_crafting':
        data['type'] = 'minecraft:crafting_shapeless'
        stack = util.anyof(data['result'], 'stack', 'id')
        util.require(stack is not None, 'Advanced shapeless crafting with complex modifiers: \'%s\'' % data['result'])
        data['result'] = stack  # Discard modifiers
        return format_crafting_recipe_from_data(context, buffer, identifier, data)
    else:
        raise util.error('Unknown crafting recipe type: %s for recipe %s' % (recipe_type, identifier))

    if recipe:
        recipe.grid = [
            format_ingredient(context, key) if key else None
            for key in recipe.grid
        ]

        buffer.append("""
        <div class="d-flex align-items-center justify-content-center">
            <div class="crafting-recipe">
                <img src="../../_images/crafting_%s.png" />
        """ % ('shapeless' if recipe.shapeless else 'shaped'))

        for i, key in enumerate(recipe.grid):
            if key:
                path, name = key
                x, y = i % 3, i // 3
                buffer.append("""
                <div class="crafting-recipe-item crafting-recipe-pos-%d-%d">
                    <span href="#" data-bs-toggle="tooltip" title="%s" class="crafting-recipe-item-tooltip"></span>
                    <img class="recipe-item" src="%s" />
                </div>
                """ % (x, y, name, path))

        out_path, out_name, out_count = recipe.output
        buffer.append("""
                <div class="crafting-recipe-item crafting-recipe-pos-out">
                    <span href="#" data-bs-toggle="tooltip" title="%s" class="crafting-recipe-item-tooltip"></span>
                    %s
                    <img class="recipe-item" src="%s" />
                </div>
            </div>
        </div>
        """ % (
            out_name,
            format_count(out_count),
             out_path
        ))


def format_ingredient(context: Context, data: Any) -> Tuple[str, str | None]:
    if 'item' in data:
        return item_loader.get_item_image(context, data['item'])
    elif 'tag' in data:
        return item_loader.get_item_image(context, '#' + data['tag'])
    elif 'type' in data and data['type'] in (
        'tfc:not_rotten',
    ):
        return format_ingredient(context, data['ingredient'])
    elif 'type' in data and data['type'] == 'tfc:fluid_item':
        util.require(data['fluid_ingredient']['ingredient'] == 'minecraft:water', 'Unknown `tfc:fluid_item` ingredient: \'%s\'' % data)
        return item_loader.get_item_image(context, 'minecraft:water_bucket')
    elif 'type' in data and data['type'] == 'tfc:fluid_content':
        util.require(data['fluid']['fluid'] == 'minecraft:water', 'Unknown `tfc:fluid_content` ingredient: \'%s\'' % data)
        return item_loader.get_item_image(context, 'minecraft:water_bucket')
    elif 'type' in data and data['type'] == 'tfc:and':
        csvstring = ''
        for i in data['children']:
            if 'item' in i:
                csvstring += ',' + str(i['item'])
        return item_loader.get_item_image(context, csvstring)
    elif isinstance(data, List):
        csvstring = ''
        for i in data:
            if 'item' in i:
                csvstring += ',' + str(i['item'])
        return item_loader.get_item_image(context, csvstring)
    else:
        util.error('Unsupported ingredient: %s' % str(data))

def format_sized_ingredient(context: Context, data: Any) -> Tuple[Tuple[str, str | Any], int]:
    ing = format_ingredient(context, data)
    return ing, 1 if 'count' not in data else data['count']

def format_item_stack(context: Context, data: Any) -> Tuple[str, str, int]:
    if 'modifiers' in data and 'stack' in data:
        return format_item_stack(context, data['stack'])  # Discard modifiers
    if 'item' in data:
        path, name = item_loader.get_item_image(context, data['item'])
    else:
        path =  '../../_images/placeholder_64.png'
        name = None
    count = 1 if 'count' not in data else data['count']
    return path, name, count

def format_count(count: int) -> str:
    return '<p class="crafting-recipe-item-count">%d</p>' % count if count > 1 else ''

class CraftingRecipe:

    def __init__(self):
        self.grid = [None] * 9  # grid[x + 3 * y]
        self.output = None
        self.shapeless = False
