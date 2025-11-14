from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.hazard import Hazard


class HazardEmbed(DNDEntryEmbed):
    def __init__(self, hazard: Hazard):
        super().__init__(hazard)
        self.description = f"*{hazard.select_description}*"
        self.add_description_fields(hazard.description)
