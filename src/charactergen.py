import random
import logging
import discord
from dnd import Background, Class, DNDData, DNDTable, Gender
from embeds import HORIZONTAL_LINE, SimpleEmbed
from stats import Stats
from user_colors import UserColor


class CharacterGen:
    name: str
    race: str  # TODO ADD SPECIES
    gender: Gender
    character_class: Class
    background: Background
    stats = Stats

    stats_class: list[tuple[str, int]]
    color = None

    def __init__(self, itr: discord.Interaction, data: DNDData):
        self.name, self.race, self.gender = data.names.get_random(None, Gender.OTHER)
        self.character_class = random.choice(
            [c_class for c_class in data.classes.entries if c_class.source == "XPHB"]
        )
        self.background = random.choice(
            [
                background
                for background in data.backgrounds.entries
                if background.source == "XPHB"
            ]
        )
        self.stats = Stats(itr)
        self.sort_stats_for_class(data)

        self.color = UserColor.get(itr)

    def sort_stats_for_class(
        self, data: DNDData
    ):  # TODO FIX BACK END TO HAVE THIS TABLE
        # Get table
        table_name = "Assign Ability Scores; Standard Array by Class"
        ability_table: DNDTable = None
        for table in data.tables.get(query=table_name):
            if table_name.lower() == table.name.lower():
                ability_table = table
                break

        if ability_table is None:
            logging.error(f"No table found under {table_name}")
            return None  # TODO: HANDLE

        # Get recommended values from table
        class_stats: list[tuple[str, int]] = []
        for row in ability_table.table["value"]["rows"]:
            class_cell = row[0]

            if class_cell.lower() == self.character_class.name.lower():
                for i, cell in enumerate(row[1:7]):
                    stat = (
                        ability_table.table["value"]["headers"][i + 1]
                        .replace(".", "")
                        .upper()
                    )
                    score = int(cell)
                    class_stats.append((stat, score))
                break

        if len(class_stats) != 6:
            logging.error(
                f"No 6 class stats found for class {self.character_class.name}"
            )
            return None  # TODO HANDLE CLASS NOT FOUND

        # Sort both stats from largest to smallest
        class_stats = sorted(class_stats, key=lambda x: x[1], reverse=True)
        stats = [score for _, score in self.stats.stats]
        stats = sorted(stats, reverse=True)

        # Overwrite recommended values with rolled values
        self.stats_class = []
        for i in range(6):
            stat = class_stats[i]
            stat = (stat[0], stats[i])
            self.stats_class.append(stat)

        # Sort self.stats_class to STR, DEX, CON, INT, WIS, CHA order
        stat_order = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        self.stats_class.sort(key=lambda x: stat_order.index(x[0]))


class CharacterGenEmbed(SimpleEmbed):
    def __init__(self, character: CharacterGen):
        desc = f"*{character.gender.value} {character.race} {character.character_class.name}*".title()
        super().__init__(title=character.name, description=None, color=character.color)
        self.description = desc

        stat_text = ""
        for stat, score in character.stats_class:
            stat_text += f"- ``{stat}``: {score}\n"

        self.add_field(name="Stats", value=stat_text, inline=True)
        self.add_field(
            name="Background",
            value=character.background.name.title(),
            inline=True,
        )
        self.add_field(name="", value=HORIZONTAL_LINE, inline=False)
