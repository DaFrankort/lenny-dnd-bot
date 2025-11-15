from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Background(DNDEntry):
    abilities: list[str]
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "background"
        self.emoji = "📕"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.abilities = obj["abilities"] or []
        self.description = obj["description"]


class BackgroundList(DNDEntryList[Background]):
    type = Background
    paths = ["backgrounds.json"]
