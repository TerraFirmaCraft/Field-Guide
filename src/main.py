"""
Prototype for converting the book JSONs into a web readable format

Planned features:
- Formatted text parsing
- Handle image pages
- Icons?
- Relative Links

Stretch Goals:
- Any kind of recipe visualization? Perhaps by an in-game tool to export required pages / images.
- Any kind of multiblock, block, or item spotlights

"""

import os
import re
import json
from sre_parse import parse_template
import warnings

from typing import Tuple, List, Dict, Any

from PIL import Image

JsonObject = Dict[str, Any]


class Category:
    buffer: List[str]
    entries: List[str]
    sort: int
    name: str

    def __init__(self):
        self.buffer = []
        self.entries = []
        self.sort = -1
        self.name = ''

    def __repr__(self) -> str: return str(self)
    def __str__(self) -> str: return self.name


class Entry:
    buffer: List[str]
    sort: int
    name: str

    def __init__(self):
        self.buffer = []
        self.sort = -1
        self.name = ''

    def __repr__(self) -> str: return str(self)
    def __str__(self) -> str: return self.name


class Context:
    book_dir: str
    image_dir: str
    output_dir: str

    categories: Dict[str, Category]

    def __init__(self, book_dir: str,image_dir: str, output_dir: str):
        self.book_dir = book_dir
        self.image_dir = image_dir
        self.output_dir = output_dir
        self.categories = {}


def main():
    # Arguments
    tfc_dir = 'D:/Minecraft/Mods/TerraFirmaCraft-1.18'
    book_rel_dir = 'src/main/resources/data/tfc/patchouli_books/field_guide/en_us'
    image_rel_dir = 'src/main/resources/assets/tfc'

    book_dir = os.path.join(tfc_dir, book_rel_dir)
    image_dir = os.path.join(tfc_dir, image_rel_dir)
    output_dir = 'out'

    category_dir = os.path.join(book_dir, 'categories')

    context = Context(book_dir, image_dir, output_dir)
    categories = context.categories

    os.makedirs(os.path.join(output_dir, '_images'), exist_ok=True)

    for category_file in walk(category_dir):
        if category_file.endswith('.json'):
            with open(category_file, 'r', encoding='utf-8') as f:
                data: JsonObject = json.load(f)

            category: Category = Category()
            category_id: str = os.path.relpath(category_file, category_dir)
            category_id = category_id[:category_id.index('.')]

            convert_category(category, category_id, data)

            categories[category_id] = category
        else:
            warnings.warn('Unknown category file: %s' % category_file)

    entry_dir = os.path.join(book_dir, 'entries')
    entries: Dict[str, Entry] = {}

    for entry_file in walk(entry_dir):
        if entry_file.endswith('.json'):
            with open(entry_file, 'r', encoding='utf-8') as f:
                data: JsonObject = json.load(f)

            entry: Entry = Entry()
            entry_id: str = os.path.relpath(entry_file, entry_dir)
            entry_id = entry_id[:entry_id.index('.')]
            category_id: str = data['category']
            category_id = category_id[category_id.index(':') + 1:]

            convert_entry(context, categories[category_id], entry, data)

            entries[entry_id] = entry
            categories[category_id].entries.append(entry_id)
        else:
            warnings.warn('Unknown entry file: %s' % entry_file)

    sorted_categories: List[Tuple[str, Category]] = sorted([(c, c_id) for c, c_id in categories.items()], key=lambda c: (c[1].sort, c[0]))

    with open(prepare(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(PREFIX.format(title='Book'))
        f.write('<h1>Book</h1><hr>\n')
        f.write('<h3>Categories</h3>')
        for cat_id, cat in sorted_categories:
            for line in cat.buffer:
                f.write(line)
            f.write('\n')
        f.write(SUFFIX)

    for category_id, cat in sorted_categories:
        with open(prepare(output_dir, category_id + '/index.html'), 'w', encoding='utf-8') as f:
            f.write(PREFIX.format(title=cat.name))
            f.write('<h1>%s</h1><hr>\n' % cat.name)
            f.write('<h3>Entries</h3>')

            sorted_entries = sorted(cat.entries, key=lambda e: (entries[e].sort, e))

            for entry_id in sorted_entries:
                entry = entries[entry_id]
                f.write('<p><a href="%s.html">%s</a></p>\n' % (os.path.relpath(entry_id, category_id), entry.name))
            f.write(SUFFIX)

    for entry_id, entry in entries.items():
        with open(prepare(output_dir, entry_id + '.html'), 'w', encoding='utf-8') as f:
            f.write(PREFIX.format(title=entry.name))
            for line in entry.buffer:
                f.write(line)
            f.write(SUFFIX)


def walk(path: str):
    if os.path.isfile(path):
        yield path
    elif os.path.isdir(path):
        for sub in os.listdir(path):
            yield from walk(os.path.join(path, sub))


def prepare(root: str, path: str) -> str:
    full = os.path.join(root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full


def convert_category(cat: Category, category_id: str, data: JsonObject):
    category_name: str = data['name']
    category_desc: str = data['description']

    cat.buffer.append('<p><a href="./%s/index.html">%s</a>: %s</p>\n' % (category_id, category_name, category_desc))
    cat.name = category_name
    cat.sort = data['sortnum']


def convert_entry(ctx: Context, cat: Category, entry: Entry, data: JsonObject):
    entry.sort = data['sortnum'] if 'sortnum' in data else -1
    entry.name = data['name']

    entry.buffer.append("""
    <div class="row">
    <div class="col-12">
    <h2>TerraFirmaCraft Guide Book</h2>
    <p><em><a href="../index.html">Index</a> / <a href="./index.html">%s</a> / <a href="#">%s</a><p></em>
    <hr>
    </div>
    </div>
    <div class="row">
    <div class="col-2"></div>
    <div class="col-8">
    """ % (
        cat.name,
        entry.name
    ))

    for page in data['pages']:
        convert_page(ctx, entry.buffer, page)

    entry.buffer.append("""
    </div>
    <div class="col-2"></div>
    """)


def convert_page(ctx: Context, buffer: List[str], data: JsonObject):
    page_type = data['type']

    if 'anchor' in data:
        buffer.append('<div id="anchor-%s">' % data['anchor'])

    if page_type == 'patchouli:text':
        if 'title' in data:
            title = data['title']
            buffer.append('<h4>%s</h4>\n' % title)
        convert_formatted_text(buffer, data['text'])
    elif page_type == 'patchouli:image':
        if 'title' in data:
            title = data['title']
            buffer.append('<h4>%s</h4>\n' % title)
        
        images = data['images']
        if len(images) == 1:
            image = images[0]
            buffer.append(IMAGE_SINGLE.format(
                id='fixme-1',
                src=convert_image(ctx, image),
                text=image
            ))
        else:
            parts = [IMAGE_MULTIPLE_PART.format(
                src=convert_image(ctx, image),
                text=image,
                active='active' if i == 0 else ''
            ) for i, image in enumerate(images)]

            seq = [IMAGE_MULTIPLE_SEQ.format(
                id='fixme-2',
                count=i
            ) for i, _ in enumerate(images) if i > 0]

            buffer.append(IMAGE_MULTIPLE.format(
                id='fixme-2',
                seq=''.join(seq),
                parts=''.join(parts)
            ))
        
        if 'text' in data:
            buffer.append('<div style="text-align: center;">')
            convert_formatted_text(buffer, data['text'])
            buffer.append('</div>')

    elif page_type == 'patchouli:empty':
        buffer.append('<hr>\n')
    else:
        buffer.append('<p>Missing Page: %s</p>' % page_type)
        warnings.warn('Unrecognized page type: "type": "%s"' % page_type)

    if 'anchor' in data:
        buffer.append('</div>')


def convert_image(ctx: Context, image: str) -> str:
    namespace, path = image.split(':')
    
    assert namespace == 'tfc'
    assert path.endswith('.png')

    src = os.path.join(ctx.image_dir, path)
    rel = os.path.join('_images', path.replace('/', '_').replace('textures_gui_book_', ''))
    dest = os.path.join(ctx.output_dir, rel)
    
    img = Image.open(src).convert('RGBA')
    width, height = img.size

    assert width == height and width % 256 == 0

    size = width * 200 // 256
    img = img.crop((0, 0, size, size))
    img.save(dest)

    return '../' + rel



def convert_formatted_text(buffer: List[str], text: str, link_root: str = '../'):
    cursor = 0
    root = ['p']
    buffer.append('<p>')
    stack = []

    def matching_tags(_start: str, _end: str):
        buffer.append(_start)
        stack.append(_end)

    def color_tags(_color: str):
        matching_tags('<span style="color:%s;">' % _color, '</span>')

    def flush_stack():
        for _end in stack[::-1]:
            buffer.append(_end)
        return []

    def update_root(_new_root: str = None):
        _old_root = root[0]
        if _new_root is None:
            if _old_root == 'p':
                buffer.append('</p>\n')
            elif _old_root == 'li':
                buffer.append('</li>\n</ul>\n')
        elif _old_root == 'p' and _new_root == 'p':
            buffer.append('</p>\n<p>')
        elif _old_root == 'p' and _new_root == 'li':
            buffer.append('</p>\n<ul>\n\t<li>')
        elif _old_root == 'li' and _new_root == 'li':
            buffer.append('</li>\n\t<li>')
        elif _old_root == 'li' and _new_root == 'p':
            buffer.append('</li>\n</ul>\n')
        root[0] = _new_root

    for match in re.finditer(r'\$\(([^)]*)\)', text):
        start, end = match.span()
        key = match.group(1)
        if start > cursor:
            buffer.append(text[cursor:start])
        if key == '':
            stack = flush_stack()
        elif key == 'bold':
            matching_tags('<strong>', '</strong>')
        elif key == 'italic':
            matching_tags('<em>', '</em>')
        elif key == 'br':
            update_root('p')
        elif key == 'br2' or key == '2br':
            update_root('p')
            update_root('p')
        elif key == 'li':
            update_root('li')
        elif key.startswith('l:http'):
            matching_tags('<a href="%s">' % key[2:], '</a>')
        elif key.startswith('l:'):
            link = key[2:]
            link = link.replace('#', '.html#anchor-') if '#' in link else link + '.html'
            matching_tags('<a href="%s%s">' % (link_root, link), '</a>')
        elif key == 'thing':
            color_tags('#490')
        elif key == 'item':
            color_tags('#b0b')
        elif key.startswith('#'):
            color_tags(key)
        elif key in VANILLA_COLORS:
            color_tags(VANILLA_COLORS[key])
        elif key.startswith('k:') and key[2:] in VANILLA_KEYS:
            buffer.append(VANILLA_KEYS[key[2:]])
        else:
            warnings.warn('Unrecognized Formatting Code $(%s)' % key)

        cursor = end

    buffer.append(text[cursor:])
    flush_stack()
    update_root()


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

VANILLA_KEYS = {
    'key.inventory': 'E',
    'key.use': 'Right Click'
}

PREFIX = """
<!DOCTYPE html>
<html style="width:100%; height:100%; padding:0px; margin:0px;">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
    <meta charset="UTF-8">
    
    <title>{title}</title>
    
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

    <style>
    .carousel-inner img {{
        margin: auto;
    }}
    .carousel-control-next,
    .carousel-control-prev /*, .carousel-indicators */ {{
        filter: invert(100%);
    }}
    </style>
</head>
<body>
<div class="container">
"""

SUFFIX = """
</div>
</body>
</html>
"""

IMAGE_SINGLE = """
<div id="{id}" class="carousel slide" data-ride="carousel">
    <div class="carousel-inner">
        <div class="carousel-item active">
            <img class="d-block w-200" src="{src}" alt="{text}">
        </div>
    </div>
</div>
"""

IMAGE_MULTIPLE_PART = """
<div class="carousel-item {active}">
    <img class="d-block w-200" src="{src}" alt="{text}">
</div>
"""

IMAGE_MULTIPLE_SEQ = """
<li data-target="#{id}" data-slide-to="{count}"></li>
"""

IMAGE_MULTIPLE = """
<div id="{id}" class="carousel slide" data-ride="carousel">
    <ol class="carousel-indicators">
        <li data-target="#{id}" data-slide-to="0" class="active"></li>
        {seq}
    </ol>
    <div class="carousel-inner">
        {parts}
    </div>
    <a class="carousel-control-prev" href="#{id}" role="button" data-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="sr-only">Previous</span>
    </a>
    <a class="carousel-control-next" href="#{id}" role="button" data-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="sr-only">Next</span>
    </a>
</div>
"""



if __name__ == '__main__':
    main()
