from embeds.dnd.abstract import DNDEntryEmbed
from logic.dnd.background import Background


class BackgroundEmbed(DNDEntryEmbed):
    def __init__(self, background: Background):
        super().__init__(background)

        abilities = ", ".join(background.abilities) or "-"
        feat = background.feat or "-"
        skills = background.skills or "-"
        tools = background.tools or "-"
        languages = background.languages or "-"
        prerequisite = background.prerequisite or "-"

        self.add_field(name="Abilities", value=abilities, inline=True)
        self.add_field(name="Feat", value=feat, inline=True)
        self.add_field(name="Skill Proficiencies", value=skills, inline=True)
        self.add_field(name="Tool Proficiencies", value=tools, inline=True)
        self.add_field(name="Languages", value=languages, inline=True)
        self.add_field(name="Prerequisite", value=prerequisite, inline=True)

        if background.equipment:
            self.add_separator_field()
            self.add_field(name="Equipment", value=background.equipment, inline=False)

        if background.description:
            self.add_separator_field()
            self.add_description_fields(background.description)
