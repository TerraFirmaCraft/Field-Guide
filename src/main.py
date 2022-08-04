import os
import json
import warnings

from typing import List, Dict, Any
from argparse import ArgumentParser

from context import Context
from category import Category
from entry import Entry


Keyable = Dict[str, Any]


KEYS = {
    'key.inventory': 'E',
    'key.attack': 'Left Click',
    'key.use': 'Right Click',
    'key.drop': 'Q',
    'key.sneak': 'Shift',

    'tfc.key.cycle_chisel_mode': 'M',
    'tfc.key.place_block': 'V'
}


def main():
    # Arguments
    parser = ArgumentParser('TFC Field Guide')
    parser.add_argument('--tfc-dir', type=str, dest='tfc_dir', default='../TerraFirmaCraft')
    parser.add_argument('--out-dir', type=str, dest='out_dir', default='out')

    args = parser.parse_args()

    tfc_dir = args.tfc_dir
    output_dir = args.out_dir

    book_rel_dir = 'src/main/resources/data/tfc/patchouli_books/field_guide/en_us'
    image_rel_dir = 'src/main/resources/assets/tfc'

    book_dir = os.path.join(tfc_dir, book_rel_dir)
    image_dir = os.path.join(tfc_dir, image_rel_dir)
    category_dir = os.path.join(book_dir, 'categories')

    context = Context(book_dir, image_dir, output_dir, KEYS)

    print('Generating docs...')

    os.makedirs(os.path.join(output_dir, '_images'), exist_ok=True)

    for category_file in walk(category_dir):
        if category_file.endswith('.json'):
            with open(category_file, 'r', encoding='utf-8') as f:
                data: Keyable = json.load(f)

            category: Category = Category()
            category_id: str = os.path.relpath(category_file, category_dir)
            category_id = category_id[:category_id.index('.')]

            convert_category(category, category_id, data)

            context.categories[category_id] = category
            print('Read category: %s at %s' % (category_id, category_file))
        else:
            warnings.warn('Unknown category file: %s' % category_file)

    entry_dir = os.path.join(book_dir, 'entries')

    for entry_file in walk(entry_dir):
        if entry_file.endswith('.json'):
            with open(entry_file, 'r', encoding='utf-8') as f:
                data: Keyable = json.load(f)

            entry: Entry = Entry()
            entry_id: str = os.path.relpath(entry_file, entry_dir)
            entry_id = entry_id[:entry_id.index('.')]
            category_id: str = data['category']
            category_id = category_id[category_id.index(':') + 1:]

            convert_entry(context, entry, data)

            context.add_entry(category_id, entry_id, entry)
            print('Read entry: %s at %s' % (entry_id, entry_file))
        else:
            warnings.warn('Unknown entry file: %s' % entry_file)

    context.sort()

    # Main Page
    with open(prepare(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(PREFIX.format(
            title=TITLE,
            index='#',
            location='<a class="text-muted" href="#">Index</a>',
            contents='\n'.join([
                '<li><a class="text-muted" href="./%s/index.html">%s</a></li>' % (cat_id, cat.name)
                for cat_id, cat in context.sorted_categories
            ])
        ))
        f.write("""
        <h3>TerraFirmaCraft Online Field Guide</h3>
        <p>This is a translation of the TerraFirmaCraft Field Guide, which is viewable in game. Some parts of this field guide are only visible in-game, such as multiblock visualizations or recipes.</p>
        <h4>Entries</h4>
        """)

        for cat_id, cat in context.sorted_categories:
            f.write("""
            <div class="card">
                <div class="card-header">
                    <a href="%s/index.html">%s</a>
                </div>
                <div class="card-body">
                    <p class="card-text">%s</p>
                </div>
            </div>
            """ % (cat_id, cat.name, cat.description))

        f.write(SUFFIX)

    # Category Pages
    for category_id, cat in context.sorted_categories:
        with open(prepare(output_dir, category_id + '/index.html'), 'w', encoding='utf-8') as f:
            f.write(PREFIX.format(
                title=TITLE,
                index='../index.html',
                location='<a class="text-muted" href="../index.html">Index</a> / <a class="text-muted" href="#">%s</a>' % cat.name,
                contents='\n'.join([
                    '<li><a class="text-muted" href="../%s/index.html">%s</a></li>' % (cat_id, cat.name) + (
                        ''
                        if cat_id != category_id else
                        '<ul class="list-unstyled push-right">%s</ul>' % '\n'.join([
                            '<li><a class="text-muted" href="./%s.html">%s</a></li>' % (os.path.relpath(ent_id, cat_id), ent.name)
                            for ent_id, ent in cat.sorted_entries 
                        ])
                    )
                    for cat_id, cat in context.sorted_categories
                ])
            ))
            f.write('<h4>%s</h4><p>%s</p><hr>' % (cat.name, cat.description))
            f.write('<div class="card-columns">')

            for entry_id, entry in cat.sorted_entries:
                f.write("""
                <div class="card">
                    <div class="card-header">
                        <a href="%s.html">%s</a>
                    </div>
                </div>
                """ % (os.path.relpath(entry_id, category_id), entry.name))
            
            f.write('</div>')
            f.write(SUFFIX)

        # Entry Pages
        for entry_id, entry in cat.sorted_entries:
            with open(prepare(output_dir, entry_id + '.html'), 'w', encoding='utf-8') as f:
                f.write(PREFIX.format(
                    title=TITLE,
                    index='../index.html',
                    location='<a class="text-muted" href="../index.html">Index</a> / <a class="text-muted" href="./index.html">%s</a> / <a class="text-muted" href="#">%s</a>' % (cat.name, entry.name),
                    contents='\n'.join([
                        '<li><a class="text-muted" href="../%s/index.html">%s</a>' % (cat_id, cat.name) + (
                            '</li>'
                            if cat_id != category_id else
                            '<ul class="list-unstyled push-right">%s</ul>' % '\n'.join([
                                '<li><a class="text-muted" href="./%s.html">%s</a></li>' % (os.path.relpath(ent_id, cat_id), ent.name)
                                for ent_id, ent in cat.sorted_entries 
                            ]) + '</li>'
                        )
                        for cat_id, cat in context.sorted_categories
                    ])
                ))
                f.write('<h4>%s</h4><hr>' % (entry.name))

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


def convert_category(category: Category, category_id: str, data: Keyable):
    category_name: str = data['name']
    category_desc: str = data['description']

    category.push('<p><a href="./%s/index.html">%s</a>: %s</p>\n' % (category_id, category_name, category_desc))
    category.name = category_name
    category.description = category_desc
    category.sort = data['sortnum']


def convert_entry(context: Context, entry: Entry, data: Keyable):
    entry.sort = data['sortnum'] if 'sortnum' in data else -1
    entry.name = data['name']

    for page in data['pages']:
        convert_page(context, entry.buffer, page)


def convert_page(context: Context, buffer: List[str], data: Keyable):
    page_type = data['type']

    if 'anchor' in data:
        buffer.append('<div id="anchor-%s">' % data['anchor'])

    if page_type == 'patchouli:text':
        context.format_title(buffer, data)
        context.format_text(buffer, data)
    elif page_type == 'patchouli:image':
        context.format_title(buffer, data)
        
        images = data['images']
        if len(images) == 1:
            image = images[0]
            uid = context.next_id()
            buffer.append(IMAGE_SINGLE.format(
                id=uid,
                src=context.convert_image(image),
                text=image
            ))
        else:
            uid = context.next_id()
            parts = [IMAGE_MULTIPLE_PART.format(
                src=context.convert_image(image),
                text=image,
                active='active' if i == 0 else ''
            ) for i, image in enumerate(images)]

            seq = [IMAGE_MULTIPLE_SEQ.format(
                id=uid,
                count=i
            ) for i, _ in enumerate(images) if i > 0]

            buffer.append(IMAGE_MULTIPLE.format(
                id=uid,
                seq=''.join(seq),
                parts=''.join(parts)
            ))
        
        context.format_centered_text(buffer, data)

    elif page_type == 'patchouli:crafting':
        context.format_title(buffer, data)
        context.format_recipe(buffer, data)
        context.format_recipe(buffer, data, 'recipe2')
        context.format_text(buffer, data)
    elif page_type == 'patchouli:spotlight':
        context.format_title(buffer, data)
        context.format_text(buffer, data)
    elif page_type == 'patchouli:entity':
        context.format_title(buffer, data, 'name')
        context.format_text(buffer, data)
    elif page_type == 'patchouli:empty':
        buffer.append('<hr>')
    elif page_type == 'patchouli:multiblock' or page_type == 'tfc:multimultiblock':
        pass
    elif page_type in (
        'tfc:welding_recipe',
        'tfc:anvil_recipe',
        'tfc:heat_recipe',
        'tfc:rock_knapping_recipe',
        'tfc:clay_knapping_recipe',
        'tfc:fire_clay_knapping_recipe',
        'tfc:leather_knapping_recipe',
        'tfc:quern_recipe'
    ):
        context.format_recipe(buffer, data)
        context.format_text(buffer, data)
    else:
        buffer.append('<p>Missing Page: %s</p>' % page_type)
        warnings.warn('Unrecognized page type: "type": "%s"' % page_type)

    if 'anchor' in data:
        buffer.append('</div>')



PREFIX = """
<!DOCTYPE html>
<html style="width:100%; height:100%; padding:0px; margin:0px;">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
    <meta charset="UTF-8">
    
    <title>{title}</title>
    
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">

    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.12.9/umd/popper.min.js" integrity="sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>

    <style>
    .carousel-inner img {{
        margin: auto;
    }}

    .carousel-control-next,
    .carousel-control-prev {{
        filter: invert(100%);
    }}

    .tooltip {{
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }}

    .push-right {{
        padding-left: 30px
    }}

    </style>

    <script type="text/javascript">
        $(function () {{
            $('[data-toggle="tooltip"]').tooltip()
        }})
    </script>
</head>
<body>

<nav class="navbar navbar-expand-sm fixed-top bg-dark">
    <div class="container-fluid">
        <div class="navbar-header">
            <a class="navbar-brand text-light" href="#">{title}</a>
        </div>
        <ul class="navbar-nav">
            <li class="nav-item active"><a class="nav-link text-light" href="{index}">Index</a></li>
            <li class="nav-item"><a class="nav-link text-light" href="https://terrafirmacraft.github.io/Documentation/"><i class="fa fa-cogs"></i> API Docs</a></li>
            <li class="nav-item"><a class="nav-link text-light" href="https://github.com/TerraFirmaCraft/TerraFirmaCraft"><i class="fa fa-github"></i> GitHub</a></li>
            <li class="nav-item"><a class="nav-link text-light" href="https://discord.gg/PRuAKvY">Discord</a></li>
        </ul>
    </div>
</nav>
<div class="container-fluid" style="margin-top:50px">
    <div class="row">
        <div class="col-2 py-1">
            <div class="sticky-top" style="top: 70px">
                <h4>Contents</h4>
                <ul class="list-unstyled">
                    {contents}
                </ul>
            </div>
        </div>
        <div class="col-9 py-3">
            <p><em>{location}</em></p>
"""

SUFFIX = """
        </div>
    </div>
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

TITLE = 'TerraFirmaCraft Field Guide'



if __name__ == '__main__':
    main()
