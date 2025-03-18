import logging
import os.path
import json
import discord
from rapidfuzz import fuzz
from discord.utils import MISSING

from parser import (
    format_casting_time,
    format_components,
    format_descriptions,
    format_duration_time,
    format_range,
    format_spell_level_school,
)


class Spell(object):
    name: str
    source: str
    level_school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    descriptions: list[tuple[str, str]]

    def __init__(self, json: any):
        self.name = json["name"]
        self.source = json["source"]
        self.level_school = format_spell_level_school(json["level"], json["school"])
        self.casting_time = format_casting_time(json["time"])
        self.spell_range = format_range(json["range"])
        self.components = format_components(json["components"])
        self.duration = format_duration_time(json["duration"])
        self.descriptions = format_descriptions(
            "Description", json["entries"], self.fallbackUrl
        )

    @property
    def fallbackUrl(self):
        url = f"https://5e.tools/spells.html#{self.name}_{self.source}"
        url = url.replace(" ", "%20")
        return url

    @property
    def is_phb2014(self) -> bool:
        return self.source == "PHB"

    def __str__(self):
        return f"{self.name} ({self.source})"

    def __repr__(self):
        return str(self)


class SpellList(object):
    spells: list[Spell] = []

    def __init__(self, path: str):
        index = os.path.join(path, "index.json")
        with open(index, "r") as file:
            sources = json.load(file)

        for source in sources:
            sourcePath = os.path.join(path, sources[source])
            self._load_spells_file(sourcePath)

    def _load_spells_file(self, path: str):
        with open(path, "r", encoding="utf-8") as file:
            spells = json.load(file)
            for raw in spells["spell"]:
                spell = Spell(raw)
                self.spells.append(spell)
                logging.debug(f"SpellList: loaded spell '{str(spell)}'")
        logging.debug(f"SpellList: loaded spell file '{path}'")

    def get(self, name: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75):
        logging.debug(
            f"SpellList: getting '{name}' (Ignoring PHB'14 = {ignore_phb2014}, threshold = {fuzzy_threshold / 100})"
        )
        name = name.strip().lower()
        exact = []
        fuzzy = []

        for spell in self.spells:
            if ignore_phb2014 and spell.is_phb2014:
                continue

            spell_name = spell.name.strip().lower()
            if name == spell_name:
                exact.append(spell)
            elif fuzz.ratio(name, spell_name) > fuzzy_threshold:
                fuzzy.append(spell)

        if len(exact) > 0:
            return exact
        return fuzzy

    def search(
        self, query: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75
    ):
        logging.debug(
            f"SpellList: searching '{query}' (Ignoring PHB'14 = {ignore_phb2014}, threshold = {fuzzy_threshold / 100})"
        )
        query = query.strip().lower()
        found = []

        for spell in self.spells:
            if ignore_phb2014 and spell.is_phb2014:
                continue

            spell_name = spell.name.strip().lower()
            if fuzz.partial_ratio(query, spell_name) > fuzzy_threshold:
                found.append(spell)
        found = sorted(found, key=lambda x: x.name)
        return found


class SpellEmbed(discord.Embed):
    spell: Spell

    def __init__(self, spell: Spell):
        self.spell = spell

        title = f"{self.spell.name} ({self.spell.source})"

        level_school = f"*{self.spell.level_school}*"
        casting_time = f"**Casting Time:** {self.spell.casting_time}"
        spell_range = f"**Range:** {self.spell.spell_range}"
        components = f"**Components:** {self.spell.components}"
        duration = f"**Duration:** {self.spell.duration}"

        super().__init__(title=title, type="rich", color=discord.Color.dark_green())
        self.add_field(name="", value=level_school, inline=False)
        self.add_field(name="", value=casting_time, inline=False)
        self.add_field(name="", value=spell_range, inline=False)
        self.add_field(name="", value=components, inline=False)
        self.add_field(name="", value=duration, inline=False)
        for name, value in self.spell.descriptions:
            self.add_field(name=name, value=value, inline=False)


class MultiSpellSelect(discord.ui.Select):
    query: str
    spells: list[Spell]

    def __init__(self, query: str, spells: list[Spell]):
        self.query = query
        self.spells = spells

        options = []
        for spell in spells:
            options.append(
                discord.SelectOption(
                    label=f"{spell.name}",
                    description=f"{spell.level_school}, {spell.source}",
                )
            )

        super().__init__(
            placeholder=f"Results for '{query}'",
            options=options,
            min_values=1,
            max_values=1,
        )

        logging.debug(f"MultiSpellSelect: found {len(spells)} spells for '{query}'")

    async def callback(self, interaction: discord.Interaction):
        name = self.values[0]
        spell = [spell for spell in self.spells if spell.name == name][0]
        logging.debug(
            f"MultiSpellSelect: user {interaction.user.display_name} selected '{name}"
        )
        await interaction.response.send_message(embed=SpellEmbed(spell))


class NoSpellsFoundEmbed(discord.Embed):
    def __init__(self, query: str):
        super().__init__(
            color=discord.Color.dark_green(),
            title="No spells found.",
            type="rich",
            url=None,
            description=None,
            timestamp=None,
        )
        self.add_field(name="", value=f"No spells found for '{query}'.")


class MultiSpellSelectView(discord.ui.View):
    def __init__(self, query: str, spells: list[Spell]):
        super().__init__()
        self.add_item(MultiSpellSelect(query, spells))
