from typing import Any

from logic.dnd.abstract import Description, DNDEntry, DNDEntryList


class Vehicle(DNDEntry):
    token_url: str | None
    creature_capacity: str | None
    cargo_capacity: str | None
    travel_pace: str | None
    description: list[Description]

    def __init__(self, json: dict[str, Any]):
        self.entry_type = "vehicle"
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


class VehicleList(DNDEntryList[Vehicle]):
    type = Vehicle
    paths = ["vehicles.json"]
