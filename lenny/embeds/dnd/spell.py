import discord

from embeds.dnd.abstract import HORIZONTAL_LINE, DNDEntryEmbed
from logic.config import Config
from logic.dnd.spell import Spell


class SpellEmbed(DNDEntryEmbed):
    """A class representing a Discord embed for a Dungeons & Dragons spell."""

    def __init__(self, itr: discord.Interaction, spell: Spell):
        sources = Config.allowed_sources(guild=itr.guild)
        classes = spell.get_formatted_classes(sources)

        super().__init__(spell)

        two_fields_per_line = len(spell.casting_time) > 20

        self._set_embed_color(spell)
        self.add_field(name="Type", value=spell.level_school, inline=True)
        self.add_field(name="Casting Time", value=spell.casting_time, inline=True)
        if two_fields_per_line:
            self.add_field(name="", value="")
        self.add_field(name="Range", value=spell.spell_range, inline=True)
        self.add_field(name="Components", value=spell.components, inline=True)
        if two_fields_per_line:
            self.add_field(name="", value="")
        self.add_field(name="Duration", value=spell.duration, inline=True)
        self.add_field(name="Classes", value=classes, inline=True)
        if two_fields_per_line:
            self.add_field(name="", value="")

        if len(spell.description) > 0:
            # Add horizontal line
            self.add_field(
                name="",
                value=HORIZONTAL_LINE,
                inline=False,
            )
            self.add_description_fields(spell.description)

    def _set_embed_color(self, spell: Spell):
        school_colors = {
            "abjuration": discord.Colour.from_rgb(0, 185, 33),
            "conjuration": discord.Colour.from_rgb(189, 0, 68),
            "divination": discord.Colour.from_rgb(0, 173, 179),
            "enchantment": discord.Colour.from_rgb(179, 0, 131),
            "evocation": discord.Colour.from_rgb(172, 1, 9),
            "illusion": discord.Colour.from_rgb(14, 109, 174),
            "necromancy": discord.Colour.from_rgb(108, 24, 141),
            "transmutation": discord.Colour.from_rgb(204, 190, 0),
        }

        school = spell.school.lower()
        self.color = school_colors.get(school, discord.Colour.green())
