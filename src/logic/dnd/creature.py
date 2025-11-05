from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Creature(DNDEntry):
    subtitle: str | None
    summoned_by_spell: str | None
    token_url: str | None
    description: list[Description]

    def __init__(self, json: dict):
        self.object_type = "creature"
        self.emoji = "🐉"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subtitle = json["subtitle"]
        self.summoned_by_spell = json["summonedBySpell"]
        self.token_url = json["tokenUrl"]
        self.description = json["description"]

        self.select_description = self.subtitle


class CreatureList(DNDEntryList[Creature]):
    path = "./submodules/lenny-dnd-data/generated/creatures.json"

    def __init__(self):
        super().__init__()
        for creature in self.read_dnd_data_contents(self.path):
            self.entries.append(Creature(creature))
