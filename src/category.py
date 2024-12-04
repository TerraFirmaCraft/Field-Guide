from typing import List, Tuple
from entry import Entry


class Category:
    entries: List[str]
    sorted_entries: List[Tuple[str, Entry]]
    sort: int
    name: str
    description: str
    is_addon: bool

    def __init__(self):
        self.entries = []
        self.sorted_entries = []
        self.sort = -1
        self.name = ''
        self.description = ''
        self.is_addon = False

    def __repr__(self) -> str: return str(self)
    def __str__(self) -> str: return self.name
