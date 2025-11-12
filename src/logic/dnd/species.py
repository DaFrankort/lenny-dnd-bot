from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Species(DNDEntry):
    image: str | None
    sizes: list[str]
    speed: list[str]
    type: str | None

    description: list[Description]
    info: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "species"
        self.emoji = "🧝"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.image = json["image"]
        self.sizes = json["sizes"]
        self.speed = json["speed"]
        self.type = json["creatureType"]

        self.description = json["description"]
        self.info = json["info"]


class SpeciesList(DNDEntryList[Species]):
    type = Species
    paths = ["species.json"]
