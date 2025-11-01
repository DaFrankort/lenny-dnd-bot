import discord

from embed import SimpleEmbed
from command import SimpleCommand
from logic.dnd.data import Data
from logic.dnd.name import Gender
from logic.namegen import generate_name
from discord.app_commands import describe, choices, autocomplete


async def species_autocomplete(_: discord.Interaction, current: str):
    species = Data.names.get_species()
    filtered_species = [spec.title() for spec in species if current.lower() in spec.lower()]
    return [discord.app_commands.Choice(name=spec, value=spec) for spec in filtered_species[:25]]


class NameGenCommand(SimpleCommand):
    name = "namegen"
    desc = "Generate a random name depending on species and gender!"
    help = "Get a random name for a humanoid, species and gender can be specified but will default to random values."

    @choices(gender=Gender.choices())
    @autocomplete(species=species_autocomplete)
    @describe(
        species="Request a name from a specific species, selects random species by default.",
        gender="Request name from a specific gender, selects random gender by default.",
    )
    async def callback(
        self,
        itr: discord.Interaction,
        species: str | None = None,
        gender: str = Gender.OTHER.value,
    ):
        self.log(itr)
        result = generate_name(species, gender)
        embed = SimpleEmbed(title=result.name, description=result.desc, color=discord.Color(result.color))
        await itr.response.send_message(embed=embed)
