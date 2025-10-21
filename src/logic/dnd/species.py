from logic.dnd.abstract import DNDObject, DNDObjectList, DNDObjectTypes, Description


class Species(DNDObject):
    image: str | None
    sizes: list[str]
    speed: list[str]
    type: str | None

    description: list[Description]
    info: list[Description]

    def __init__(self, json: any):
        self.object_type = DNDObjectTypes.SPECIES.value

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.image = json["image"]
        self.sizes = json["sizes"]
        self.speed = json["speed"]
        self.type = json["creatureType"]

        self.description = json["description"]
        self.info = json["info"]


class SpeciesList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/species.json"

    def __init__(self):
        super().__init__(DNDObjectTypes.SPECIES.value)
        for species in self.read_dnd_data_contents(self.path):
            self.entries.append(Species(species))
