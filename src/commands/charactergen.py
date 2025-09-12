import random
import discord

from charts import get_radar_chart
from components.items import SimpleSeparator, TitleTextDisplay
from logic.app_commands import SimpleCommand
from dnd import Background, Class, Data, DNDObject, DNDTable, Gender, Species
from embeds import SimpleEmbed
from methods import build_table_from_rows
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


class CharacterGenContainerView(discord.ui.LayoutView):
    file: discord.File = None

    def _build_ability_table(
        self,
        background: Background,
        stats: list[tuple[int, str]],
        boosted_stats: list[tuple[int, str]],
    ):
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

            bg_abilities = [f"{a[:3].lower()}." for a in background.abilities]
            if name.lower() in bg_abilities:
                name += "*"  # mark bg abilities

            ability_value = str(base_value)
            if boosted_value != base_value:
                diff = boosted_value - base_value
                ability_value = f"{base_value} + {diff}"

            mod = ability_modifier(boosted_value)
            rows.append([name, ability_value, mod])

        return build_table_from_rows(headers=headers, rows=rows)

    def __init__(
        self,
        name: str,
        gender: Gender,
        species: Species,
        char_class: Class,
        background: Background,
        stats: list[tuple[int, str]],
        boosted_stats: list[tuple[int, str]],
        backstory: str,
    ):
        super().__init__(timeout=None)
        color = discord.Color(UserColor.generate(name))
        container = discord.ui.Container(accent_color=color)
        container.add_item(TitleTextDisplay(name))

        btn_row = discord.ui.ActionRow()
        species_emoji = "🧝‍♀️" if gender is Gender.FEMALE else "🧝‍♂️"
        species_btn = discord.ui.Button(
            style=discord.ButtonStyle.url,
            label=species.name,
            emoji=species_emoji,
            url=species.url,
        )
        btn_row.add_item(species_btn)
        class_emoji = "🧙‍♀️" if gender is Gender.FEMALE else "🧙‍♂️"
        class_btn = discord.ui.Button(
            style=discord.ButtonStyle.url,
            label=char_class.name,
            emoji=class_emoji,
            url=char_class.url,
        )
        btn_row.add_item(class_btn)
        background_btn = discord.ui.Button(
            style=discord.ButtonStyle.url,
            label=background.name,
            emoji=background.emoji,
            url=background.url,
        )
        btn_row.add_item(background_btn)

        container.add_item(btn_row)
        container.add_item(SimpleSeparator())
        container.add_item(discord.ui.TextDisplay(backstory))
        container.add_item(SimpleSeparator())

        ability_table = self._build_ability_table(background, stats, boosted_stats)
        total = sum([val for val, _ in stats])
        ability_desc = ability_table + f"\n**Total**: {total} + 3"

        self.file = get_radar_chart(
            results=stats, boosted_results=boosted_stats, color=color.value
        )
        ability_image = discord.ui.Thumbnail(media=self.file)
        ability_section = discord.ui.Section(ability_desc, accessory=ability_image)
        container.add_item(ability_section)

        self.add_item(container)


class CharacterGenCommand(SimpleCommand):
    name = "charactergen"
    desc = "Generate a random D&D character!"
    help = "Generates a random D&D 5e character, using XPHB classes, species and backgrounds."

    def _get_random_xphb_object(self, entries: list[DNDObject]) -> DNDObject:
        xphb_entries = [e for e in entries if e.source == "XPHB" and "(" not in e.name]
        return random.choice(xphb_entries)

    def _get_dnd_table(
        self, table_name: str, source: str = "XPHB", raise_errors: bool = True
    ) -> DNDTable:
        table: DNDTable = None
        for t in Data.tables.get(query=table_name, allowed_sources=set([source])):
            if t.name == table_name:
                table = t
                break
        if table is None:
            if raise_errors:
                raise f"CharacterGen - Table '{table_name}' no longer exists in 5e.tools, charactergen will not work without it."
            return None
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

    def get_backstory(self, table_name: str, object: DNDObject) -> str:
        table_name = f"{table_name} [{object.name}]"
        table = self._get_dnd_table(table_name, "XGE", False)
        if table is None:
            return ""

        reason = table.roll()[0][1]
        if not reason.startswith("I "):
            reason = reason[0].lower() + reason[1:]

        prefix = table.table["value"]["headers"][1].replace("...", " ")
        return prefix + reason

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        species: Species = self._get_random_xphb_object(Data.species.entries)
        full_name, _, gender = Data.names.get_random(species.name, Gender.OTHER)
        char_class: Class = self._get_random_xphb_object(Data.classes.entries)
        background = self.get_optimal_background(char_class)

        class_backstory = self.get_backstory("Class Training; I became...", char_class)
        background_backstory = self.get_backstory("Background; I became...", background)
        backstory = class_backstory + "\n" + background_backstory

        stats = self.get_optimal_stats(itr, char_class)
        boosted_stats = self.apply_bg_boosts(
            stats=stats, background=background, char_class=char_class
        )

        view = CharacterGenContainerView(
            full_name,
            gender,
            species,
            char_class,
            background,
            stats,
            boosted_stats,
            backstory,
        )
        await itr.response.send_message(view=view, file=view.file)
