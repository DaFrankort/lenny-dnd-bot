import logging
import json
import re
import discord
from rapidfuzz import fuzz
from discord.utils import MISSING


class Spell(object):
    name: str
    source: str
    level: str
    school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    description: list
    classes: set[str]

    def __init__(self, json: any):
        self.name = json["name"]
        self.source = json["source"]
        self.level = json["level"]
        self.school = json["school"]
        self.casting_time = json["casting_time"]
        self.spell_range = json["range"]
        self.components = json["components"]
        self.duration = json["duration"]
        self.description = json["description"]

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
    spells_path = "./submodules/5etools-src/data/spells"
    sources_path = "./submodules/5etools-src/data/spells/sources.json"

    spells: list[Spell] = []

    def __init__(self, path: str):
        with open(path, "r") as file:
            data = json.load(file)
            for spell in data:
                self.spells.append(Spell(spell))

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

    def get_exact_index(self, name: str, source: str) -> int:
        for i, spell in enumerate(self.spells):
            if spell.name == name and spell.source == source:
                return i
        return -1

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

        level_school = f"*{self.spell.level} {self.spell.school}*"
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
        for description in self.spell.description:
            self.add_field(name=description["name"], value=description["text"], inline=False)


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
                    label=f"{spell.name} ({spell.source})",
                    description=f"{spell.level} {spell.school}",
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
