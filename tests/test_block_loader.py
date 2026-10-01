import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from components.block_loader import create_block_model_image


class BlockLoaderTests(unittest.TestCase):
    def test_inherited_elements_render_with_child_texture(self):
        loader = Mock()
        loader.load_model.side_effect = lambda parent: {
            'tfc:block/template': {
                'parent': 'block/block',
                'textures': {'side': 'tfc:block/default'},
                'elements': [{
                    'from': [0, 0, 0], 'to': [16, 16, 16],
                    'faces': {
                        'west': {'texture': '#side'},
                        'south': {'texture': '#side'},
                        'up': {'texture': '#side'},
                    },
                }],
            },
            'minecraft:block/block': {},
        }[parent]
        loader.load_texture.return_value = Image.new('RGBA', (16, 16), 'red')
        image = create_block_model_image(SimpleNamespace(loader=loader), 'tfc:example', {
            'parent': 'tfc:block/template',
            'textures': {'side': 'tfc:block/override'},
        })
        self.assertEqual(image.size, (256, 256))
        self.assertIsNotNone(image.getbbox())
        loader.load_texture.assert_any_call('tfc:block/override')


if __name__ == '__main__':
    unittest.main()
