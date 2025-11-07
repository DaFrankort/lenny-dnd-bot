from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Spell(DNDEntry):
    """A class representing a Dungeons & Dragons spell."""

    level: str
    school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    description: list[Description]
    classes: list

    def __init__(self, json: dict):
        self.entry_type = "spell"
        self.emoji = "🔥"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.level = json["level"]
        self.school = json["school"]
        self.casting_time = json["casting_time"]
        self.spell_range = json["range"]
        self.components = json["components"]
        self.duration = json["duration"]
        self.description = json["description"]
        self.classes = json["classes"]

        self.select_description = f"{self.level} {self.school}"

    def __str__(self):
        return f"{self.name} ({self.source})"

    def __repr__(self):
        return str(self)

    def get_formatted_classes(self, allowed_sources: set[str]):
        classes = set()
        for class_ in self.classes:
            if class_["source"] not in allowed_sources:
                continue
            classes.add(class_["name"])
        return ", ".join(sorted(list(classes)))

    @property
    def level_school(self) -> str:
        return f"{self.level} {self.school}"


class SpellList(DNDEntryList[Spell]):
    path = "./submodules/lenny-dnd-data/generated/spells.json"

    def __init__(self):
        super().__init__()
        data = self.read_dnd_data_contents(self.path)
        for spell in data:
            self.entries.append(Spell(spell))
