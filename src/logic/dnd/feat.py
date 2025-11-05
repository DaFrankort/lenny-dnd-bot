from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Feat(DNDEntry):
    prerequisite: str | None
    ability_increase: str | None
    description: list[Description]

    def __init__(self, json: dict):
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
    paths = [
        "./submodules/lenny-dnd-data/generated/feats.json",
        "./submodules/lenny-dnd-data/generated/classfeats.json",
    ]

    def __init__(self):
        super().__init__()
        for path in self.paths:
            for feat in self.read_dnd_data_contents(path):
                self.entries.append(Feat(feat))
