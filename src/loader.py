from typing import List, Any
from components import mcmeta
from util import InternalError
from PIL import Image

import json
import util
import versions
import os


class Loader:

    def __init__(self, tfc_dir: str, output_dir: str, use_mcmeta: bool, use_addons: bool):
        self.tfc_dir = tfc_dir
        self.output_dir = output_dir

        self.loaders = [('tfc', ('tfc', 'forge', 'minecraft'), self.load_from_tfc)]
        self.domains = ['tfc']
        if use_mcmeta:
            self.loaders += [
                ('forge', ('forge', 'minecraft'), mcmeta.load_from_forge),
                ('minecraft', ('minecraft',), mcmeta.load_from_mc)
            ]
            self.domains += ['forge', 'minecraft']
        if use_addons:
            for addon in versions.ADDONS:
                self.loaders.append((addon.mod_id, (addon.mod_id,), make_load_from_addon(addon)))
                self.domains.append(addon.mod_id)

    
    def save_image(self, path: str, img: Image.Image) -> str:
        """ Saves an image to a location based on an identifier. Returns the relative path to that location. """

        _, path = util.resource_location(path).split(':')
        path = util.path_join('_images', path.replace('/', '_'))
        path = suffix(path, '.png')

        img.save(util.path_join(self.output_dir, path))
        return util.path_join('../../', path)
    
    def save_gif(self, path: str, images: List[Image.Image]) -> str:
        """ Saves multiple images to a .gif based on an identifier. Returns the relative path to that location. """

        first, *others = images

        _, path = util.resource_location(path).split(':')
        path = suffix(path.replace('.png', ''), '.gif')
        path = util.path_join('_images', path.replace('/', '_'))

        first.save(util.path_join(self.output_dir, path), save_all=True, append_images=others, duration=1000, loop=0, disposal=2)
        return util.path_join('../../', path)

    def load_block_state(self, path: str) -> Any: return self.load_resource(path, 'blockstates', 'assets', '.json', json_reader)
    def load_block_model(self, path: str) -> Any: return self.load_resource(path, 'models/block', 'assets', '.json', json_reader)
    def load_item_model(self, path: str) -> Any: return self.load_resource(path, 'models/item', 'assets', '.json', json_reader)
    def load_model(self, path: str) -> Any: return self.load_resource(path, 'models', 'assets', '.json', json_reader)
    def load_recipe(self, path: str) -> Any: return self.load_resource(path, 'recipes', 'data', '.json', json_reader)

    def load_block_tag(self, path: str) -> Any: return self.load_resource(path, 'tags/blocks', 'data', '.json', json_reader)
    def load_item_tag(self, path: str) -> Any: return self.load_resource(path, 'tags/items', 'data', '.json', json_reader)
    def load_fluid_tag(self, path: str) -> Any: return self.load_resource(path, 'tags/fluids', 'data', '.json', json_reader)

    def load_lang(self, path: str, source: str) -> Any: return self.load_resource(source + ':' + path, 'lang', 'assets', '.json', json_reader, source)

    def load_explicit_texture(self, path: str) -> Image.Image: return self.load_resource(path, '', 'assets', '.png', image_reader)
    def load_texture(self, path: str) -> Image.Image: return self.load_resource(path, 'textures', 'assets', '.png', image_reader)
    
    def load_resource(self, path: str, resource_type: str, resource_root: str, resource_suffix: str, reader, source: str = None) -> Any:
        path = util.resource_location(path)
        domain, path = path.split(':')
        path = util.path_join(resource_root, domain, resource_type, path)
        path = suffix(path, resource_suffix)

        for key, serves, loader in self.loaders:
            if (source is None or key == source) and domain in serves:  # source only loads from a specific loader domain
                try:
                    return loader(path, reader)
                except InternalError as e:
                    if source is not None:  # Directly error if using a single source  
                        util.error(str(e))
        
        util.error('Missing Resource \'%s\'' % path)  # Aggregate errors
    
    def load_from_tfc(self, path: str, reader):
        try:
            path = util.path_join(self.tfc_dir, 'src/main/resources', path)
            if not os.path.exists(path):
                path = util.path_join(self.tfc_dir, 'src/generated/resources', path)
            if path.endswith('.png'):
                with open(path, 'rb') as f:
                    return reader(f)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    return reader(f)
        except OSError:
            util.error('Reading \'%s\' from \'tfc\'' % path)


def suffix(path: str, suffix_with: str) -> str:
    return path if path.endswith(suffix_with) else path + suffix_with

def prefix(path: str, prefix_with: str) -> str:
    return path if path.startswith(prefix_with) else prefix_with + path

def image_reader(f):
    return Image.open(f).convert('RGBA')

def json_reader(f):
    return json.load(f)

def make_load_from_addon(addon: versions.Addon):
    def load_from_addon(path: str, reader):
        try:
            path = util.path_join('addons', '%s-%s' % (addon.mod_id, addon.version), addon.resource_path, path)
            if path.endswith('.png'):
                with open(path, 'rb') as f:
                    return reader(f)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    return reader(f)
        except OSError:
            util.error('Reading \'%s\' from addon \'%s\'' % (path, addon.mod_id))
    return load_from_addon