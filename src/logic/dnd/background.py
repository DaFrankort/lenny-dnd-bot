from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


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
    path = "./submodules/lenny-dnd-data/generated/backgrounds.json"

    def __init__(self):
        super().__init__()
        for background in self.read_dnd_data_contents(self.path):
            self.entries.append(Background(background))
