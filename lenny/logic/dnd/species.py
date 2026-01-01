from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Species(DNDEntry):
    image: str | None
    sizes: list[str]
    speed: list[str]
    type: str | None

    description: list[Description]
    info: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.SPECIES

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.image = obj["image"]
        self.sizes = obj["sizes"]
        self.speed = obj["speed"]
        self.type = obj["creatureType"]

        self.description = obj["description"]
        self.info = obj["info"]


class SpeciesList(DNDEntryList[Species]):
    type = Species
    paths = ["species.json"]
