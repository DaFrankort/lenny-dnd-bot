from embeds.dnd.abstract import HORIZONTAL_LINE, DNDEntryEmbed
from logic.dnd.species import Species


class SpeciesEmbed(DNDEntryEmbed):
    def __init__(self, species: Species):
        super().__init__(species)

        if species.type:
            self.add_field(name="Creature Type", value=species.type, inline=True)
        if species.sizes:
            self.add_field(name="Size", value=" or ".join(species.sizes), inline=True)
        if species.speed:
            self.add_field(name="Speed", value=", ".join(species.speed), inline=True)
        if species.description:
            self.add_description_fields(species.description)

        if species.info:
            self.add_field(name="", value=HORIZONTAL_LINE)
            self.add_description_fields(species.info)
