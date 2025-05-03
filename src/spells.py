import logging
import os.path
import json
import re
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
    """A class representing a Dungeons & Dragons spell."""

    name: str
    source: str
    level_school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    descriptions: list[tuple[str, str]]
    classes: set[str]

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
        if "entriesHigherLevel" in json:
            for entry in json["entriesHigherLevel"]:
                name = entry["name"]
                entries = entry["entries"]
                self.descriptions.extend(
                    format_descriptions(name, entries, self.fallbackUrl)
                )
        self.classes = set()

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

    def add_class(self, class_name: str) -> None:
        self.classes.add(class_name)


class SpellList(object):
    """A class representing a list of Dungeons & Dragons spells."""
    spells_path = "./submodules/5etools-src/data/spells"
    sources_path = "./submodules/5etools-src/data/spells/sources.json"

    spells: list[Spell] = []

    def __init__(self, ignore_phb2014: bool = True):
        index = os.path.join(self.spells_path, "index.json")
        with open(index, "r") as file:
            spell_file = json.load(file)

        for spell_source in spell_file:
            spell_path = os.path.join(self.spells_path, spell_file[spell_source])
            self._load_spells_file(spell_path)

        with open(self.sources_path, "r") as file:
            sources = json.load(file)
            for source in sources:
                if ignore_phb2014 and source == "PHB":
                    continue
                for spell in sources[source]:
                    index = self.get_exact_index(spell, source)
                    if "class" in sources[source][spell]:
                        for caster_class in sources[source][spell]["class"]:
                            self.spells[index].add_class(caster_class["name"])
                    if "classVariant" in sources[source][spell]:
                        for caster_class in sources[source][spell]["classVariant"]:
                            self.spells[index].add_class(caster_class["name"])

    def _load_spells_file(self, path: str):
        """
        Loads spells from a JSON file and appends them to the spell list.
        Raises:
            FileNotFoundError: If the specified file does not exist.
            json.JSONDecodeError: If the file content is not valid JSON.
        """
        with open(path, "r", encoding="utf-8") as file:
            spells = json.load(file)
            for raw in spells["spell"]:
                spell = Spell(raw)
                self.spells.append(spell)
                logging.debug(f"SpellList: loaded spell '{str(spell)}'")
        logging.debug(f"SpellList: loaded spell file '{path}'")

    def get(self, name: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75) -> list[Spell]:
        """
        Retrieve spells from the spell list based on their name, with optional fuzzy matching.
        Returns:
            list: A list of spells that match the given name. If exact matches are found, 
                only exact matches are returned. Otherwise, fuzzy matches are returned.
        """
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

    def get_exact_index(self, name: str, source: str) -> int:
        """Retrieves the exact index of a spell in the spells list based on its name and source."""
        for i, spell in enumerate(self.spells):
            if spell.name == name and spell.source == source:
                return i
        return -1

    def search(self, query: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75):
        """
        Searches for spells in the spell list based on a query string.
        Returns:
            list: A list of spells that match the query, sorted alphabetically by name.
        """
        
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
    """A class representing a Discord embed for a Dungeons & Dragons spell."""
    spell: Spell

    def __init__(self, spell: Spell):
        self.spell = spell

        title = f"{self.spell.name} ({self.spell.source})"

        level_school = f"*{self.spell.level_school}*"
        casting_time = f"**Casting Time:** {self.spell.casting_time}"
        spell_range = f"**Range:** {self.spell.spell_range}"
        components = f"**Components:** {self.spell.components}"
        duration = f"**Duration:** {self.spell.duration}"

        class_names = ", ".join(sorted(list(spell.classes)))
        classes = f"**Classes:** {class_names}"

        super().__init__(title=title, type="rich", color=discord.Color.dark_green())
        self.add_field(name="", value=level_school, inline=False)
        self.add_field(name="", value=casting_time, inline=False)
        self.add_field(name="", value=spell_range, inline=False)
        self.add_field(name="", value=components, inline=False)
        self.add_field(name="", value=duration, inline=False)
        self.add_field(name="", value=classes, inline=False)
        for name, value in self.spell.descriptions:
            self.add_field(name=name, value=value, inline=False)


class MultiSpellSelect(discord.ui.Select):
    """A class representing a Discord select menu for multiple spell selection."""
    query: str
    spells: list[Spell]

    def __init__(self, query: str, spells: list[Spell]):
        self.query = query
        self.spells = spells

        options = []
        for spell in spells:
            options.append(
                discord.SelectOption(
                    label=f"{spell.name} ({spell.source})",
                    description=f"{spell.level_school}",
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
        """Handles the selection of a spell from the select menu."""
        full_name = self.values[0]
        name_pattern = r"^(.+) \(([^\)]+)\)"  # "Name (Source)"
        name_match = re.match(name_pattern, full_name)
        name = name_match.group(1)
        source = name_match.group(2)

        spell = [
            spell
            for spell in self.spells
            if spell.name == name and spell.source == source
        ][0]
        logging.debug(
            f"MultiSpellSelect: user {interaction.user.display_name} selected '{name}"
        )
        await interaction.response.send_message(embed=SpellEmbed(spell))


class NoSpellsFoundEmbed(discord.Embed):
    """A class representing a Discord embed for when no spells are found."""
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
    """A class representing a Discord view for multiple spell selection."""
    def __init__(self, query: str, spells: list[Spell]):
        super().__init__()
        self.add_item(MultiSpellSelect(query, spells))
