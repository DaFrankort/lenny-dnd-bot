from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList, DNDEntryType


class Skill(DNDEntry):
    ability: str
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.SKILL

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = None
        self.ability = obj["ability"]

        self.description = obj["description"]


class SkillList(DNDEntryList[Skill]):
    type = Skill
    paths = ["skills.json"]

    def get_abilities(self) -> list[str]:
        abilities: set[str] = set()
        for skill in self.entries:
            abilities.add(skill.ability)
        abilities.add("Constitution")  # Constitution has no associated skills.
        return list(abilities)
