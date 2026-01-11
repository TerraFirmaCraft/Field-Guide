from typing import List, Any, Callable, Tuple
from components import mcmeta, colorization
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

        self.loaders: List[Tuple[str, Tuple[str, ...], Callable[[str, Any], Any]]] = [('tfc', ('tfc', 'forge', 'minecraft', 'c'), self.load_from_tfc)]
        self.domains = ['tfc']
        if use_mcmeta:
            self.loaders += [
                ('forge', ('forge', 'minecraft', 'c'), mcmeta.load_from_forge),
                ('minecraft', ('minecraft',), mcmeta.load_from_mc)
            ]
            self.domains += ['forge', 'minecraft']
        if use_addons:
            for addon in versions.ADDONS:
                self.loaders.append((addon.mod_id, (addon.mod_id, 'c', 'tfc', 'minecraft'), make_load_from_addon(addon)))
                self.domains.append(addon.mod_id)

        # Load paletted permutation textures from atlas
        self.paletted_textures = self._load_paletted_textures()

    
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
    def load_recipe(self, path: str) -> Any: return self.load_resource(path, versions.registry('recipe'), 'data', '.json', json_reader)

    def load_block_tag(self, path: str) -> Any: return self.load_resource(path, versions.registry('tags/block'), 'data', '.json', json_reader)
    def load_item_tag(self, path: str) -> Any: return self.load_resource(path, versions.registry('tags/item'), 'data', '.json', json_reader)
    def load_fluid_tag(self, path: str) -> Any: return self.load_resource(path, versions.registry('tags/fluid'), 'data', '.json', json_reader)

    def load_lang(self, path: str, source: str) -> Any: return self.load_resource(source + ':' + path, 'lang', 'assets', '.json', json_reader, source)

    def load_explicit_texture(self, path: str) -> Image.Image: return self.load_resource(path, '', 'assets', '.png', image_reader)

    def load_texture(self, path: str) -> Image.Image:
        try:
            return self.load_resource(path, 'textures', 'assets', '.png', image_reader)
        except InternalError:
            # Check if this is a paletted permutation texture
            base_path, suffix = self._strip_paletted_suffix(path)
            if base_path and base_path != path:
                try:
                    base_texture = self.load_resource(base_path, 'textures', 'assets', '.png', image_reader)
                    # Try to colorize it
                    colorized = self._colorize_paletted_texture(base_texture, base_path, suffix)
                    return colorized if colorized else base_texture
                except InternalError:
                    pass
            raise
    
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

    def _load_paletted_textures(self) -> dict:
        """Load the atlas file and extract all base textures that use paletted_permutations"""
        paletted = {}
        try:
            atlas_path = util.path_join(self.tfc_dir, 'src/main/resources/assets/minecraft/atlases/blocks.json')
            with open(atlas_path, 'r', encoding='utf-8') as f:
                atlas = json.load(f)

            for source in atlas.get('sources', []):
                if source.get('type') == 'paletted_permutations':
                    palette_key = source.get('palette_key')
                    permutations = source.get('permutations', {})
                    for texture in source.get('textures', []):
                        paletted[texture] = {
                            'palette_key': palette_key,
                            'permutations': permutations
                        }
        except (OSError, json.JSONDecodeError, KeyError):
            pass  # If we can't load the atlas, just continue without paletted texture support

        return paletted

    def _strip_paletted_suffix(self, texture_path: str) -> tuple[str | None, str | None]:
        """
        Check if a texture path is a paletted permutation and return the base texture and suffix.
        For example: 'tfc:item/wood/lumber_acacia' -> ('tfc:item/wood/lumber', 'acacia')
        """
        texture_path = util.resource_location(texture_path)

        for base_texture in self.paletted_textures:
            # Check if the texture_path starts with the base texture followed by an underscore
            base_with_namespace = util.resource_location(base_texture)
            if texture_path.startswith(base_with_namespace + '_'):
                suffix = texture_path[len(base_with_namespace) + 1:]  # +1 for the underscore
                return base_with_namespace, suffix

        return None, None

    def _colorize_paletted_texture(self, base_texture: Image.Image, base_path: str, suffix: str) -> Image.Image | None:
        """
        Colorize a paletted permutation texture by applying the color palette.
        Returns the colorized image, or None if colorization failed.
        """
        try:
            # Get palette info for this base texture
            palette_info = self.paletted_textures.get(base_path)
            if not palette_info:
                return None

            palette_key_path = palette_info['palette_key']
            permutations = palette_info['permutations']

            # Get the permutation path for this suffix
            permutation_path = permutations.get(suffix)
            if not permutation_path:
                return None

            # Load the palette key and permutation
            palette_key = self.load_resource(palette_key_path, 'textures', 'assets', '.png', image_reader)
            permutation = self.load_resource(permutation_path, 'textures', 'assets', '.png', image_reader)

            # Apply the paletted permutation using the colorization utility
            return colorization.apply_paletted_permutation(base_texture, palette_key, permutation)
        except Exception:
            return None

    def load_from_tfc(self, path: str, reader):
        try:
            base_path = path
            path = util.path_join(self.tfc_dir, 'src/main/resources', base_path)
            if not os.path.exists(path):
                path = util.path_join(self.tfc_dir, 'src/generated/resources', base_path)
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
    resource_paths = addon.resource_paths()
    def load_from_addon(path: str, reader):
        try:
            count = 0
            full_path = util.path_join('addons', '%s-%s' % (addon.mod_id, addon.version), resource_paths[count], path)
            while not os.path.exists(full_path):
                count += 1
                full_path = util.path_join('addons', '%s-%s' % (addon.mod_id, addon.version), resource_paths[count], path)
            if full_path.endswith('png'):
                with open(full_path, 'rb') as f:
                    return reader(f)
            else:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return reader(f)
        except (OSError, IndexError):
            util.error('Reading \'%s\' from addon \'%s\'' % (path, addon.mod_id))
    return load_from_addon