from typing import NamedTuple


class Addon(NamedTuple):
    user: str  # Username of a GitHub repository for the addon's source code
    repo: str  # Repository name
    version: str  # Addon version - this must be a tag, or commit hash (it will be passed to `git -b <version> clone`)
    mod_id: str  # Mod ID of the addon
    resource_path: str  # Directory path within the repository of a `resources` folder (where `data` and `assets` might be loaded from)

    def book_dir(self, resource_pack: bool) -> str:
        return 'addons/%s-%s/%s/%s/tfc/patchouli_books/field_guide/' % (
            self.mod_id,
            self.version,
            self.resource_path,
            ('assets' if resource_pack else 'data'),
        )


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


VERSION = 'v3.2.0'
MC_VERSION = '1.20.1'
FORGE_VERSION = '47.1.3'
LANGUAGES = ('en_us', 'ja_jp', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_hk', 'zh_tw', 'ru_ru')

ADDONS = (
    Addon('eerussianguy', 'firmalife', 'v2.1.8', 'firmalife', 'src/main/resources'),
    Addon('HyperDashPony', 'FirmaCiv', '0.2.5-alpha-1.20.1', 'firmaciv', 'src/main/resources'),
    Addon('eerussianguy', 'beneath', 'v1.0', 'beneath', 'src/main/resources'),
    Addon('MrHiTech123', 'Artisanal', 'v1.0', 'artisanal', 'src/main/resources'),
)

OLD_VERSIONS = (
    OldVersion('18', '1.18.2 - v2.2.32', False),
)

TFC_VERSION = '%s - %s' % (MC_VERSION, VERSION)


if __name__ == '__main__':
    print(VERSION)
