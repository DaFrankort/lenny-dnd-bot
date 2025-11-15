from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Spell(DNDEntry):
    """A class representing a Dungeons & Dragons spell."""

    level: str
    school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    description: list[Description]
    classes: list[Any]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = "spell"
        self.emoji = "🔥"

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.level = obj["level"]
        self.school = obj["school"]
        self.casting_time = obj["casting_time"]
        self.spell_range = obj["range"]
        self.components = obj["components"]
        self.duration = obj["duration"]
        self.description = obj["description"]
        self.classes = obj["classes"]

        self.select_description = f"{self.level} {self.school}"

    def __str__(self):
        return f"{self.name} ({self.source})"

    def __repr__(self):
        return str(self)

    def get_formatted_classes(self, allowed_sources: set[str]):
        classes: set[str] = set()
        for class_ in self.classes:
            if class_["source"] not in allowed_sources:
                continue
            classes.add(class_["name"])
        return ", ".join(sorted(list(classes)))

    @property
    def level_school(self) -> str:
        return f"{self.level} {self.school}"


class SpellList(DNDEntryList[Spell]):
    type = Spell
    paths = ["spells.json"]
