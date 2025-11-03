from embeds.dnd.abstract import DNDObjectEmbed
from logic.dnd.vehicle import Vehicle


class VehicleEmbed(DNDObjectEmbed):
    def __init__(self, vehicle: Vehicle):
        super().__init__(vehicle)
        self.description = f"*{vehicle.select_description}*"

        if vehicle.token_url:
            self.set_thumbnail(url=vehicle.token_url)

        if vehicle.creature_capacity:
            self.add_field(name="Creature Capacity", value=vehicle.creature_capacity)
        if vehicle.cargo_capacity:
            self.add_field(name="Cargo Capacity", value=vehicle.cargo_capacity)
        if vehicle.travel_pace:
            self.add_field(name="Travel Pace", value=vehicle.travel_pace)

        if vehicle.description:
            self.add_description_fields(vehicle.description, ignore_tables=True, MAX_FIELDS=3)
