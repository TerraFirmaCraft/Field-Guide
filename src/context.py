from typing import Dict, List, Tuple, Any
from PIL import Image
from category import Category
from entry import Entry
from util import LOG, InternalError
from i18n import I18n
from components import text_formatter
from loader import Loader

import util
import json

IMAGE_CACHE: Dict[str, str] = {}


class Context:

    def __init__(self, tfc_dir: str, output_dir: str, use_mcmeta: bool, use_addons: bool, debug_i18n: bool):
        self.tfc_dir = tfc_dir
        self.output_root_dir = output_dir
        self.output_dir = output_dir
        self.loader: Loader = Loader(tfc_dir, output_dir, use_mcmeta, use_addons)
        self.last_context = None
        self.debug_i18n = debug_i18n

        self.categories: Dict[str, Category] = {}
        self.entries: Dict[str, Entry] = {}
        self.sorted_categories: List[Tuple[str, Category]] = []

        self.keybindings: Dict[str, str] = {}

        self.lang = None
        self.lang_keys = {}
        self.last_uid = {
            'content': 0,
            'image': 0,
            'item': 0,
            'block': 0,
            'fluid': 0,
        }

        self.recipes_failed = 0
        self.recipes_passed = 0
        self.recipes_skipped = 0
        self.items_passed = 0
        self.items_failed = 0
        self.blocks_passed = 0
        self.blocks_failed = 0
    
    def with_lang(self, lang: str):
        self.lang = lang
        self.output_dir = util.path_join(self.output_root_dir, lang)

        # Instance Properties
        self.categories = {}
        self.entries = {}
        self.sorted_categories = []

        self.lang_keys = {}
        for domain in self.loader.domains:
            try:
                self.lang_keys.update(self.loader.load_lang(lang, domain))
            except InternalError as e:
                LOG.warning('Translation : %s' % e)
        
        self.with_local_lang('en_us')  # First load en_us
        self.with_local_lang(lang)  # Then load the current language

        # Load keybindings
        self.keybindings = {k[len('field_guide.'):]: self.translate(k) for k in I18n.KEYS}

        return self
    
    def with_local_lang(self, lang: str):
        try:
            with open(util.path_join('./assets/lang/%s.json' % lang), 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k, v in data.items():
                self.lang_keys['field_guide.%s' % k] = v
        except OSError as e:
            LOG.warning('Local Translation : %s : %s' % (lang, e))

    def next_id(self, prefix: str = 'content') -> str:
        """ Returns a unique ID to be used in a id="" field. Successive calls will return a new ID. """
        self.last_uid[prefix] += 1
        return '%s%d' % (prefix, self.last_uid[prefix])
    
    def add_entry(self, category_id: str, entry_id: str, entry: Entry):
        self.entries[entry_id] = entry
        self.categories[category_id].entries.append(entry_id)
    
    def sort(self):
        """ Initializes sorted lists for all categories and entries. """
        self.sorted_categories = sorted([
            (c, c_id) for c, c_id in self.categories.items()
        ], key=lambda c: (c[1].sort, c[0]))

        for _, cat in self.sorted_categories:
            sorted_entry_names = sorted(cat.entries, key=lambda e: (self.entries[e].sort, e))
            cat.sorted_entries = [(e, self.entries[e]) for e in sorted_entry_names]
    
    def format_text(self, buffer: List[str], data: Any, key: str = 'text'):
        if key in data:
            text_formatter.format_text(buffer, data[key], self.keybindings)
    
    def format_title(self, buffer: List[str], data: Any, key: str = 'title'):
        if key in data:
            buffer.append('<h5>%s</h5>\n' % text_formatter.strip_vanilla_formatting(data[key]))

    def format_title_with_icon(self, buffer: List[str], icon_src: str, icon_name: str | None, data: Any, key: str = 'title'):
        title = icon_name
        if key in data:
            title = text_formatter.strip_vanilla_formatting(data[key])
            if not icon_name:  # For multi-items, no name, but title is present
                icon_name = title
        buffer.append("""
        <div class="item-header">
            <span href="#" data-toggle="tooltip" title="%s">
                <img src="%s" alt="%s" />
            </span>
            <h5>%s</h5>
        </div>
        """ % (icon_name, icon_src, title, title))

    def format_centered_text(self, buffer: List[str], data: Any, key: str = 'text'):
        buffer.append('<div style="text-align: center;">')
        self.format_text(buffer, data, key)
        buffer.append('</div>')
    
    def format_with_tooltip(self, buffer: List[str], text: str, tooltip: str):
        buffer.append("""
        <div style="text-align: center;">
            <p class="text-muted"><span href="#" data-toggle="tooltip" title="%s">%s</span></p>
        </div>
        """ % (tooltip, text))
    
    def format_recipe(self, buffer: List[str], data: Any, key: str = 'recipe'):
        if key in data:
            self.format_with_tooltip(buffer, '%s: <code>%s</code>' % (
                self.translate(I18n.RECIPE),
                data[key]
            ), self.translate(I18n.RECIPE_ONLY_IN_GAME))

    def translate(self, *keys: str) -> str:
        if self.debug_i18n:
            return '{%s}' % keys[0]
        for key in keys:
            if key in self.lang_keys:
                return self.lang_keys[key]
        util.error('Missing Translation Keys %s' % repr(keys))

    def convert_image(self, image: str) -> str:
        if image in IMAGE_CACHE:
            return IMAGE_CACHE[image]

        img = self.loader.load_explicit_texture(image)
        
        width, height = img.size
        assert width == height and width % 256 == 0
        size = width * 200 // 256
        img = img.crop((0, 0, size, size))
        if size != 400:
            # Resize to 400 x 400, for consistent size images
            img = img.resize((400, 400), Image.Resampling.NEAREST)

        ref = self.loader.save_image(self.next_id('image'), img)
        IMAGE_CACHE[image] = ref
        return ref
