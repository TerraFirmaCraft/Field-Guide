import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from components.crafting_recipe import format_item_stack


class CraftingRecipeTests(unittest.TestCase):
    def test_string_result_from_advanced_recipe(self):
        with patch('components.crafting_recipe.item_loader.get_item_image', return_value=('item.png', 'Wool Yarn')) as image:
            result = format_item_stack(SimpleNamespace(), 'tfc:wool_yarn')
        self.assertEqual(result, ('item.png', 'Wool Yarn', 1))
        image.assert_called_once_with(ANY, 'tfc:wool_yarn')

    def test_copy_input_result_reuses_ingredient_icon(self):
        context = SimpleNamespace()
        output = {'modifiers': [{'type': 'tfc:copy_input'}, {'type': 'tfc:dye_leather', 'color': 'red'}]}
        with patch('components.crafting_recipe.format_ingredient', return_value=('fruit.gif', 'Fruit')) as ingredient:
            result = format_item_stack(context, output, {'tag': 'c:foods/fruit'})
        self.assertEqual(result, ('fruit.gif', 'Fruit', 1))
        ingredient.assert_called_once_with(context, {'tag': 'c:foods/fruit'})


if __name__ == '__main__':
    unittest.main()
