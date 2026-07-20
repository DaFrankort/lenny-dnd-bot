from typing import Any, Literal

from methods import ChoicedEnum, read_json_file


class ContentChoice(ChoicedEnum):
    ALL = "all"
    OFFICIAL = "official"
    PARTNERED = "partnered"


class Source:
    """Note: this object does not inherit from DNDEntry as it is meta data about DNDEntries"""

    name: str
    abbreviation: str
    source: str
    published: str | None
    category: Literal["core", "supplemental", "core-supplemental", "adventure", "partnered"]
    legacy: bool

    def __init__(self, source: dict[str, Any]):
        self.name = source["name"]
        self.abbreviation = source["abbreviation"]
        self.source = source["source"]
        self.published = source["published"]
        self.category = source["category"]
        self.legacy = source["legacy"]


class GlobalSourceList:
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
            data = read_json_file(path)
            self.entries.extend([Source(e) for e in data])

    def contains(self, source: str) -> bool:
        return source in self.source_ids

    @property
    def source_ids(self) -> set[str]:
        return set(entry.source for entry in self.entries)

    def get(self, source_id: str) -> Source:
        for source in self.entries:
            if source.source == source_id:
                return source
        raise KeyError(f"Could not find source by id '{source_id}'")

    def get_from_abbreviation(self, abbreviation: str) -> Source:
        abbreviation = abbreviation.lower()
        for source in self.entries:
            if source.abbreviation.lower() == abbreviation:
                return source
        raise KeyError(f"Could not find source by abbreviation '{abbreviation}'")


SourceList = GlobalSourceList()
