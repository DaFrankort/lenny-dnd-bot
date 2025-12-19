from typing import Any

from logic.dnd.abstract import DNDEntryList
from methods import ChoicedEnum


class ContentChoice(ChoicedEnum):
    ALL = "all"
    OFFICIAL = "official"
    PARTNERED = "partnered"


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
    path_official = "./submodules/lenny-dnd-data/generated/official/sources.json"
    path_partnered = "./submodules/lenny-dnd-data/generated/partnered/sources.json"
    entries: list[Source]

    @property
    def paths(self) -> list[str]:
        return [self.path_official, self.path_partnered]

    def __init__(self, content: ContentChoice = ContentChoice.ALL):
        self.entries = []
        paths: list[str] = []
        match content:
            case ContentChoice.ALL:
                paths = self.paths
            case ContentChoice.OFFICIAL:
                paths = [self.path_official]
            case ContentChoice.PARTNERED:
                paths = [self.path_partnered]

        for path in paths:
            data = DNDEntryList.read_dnd_data_contents(path)
            self.entries.extend([Source(e) for e in data])

    def contains(self, source: str) -> bool:
        return any([entry.id == source for entry in self.entries])

    @property
    def source_ids(self) -> set[str]:
        return set([entry.id for entry in self.entries])
