from logic.dnd.abstract import DNDObject, DNDObjectList, Description


class Action(DNDObject):
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = "action"
        self.emoji = "🏃"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.select_description = json["time"]

        self.description = json["description"]


class ActionList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/actions.json"

    def __init__(self):
        super().__init__()
        for action in self.read_dnd_data_contents(self.path):
            self.entries.append(Action(action))
