from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Feat(DNDEntry):
    prerequisite: str | None
    ability_increase: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "feat"
        self.emoji = "🎖️"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]
        self.select_description = obj["type"]

        self.prerequisite = obj["prerequisite"]
        self.ability_increase = obj["abilityIncrease"]
        self.description = obj["description"]


class FeatList(DNDEntryList[Feat]):
    type = Feat
    paths = ["feats.json", "classfeats.json"]
