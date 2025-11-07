from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Hazard(DNDEntry):
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "hazard"
        self.emoji = "🪤"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["subtitle"]

        self.description = json["description"]


class HazardList(DNDEntryList[Hazard]):
    paths = [
        "./submodules/lenny-dnd-data/generated/traps.json",
        "./submodules/lenny-dnd-data/generated/hazards.json",
    ]

    def __init__(self):
        super().__init__()
        for path in self.paths:
            data = self.read_dnd_data_contents(path)
            for hazard in data:
                self.entries.append(Hazard(hazard))
