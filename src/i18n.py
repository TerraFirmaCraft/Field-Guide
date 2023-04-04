

def key(text: str) -> str:
    return 'field_guide.' + text


class I18n:
    TITLE = key('title')
    INDEX = key('index')
    CONTENTS = key('contents')
    VERSION = key('version')
    API_DOCS = key('api_docs')
    GITHUB = key('github')
    DISCORD = key('discord')
    CATEGORIES = key('categories')
    HOME = key('home')
    MULTIBLOCK = key('multiblock')
    MULTIBLOCK_ONLY_IN_GAME = key('multiblock_only_in_game')
    RECIPE = key('recipe')
    RECIPE_ONLY_IN_GAME = key('recipe_only_in_game')
    ITEM = key('item')
    ITEMS = key('items')
    ITEM_ONLY_IN_GAME = key('item_only_in_game')
    ADDON = key('addon')
    TICKS = key('ticks')

    KEY_INVENTORY = key('key.inventory')
    KEY_ATTACK = key('key.attack')
    KEY_USE = key('key.use')
    KEY_DROP = key('key.drop')
    KEY_SNEAK = key('key.sneak')
    KEY_CYCLE_CHISEL_MODE = key('tfc.key.cycle_chisel_mode')
    KEY_PLACE_BLOCK = key('tfc.key.place_block')

    KEYS = (KEY_INVENTORY, KEY_ATTACK, KEY_USE, KEY_DROP, KEY_SNEAK, KEY_CYCLE_CHISEL_MODE, KEY_PLACE_BLOCK)

    LANGUAGE_NAME = key('language.%s')
