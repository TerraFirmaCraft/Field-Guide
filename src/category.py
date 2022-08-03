from typing import List, Tuple
from entry import Entry


class Category:
    buffer: List[str]
    entries: List[str]
    sorted_entries: List[Tuple[str, Entry]]
    sort: int
    name: str
    description: str

    def __init__(self):
        self.buffer = []
        self.entries = []
        self.sorted_entries = []
        self.sort = -1
        self.name = ''
        self.description = ''
    
    def push(self, text: str):
        self.buffer.append(text)

    def __repr__(self) -> str: return str(self)
    def __str__(self) -> str: return self.name
