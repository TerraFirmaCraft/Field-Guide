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
from components import item_loader, block_loader, crafting_recipe, knapping_recipe, misc_recipe, mcmeta, text_formatter, barrel_recipe, table_formatter


TEMPLATE = util.load_html('default')


def main():
    # Arguments
    parser = ArgumentParser('TFC Field Guide')
    parser.add_argument('--tfc-dir', type=str, dest='tfc_dir', default='../TerraFirmaCraft', help='The source TFC directory')
    parser.add_argument('--out-dir', type=str, dest='out_dir', default='out', help='The output directory')
    parser.add_argument('--root-dir', type=str, dest='root_dir', default='', help='The root directory to fetch static assets from')

    # Version handling
    parser.add_argument('--old-version-key', type=str, dest='old_version_key', default=None, help='If present, the key of the old version to generate')
    parser.add_argument('--copy-existing-versions', action='store_true', dest='copy_existing_versions', default=False, help='If present, this will copy existing old versions from /assets/versions/ into the root output directory')
    parser.add_argument('--resource-pack-book', action='store_true', dest='resource_pack_book', default=False, help='If the book is stored as a resource pack (core content in /assets/) vs. not (core content in /data/)')

    # External resources
    parser.add_argument('--use-mcmeta', action='store_true', dest='use_mcmeta', help='Download Minecraft and Forge source')
    parser.add_argument('--use-addons', action='store_true', dest='use_addons', help='Download addons directly from source')

    # Debug options
    parser.add_argument('--debug', action='store_true', dest='log_debug', help='Enable debug logging')
    parser.add_argument('--debug-i18n', action='store_true', dest='debug_i18n', help='Replace all translated text with translation keys')
    parser.add_argument('--debug-only-en-us', action='store_true', dest='debug_only_en_us', help='Only generate en_us (faster)')

    args = parser.parse_args()

    LOG.setLevel(level=logging.DEBUG if args.log_debug else logging.INFO)

    tfc_dir = args.tfc_dir
    out_dir = args.out_dir
    use_mcmeta = args.use_mcmeta
    use_addons = args.use_addons
    old_version: bool = args.old_version_key is not None

    if old_version:  # If present, output everything to a subdir
        out_dir = os.path.join(out_dir, args.old_version_key)

    # Images, local to each version
    os.makedirs(util.path_join(out_dir, '_images'), exist_ok=True)

    for tex in os.listdir('assets/textures'):
        shutil.copy('assets/textures/%s' % tex, '%s/_images/%s' % (out_dir, tex))

    if not old_version:  # Top level (not old versions)
        shutil.copytree('assets/static', '%s/static' % out_dir, dirs_exist_ok=True)

        # Write metadata.js
        with open(os.path.join(out_dir, 'static', 'metadata.js'), 'w', encoding='utf-8') as f:
            f.write('window._VERSIONS = [\n')
            f.write('    ["%s - %s", null, false],\n' % (versions.MC_VERSION, versions.VERSION))
            for old in versions.OLD_VERSIONS:
                f.write('    ["%s", "%s", %s],\n' % (old.name, old.key, 'true' if old.sneaky else 'false'))
            f.write('];')

    # Always copy the redirect, which defaults to en_us/
    shutil.copy('assets/templates/redirect.html', '%s/index.html' % out_dir)

    # Just copy old versions that exist in the directory
    if args.copy_existing_versions and os.path.isdir('assets/versions'):
        for old in os.listdir('assets/versions'):
            shutil.copytree('assets/versions/%s' % old, '%s/%s' % (out_dir, old), dirs_exist_ok=True)

    root_dir = args.root_dir

    if args.root_dir != '' and not root_dir.startswith('/'):
        root_dir = '/' + root_dir

    LOG.info('Setting root output dir to "%s"' % root_dir)

    context = Context(tfc_dir, out_dir, root_dir, use_mcmeta, use_addons, args.debug_i18n, args.resource_pack_book)

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
    category_dir = context.resource_dir('categories')

    for category_file in util.walk(category_dir):
        parse_category(context, category_dir, category_file)

    if use_addons:
        for addon in versions.ADDONS:
            addon_dir = util.path_join(addon.book_dir(context.resource_pack), context.lang, 'categories')
            for category_file in util.walk(addon_dir):
                parse_category(context, addon_dir, category_file, is_addon=True)

    entry_dir = context.resource_dir('entries')

    for entry_file in util.walk(entry_dir):
        parse_entry(context, entry_dir, entry_file)

    if use_addons:
        for addon in versions.ADDONS:
            addon_dir = util.path_join(addon.book_dir(context.resource_pack), context.lang, 'entries')
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

    entry.sort = data['sortnum'] if 'sortnum' in data else -1
    entry.name = text_formatter.strip_vanilla_formatting(data['name'])
    entry.id = entry_id
    entry.rel_id = os.path.relpath(entry_id, category_id)

    try:
        item_src, item_name = item_loader.get_item_image(context, data['icon'], False)
        entry.icon = item_src
        entry.icon_name = item_name
    except InternalError as e:
        e.prefix('Entry: %s' % entry).warning(False)

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
                count=i,
                count_human_readable=i+1
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
            if 'recipe' in data:
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
            if isinstance(data['item'], str):
                item_src, item_name = item_loader.get_item_image(context, data['item'], False)
                context.format_title_with_icon(buffer, item_src, item_name, data)
                context.items_passed += 1
            elif 'tag' in data['item']:
                item_src, item_name = item_loader.get_item_image(context, '#' + data['item']['tag'], False)
                context.format_title_with_icon(buffer, item_src, item_name, data)
                context.items_passed += 1
            else:
                util.error('Spotlight page did not have an item or tag key: %s' % data)
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
        'tfc:glassworking_recipe',
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
        'tfc:instant_barrel_recipe',
        'tfc:sealed_barrel_recipe'
    ):
        try:
            barrel_recipe.format_barrel_recipe(context, buffer, data['recipe'])
            context.recipes_passed += 1
        except InternalError as e:
            e.prefix('barrel recipe \'%s\'' % page_type).warning(True)
            context.format_recipe(buffer, data)
            context.recipes_failed += 1
    elif page_type in (
        'tfc:welding_recipe',
    ):
        context.format_recipe(buffer, data)
        context.format_text(buffer, data)
        context.recipes_skipped += 1
    elif page_type in (
        # In 1.18
        'tfc:clay_knapping_recipe',
        'tfc:fire_clay_knapping_recipe',
        'tfc:leather_knapping_recipe',
        'tfc:rock_knapping_recipe',
        # In 1.20
        'tfc:knapping_recipe'
    ):
        try:
            recipe_id, image = knapping_recipe.format_knapping_recipe(context, data)
            buffer.append(IMAGE_KNAPPING.format(
                src=image,
                text='Recipe: %s' % recipe_id
            ))
            context.recipes_passed += 1
        except InternalError as e:
            e.warning(True)
            context.format_recipe(buffer, data)
            context.recipes_failed += 1
        context.format_text(buffer, data)
    elif page_type == 'tfc:table':
        try:
            table_formatter.format_table(context, buffer, data)
        except InternalError as e:
            e.warning(True)
    else:
        LOG.warning('Unrecognized page type: %s' % page_type)


# === Book HTML ===


def build_book_html(context: Context):

    # Main Page
    util.write_html(context.output_dir, 'index.html', html=TEMPLATE.format(
        title=context.translate(I18n.TITLE),
        long_title=context.translate(I18n.TITLE),
        short_description=context.translate(I18n.HOME),
        preview_image=get_splash_location(),
        text_index=context.translate(I18n.INDEX),
        text_contents=context.translate(I18n.CONTENTS),
        text_version=context.translate(I18n.VERSION),
        text_api_docs=context.translate(I18n.API_DOCS),
        text_github=context.translate(I18n.GITHUB),
        text_discord=context.translate(I18n.DISCORD),
        current_lang_key=context.lang,
        current_lang=context.translate(I18n.LANGUAGE_NAME % context.lang),
        langs='\n'.join([
            '<a href="../%s/" class="dropdown-item">%s</a>' % (l, context.translate(I18n.LANGUAGE_NAME % l)) for l in versions.LANGUAGES
        ]),
        index='#',
        root=context.root_dir,
        tfc_version=versions.TFC_VERSION,
        location=index_breadcrumb(None),
        contents='\n'.join([
            '<li><a href="./%s/">%s</a></li>' % (cat_id, cat.name)
            for cat_id, cat in context.sorted_categories
        ]),
        page_content="""
            <img class="d-block w-200 mx-auto mb-3 img-fluid" src="../_images/{splash_image}.png" alt="TerraFirmaCraft Field Guide Splash Image">
            <p>{text_home}</p>
            <p><strong>{text_entries}</strong></p>
            <div class="row row-cols-1 row-cols-md-2 g-3">
        """.format(
            text_home=context.translate(I18n.HOME),
            text_entries=context.translate(I18n.CATEGORIES),
            splash_image=get_splash_location()
        ) + '\n'.join(
            """
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        <a href="%s/index.html">%s</a>
                    </div>
                    <div class="card-body">%s</div>
                </div>
            </div>
            """ % (
                cat_id,
                cat.name,
                cat.description
            )
            for cat_id, cat in context.sorted_categories
        ) + '</div>'
    ))

    # Category Pages
    for category_id, cat in context.sorted_categories:
        util.write_html(context.output_dir, category_id, 'index.html', html=TEMPLATE.format(
            title=context.translate(I18n.TITLE),
            long_title=cat.name + " | " + context.translate(I18n.TITLE),
            short_description=cat.name,
            preview_image=get_splash_location(),
            text_index=context.translate(I18n.INDEX),
            text_contents=context.translate(I18n.CONTENTS),
            text_version=context.translate(I18n.VERSION),
            text_api_docs=context.translate(I18n.API_DOCS),
            text_github=context.translate(I18n.GITHUB),
            text_discord=context.translate(I18n.DISCORD),
            current_lang_key=context.lang,
            current_lang=context.translate(I18n.LANGUAGE_NAME % context.lang),
            langs='\n'.join([
                '<a href="../../%s/%s/" class="dropdown-item">%s</a>' % (l, category_id, context.translate(I18n.LANGUAGE_NAME % l)) for l in versions.LANGUAGES
            ]),
            index='../',
            root=context.root_dir,
            tfc_version=versions.TFC_VERSION,
            location="""
                {index_breadcrumb}
                <li class="breadcrumb-item active" aria-current="page">{category_name}</li>
            """.format(
                index_breadcrumb=index_breadcrumb('../'),
                category_name=cat.name
            ),
            contents='\n'.join([
                '<li><a href="../%s/">%s</a>' % (cat_id, cat.name) + (
                    ''
                    if cat_id != category_id else
                    '<ul>%s</ul>' % '\n'.join([
                        '<li><a href="./%s.html">%s</a></li>' % (os.path.relpath(ent_id, cat_id), ent.name)
                        for ent_id, ent in cat.sorted_entries
                    ])
                ) + '</li>'
                for cat_id, cat in context.sorted_categories
            ]),
            page_content="""
                <h1 class="mb-4">{category_name}</h1>
                <p>{category_description}</p>
                <div class="row row-cols-1 row-cols-md-3 g-3">
                    {category_listing}
                </div>
            """.format(
                category_name=cat.name,
                category_description=cat.description,
                category_listing='\n'.join(
                    """
                    <div class="col">
                        <div class="card">%s</div>
                    </div>
                    """ % entry_card_with_default_icon(entry.rel_id, entry.name, entry.icon, entry.icon_name)
                    for _, entry in cat.sorted_entries
                )
            )
        ))

         # Entry Pages
        for entry_id, entry in cat.sorted_entries:
            util.write_html(context.output_dir, entry_id + '.html', html=TEMPLATE.format(
                title=context.translate(I18n.TITLE),
                long_title=entry.name + " | " + cat.name + " | " + context.translate(I18n.TITLE),
                short_description=entry.name,
                preview_image=entry.icon,
                text_index=context.translate(I18n.INDEX),
                text_contents=context.translate(I18n.CONTENTS),
                text_version=context.translate(I18n.VERSION),
                text_api_docs=context.translate(I18n.API_DOCS),
                text_github=context.translate(I18n.GITHUB),
                text_discord=context.translate(I18n.DISCORD),
                current_lang_key=context.lang,
                current_lang=context.translate(I18n.LANGUAGE_NAME % context.lang),
                langs='\n'.join([
                    '<a href="../../%s/%s.html" class="dropdown-item">%s</a>' % (l, entry_id, context.translate(I18n.LANGUAGE_NAME % l)) for l in versions.LANGUAGES
                ]),
                index='../',
                root=context.root_dir,
                tfc_version=versions.TFC_VERSION,
                location="""
                    {index_breadcrumb}
                    <li class="breadcrumb-item"><a href="./">{category_name}</a></li>
                    <li class="breadcrumb-item active" aria-current="page">{entry_name}</li>
                """.format(
                    index_breadcrumb=index_breadcrumb('../'),
                    category_name=cat.name,
                    entry_name=entry.name
                ),
                contents='\n'.join([
                    '<li><a href="../%s/">%s</a>' % (cat_id, cat.name) + (
                        '</li>'
                        if cat_id != category_id else
                        '<ul>%s</ul>' % '\n'.join([
                            '<li><a href="./%s.html">%s</a></li>' % (os.path.relpath(ent_id, cat_id), ent.name)
                            for ent_id, ent in cat.sorted_entries
                        ]) + '</li>'
                    )
                    for cat_id, cat in context.sorted_categories
                ]),
                page_content="""
                <h1 class="d-flex align-items-center mb-4">{entry_name}</h1>
                {inner_content}
                """.format(
                    entry_name=title_with_optional_icon(entry.name, entry.icon, entry.icon_name),
                    inner_content=''.join(entry.buffer)
                )
            ))

def title_with_optional_icon(text: str, icon_src: str, icon_title: str) -> str:
    if icon_src:
        return """
        <img class="icon-title me-3" src="{icon_src}" alt="{text}" title="{icon_title}" /><span>{text}</span>
        """.format(
            icon_title=icon_title,
            icon_src=icon_src,
            text=text
        )
    else:
        return text

def get_splash_location():
    return 'splash' if versions.MC_VERSION != '1.20.1' else 'splash_120'

def entry_card_with_default_icon(entry_page: str, entry_title: str, icon_src: str, icon_title: str) -> str:
    if not icon_src:
        icon_src = util.path_join('..', '..', '_images', 'placeholder_16.png')

    return """
    <div class="card-body">
        <div class="d-flex align-items-center">
            <img class="entry-card-icon me-2" src="{icon_src}" alt="{entry_title}" />
            <a href="{entry_page}.html">{entry_title}</a>
        </div>
    </div>
    """.format(
        icon_title=icon_title,
        icon_src=icon_src,
        entry_title=entry_title,
        entry_page=entry_page
    )

def index_breadcrumb(relative_path: str|None) -> str:
    icon_html = '<i class="bi bi-house-fill"></i>'
    if not relative_path:
        return f'<li class="breadcrumb-item">{icon_html}</li>'
    else:
        return f"""
            <li class="breadcrumb-item">
                <a href="{relative_path}">{icon_html}</a>
            </li>
        """

IMAGE_SINGLE = """
<img class="d-block w-200 mx-auto img-fluid" src="{src}" alt="{text}">
"""

IMAGE_KNAPPING = """
<div class="d-flex align-items-center justify-content-center">
    <div class="knapping-recipe">
        <img class="knapping-recipe-img" src="../../_images/knapping.png">
        <div class="knapping-recipe-overlay">
            <img class="knapping-recipe-img" src="{src}" alt="{text}">
        </div>
    </div>
</div>
"""

IMAGE_MULTIPLE_PART = """
<div class="carousel-item {active}">
    <img class="d-block w-200 mx-auto img-fluid" src="{src}" alt="{text}">
</div>
"""

IMAGE_MULTIPLE_SEQ = """
<button type="button" data-bs-target="#{id}" data-bs-slide-to="{count}" aria-label="Slide {count_human_readable}"></button>
"""

IMAGE_MULTIPLE = """
<div id="{id}" class="carousel slide" data-bs-ride="carousel">
    <div class="carousel-indicators">
        <button type="button" data-bs-target="#{id}" data-bs-slide-to="0" class="active" aria-current="true" aria-label="Slide 1"></button>
        {seq}
    </div>
    <div class="carousel-inner">
        {parts}
    </div>
    <button type="button" class="carousel-control-prev" data-bs-target="#{id}" data-bs-slide="prev">
        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Previous</span>
    </button>
    <button type="button" class="carousel-control-next" data-bs-target="#{id}" data-bs-slide="next">
        <span class="carousel-control-next-icon" aria-hidden="true"></span>
        <span class="visually-hidden">Next</span>
    </button>
</div>
"""

if __name__ == '__main__':
    main()
