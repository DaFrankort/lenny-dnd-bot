from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class Species(DNDEntry):
    image: str | None
    sizes: list[str]
    speed: list[str]
    type: str | None

    description: list[Description]
    info: list[Description]

    def __init__(self, json: dict):
        self.entry_type = "species"
        self.emoji = "🧝"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.image = json["image"]
        self.sizes = json["sizes"]
        self.speed = json["speed"]
        self.type = json["creatureType"]

        self.description = json["description"]
        self.info = json["info"]


class SpeciesList(DNDEntryList[Species]):
    path = "./submodules/lenny-dnd-data/generated/species.json"

    def __init__(self):
        super().__init__()
        for species in self.read_dnd_data_contents(self.path):
            self.entries.append(Species(species))
