from logic.dnd.abstract import DNDObject, DNDObjectList, Description


class Object(DNDObject):
    description: list[Description]
    token_url: str

    def __init__(self, json: dict):
        self.object_type = "object"
        self.emoji = "🪨"

        self.name = json["name"]
        self.source = json["source"]
        self.select_description = json["subtitle"]
        self.url = json["url"]
        self.token_url = json["tokenUrl"]

        self.description = json["description"]


class ObjectList(DNDObjectList[Object]):
    path = "./submodules/lenny-dnd-data/generated/objects.json"

    def __init__(self):
        super().__init__()
        for obj in self.read_dnd_data_contents(self.path):
            self.entries.append(Object(obj))
