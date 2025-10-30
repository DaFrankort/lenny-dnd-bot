from logic.dnd.abstract import DNDObject, DNDObjectList, Description


class Background(DNDObject):
    abilities: list[str]
    description: list[Description]

    def __init__(self, json: dict):
        self.object_type = "background"
        self.emoji = "📕"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.abilities = json["abilities"] or []
        self.description = json["description"]


class BackgroundList(DNDObjectList[Background]):
    path = "./submodules/lenny-dnd-data/generated/backgrounds.json"

    def __init__(self):
        super().__init__()
        for background in self.read_dnd_data_contents(self.path):
            self.entries.append(Background(background))
