from typing import Any

from logic.dnd.abstract import DNDEntryList


class Source:
    """Note: this object does not inherit from DNDEntry as it is meta data about DNDEntries"""

    id: str
    name: str
    source: str
    published: str
    author: str | None
    group: str

    def __init__(self, source: dict[str, Any]):
        self.id = source["id"]
        self.name = source["name"]
        self.source = source["source"]
        self.published = source["published"]
        self.author = source["author"]
        self.group = source["group"]


class SourceList:
    paths = ["./submodules/lenny-dnd-data/generated/sources.json"]
    entries: list[Source]

    def __init__(self):
        self.entries = []
        for path in self.paths:
            data = DNDEntryList.read_dnd_data_contents(path)
            self.entries.extend([Source(e) for e in data])
