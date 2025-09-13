import random
import discord

from embeds.charactergen import CharacterGenContainerView
from logic.app_commands import SimpleCommand, send_error_message
from dnd import Background, Class, Data, DNDObject, DNDTable, Gender, Species
from embed import SimpleEmbed
from logic.charactergen import generate_dnd_character
from stats import Stats

GenderChoices = [
    discord.app_commands.Choice(name="Female", value=Gender.FEMALE.value),
    discord.app_commands.Choice(name="Male", value=Gender.MALE.value),
    discord.app_commands.Choice(name="Other", value=Gender.OTHER.value),
]


class NameGenCommand(SimpleCommand):
    name = "namegen"
    desc = "Generate a random name depending on species and gender!"
    help = "Get a random name for a humanoid, species and gender can be specified but will default to random values."

    async def species_autocomplete(self, _: discord.Interaction, current: str):
        species = Data.names.get_species()
        filtered_species = [
            spec.title() for spec in species if current.lower() in spec.lower()
        ]
        return [
            discord.app_commands.Choice(name=spec, value=spec)
            for spec in filtered_species[:25]
        ]

    @discord.app_commands.describe(
        species="Request a name from a specific species, selects random species by default.",
        gender="Request name from a specific gender, selects random gender by default.",
    )
    @discord.app_commands.choices(gender=GenderChoices)
    @discord.app_commands.autocomplete(species=species_autocomplete)
    async def callback(
        self,
        itr: discord.Interaction,
        species: str = None,
        gender: str = Gender.OTHER.value,
    ):
        self.log(itr)
        gender = Gender(gender)
        name, new_species, new_gender = Data.names.get_random(species, gender)

        if name is None:
            await send_error_message(itr, "Can't generate names at this time")
            return

        description = f"*{new_gender.value} {new_species}*".title()

        embed = SimpleEmbed(title=name, description=description)
        await itr.response.send_message(embed=embed)


class CharacterGenCommand(SimpleCommand):
    name = "charactergen"
    desc = "Generate a random D&D character!"
    help = "Generates a random D&D 5e character, using XPHB classes, species and backgrounds."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        result = generate_dnd_character(itr)
        view = CharacterGenContainerView(result)
        await itr.response.send_message(view=view, file=view.chart)
