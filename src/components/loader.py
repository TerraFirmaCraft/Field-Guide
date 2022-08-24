from typing import Tuple, List, Any
from PIL import Image

import json
import util


class Loader:

    def __init__(self, tfc_dir: str, output_dir: str):
        self.tfc_dir = tfc_dir
        self.output_dir = output_dir

    @util.context(lambda _, i: 'identifier = %s' % i)
    def load_image(self, identifier: str) -> Tuple[str, Image.Image]:
        """ Loads an image file. Returns the PIL Image and the resource path to the image """

        path = src = split_identifier(identifier)
        path = prefix(path, 'textures/')
        path = util.path_join(self.tfc_dir, 'src/main/resources/assets/tfc', path)
        path = suffix(path, '.png')

        try:
            img = Image.open(path).convert('RGBA')
            return src, img
        except OSError:
            util.error('Image file not found at: \'%s\'' % path)
    
    @util.context(lambda _, i, _1: 'identifier = \'%s\'' % i)
    def save_image(self, identifier: str, img: Image.Image) -> str:
        """ Saves an image to a location based on an identifier. Returns the relative path to that location. """

        path = split_identifier(identifier)
        path = suffix(path, '.png')
        rel = util.path_join('_images', path.replace('/', '_').replace('textures_', ''))
        dest = util.path_join(self.output_dir, '../', rel)  # Images are saved one level up, in lang-independent location

        img.save(dest)
        return '../../' + rel
    
    @util.context(lambda _, i, _1: 'identifier = \'%s\'' % i)
    def save_gif(self, identifier: str, images: List[Image.Image]) -> str:
        """ Saves multiple images to a .gif based on an identifier. Returns the relative path to that location. """

        first, *others = images

        path = split_identifier(identifier)
        path = path.replace('.png', '')
        path = suffix(path, '.gif')
        rel = util.path_join('_images', path.replace('/', '_').replace('textures_', ''))
        dest = util.path_join(self.output_dir, '../', rel)  # Images are saved one level up, in lang-independent location

        first.save(dest, save_all=True, append_images=others, duration=1000, loop=0)
        return '../../' + rel

    def load_item_model(self, identifier: str) -> Any:
        return self.load_json(identifier, 'models/item', 'assets')

    def load_recipe(self, identifier: str) -> Any:
        return self.load_json(identifier, 'recipes', 'data')

    @util.context(lambda _, i, rt, rr: 'identifier = %s, resource_type = %s, resource_root = %s' % (i, rt, rr))
    def load_json(self, identifier: str, resource_type: str, resource_root: str) -> Any:
        """ Loads a json file of a specific resource type (tags, models, etc.) and resource root (assets, data)."""

        path = split_identifier(identifier)
        path = util.path_join(self.tfc_dir, 'src/main/resources', resource_root, 'tfc', resource_type, path)
        path = suffix(path, '.json')

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except OSError:
            util.error('Resource file not found')


def split_identifier(identifier: str) -> str:
    if ':' not in identifier:
        return identifier
    if '{' in identifier or '[' in identifier:
        util.error('Invalid identifier: \'%s\'' % identifier)
    namespace, path = identifier.split(':')
    util.require(namespace == 'tfc', 'Non-tfc namespace: %s' % identifier)
    return path

def suffix(path: str, suffix_with: str) -> str:
    return path if path.endswith(suffix_with) else path + suffix_with

def prefix(path: str, prefix_with: str) -> str:
    return path if path.startswith(prefix_with) else prefix_with + path
