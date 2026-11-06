import discord
from discord.app_commands import choices, describe

from commands.command import BaseCommand
from embeds.charactergen import CharacterGenContainerView
from logic.charactergen import class_choices, generate_dnd_character, species_choices
from logic.csheet import generate_character_sheet
from logic.dnd.name import Gender


class CharacterGenCommand(BaseCommand):
    name = "charactergen"
    desc = "Generate a random Lvl. 1 D&D character!"
    help = "Generates a random Level 1 D&D 5e character, for inspiration or quick-start purposes. Limited to strictly XPHB classes, species, and backgrounds.\nIf XGE life-data is available for your class or background, random life-inspiration will be provided too."

    @choices(gender=Gender.choices(), species=species_choices(), char_class=class_choices())
    @describe(
        gender="The gender your random character should have. Random by default.",
        species="The race your random character should have. Random by default.",
        char_class="The class your random character should have. Random by default.",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        gender: str | None = None,
        species: str | None = None,
        char_class: str | None = None,
    ):
        result = generate_dnd_character(gender, species, char_class)
        sheet = generate_character_sheet(result)
        view = CharacterGenContainerView(result, sheet)
        await itr.response.send_message(view=view, files=[view.chart, view.sheet])
