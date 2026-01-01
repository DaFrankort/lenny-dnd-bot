from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.boon import Boon


class BoonEmbed(DNDEntryEmbed):
    def __init__(self, boon: Boon):
        super().__init__(boon)

        self.add_field(name="", value=f"*{boon.type} boon*", inline=False)

        if boon.description:
            self.add_description_fields(boon.description)

        if boon.signature_spells:
            self.add_field(name="Spells", value=boon.signature_spells, inline=False)
