import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from components.item_loader import create_item_image


class ItemLoaderTests(unittest.TestCase):
    def test_fluid_container_uses_empty_base_texture(self):
        for loader_name in ('tfc:contained_fluid', 'tfc:fluid_container'):
            with self.subTest(loader=loader_name):
                loader = Mock()
                loader.load_item_model.return_value = {
                    'loader': loader_name,
                    'parent': 'neoforge:item/default',
                    'textures': {'base': 'tfc:item/ceramic/fired_mold/ingot_empty'},
                }
                image = create_item_image(SimpleNamespace(loader=loader), 'tfc:ceramic/ingot_mold')
                self.assertIs(image, loader.load_texture.return_value)
                loader.load_texture.assert_called_once_with('tfc:item/ceramic/fired_mold/ingot_empty')

    def test_trim_uses_untrimmed_armor_texture(self):
        loader = Mock()
        loader.load_item_model.return_value = {
            'loader': 'tfc:trim',
            'parent': 'neoforge:item/default',
            'textures': {'armor': 'tfc:item/metal/helmet/copper'},
        }
        create_item_image(SimpleNamespace(loader=loader), 'tfc:metal/helmet/copper')
        loader.load_texture.assert_called_once_with('tfc:item/metal/helmet/copper')

    def test_separate_transforms_uses_gui_model(self):
        loader = Mock()
        loader.load_item_model.return_value = {
            'loader': 'neoforge:separate_transforms',
            'base': {'parent': 'tfc:item/blowpipe/empty_held'},
            'perspectives': {'gui': {'parent': 'tfc:item/blowpipe/empty_gui'}},
        }
        loader.load_model.return_value = {
            'parent': 'item/generated',
            'textures': {'layer0': 'tfc:item/blowpipe'},
        }
        create_item_image(SimpleNamespace(loader=loader), 'tfc:blowpipe')
        loader.load_model.assert_called_once_with('tfc:item/blowpipe/empty_gui')
        loader.load_texture.assert_called_once_with('tfc:item/blowpipe')


if __name__ == '__main__':
    unittest.main()
