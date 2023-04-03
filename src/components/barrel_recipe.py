from typing import List, Any

from context import Context
from components import crafting_recipe, fluid_loader

import util

def format_barrel_recipe(context: Context, buffer: List[str], identifier: str):
    data = context.loader.load_recipe(identifier)
    recipe_type = data['type']
    if recipe_type == 'tfc:barrel_sealed':
        format_barrel_recipe_from_data(context, buffer, identifier, data)
    elif recipe_type == 'tfc:barrel_instant':
        format_barrel_recipe_from_data(context, buffer, identifier, data)
    else:
        util.error('Cannot handle barrel recipe type: %s' % recipe_type)

def format_barrel_recipe_from_data(context: Context, buffer: List[str], identifier: str, data: Any):
    in_path = in_name = out_path = out_name = None
    in_count = out_count = 0
    
    if 'input_item' in data:
        in_path, in_name = crafting_recipe.format_ingredient(context, data['input_item']['ingredient'])
        in_count = data['input_item']['count'] if 'count' in data['input_item'] else 1
    if 'output_item' in data:
        out_path, out_name, out_count = crafting_recipe.format_item_stack(context, data['output_item'])
    if 'input_fluid' in data:
        f_in_path, f_in_name = fluid_loader.decode_fluid(context, data['input_fluid'])
    if 'output_fluid' in data:
        f_out_path, f_out_name = fluid_loader.decode_fluid(context, data['output_fluid'])

    input_item_div = f"""
    <div class="crafting-recipe-item two-recipe-pos-1">
        <span href="#" data-toggle="tooltip" title="{in_name}" class="crafting-recipe-item-tooltip"></span>
        {crafting_recipe.format_count(in_count)}
        <img src="{in_path}" />
    </div>""" if in_path is not None else ""
    output_item_div = f"""
    <div class="crafting-recipe-item two-recipe-pos-3">
        <span href="#" data-toggle="tooltip" title="{out_name}" class="crafting-recipe-item-tooltip"></span>
        {crafting_recipe.format_count(out_count)}
        <img src="{out_path}" />
    </div>
    """ if out_path is not None else ""
    input_fluid_div = f"""
    <div class="crafting-recipe-item two-recipe-pos-2">
        <span href="#" data-toggle="tooltip" title="{f_in_name}" class="crafting-recipe-item-tooltip"></span>
        <img src="{f_in_path}" />
    </div>
    """ if f_in_path is not None else ""
    output_fluid_div = f"""
    <div class="crafting-recipe-item two-recipe-pos-4">
        <span href="#" data-toggle="tooltip" title="{f_out_name}" class="crafting-recipe-item-tooltip"></span>
        <img src="{f_out_path}" />
    </div>
    """ if f_out_path is not None else ""

    buffer.append(f"""
    <div class="d-flex align-items-center justify-content-center">
        <div class="crafting-recipe">
            <img src="../../_images/2to2.png" />
            {input_item_div}
            {input_fluid_div}
            {output_item_div}
            {output_fluid_div}
        </div>
    </div>
    """
    )