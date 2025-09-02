import random
import discord

from charts import get_radar_chart
from logic.app_commands import SimpleCommand
from dnd import Background, Class, DNDData, DNDObject, DNDTable, Gender, Species
from embeds import SimpleEmbed
from stats import Stats
from user_colors import UserColor

GenderChoices = [
    discord.app_commands.Choice(name="Female", value=Gender.FEMALE.value),
    discord.app_commands.Choice(name="Male", value=Gender.MALE.value),
    discord.app_commands.Choice(name="Other", value=Gender.OTHER.value),
]


class NameGenCommand(SimpleCommand):
    name = "namegen"
    desc = "Generate a random name depending on species and gender!"
    help = "Get a random name for a humanoid, species and gender can be specified but will default to random values."

    data: DNDData

    def __init__(self, data: DNDData):
        self.data = data
        super().__init__()

    async def species_autocomplete(self, _: discord.Interaction, current: str):
        species = self.data.names.get_species()
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
        name, new_species, new_gender = self.data.names.get_random(species, gender)

        if name is None:
            await itr.response.send_message(
                "❌ Can't generate names at this time ❌", ephemeral=True
            )
            return

        description = f"*{new_gender.value} {new_species}*".title()

        embed = SimpleEmbed(title=name, description=description)
        await itr.response.send_message(embed=embed)


class CharacterGenCommand(SimpleCommand):
    name = "charactergen"
    desc = "Generate a random D&D character!"
    help = "Generates a random D&D 5e character, using XPHB classes, species and backgrounds."

    def __init__(self):
        super().__init__()

    def _get_random_xphb_object(self, entries: list[DNDObject]) -> DNDObject:
        xphb_entries = [e for e in entries if e.source == "XPHB"]
        return random.choice(xphb_entries)

    def _get_dnd_table(self, table_name: str) -> DNDTable:
        table: DNDTable = None
        for t in self.data.tables.get(table_name):
            if t.name == table_name:
                table = t
                break

        if table is None:
            error_message = f"CharacterGen - Table {table_name} no longer exists in 5e.tools, charactergen will not work without it."
            raise ModuleNotFoundError(error_message)

        return table

    async def callback(self, itr: discord.Interaction):
        # TODO Move sections to private methods, for cleanup
        color = UserColor.get(itr)
        char_class: Class = self._get_random_xphb_object(self.data.classes.entries)
        species: Species = self._get_random_xphb_object(self.data.species.entries)
        full_name, _, _ = self.data.names.get_random(species.name, Gender.OTHER)

        # ===== BACKGROUND =====
        # To get an optimal background, we need to base ourselves off of the class' primary ability
        # We make use of the Choose a Background; table, this table shows which backgrounds would match well with your primary abilit(ies).
        # By gathering the recommended backgrounds for our class, we can easily select a random one from there.
        # NOTE: Only XPHB classes have primary abilities, so this will not work with older data than XPHB.
        background_table = self._get_dnd_table("Choose a Background; Ability Scores and Backgrounds")
        recommended_backgrounds: set[str] = set()  # Use a set to avoid duplicate backgrounds
        for row in background_table.table["value"]["rows"]:
            if row[0].lower() in char_class.primary_ability.lower():
                recommended_backgrounds.update(r.strip().lower() for r in row[1].split(','))

        backgrounds = [
            entry for entry in self.data.backgrounds.entries
            if entry.name.lower() in recommended_backgrounds
        ]
        background: Background = self._get_random_xphb_object(backgrounds)

        # ===== CHARACTER BACKSTORY =====
        # TODO Determine backstory?
        # --- Table: Class Training; I became...
        # --- Table: Background; I became...

        # ===== OPTIMAL CLASS STATS =====
        # We want to divide our rolled stats optimally, for this we use the Assign Ability Scores; table.
        # From there we look for the 'optimal' ability score array belonging to our class.
        # Then both stat rows are sorted from large to small, so that we can overwrite the 'optimal' stats with our actual rolled stats.
        # At the end we re-sort the list to be in the standard D&D order (Str, Dex, Con, Int, Wis, Cha)
        ability_table = self._get_dnd_table("Assign Ability Scores; Standard Array by Class")
        headers = ability_table.table["value"]["headers"][1:]  # skip "Class"
        optimal_stats = None
        for row in ability_table.table["value"]["rows"]:
            if row[0].lower() != char_class.name.lower():
                values = row[1:]
                optimal_stats = [(int(val), stat) for stat, val in zip(headers, values)]
                optimal_stats.sort(key=lambda x: x[0], reverse=True)
                break

        if optimal_stats is None:
            error_message = f"CharacterGen - Class '{char_class.name}' does not exist in Standard Array table!"
            raise ModuleNotFoundError(error_message)

        stats = Stats()
        rolled_stats = [val for val, _ in stats.stats]
        rolled_stats.sort(reverse=True)

        character_stats: list[tuple[int, str]] = [
            (rolled_stats[i], stat_name)
            for i, (_, stat_name) in enumerate(optimal_stats)
        ]
        character_stats.sort(key=lambda x: headers.index(x[1]))  # Put back in standard stat-order
        chart_image = get_radar_chart(results=character_stats, color=color)

        # TODO Apply background's ability score boosts
        # --- Prioritize stats related to the class
        # --- Keep stats as even as possible => uneven does not give bonus on modifiers

        # ===== SEND RESULT =====
        description = f"*{species.name} - {char_class.name} - {background.name}*"
        embed = SimpleEmbed(title=full_name, description=description)
        embed.set_image(url=f"attachment://{chart_image.filename}")
        await itr.response.send_message(embed=embed, file=chart_image)
