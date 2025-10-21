from logic.dnd.abstract import DNDObject, DNDObjectList, DNDObjectTypes, Description


class Background(DNDObject):
    abilities: list[str] | None
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = DNDObjectTypes.BACKGROUND.value

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.abilities = json["abilities"]
        self.description = json["description"]


class BackgroundList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/backgrounds.json"

    def __init__(self):
        super().__init__(DNDObjectTypes.BACKGROUND.value)
        for background in self.read_dnd_data_contents(self.path):
            self.entries.append(Background(background))
