from typing import NamedTuple

class Addon(NamedTuple):
    user: str  # Username of a GitHub repository for the addon's source code
    repo: str  # Repository name
    version: str  # Addon version - this must be a tag, or commit hash (it will be passed to `git -b <version> clone`)
    mod_id: str  # Mod ID of the addon
    resource_path: str  # Directory path within the repository of a `resources` folder (where `data` and `assets` might be loaded from)

    def book_dir(self) -> str:
        return 'addons/%s-%s/%s/data/%s/patchouli_books/field_guide/' % (self.mod_id, self.version, self.resource_path, self.mod_id)

VERSION = 'v2.2.17'
MC_VERSION = '1.18.2'
FORGE_VERSION = '40.1.73'
LANGUAGES = ['en_us', 'pt_br', 'ko_kr', 'uk_ua', 'zh_cn', 'zh_hk', 'zh_tw']

ADDONS = [
    Addon('eerussianguy', 'firmalife', 'v1.2.9', 'firmalife', 'src/main/resources'),
    Addon('gaelmare', 'waterflasks', '2.0.6', 'waterflasks', 'src/main/resources'),
    Addon('gaelmare', 'tfcgyresorehints', '1.4', 'tfcgyres_orehints', 'src'),
]


if __name__ == '__main__':
    print(VERSION)
