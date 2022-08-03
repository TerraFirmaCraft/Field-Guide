import re
import os
import warnings

from typing import Dict, List, Tuple, Any
from PIL import Image
from category import Category
from entry import Entry


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
        'p': '</li>\n<p>'
    },
    'ol': {
        None: '</li>\n</ol>\n',
        'ol': '</li>\n\t<li>',
        'p': '</li>\n<p>'
    }
}

Keyable = Dict[str, Any]


class Context:
    book_dir: str
    image_dir: str
    output_dir: str

    keys: Dict[str, str]

    categories: Dict[str, Category]
    entries: Dict[str, Entry]

    sorted_categories: List[Tuple[str, Category]]

    last_uid: int

    def __init__(self, book_dir: str, image_dir: str, output_dir: str, keys: Dict[str, str]):
        self.book_dir = book_dir
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.keys = keys
        self.categories = {}
        self.entries = {}
        self.sorted_categories = []
        self.last_uid = 0
    
    def next_id(self) -> str:
        """ Returns a unique ID to be used in a id="" field. Successive calls will return a new ID. """
        self.last_uid += 1
        return 'content-element-%d' % self.last_uid
    
    def sort(self):
        """ Initializes sorted lists for all categories and entries. """
        self.sorted_categories = sorted([
            (c, c_id) for c, c_id in self.categories.items()
        ], key=lambda c: (c[1].sort, c[0]))

        for _, cat in self.sorted_categories:
            sorted_entry_names = sorted(cat.entries, key=lambda e: (self.entries[e].sort, e))
            cat.sorted_entries = [(e, self.entries[e]) for e in sorted_entry_names]
    
    def format_text(self, buffer: List[str], data: Keyable, key: str = 'text'):
        if key in data:
            TextFormatter(buffer, data[key])
    
    def format_title(self, buffer: List[str], data: Keyable, key: str = 'title'):
        if key in data:
            buffer.append('<h5>%s</h5>\n' % data[key])
    
    def format_centered_text(self, buffer: List[str], data: Keyable, key: str = 'text'):
        buffer.append('<div style="text-align: center;">')
        self.format_text(buffer, data, key)
        buffer.append('</div>')
    
    def format_with_tooltip(self, buffer: List[str], text: str, tooltip: str):
        buffer.append("""
        <div style="text-align: center;">
            <p><em><a href="#" data-toggle="tooltip" title="%s">%s</a></em></p>
        </div>
        """ % (tooltip, text))
    
    def format_recipe(self, buffer: List[str], data: Keyable, key: str = 'recipe'):
        if key in data:
            self.format_with_tooltip(buffer, 'Recipe: <code>%s</code>' % data[key], 'View the field guide in Minecraft to see recipes')
    
    def convert_image(self, image: str) -> str:
        namespace, path = image.split(':')

        assert namespace == 'tfc'
        assert path.endswith('.png')

        src = os.path.join(self.image_dir, path)
        rel = os.path.join('_images', path.replace('/', '_').replace('textures_gui_book_', ''))
        dest = os.path.join(self.output_dir, rel)

        img = Image.open(src).convert('RGBA')
        width, height = img.size

        assert width == height and width % 256 == 0

        size = width * 200 // 256
        img = img.crop((0, 0, size, size))
        if size != 400:
            # Resize to 400 x 400, for consistent size images
            img = img.resize((400, 400), Image.Resampling.NEAREST)
        img.save(dest)

        return '../' + rel


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
            elif key == 'bold':
                self.matching_tags('<strong>', '</strong>')
            elif key == 'italic':
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
                warnings.warn('Unrecognized Formatting Code $(%s)' % key)

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
