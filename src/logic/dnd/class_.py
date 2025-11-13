from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Class(DNDEntry):
    subclass_unlock_level: int | None
    primary_ability: str | None
    spellcast_ability: str | None
    base_info: list[Description]
    level_resources: dict[str, list[Description]]
    level_features: dict[str, list[Description]]
    subclass_level_features: dict[str, dict[str, list[Description]]]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "class"
        self.emoji = "🧙‍♂️"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subclass_unlock_level = json["subclassUnlockLevel"]
        self.primary_ability = json["primaryAbility"]
        self.spellcast_ability = json["spellcastAbility"]
        self.base_info = json["baseInfo"]
        self.level_resources = json["levelResources"]
        self.level_features = json["levelFeatures"]
        self.subclass_level_features = json["subclassLevelFeatures"]

    def __repr__(self):
        return str(self)


class ClassList(DNDEntryList[Class]):
    type = Class
    paths = ["classes.json"]
