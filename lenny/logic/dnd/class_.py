from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Class(DNDEntry):
    subclass_unlock_level: int | None
    primary_ability: str | None
    spellcast_ability: str | None
    base_info: list[Description]
    level_resources: dict[str, list[Description]]
    level_features: dict[str, list[Description]]
    subclass_level_features: dict[str, dict[str, list[Description]]]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.CLASS

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.subclass_unlock_level = obj["subclassUnlockLevel"]
        self.primary_ability = obj["primaryAbility"]
        self.spellcast_ability = obj["spellcastAbility"]
        self.base_info = obj["baseInfo"]
        self.level_resources = obj["levelResources"]
        self.level_features = obj["levelFeatures"]
        self.subclass_level_features = obj["subclassLevelFeatures"]

    def __repr__(self):
        return str(self)

    def has_subclass(self, subclass: str) -> bool:
        subclasses = set(sub.lower().strip() for sub in self.subclasses)
        subclass = subclass.lower().strip()
        return subclass in subclasses

    @property
    def subclasses(self) -> set[str]:
        return set(self.subclass_level_features.keys())


class ClassList(DNDEntryList[Class]):
    type = Class
    paths = ["classes.json"]
