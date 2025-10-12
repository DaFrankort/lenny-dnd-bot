import discord

from embed import SimpleEmbed
from logic.app_commands import SimpleCommand
from logic.dnd.data import Data
from logic.dnd.name import Gender
from logic.namegen import generate_name


class NameGenCommand(SimpleCommand):
    name = "namegen"
    desc = "Generate a random name depending on species and gender!"
    help = "Get a random name for a humanoid, species and gender can be specified but will default to random values."

    async def species_autocomplete(self, _: discord.Interaction, current: str):
        species = Data.names.get_species()
        filtered_species = [spec.title() for spec in species if current.lower() in spec.lower()]
        return [discord.app_commands.Choice(name=spec, value=spec) for spec in filtered_species[:25]]

    @discord.app_commands.describe(
        species="Request a name from a specific species, selects random species by default.",
        gender="Request name from a specific gender, selects random gender by default.",
    )
    @discord.app_commands.choices(gender=Gender.choices())
    @discord.app_commands.autocomplete(species=species_autocomplete)
    async def callback(
        self,
        itr: discord.Interaction,
        species: str = None,
        gender: str = Gender.OTHER.value,
    ):
        self.log(itr)
        result = generate_name(species, gender)
        embed = SimpleEmbed(title=result.name, description=result.desc, color=result.color)
        await itr.response.send_message(embed=embed)
