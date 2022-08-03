from typing import List


class Entry:
    buffer: List[str]
    sort: int
    name: str

    def __init__(self):
        self.buffer = []
        self.sort = -1
        self.name = ''
    
    def push(self, text: str):
        self.buffer.append(text)

    def __repr__(self) -> str: return str(self)
    def __str__(self) -> str: return self.name
