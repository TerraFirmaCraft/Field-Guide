import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from components.item_loader import CACHE, create_item_image, get_item_image
from util import InternalError


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

    def test_nested_item_parent_inherits_generated_texture(self):
        loader = Mock()
        loader.load_item_model.return_value = {'parent': 'tfc:item/template'}
        loader.load_model.return_value = {
            'parent': 'item/generated',
            'textures': {'layer0': 'tfc:item/example'},
        }
        create_item_image(SimpleNamespace(loader=loader), 'tfc:example')
        loader.load_texture.assert_called_once_with('tfc:item/example')

    def test_item_parent_elements_use_child_texture_override(self):
        loader = Mock()
        loader.load_item_model.return_value = {
            'parent': 'tfc:item/template',
            'textures': {'face': 'tfc:item/override'},
        }
        loader.load_model.side_effect = lambda parent: {
            'tfc:item/template': {
                'parent': 'block/block',
                'textures': {'face': 'tfc:item/default'},
                'elements': [{
                    'from': [0, 0, 0], 'to': [16, 16, 16],
                    'faces': {'up': {'texture': '#face'}},
                }],
            },
            'minecraft:block/block': {},
        }[parent]
        loader.load_texture.return_value = Image.new('RGBA', (16, 16), 'red')
        image = create_item_image(SimpleNamespace(loader=loader), 'tfc:example')
        self.assertEqual(image.size, (64, 64))
        self.assertIsNotNone(image.getbbox())
        loader.load_texture.assert_called_with('tfc:item/override')

    def test_unrenderable_tag_alternative_does_not_hide_others(self):
        CACHE.clear()
        loader = Mock()
        loader.save_image.return_value = '../../_images/usable.png'
        context = SimpleNamespace(loader=loader, translate=lambda *args: 'tag %s', next_id=lambda prefix: 'item1')
        with patch('components.item_loader.tag_loader.load_item_tag', return_value=['tfc:bad', 'tfc:good']), \
                patch('components.item_loader.create_item_image', side_effect=[InternalError('bad model'), Image.new('RGBA', (16, 16), 'red')]):
            path, _ = get_item_image(context, '#tfc:examples')
        self.assertEqual(path, '../../_images/usable.png')
        loader.save_image.assert_called_once()

    def test_data_component_icon_uses_base_item_model(self):
        CACHE.clear()
        loader = Mock()
        loader.save_image.return_value = '../../_images/mold.png'
        context = SimpleNamespace(loader=loader, translate=lambda *args: 'Ingot Mold', next_id=lambda prefix: 'item2')
        with patch('components.item_loader.create_item_image', return_value=Image.new('RGBA', (16, 16), 'red')) as render:
            path, name = get_item_image(context, 'tfc:ceramic/ingot_mold[tfc:fluid={id:"tfc:metal/bronze"}]')
        self.assertEqual((path, name), ('../../_images/mold.png', 'Ingot Mold'))
        render.assert_called_once_with(context, 'tfc:ceramic/ingot_mold')


if __name__ == '__main__':
    unittest.main()
