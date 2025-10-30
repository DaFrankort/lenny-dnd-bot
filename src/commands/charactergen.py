import discord
from embeds.charactergen import CharacterGenContainerView
from command import SimpleCommand
from logic.charactergen import class_choices, generate_dnd_character, species_choices
from logic.dnd.name import Gender


class CharacterGenCommand(SimpleCommand):
    name = "charactergen"
    desc = "Generate a random D&D character!"
    help = "Generates a random D&D 5e character, using XPHB classes, species and backgrounds."

    @discord.app_commands.choices(gender=Gender.choices(), species=species_choices(), char_class=class_choices())
    async def callback(self, itr: discord.Interaction, gender: str = None, species: str = None, char_class: str = None):
        self.log(itr)
        result = generate_dnd_character(gender, species, char_class)
        view = CharacterGenContainerView(result)
        await itr.response.send_message(view=view, file=view.chart)
