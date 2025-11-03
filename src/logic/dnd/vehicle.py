from logic.dnd.abstract import DNDObject, DNDObjectList, Description


class Vehicle(DNDObject):
    token_url: str | None
    creature_capacity: str | None
    cargo_capacity: str | None
    travel_pace: str | None
    description: list[Description]

    def __init__(self, json: dict):
        self.object_type = "vehicle"
        self.emoji = "⛵"

        self.name = json["name"]
        self.source = json["source"]
        self.url = json["url"]

        self.token_url = json["tokenUrl"]
        self.creature_capacity = json["creatureCapacity"]
        self.cargo_capacity = json["cargoCapacity"]
        self.travel_pace = json["travelPace"]
        self.description = json["description"]

        self.select_description = json["subtitle"]


class VehicleList(DNDObjectList[Vehicle]):
    path = "./submodules/lenny-dnd-data/generated/vehicles.json"

    def __init__(self):
        super().__init__()
        for vehicle in self.read_dnd_data_contents(self.path):
            self.entries.append(Vehicle(vehicle))
