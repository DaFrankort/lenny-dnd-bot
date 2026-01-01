from typing import Any

from logic.dnd.abstract import DNDEntryType, Description, DNDEntry, DNDEntryList


class Vehicle(DNDEntry):
    token_url: str | None
    creature_capacity: str | None
    cargo_capacity: str | None
    travel_pace: str | None
    description: list[Description]

    def __init__(self, obj: dict[str, Any]):
        self.entry_type = DNDEntryType.VEHICLE

        self.name = obj["name"]
        self.source = obj["source"]
        self.url = obj["url"]

        self.token_url = obj["tokenUrl"]
        self.creature_capacity = obj["creatureCapacity"]
        self.cargo_capacity = obj["cargoCapacity"]
        self.travel_pace = obj["travelPace"]
        self.description = obj["description"]

        self.select_description = obj["subtitle"]


class VehicleList(DNDEntryList[Vehicle]):
    type = Vehicle
    paths = ["vehicles.json"]
