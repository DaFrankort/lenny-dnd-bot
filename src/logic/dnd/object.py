from logic.dnd.abstract import DNDEntry, DNDEntryList, Description


class DNDObject(DNDEntry):
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


class DNDObjectList(DNDEntryList[DNDObject]):
    path = "./submodules/lenny-dnd-data/generated/objects.json"

    def __init__(self):
        super().__init__()
        for obj in self.read_dnd_data_contents(self.path):
            self.entries.append(DNDObject(obj))
