import os.path
import json
import discord
from rapidfuzz import fuzz
import re

SPELL_SCHOOLS = {
    "A": "Abjuration",
    "C": "Conjuration",
    "D": "Divination",
    "E": "Enchantment",
    "V": "Evocation",
    "I": "Illusion",
    "N": "Necromancy",
    "P": "Psionic",
    "T": "Transmutation",
}


def clean_dnd_text(text: str) -> str:
    text = re.sub(r"\{@damage (.*?)\}", r"**\1**", text)
    text = re.sub(r"\{@i (.*?)\}", r"*\1*", text)
    text = re.sub(r"\{@spell (.*?)\}", r"__\1__", text)
    text = re.sub(r"\{@creature (.*?)(\|.*?)?\}", r"__\1__", text)
    text = re.sub(r"\{@status (.*?)\}", r"*\1*", text)
    text = re.sub(r"\{@skill (.*?)\}", r"*\1*", text)
    text = re.sub(r"\{@dice (.*?)\}", r"\1", text)

    return text


class Spell(object):
    name: str
    source: str
    level: str
    school: str
    description: list[any]

    def __init__(self, json: any):
        self.name = json["name"]
        self.source = json["source"]
        self.level = json["level"]
        self.school = json["school"]
        self.description = json["entries"]

    @property
    def schoolName(self) -> str:
        return SPELL_SCHOOLS[self.school]

    @property
    def is_phb2024(self) -> bool:
        return self.source == "XPHB"

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
            for spell in spells["spell"]:
                self.spells.append(Spell(spell))

    def search(
        self, query: str, ignore_phb2014: bool = True, fuzzy_threshold: float = 75
    ):
        query = query.strip().lower()
        exact = []
        fuzzy = []

        for spell in self.spells:
            if ignore_phb2014 and spell.is_phb2024:
                continue

            name = spell.name.strip().lower()
            if name == spell.name:
                exact.append(spell)
            elif fuzz.ratio(query, name) > fuzzy_threshold:
                fuzzy.append(spell)

        if len(exact) > 0:
            return exact
        return fuzzy


class SpellEmbed(object):
    spell: Spell

    def __init__(self, spell: Spell):
        self.spell = spell

    def build(self) -> discord.Embed:
        title = f"{self.spell.name} ({self.spell.source})"

        if self.spell.level == 0:
            level = "Cantrip"
        else:
            level = f"Level {self.spell.level}"
        info = f"*{level} {self.spell.schoolName}*"
        descriptions = self._build_description("Description", self.spell.description)

        embed = discord.Embed(title=title, type="rich")
        embed.color = discord.Color.dark_green()
        embed.add_field(name="", value=info)
        for name, value in descriptions:
            embed.add_field(name=name, value=value, inline=False)

        return embed

    @staticmethod
    def _build_description_block(description: any) -> str:
        if isinstance(description, str):
            return clean_dnd_text(description)

        if description["type"] == "quote":
            quote = SpellEmbed._build_description_block_from_blocks(
                description["entries"]
            )
            by = description["by"]
            return f"*{quote}* - {by}"

        if description["type"] == "list":
            bullet = "•"  # U+2022
            points = []
            for item in description["items"]:
                points.append(f"{bullet} {SpellEmbed._build_description_block(item)}")
            return "\n".join(points)

        if description["type"] == "inset":
            return f"*{SpellEmbed._build_description_block_from_blocks(description['entries'])}*"

        return f"**VERY DANGEROUS WARNING: This description has a type '{description['type']}' which isn't implemented yet. Please complain to your local software engineer.**"

    @staticmethod
    def _build_description_block_from_blocks(descriptions: list[any]) -> str:
        blocks = [SpellEmbed._build_description_block(desc) for desc in descriptions]
        return "\n\n".join(blocks)

    @staticmethod
    def _build_description_from_table(description: any) -> str:
        return "TODO"

    @staticmethod
    def _build_description(name: str, description: list[any]) -> list[tuple[str, str]]:
        subdescriptions: list[tuple[str, str]] = []

        blocks: list[str] = []

        for desc in description:
            # Special case scenario where an entry is a description on its own
            # These will be handled separately
            if not isinstance(desc, str):
                if desc["type"] == "entries":
                    subdescriptions.extend(
                        SpellEmbed._build_description(desc["name"], desc["entries"])
                    )
                elif desc["type"] == "table":
                    subdescriptions.append(
                        SpellEmbed._build_description_from_table(desc)
                    )
            else:
                blocks.append(SpellEmbed._build_description_block(desc))

        descriptions = []
        if len(blocks) > 0:
            descriptions.append((name, blocks[0]))
        for i in range(1, len(blocks)):
            descriptions.append(("", blocks[i]))
        descriptions.extend(subdescriptions)

        return descriptions


class SpellSearchEmbed(object):
    query: str
    spells: list[Spell]

    def __init__(self, query: str, spells: list[Spell]):
        self.query = query
        self.spells = spells

    def build(self):
        # One spell found
        if len(self.spells) == 1:
            return SpellEmbed(self.spells[0]).build()

        # Multiple spells found
        if len(self.spells) > 1:
            embed = discord.Embed(title=f"Results for '{self.query}`", type="rich")
            results = []
            for i, spell in enumerate(self.spells):
                results.append(f"{i+1} {spell.name}")
            embed.add_field(name="", value="\n".join(results))
            return embed

        # No spells found
        embed = discord.Embed(title="No results found.", type="rich")
        embed.add_field(name="", value=f"No results found for '{self.query}'.")
        return embed
