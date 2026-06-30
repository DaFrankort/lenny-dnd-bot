from dataclasses import dataclass
from typing import Any

from logic.app_emojis import AppEmoji
from logic.dnd.abstract import (
    Description,
    DNDEntry,
    DNDEntryList,
    DNDEntryType,
    ProficiencyOptions,
)


@dataclass
class ClassStartingProficiencies:
    armor: list[str]
    tools: list[str]
    weapons: list[str]
    skills: ProficiencyOptions
    saving: list[str]

    @classmethod
    def from_data(cls, obj: dict[str, Any]) -> "ClassStartingProficiencies | None":
        proficiencies = obj.get("startingProficiencies", None)
        if proficiencies is None:
            return None

        skills = proficiencies["skills"]
        return cls(
            armor=proficiencies["armor"],
            tools=proficiencies["tools"],
            weapons=proficiencies["weapons"],
            skills=ProficiencyOptions(options=skills["options"], amount=skills["amount"]),
            saving=proficiencies["saving"],
        )


class Class(DNDEntry):
    subclass_unlock_level: int | None
    primary_ability: str | None
    spellcast_ability: str | None
    start_prof: ClassStartingProficiencies | None  # Sidekicks do not have this data.
    hp: int | None  # The start HP for and the sides for the HP-die. For Sidekicks, this value is None.
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
        self.start_prof = ClassStartingProficiencies.from_data(obj)
        self.hp = obj["hp"]
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

    @property
    def class_emoji(self) -> str:
        key = "class_" + self.name.lower()
        try:
            return AppEmoji(key).emoji
        except ValueError:
            return ""


class ClassList(DNDEntryList[Class]):
    type = Class
    paths = ["classes.json"]
