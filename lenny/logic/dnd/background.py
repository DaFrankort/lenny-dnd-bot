from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Background(DNDEntry):
    abilities: list[str]
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "background"
        self.emoji = "📕"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.abilities = json["abilities"] or []
        self.description = json["description"]


class BackgroundList(DNDEntryList[Background]):
    type = Background
    paths = ["backgrounds.json"]
