from typing import NamedTuple


class Addon(NamedTuple):
    user: str  # Username of a GitHub repository for the addon's source code
    repo: str  # Repository name
    version: str  # Addon version - this must be a tag, or commit hash (it will be passed to `git -b <version> clone`)
    mod_id: str  # Mod ID of the addon
    resource_path: str | list[str]  # Directory path or paths within the repository of a `resources` folder (where `data` and `assets` might be loaded from). If a list, the first path must contain patchouli pages

    def book_dir(self, resource_pack: bool) -> str:
        return 'addons/%s-%s/%s/%s/tfc/patchouli_books/field_guide/' % (
            self.mod_id,
            self.version,
            self.resource_paths()[0],
            ('assets' if resource_pack else 'data'),
        )
    
    def resource_paths(self) -> list[str]:
        return self.resource_path if type(self.resource_path) == list else [self.resource_path]


class OldVersion(NamedTuple):
    key: str  # The key in paths. Current version is /<lang>/... where old versions are /<key>/<lang>/...
    name: str  # A name displayed in the dropdown
    sneaky: bool  # If sneaky, only display when the URL contains ?test=true - this is for debug purposes in prod only


# 1.18.2 Versions
# 
# These are kept in case the old version ever needs to be regenerated
#
# VERSION = 'v2.2.30'
# MC_VERSION = '1.18.2'
# FORGE_VERSION = '40.1.73'
# LANGUAGES = ['en_us', 'ja_jp', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_hk', 'zh_tw']
#
# ADDONS = (
#     Addon('eerussianguy', 'firmalife', 'v1.2.12', 'firmalife', 'src/main/resources'),
#     Addon('gaelmare', 'waterflasks', '2.0.6', 'waterflasks', 'src/main/resources'),
#     Addon('gaelmare', 'tfcgyresorehints', '1.4', 'tfcgyres_orehints', 'src'),
#     Addon('HyperDashPony', 'FirmaCiv', '0.0.30-alpha-1.18.2', 'firmaciv', 'src/main/resources'),
# )
#
# 1.20.1 Versions
# 
# VERSION = 'v3.2.19'
# MC_VERSION = '1.20.1'
# FORGE_VERSION = '47.1.3'
# LANGUAGES = ('en_us', 'ja_jp', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_hk', 'zh_tw', 'ru_ru')

# ADDONS = (
#     Addon('eerussianguy', 'firmalife', 'v2.1.22', 'firmalife', 'src/main/resources'),
#     Addon('HyperDashPony', 'FirmaCiv', '0.2.5-alpha-1.20.1', 'firmaciv', 'src/main/resources'),
#     Addon('eerussianguy', 'beneath', 'v1.0', 'beneath', 'src/main/resources'),
#     Addon('MrHiTech123', 'Artisanal', '1.7.0', 'artisanal', 'src/main/resources'),
#     Addon('MrHiTech123', 'BetterStoneAge', '1.2.1', 'bsa', 'src/main/resources'),
#     Addon('Therighthon', 'ArborFirmaCraft', 'v1.0.13', 'afc', 'src/main/resources'),
#     Addon('Therighthon', 'RoadsAndRoofsTFC', 'v0.2.0', 'rnr', 'src/main/resources'),
#     Addon('redstoneguy10ls', 'lithiccoins', '1.1.1', 'lithiccoins', 'src/main/resources'),
#     Addon('redstoneguy10ls', 'lithicaddon', '1.3.6', 'lithicaddon', 'src/main/resources'),
# )


VERSION = 'v4.0.16-beta'
MC_VERSION = '1.21.1'
FORGE_VERSION = '21.1.197'
LANGUAGES = ('en_us', 'ja_jp', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_hk', 'zh_tw', 'ru_ru')

ADDONS = (
    Addon('eerussianguy', 'firmalife', 'v3.0.1', 'firmalife', ['src/main/resources', 'src/generated/resources']),
    Addon('Notenoughmail', 'precision-prospecting', 'v2.0', 'precisionprospecting', ['src/generated/resources', 'src/main/resources']),
)

OLD_VERSIONS = (
    OldVersion('18', '1.18.2 - v2.2.32', False),
    OldVersion('20', '1.20.1 - v3.2.19', False)
)

TFC_VERSION = '%s - %s' % (MC_VERSION, VERSION)

IS_RESOURCE_PACK = MC_VERSION != '1.18.2'

IS_PLURAL_REGISTRIES = MC_VERSION == '1.18.2' or MC_VERSION == '1.20.1'

def registry(path: str) -> str:
    if IS_PLURAL_REGISTRIES:
        return path + 's'
    else:
        return path

if __name__ == '__main__':
    print(VERSION)
