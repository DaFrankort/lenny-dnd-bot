from logic.dnd.abstract import DNDObject, DNDObjectList, DNDObjectTypes, Description


class Item(DNDObject):
    value: str | None
    weight: str | None
    type: list[str]
    properties: list[str]
    description: list[Description]

    def __init__(self, json: any):
        self.object_type = DNDObjectTypes.ITEM.value

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]
        self.value = json["value"]
        self.weight = json["weight"]
        self.type = json["type"]
        self.properties = json["properties"]
        self.description = json["description"]

    @property
    def formatted_value_weight(self) -> str | None:
        value_weight = []
        if self.value is not None:
            value_weight.append(self.value)
        if self.weight is not None:
            value_weight.append(self.weight)

        if len(value_weight) == 0:
            return None
        return ", ".join(value_weight)

    @property
    def formatted_type(self) -> str | None:
        if len(self.type) == 0:
            return None
        return ", ".join(self.type).capitalize()

    @property
    def formatted_properties(self) -> str | None:
        if len(self.properties) == 0:
            return None
        return ", ".join(self.properties).capitalize()


class ItemList(DNDObjectList):
    path = "./submodules/lenny-dnd-data/generated/items.json"

    def __init__(self):
        super().__init__(DNDObjectTypes.ITEM.value)
        data = self.read_dnd_data_contents(self.path)
        for item in data:
            self.entries.append(Item(item))
