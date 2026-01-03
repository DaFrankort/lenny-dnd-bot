import discord
from discord.app_commands import autocomplete, choices, describe

from commands.command import BaseCommand
from embeds.embed import BaseEmbed
from logic.color import UserColor
from logic.dnd.data import Data
from logic.dnd.name import Gender
from logic.namegen import generate_name


async def species_autocomplete(_: discord.Interaction, current: str):
    species = Data.names.get_species()
    filtered_species = [spec.title() for spec in species if current.lower() in spec.lower()]
    return [discord.app_commands.Choice(name=spec, value=spec) for spec in filtered_species[:25]]


class NameGenCommand(BaseCommand):
    name = "namegen"
    desc = "Generate a random name depending on species and gender!"
    help = "Get a random name for a humanoid, species and gender can be specified but will default to random values."

    @choices(gender=Gender.choices())
    @autocomplete(species=species_autocomplete)
    @describe(
        species="Request a name from a specific species, selects random species by default.",
        gender="Request name from a specific gender, selects random gender by default.",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        species: str | None = None,
        gender: str = Gender.OTHER.value,
    ):
        self.log(itr)
        result = generate_name(species, gender)

        desc = f"*{result.gender} {result.species}*".title()
        color = UserColor.generate(result.name)

        embed = BaseEmbed(title=result.name, description=desc, color=discord.Color(color))
        await itr.response.send_message(embed=embed)
