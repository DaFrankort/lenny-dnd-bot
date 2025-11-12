from typing import Any
from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Feat(DNDEntry):
    prerequisite: str | None
    ability_increase: str | None
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "feat"
        self.emoji = "🎖️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["type"]

        self.prerequisite = json["prerequisite"]
        self.ability_increase = json["abilityIncrease"]
        self.description = json["description"]


class FeatList(DNDEntryList[Feat]):
    type = Feat
    paths = ["feats.json", "classfeats.json"]
