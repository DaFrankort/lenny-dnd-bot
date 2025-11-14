from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


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
    type = Hazard
    paths = ["traps.json", "hazards.json"]
