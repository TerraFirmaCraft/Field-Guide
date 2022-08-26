from typing import List
from util import LOG

import re


def format_text(buffer: List[str], text: str):
    TextFormatter(buffer, text)


class TextFormatter:
    
    def __init__(self, buffer: List[str], text: str):
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
            elif key == 'd':  # We use this color instead of white for temperature tooltips. Use custom CSS for white.
                self.matching_tags('<span class="minecraft-white">', '</span>')
            elif key in VANILLA_COLORS:
                self.color_tags(VANILLA_COLORS[key])
            elif key.startswith('k:') and key[2:] in KEYS:
                self.buffer.append(KEYS[key[2:]])
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

KEYS = {
    'key.inventory': 'E',
    'key.attack': 'Left Click',
    'key.use': 'Right Click',
    'key.drop': 'Q',
    'key.sneak': 'Shift',

    'tfc.key.cycle_chisel_mode': 'M',
    'tfc.key.place_block': 'V'
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
