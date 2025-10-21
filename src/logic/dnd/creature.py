from logic.dnd.abstract import DNDObject, DNDObjectList, DNDObjectTypes, Description


class Creature(DNDObject):
    subtitle: str | None
    summoned_by_spell: str | None
    token_url: str | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = DNDObjectTypes.CREATURE.value

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.subtitle = json["subtitle"]
        self.summoned_by_spell = json["summonedBySpell"]
        self.token_url = json["tokenUrl"]
        self.description = json["description"]

        self.select_description = self.subtitle


class CreatureList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/creatures.json"

    def __init__(self):
        super().__init__(DNDObjectTypes.CREATURE.value)
        for creature in self.read_dnd_data_contents(self.path):
            self.entries.append(Creature(creature))
