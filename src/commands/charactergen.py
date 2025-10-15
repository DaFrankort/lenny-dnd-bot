import discord
from embeds.charactergen import CharacterGenContainerView
from logic.app_commands import SimpleCommand
from logic.charactergen import generate_dnd_character
from logic.dnd.data import Data
from logic.dnd.name import Gender


def species_choices():
    species = [e.name for e in Data.species.entries if (e.source == "XPHB" and "(" not in e.name)]
    print(species)
    return [discord.app_commands.Choice(name=spec, value=spec) for spec in species[:25]]


def class_choices():
    classes = [e.name for e in Data.classes.entries if e.source == "XPHB"]
    return [discord.app_commands.Choice(name=char_cls, value=char_cls) for char_cls in classes[:25]]


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
