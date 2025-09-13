import discord
from embeds.charactergen import CharacterGenContainerView
from logic.app_commands import SimpleCommand
from logic.charactergen import generate_dnd_character


class CharacterGenCommand(SimpleCommand):
    name = "charactergen"
    desc = "Generate a random D&D character!"
    help = "Generates a random D&D 5e character, using XPHB classes, species and backgrounds."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        result = generate_dnd_character(itr)
        view = CharacterGenContainerView(result)
        await itr.response.send_message(view=view, file=view.chart)
