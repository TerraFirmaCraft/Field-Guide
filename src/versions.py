from typing import NamedTuple

class Addon(NamedTuple):
    user: str  # Username of a GitHub repository for the addon's source code
    repo: str  # Repository name
    version: str  # Addon version - this must be a tag, or commit hash (it will be passed to `git -b <version> clone`)
    mod_id: str  # Mod ID of the addon

VERSION = 'v2.2.15'
MC_VERSION = '1.18.2'
FORGE_VERSION = '40.1.73'
LANGUAGES = ['en_us', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_tw']

ADDONS = [
    Addon('eerussianguy', 'firmalife', 'v1.2.8', 'firmalife'),
]


if __name__ == '__main__':
    print(VERSION)
