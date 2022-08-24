import re

from typing import Dict, List, Tuple, Any
from PIL import Image
from category import Category
from entry import Entry
from util import LOG, InternalError
from components.loader import Loader


VANILLA_COLORS = {
    '0': '#000000',
    '1': '#0000AA',
    '2': '#00AA00',
    '3': '#00AAAA',
    '4': '#AA0000',
    '5': '#AA00AA',
    '6': '#FFAA00',
    '7': '#AAAAAA',
    '8': '#555555',
    '9': '#5555FF',
    'a': '#55FF55',
    'b': '#55FFFF',
    'c': '#FF5555',
    'd': '#FF55FF',
    'e': '#FFFF55',
    'f': '#FFFFFF',
}

ROOT_TAGS = {
    'p': {
        None: '</p>\n',
        'p': '</p>\n<p>',
        'li': '</p>\n<ul>\n\t<li>',
        'ol': '</p>\n<ol>\n\t<li>'
    },
    'li': {
        None: '</li>\n</ul>\n',
        'li': '</li>\n\t<li>',
        'p': '</li>\n</ul><p>'
    },
    'ol': {
        None: '</li>\n</ol>\n',
        'ol': '</li>\n\t<li>',
        'p': '</li>\n</ol><p>'
    }
}

RECIPE_DIR = 'src/main/resources/data/tfc/recipes'


class Context:
    book_dir: str
    output_dir: str

    keys: Dict[str, str]

    categories: Dict[str, Category]
    entries: Dict[str, Entry]

    sorted_categories: List[Tuple[str, Category]]

    last_uid: int

    loader: Loader

    def __init__(self, tfc_dir: str, book_dir: str, output_dir: str, lang: str, keys: Dict[str, str]):
        self.tfc_dir = tfc_dir
        self.book_dir = book_dir
        self.output_dir = output_dir
        self.lang = lang
        self.keys = keys
        self.categories = {}
        self.entries = {}
        self.sorted_categories = []
        self.last_uid = 0
        self.loader = Loader(tfc_dir, output_dir)
        try:
            self.lang_json = self.loader.load_json(lang, 'lang', 'assets')
        except InternalError as e:
            e.warning()
            self.lang_json = {}
    
    def next_id(self) -> str:
        """ Returns a unique ID to be used in a id="" field. Successive calls will return a new ID. """
        self.last_uid += 1
        return 'content-element-%d' % self.last_uid
    
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
            TextFormatter(self, buffer, data[key])
    
    def format_title(self, buffer: List[str], data: Any, key: str = 'title'):
        if key in data:
            buffer.append('<h5>%s</h5>\n' % data[key])

    def format_title_with_icon(self, buffer: List[str], icon_src: str, icon_name: str | None, data: Any, key: str = 'title'):
        title = icon_name
        if key in data:
            title = data[key]
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
            self.format_with_tooltip(buffer, 'Recipe: <code>%s</code>' % data[key], 'View the field guide in Minecraft to see recipes')

    def convert_image(self, image: str) -> str:
        _, img = self.loader.load_image(image)
        
        width, height = img.size
        assert width == height and width % 256 == 0
        size = width * 200 // 256
        img = img.crop((0, 0, size, size))
        if size != 400:
            # Resize to 400 x 400, for consistent size images
            img = img.resize((400, 400), Image.Resampling.NEAREST)

        return self.loader.save_image(image, img)


class TextFormatter:
    
    def __init__(self, context: Context, buffer: List[str], text: str):
        self.root = 'p'
        self.stack = []
        self.buffer = buffer
        self.buffer.append('<p>')

        cursor = 0

        # Patchy doesn't have an ordered list function / macro. So we have to recognize a specific pattern outside of a macro to properly HTML-ify them
        text = re.sub(r'\$\(br\)  [0-9+]. ', '$(ol)', text)

        for match in re.finditer(r'\$\(([^)]*)\)', text):
            start, end = match.span()
            key = match.group(1)
            if start > cursor:
                self.buffer.append(text[cursor:start])
            if key == '':
                self.flush_stack()
            elif key == 'bold' or key == 'l':
                self.matching_tags('<strong>', '</strong>')
            elif key == 'italic' or key == 'italics' or key == 'o':
                self.matching_tags('<em>', '</em>')
            elif key == 'br':
                self.update_root('p')
            elif key == 'br2' or key == '2br':
                self.update_root('p')
                self.update_root('p')
            elif key == 'ol':  # Fake formatting code
                self.update_root('ol')
            elif key == 'li':
                self.update_root('li')
            elif key.startswith('l:http'):
                self.matching_tags('<a href="%s">' % key[2:], '</a>')
            elif key.startswith('l:'):
                link = key[2:]
                link = link.replace('#', '.html#anchor-') if '#' in link else link + '.html'
                self.matching_tags('<a href="../%s">' % link, '</a>')
            elif key == 'thing':
                self.color_tags('#490')
            elif key == 'item':
                self.color_tags('#b0b')
            elif key.startswith('#'):
                self.color_tags(key)
            elif key in VANILLA_COLORS:
                self.color_tags(VANILLA_COLORS[key])
            elif key.startswith('k:') and key[2:] in context.keys:
                self.buffer.append(context.keys[key[2:]])
            elif key.startswith('t'):
                pass  # Discard tooltips
            else:
                LOG.warning('Unrecognized Formatting Code $(%s)' % key)

            cursor = end

        self.buffer.append(text[cursor:])
        self.flush_stack()
        self.update_root()
    
    def matching_tags(self, start: str, end: str):
        self.buffer.append(start)
        self.stack.append(end)

    def color_tags(self, color: str):
        self.matching_tags('<span style="color:%s;">' % color, '</span>')

    def flush_stack(self):
        for _end in self.stack[::-1]:
            self.buffer.append(_end)
        self.stack = []

    def update_root(self, new_root: str = None):
        self.buffer.append(ROOT_TAGS[self.root][new_root])
        self.root = new_root
