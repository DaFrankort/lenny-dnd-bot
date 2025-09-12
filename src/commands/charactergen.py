import random
import discord

from charts import get_radar_chart
from logic.app_commands import SimpleCommand
from dnd import Background, Class, Data, DNDObject, DNDTable, Gender, Species
from embeds import SimpleEmbed
from methods import build_table_from_rows, when
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

    def _get_random_xphb_object(self, entries: list[DNDObject]) -> DNDObject:
        xphb_entries = [e for e in entries if e.source == "XPHB" and "(" not in e.name]
        return random.choice(xphb_entries)

    def _get_dnd_table(self, table_name: str, source: str = "XPHB") -> DNDTable:
        table: DNDTable = None
        for t in Data.tables.get(query=table_name, allowed_sources=set([source])):
            if t.name == table_name:
                table = t
                break
        if table is None:
            raise f"CharacterGen - Table '{table_name}' no longer exists in 5e.tools, charactergen will not work without it."
        return table

    def get_optimal_background(self, char_class: Class) -> Background:
        # To get an optimal background, we need to base ourselves off of the class' primary ability
        # We make use of the Choose a Background; table, this table shows which backgrounds would match well with your primary abilit(ies).
        # NOTE: Only XPHB classes have primary abilities, so this will not work with older data than XPHB.

        table_name = "Choose a Background; Ability Scores and Backgrounds"
        background_table = self._get_dnd_table(table_name)
        recommended_backgrounds: set[str] = set()
        for row in background_table.table["value"]["rows"]:
            if row[0].lower() in char_class.primary_ability.lower():
                recommended_backgrounds.update(
                    r.strip().lower() for r in row[1].split(",")
                )

        backgrounds = [
            entry
            for entry in Data.backgrounds.entries
            if entry.name.lower() in recommended_backgrounds
        ]
        background: Background = self._get_random_xphb_object(backgrounds)
        return background

    def get_optimal_stats(
        self, itr: discord.Interaction, char_class: Class
    ) -> list[tuple[int, str]]:
        # We want to divide our rolled stats optimally, for this we use the Assign Ability Scores; table.
        # optimal stats and rolled stats are sorted from large to small, so that we can overwrite the 'optimal' stats with our actual rolled stats.
        # At the end we re-sort the list to be in the standard D&D order (Str, Dex, Con, Int, Wis, Cha)

        table_name = "Assign Ability Scores; Standard Array by Class"
        ability_table = self._get_dnd_table(table_name)
        headers = ability_table.table["value"]["headers"][1:]  # skip "Class"
        optimal_stats = None
        for row in ability_table.table["value"]["rows"]:
            if row[0].lower() == char_class.name.lower():
                values = row[1:]
                optimal_stats = [(int(val), stat) for stat, val in zip(headers, values)]
                optimal_stats.sort(key=lambda x: x[0], reverse=True)
                break
        if optimal_stats is None:
            raise f"CharacterGen - Class '{char_class.name}' does not exist in Standard Array table!"

        stats = Stats(itr)
        rolled_stats = [val for _, val in stats.stats]
        rolled_stats.sort(reverse=True)

        character_stats: list[tuple[int, str]] = [
            (rolled_stats[i], stat_name)
            for i, (_, stat_name) in enumerate(optimal_stats)
        ]
        # Put back in standard stat-order
        character_stats.sort(key=lambda x: headers.index(x[1]))
        return character_stats

    def apply_bg_boosts(
        self, stats: list[tuple[int, str]], background: Background, char_class: Class
    ):
        bg_abilities = [f"{ability[:3].title()}." for ability in background.abilities]
        abilities = [(value, name) for value, name in stats if name in bg_abilities]
        abilities.sort(key=lambda x: x[0], reverse=True)

        up_each_by_one = True
        if abilities[2][0] < 13:  # Lowest ability below 13.
            up_each_by_one = False
        elif abilities[0][0] % 2 == 0:  # Highest value is round number
            up_each_by_one = False

        if not up_each_by_one:
            primary_abilities = {
                f"{word[:3].title()}."
                for word in char_class.primary_ability.replace(" or ", " ")
                .replace(" and ", " ")
                .split()
            }
            abilities.sort(key=lambda x: (x[1] not in primary_abilities, -x[0]))

        if up_each_by_one:
            updated = [(value + 1, name) for value, name in abilities]
        else:
            updated = [
                (abilities[0][0] + 2, abilities[0][1]),
                (abilities[1][0] + 1, abilities[1][1]),
                abilities[2],
            ]

        new_stats = [
            (
                next((val, nm) for val, nm in updated if nm == name)
                if name in bg_abilities
                else (val, name)
            )
            for val, name in stats
        ]

        return new_stats

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        species: Species = self._get_random_xphb_object(Data.species.entries)
        full_name, _, gender = Data.names.get_random(species.name, Gender.OTHER)
        char_class: Class = self._get_random_xphb_object(Data.classes.entries)
        background = self.get_optimal_background(char_class)

        color = discord.Color(UserColor.generate(full_name))
        title = f"{full_name}"
        species_emoji = "🧝‍♀️" if gender is Gender.FEMALE else "🧝‍♂️"
        class_emoji = "🧙‍♀️" if gender is Gender.FEMALE else "🧙‍♂️"
        embed = SimpleEmbed(title=title, description=None, color=color)
        embed.add_field(
            name="", value=f"{species_emoji} [{species.name}]({species.url})"
        )
        embed.add_field(
            name="", value=f"{class_emoji} [{char_class.name}]({char_class.url})"
        )
        embed.add_field(
            name="", value=f"{background.emoji} [{background.name}]({background.url})"
        )

        # Stats
        stats = self.get_optimal_stats(itr, char_class)
        boosted_stats = self.apply_bg_boosts(
            stats=stats, background=background, char_class=char_class
        )

        def ability_modifier(score: int) -> str:
            mod = (score - 10) // 2
            if mod < 0:
                return f"- {abs(mod)}"
            return f"+ {mod}"

        headers = ["Ability", "Score", "Mod"]
        rows = []
        for stat, boosted in zip(stats, boosted_stats):
            base_value, name = stat
            boosted_value, _ = boosted

            ability_value = str(base_value)
            if boosted_value != base_value:
                diff = boosted_value - base_value
                ability_value = f"{base_value} + {diff}"

            mod = ability_modifier(boosted_value)

            rows.append([name, ability_value, mod])

        ability_table = build_table_from_rows(headers=headers, rows=rows)
        total = sum([val for val, _ in stats])

        embed.add_field(
            name="Ability Scores",
            value=ability_table + f"\n**Total:** {total} + 3",
            inline=False,
        )

        chart_image = get_radar_chart(
            results=stats, boosted_results=boosted_stats, color=color.value
        )

        embed.set_image(url=f"attachment://{chart_image.filename}")
        await itr.response.send_message(embed=embed, file=chart_image)
