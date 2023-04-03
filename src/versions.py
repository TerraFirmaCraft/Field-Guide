from typing import NamedTuple

class Addon(NamedTuple):
    user: str
    repo: str
    version: str
    mod_id: str

VERSION = 'v2.2.15'
MC_VERSION = '1.18.2'
FORGE_VERSION = '40.1.73'
LANGUAGES = ['en_us', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_tw']

ADDONS = [
    Addon('eerussianguy', 'firmalife', 'v1.2.8', 'firmalife'),
]


if __name__ == '__main__':
    print(VERSION)
