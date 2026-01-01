from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.cults import Cult


class CultEmbed(DNDEntryEmbed):
    def __init__(self, cult: Cult):
        super().__init__(cult)

        self.add_field(name="", value=f"*{cult.type} cult*", inline=False)

        if cult.description:
            self.add_description_fields(cult.description)

        if cult.goal:
            self.add_field(name="Goal", value=cult.goal, inline=False)
        if cult.cultists:
            self.add_field(name="Cultists", value=cult.cultists, inline=False)
        if cult.signature_spells:
            self.add_field(name="Spells", value=cult.signature_spells, inline=False)
