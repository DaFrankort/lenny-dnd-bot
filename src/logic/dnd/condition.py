from logic.dnd.abstract import DNDObject, DNDObjectList, Description


class Condition(DNDObject):
    description: list[Description]
    image: str | None

    def __init__(self, json: any):
        self.object_type = "condition"
        self.emoji = "💀"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.description = json["description"]
        self.image = json["image"]


class ConditionList(DNDObjectList):
    paths = [
        "./submodules/lenny-dnd-data/generated/conditions.json",
        "./submodules/lenny-dnd-data/generated/diseases.json",
    ]

    def __init__(self):
        super().__init__()
        for path in self.paths:
            data = self.read_dnd_data_contents(path)
            for condition in data:
                self.entries.append(Condition(condition))
