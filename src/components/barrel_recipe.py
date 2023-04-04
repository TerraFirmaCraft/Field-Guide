from typing import List, Any

from context import Context
from components import crafting_recipe, fluid_loader

import util

def format_barrel_recipe(context: Context, buffer: List[str], identifier: str):
    data = context.loader.load_recipe(identifier)
    recipe_type = data['type']
    if recipe_type == 'tfc:barrel_sealed':
        format_barrel_recipe_from_data(context, buffer, data)
    elif recipe_type == 'tfc:barrel_instant':
        format_barrel_recipe_from_data(context, buffer, data)
    else:
        util.error('Cannot handle barrel recipe type: %s' % recipe_type)

def format_barrel_recipe_from_data(context: Context, buffer: List[str], data: Any):
    in_path = in_name = out_path = out_name = f_out_name = f_out_path = f_in_name = f_in_path = None
    in_count = out_count = 0
    input_fluid_div = input_item_div = output_fluid_div = output_item_div = """"""
    
    if 'input_item' in data:
        in_path, in_name = crafting_recipe.format_ingredient(context, data['input_item']['ingredient'])
        in_count = data['input_item']['count'] if 'count' in data['input_item'] else 1
        input_item_div = make_icon(in_name, in_path, 1, crafting_recipe.format_count(in_count))
    if 'output_item' in data:
        out_path, out_name, out_count = crafting_recipe.format_item_stack(context, data['output_item'])
        output_item_div = make_icon(out_name, out_path, 3, crafting_recipe.format_count(out_count))
    if 'input_fluid' in data:
        f_in_path, f_in_name = fluid_loader.get_fluid_image(context, data['input_fluid'])
        input_fluid_div = make_icon(f_in_name, f_in_path, 2)
    if 'output_fluid' in data:
        f_out_path, f_out_name = fluid_loader.get_fluid_image(context, data['output_fluid'])
        output_fluid_div = make_icon(f_out_name, f_out_path, 4)
    
    to_append = f"""
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
    buffer.append(to_append)

def make_icon(name, path, index: int, extra_bit: str = "") -> str:
    return f"""
        <div class="crafting-recipe-item two-recipe-pos-{str(index)}">
            <span href="#" data-toggle="tooltip" title="{name}" class="crafting-recipe-item-tooltip"></span>
            <img src="{path}" />
            {extra_bit}
        </div>
        """