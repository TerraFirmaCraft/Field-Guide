import os
import json
import util
import shutil
import logging
import versions
import subprocess

from typing import List, Any
from argparse import ArgumentParser

from util import LOG, InternalError
from context import Context
from category import Category
from entry import Entry
from i18n import I18n
from components import item_loader, block_loader, crafting_recipe, knapping_recipe, misc_recipe, mcmeta, text_formatter


BOOK_DIR = 'src/main/resources/data/%s/patchouli_books/field_guide/'
TEMPLATE = util.load_html('default')


def main():
    # Arguments
    parser = ArgumentParser('TFC Field Guide')
    parser.add_argument('--tfc-dir', type=str, dest='tfc_dir', default='../TerraFirmaCraft')
    parser.add_argument('--out-dir', type=str, dest='out_dir', default='out')
    parser.add_argument('--debug', action='store_true', dest='log_debug')
    parser.add_argument('--use-mcmeta', action='store_true', dest='use_mcmeta')
    parser.add_argument('--use-addons', action='store_true', dest='use_addons', help='Download addons directly from source')
    parser.add_argument('--debug-i18n', action='store_true', dest='debug_i18n')
    parser.add_argument('--debug-only-en-us', action='store_true', dest='debug_only_en_us')

    args = parser.parse_args()

    LOG.setLevel(level=logging.DEBUG if args.log_debug else logging.INFO)

    tfc_dir = args.tfc_dir
    out_dir = args.out_dir
    use_mcmeta = args.use_mcmeta
    use_addons = args.use_addons

    os.makedirs(util.path_join(out_dir, '_images'), exist_ok=True)
    shutil.copy('style.css', '%s/style.css' % out_dir)
    shutil.copy('font.otf', '%s/font.otf' % out_dir)
    shutil.copy('assets/templates/redirect.html', '%s/index.html' % out_dir)
    for tex in os.listdir('assets/textures'):
        shutil.copy('assets/textures/%s' % tex, '%s/_images/%s' % (out_dir, tex))

    context = Context(tfc_dir, out_dir, use_mcmeta, use_addons, args.debug_i18n)

    if use_mcmeta:
        mcmeta.load_cache()
    
    if use_addons:
        for addon in versions.ADDONS:
            if not os.path.isdir('addons/%s-%s' % (addon.mod_id, addon.version)):
                LOG.info('Cloning %s/%s...' % (addon.user, addon.repo))
                os.makedirs('addons/%s-%s' % (addon.mod_id, addon.version), exist_ok=True)
                subprocess.call('git clone -b %s https://github.com/%s/%s addons/%s-%s' % (addon.version, addon.user, addon.repo, addon.mod_id, addon.version), shell=True)

    LOG.info('Generating docs...')
    LOG.debug('Running with:\n  tfc_dir = %s\n  out_dir = %s\n  langs = %s\n  version = %s' % (
        tfc_dir, out_dir, versions.LANGUAGES, versions.VERSION
    ))

    os.makedirs(os.path.join(out_dir, '_images'), exist_ok=True)

    for lang in versions.LANGUAGES:
        if args.debug_only_en_us and lang != 'en_us':
            LOG.debug('Skipping lang %s because --debug-only-en-us was present' % lang)
            continue
        LOG.info('Language: %s' % lang)
        parse_book(context.with_lang(lang), use_addons)
    
        context.sort()
        build_book_html(context)
    
    LOG.info('Done')
    LOG.info('  Recipes : %d passed / %d failed / %d skipped' % (context.recipes_passed, context.recipes_failed, context.recipes_skipped))
    LOG.info('  Items   : %d passed / %d failed' % (context.items_passed, context.items_failed))
    LOG.info('  Block   : %d passed / %d failed' % (context.blocks_passed, context.blocks_failed))
    LOG.info('  Total   : %d blocks / %d items / %d images' % (context.last_uid['block'], context.last_uid['item'], context.last_uid['image']))


def parse_book(context: Context, use_addons: bool):

    book_dir = util.path_join(context.tfc_dir, BOOK_DIR % 'tfc', context.lang)
    category_dir = util.path_join(book_dir, 'categories')

    for category_file in util.walk(category_dir):
        parse_category(context, category_dir, category_file)
    
    if use_addons:
        for addon in versions.ADDONS:
            addon_dir = util.path_join(addon.book_dir(), context.lang, 'categories')
            for category_file in util.walk(addon_dir):
                parse_category(context, addon_dir, category_file, is_addon=True)

    entry_dir = util.path_join(book_dir, 'entries')

    for entry_file in util.walk(entry_dir):
        parse_entry(context, entry_dir, entry_file)
    
    if use_addons:
        for addon in versions.ADDONS:
            addon_dir = util.path_join(addon.book_dir(), context.lang, 'entries')
            for entry_file in util.walk(addon_dir):
                parse_entry(context, addon_dir, entry_file)


def parse_category(context: Context, category_dir: str, category_file: str, is_addon: bool = False):
    category: Category = Category()
    category_id: str = os.path.relpath(category_file, category_dir)
    category_id = category_id[:category_id.index('.')]

    LOG.debug('Category: %s' % category_id)
    with open(category_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    context.format_text(desc := [], data, 'description')

    category.name = text_formatter.strip_vanilla_formatting(data['name'])
    category.description = ''.join(desc)
    category.sort = data['sortnum']

    if is_addon and not context.debug_i18n:
        category.name = context.translate(I18n.ADDON) % category.name
        category.sort += 10000  # Addons go LAST

    context.categories[category_id] = category


def parse_entry(context: Context, entry_dir: str, entry_file: str):
    entry: Entry = Entry()
    entry_id: str = os.path.relpath(entry_file, entry_dir)
    entry_id = entry_id[:entry_id.index('.')]

    LOG.debug('Entry: %s' % entry_id)
    with open(entry_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    category_id: str = data['category']
    category_id = category_id[category_id.index(':') + 1:]

    entry: Entry = Entry()
    entry_id: str = os.path.relpath(entry_file, entry_dir)
    entry_id = entry_id[:entry_id.index('.')]
    category_id: str = data['category']
    category_id = category_id[category_id.index(':') + 1:]

    entry.sort = data['sortnum'] if 'sortnum' in data else -1
    entry.name = text_formatter.strip_vanilla_formatting(data['name'])
    entry.id = entry_id
    entry.rel_id = os.path.relpath(entry_id, category_id)


    for page in data['pages']:
        try:
            parse_page(context, entry_id, entry.buffer, page)
        except InternalError as e:
            e.warning()

    context.add_entry(category_id, entry_id, entry)


def parse_page(context: Context, entry_id: str, buffer: List[str], data: Any):
    page_type = data['type']

    if 'anchor' in data:
        buffer.append('<a class="anchor" id="%s"></a>' % data['anchor'])

    if page_type == 'patchouli:text':
        context.format_title(buffer, data)
        context.format_text(buffer, data)
    elif page_type == 'patchouli:image':
        context.format_title(buffer, data)

        images = data['images']

        try:
            images = [(i, context.convert_image(i)) for i in images]
        except InternalError as e:
            e.prefix('Entry: \'%s\'' % entry_id).warning()
            images = []

        if len(images) == 1:
            image_text, image_src = images[0]
            buffer.append(IMAGE_SINGLE.format(
                src=image_src,
                text=image_text
            ))
        elif len(images) > 0:
            uid = context.next_id()
            parts = [IMAGE_MULTIPLE_PART.format(
                src=image_src,
                text=image_text,
                active='active' if i == 0 else ''
            ) for i, (image_text, image_src) in enumerate(images)]

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
        try:
            crafting_recipe.format_crafting_recipe(context, buffer, data['recipe'])
            context.recipes_passed += 1
        except InternalError as e:
            e.prefix('Recipe: \'%s\'' % data['recipe']).warning(True)

            # Fallback
            context.format_recipe(buffer, data)
            context.recipes_failed += 1
        
        try:
            if 'recipe2' in data:
                crafting_recipe.format_crafting_recipe(context, buffer, data['recipe2'])
                context.recipes_passed += 1
        except InternalError as e:
            e.prefix('Recipe: \'%s\'' % data['recipe2']).warning(True)

            # Fallback
            context.format_recipe(buffer, data, 'recipe2')
            context.recipes_failed += 1
        
        context.format_text(buffer, data)
    elif page_type == 'patchouli:spotlight':
        # Item Images
        try:
            item_src, item_name = item_loader.get_item_image(context, data['item'], False)
            context.format_title_with_icon(buffer, item_src, item_name, data)
            context.items_passed += 1
        except InternalError as e:
            e.warning()
            
            # Fallback
            context.format_title(buffer, data)
            item_str = item_loader.decode_item(data['item'])
            items = '%s: <code>%s</code>' % (
                context.translate(I18n.ITEMS) if ',' in item_str else context.translate(I18n.ITEM),
                '</code>, <code>'.join(item_str.split(','))
            )
            context.format_with_tooltip(buffer, items, context.translate(I18n.ITEM_ONLY_IN_GAME))
            context.items_failed += 1
        
        context.format_text(buffer, data)

    elif page_type == 'patchouli:entity':
        context.format_title(buffer, data, 'name')
        context.format_text(buffer, data)
    elif page_type == 'patchouli:empty':
        buffer.append('<hr>')
    elif page_type == 'patchouli:multiblock' or page_type == 'tfc:multimultiblock':
        context.format_title(buffer, data, 'name')
        
        try:
            src = block_loader.get_multi_block_image(context, data)
            buffer.append(IMAGE_SINGLE.format(
                src=src,
                text='Block Visualization'
            ))
            context.format_centered_text(buffer, data)
            context.blocks_passed += 1
        except InternalError as e:
            e.warning()

            # Fallback
            if 'multiblock_id' in data:
                context.format_with_tooltip(buffer, '%s: <code>%s</code>' % (
                    context.translate(I18n.MULTIBLOCK),
                    data['multiblock_id']
                ), context.translate(I18n.MULTIBLOCK_ONLY_IN_GAME))
            else:
                context.format_with_tooltip(buffer, context.translate(I18n.MULTIBLOCK), context.translate(I18n.MULTIBLOCK_ONLY_IN_GAME))
            context.format_text(buffer, data)
            context.blocks_failed += 1
    elif page_type in (
        'tfc:heat_recipe',
        'tfc:quern_recipe',
        'tfc:loom_recipe',
        'tfc:anvil_recipe',
    ):
        try:
            misc_recipe.format_misc_recipe(context, buffer, data['recipe'])
            context.recipes_passed += 1
        except InternalError as e:
            e.prefix('misc_recipe \'%s\'' % page_type).warning(True)

            # Fallback
            context.format_recipe(buffer, data)
            context.recipes_failed += 1
        
        context.format_text(buffer, data)
    elif page_type in (
        'tfc:welding_recipe',
        'tfc:instant_barrel_recipe',
        'tfc:sealed_barrel_recipe',
    ):
        context.format_recipe(buffer, data)
        context.format_text(buffer, data)
        context.recipes_skipped += 1
    elif page_type in (
        'tfc:clay_knapping_recipe',
        'tfc:fire_clay_knapping_recipe',
        'tfc:leather_knapping_recipe',
        'tfc:rock_knapping_recipe',
    ):
        try:
            recipe_id, image = knapping_recipe.format_knapping_recipe(context, data)
            buffer.append(IMAGE_SINGLE.format(
                src=image,
                text='Recipe: %s' % recipe_id
            ))
            context.recipes_passed += 1
        except InternalError as e:
            e.warning(True)
            context.format_recipe(buffer, data)
            context.recipes_failed += 1
        context.format_text(buffer, data)
    else:
        LOG.warning('Unrecognized page type: %s' % page_type)


# === Book HTML ===


def build_book_html(context: Context):
    
    # Main Page
    util.write_html(context.output_dir, 'index.html', html=TEMPLATE.format(
        title=context.translate(I18n.TITLE),
        text_index=context.translate(I18n.INDEX),
        text_contents=context.translate(I18n.CONTENTS),
        text_version=context.translate(I18n.VERSION),
        text_api_docs=context.translate(I18n.API_DOCS),
        text_github=context.translate(I18n.GITHUB),
        text_discord=context.translate(I18n.DISCORD),
        current_lang=context.translate(I18n.LANGUAGE_NAME % context.lang),
        langs='\n'.join([
            '<a href="../%s/" class="dropdown-item">%s</a>' % (l, context.translate(I18n.LANGUAGE_NAME % l)) for l in versions.LANGUAGES
        ]),
        index='#',
        style='../style.css',
        tfc_version=versions.VERSION,
        location='<a class="text-muted" href="#">%s</a>' % context.translate(I18n.INDEX),
        contents='\n'.join([
            '<li><a class="text-muted" href="./%s/">%s</a></li>' % (cat_id, cat.name)
            for cat_id, cat in context.sorted_categories
        ]),
        page_content="""
            <img class="d-block w-200 mx-auto img-fluid" src="../_images/splash.png" alt="TerraFirmaCraft Field Guide Splash Image">
            <p>{text_home}</p>
            <h4>{text_entries}</h4>
        """.format(
            text_home=context.translate(I18n.HOME),
            text_entries=context.translate(I18n.CATEGORIES)
        ) + '\n'.join(
            """
            <div class="card">
                <div class="card-header">
                    <a href="%s/index.html">%s</a>
                </div>
                <div class="card-body">
                    %s
                </div>
            </div>
            """ % (
                cat_id,
                cat.name,
                cat.description
            )
            for cat_id, cat in context.sorted_categories
        )
    ))

    # Category Pages
    for category_id, cat in context.sorted_categories:
        util.write_html(context.output_dir, category_id, 'index.html', html=TEMPLATE.format(
            title=context.translate(I18n.TITLE),
            text_index=context.translate(I18n.INDEX),
            text_contents=context.translate(I18n.CONTENTS),
            text_version=context.translate(I18n.VERSION),
            text_api_docs=context.translate(I18n.API_DOCS),
            text_github=context.translate(I18n.GITHUB),
            text_discord=context.translate(I18n.DISCORD),
            current_lang=context.translate(I18n.LANGUAGE_NAME % context.lang),
            langs='\n'.join([
                '<a href="../../%s/%s/" class="dropdown-item">%s</a>' % (l, category_id, context.translate(I18n.LANGUAGE_NAME % l)) for l in versions.LANGUAGES
            ]),
            index='../',
            style='../../style.css',
            tfc_version=versions.VERSION,
            location='<a class="text-muted" href="../">%s</a> / <a class="text-muted" href="#">%s</a>' % (
                context.translate(I18n.INDEX),
                cat.name
            ),
            contents='\n'.join([
                '<li><a class="text-muted" href="../%s/">%s</a></li>' % (cat_id, cat.name) + (
                    ''
                    if cat_id != category_id else
                    '<ul class="list-unstyled push-right">%s</ul>' % '\n'.join([
                        '<li><a class="text-muted" href="./%s.html">%s</a></li>' % (os.path.relpath(ent_id, cat_id), ent.name)
                        for ent_id, ent in cat.sorted_entries 
                    ])
                )
                for cat_id, cat in context.sorted_categories
            ]),
            page_content="""
                <h4>{category_name}</h4><p>{category_description}</p>
                <hr>
                <div class="card-columns">
                    {category_listing}
                </div>
            """.format(
                category_name=cat.name,
                category_description=cat.description,
                category_listing='\n'.join(
                    """
                    <div class="card">
                        <div class="card-header">
                            <a href="%s.html">%s</a>
                        </div>
                    </div>
                    """ % (entry.rel_id, entry.name)
                    for _, entry in cat.sorted_entries
                )
            )
        ))

         # Entry Pages
        for entry_id, entry in cat.sorted_entries:
            util.write_html(context.output_dir, entry_id + '.html', html=TEMPLATE.format(
                title=context.translate(I18n.TITLE),
                text_index=context.translate(I18n.INDEX),
                text_contents=context.translate(I18n.CONTENTS),
                text_version=context.translate(I18n.VERSION),
                text_api_docs=context.translate(I18n.API_DOCS),
                text_github=context.translate(I18n.GITHUB),
                text_discord=context.translate(I18n.DISCORD),
                current_lang=context.translate(I18n.LANGUAGE_NAME % context.lang),
                langs='\n'.join([
                    '<a href="../../%s/%s.html" class="dropdown-item">%s</a>' % (l, entry_id, context.translate(I18n.LANGUAGE_NAME % l)) for l in versions.LANGUAGES
                ]),
                index='../',
                style='../../style.css',
                tfc_version=versions.VERSION,
                location='<a class="text-muted" href="../">%s</a> / <a class="text-muted" href="./">%s</a> / <a class="text-muted" href="#">%s</a>' % (
                    context.translate(I18n.INDEX),
                    cat.name, 
                    entry.name
                ),
                contents='\n'.join([
                    '<li><a class="text-muted" href="../%s/">%s</a>' % (cat_id, cat.name) + (
                        '</li>'
                        if cat_id != category_id else
                        '<ul class="list-unstyled push-right">%s</ul>' % '\n'.join([
                            '<li><a class="text-muted" href="./%s.html">%s</a></li>' % (os.path.relpath(ent_id, cat_id), ent.name)
                            for ent_id, ent in cat.sorted_entries 
                        ]) + '</li>'
                    )
                    for cat_id, cat in context.sorted_categories
                ]),
                page_content="""
                <h4>{entry_name}</h4>
                <hr>
                {inner_content}
                """.format(
                    entry_name=entry.name,
                    inner_content=''.join(entry.buffer)
                )
            ))


IMAGE_SINGLE = """
<img class="d-block w-200 mx-auto img-fluid" src="{src}" alt="{text}">
"""

IMAGE_MULTIPLE_PART = """
<div class="carousel-item {active}">
    <img class="d-block w-200 mx-auto img-fluid" src="{src}" alt="{text}">
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
