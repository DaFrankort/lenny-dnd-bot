import discord
from discord.app_commands import choices, describe

from commands.command import SimpleCommand
from embeds.charactergen import CharacterGenContainerView
from logic.charactergen import class_choices, generate_dnd_character, species_choices
from logic.dnd.name import Gender


class CharacterGenCommand(SimpleCommand):
    name = "charactergen"
    desc = "Generate a random D&D character!"
    help = "Generates a random D&D 5e character, using XPHB classes, species and backgrounds."

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
        self.log(itr)
        result = generate_dnd_character(gender, species, char_class)
        view = CharacterGenContainerView(result)
        await itr.response.send_message(view=view, file=view.chart)
