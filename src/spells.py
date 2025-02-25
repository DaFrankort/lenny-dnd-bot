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


def format_dnd_text(text: str) -> str:
    text = re.sub(r"\{@damage (.*?)\}", r"**\1**", text)
    text = re.sub(r"\{@i (.*?)\}", r"*\1*", text)
    text = re.sub(r"\{@spell (.*?)\}", r"__\1__", text)
    text = re.sub(r"\{@creature (.*?)(\|.*?)?\}", r"__\1__", text)
    text = re.sub(r"\{@status (.*?)\}", r"*\1*", text)
    text = re.sub(r"\{@skill (.*?)\}", r"*\1*", text)
    text = re.sub(r"\{@dice (.*?)\}", r"\1", text)
    text = re.sub(r"\{@condition (.*?)\}", r"\1", text)

    return text


def format_spell_level_school(level: int, school: str) -> str:
    if level == 0:
        level_str = "Cantrip"
    else:
        level_str = f"Level {level}"
    return f"*{level_str} {SPELL_SCHOOLS[school]}*"


def format_casting_time(time: any) -> str:
    if len(time) > 1:
        return f"Unsupported casting time type: '{len(time)}'"
    amount = time[0]["number"]
    unit = time[0]["unit"]

    if unit == "action":
        if amount == 1:
            return "Action"
        else:
            return f"{amount} actions"

    if unit == "bonus":
        if amount == 1:
            return "Bonus action"
        else:
            return f"{amount} bonus actions"

    if amount == 1:
        return f"{amount} {unit}"
    return f"{amount} {unit}s"


def format_duration_time(duration: any) -> str:
    duration = duration[0]
    if duration["type"] == "instant":
        return "Instantaneous"

    if duration["type"] == "permanent":
        return "Permanent"

    if duration["type"] == "timed":
        amount = duration["duration"]["amount"]
        unit = duration["duration"]["type"]
        if amount > 1:
            unit += "s"
        return f"{amount} {unit}"

    return f"Unsupported duration type: '{duration['type']}'"


def format_range(spell_range: any) -> str:
    if spell_range["type"] == "point":
        if spell_range["distance"]["type"] == "touch":
            return "Touch"
        
        if spell_range["distance"]["type"] == "self":
            return "Self"
        
        if spell_range["distance"]["type"] == "feet":
            return f"{spell_range['distance']['amount']} feet"
        
        return f"Unsupported point range type: {spell_range['distance']['type']}"

    return f"Unsupported range type: '{spell_range['type']}'"


def format_components(components: dict) -> str:
    result = []
    if components.get("v", False):
        result.append("V")
    if components.get("s", False):
        result.append("S")
    if "m" in components.keys():
        material = components["m"]
        if not isinstance(material, str):
            material = material["text"]
        result.append(f"M ({material})")
    return ", ".join(result)


def _format_description_block(description: any) -> str:
    if isinstance(description, str):
        return format_dnd_text(description)

    if description["type"] == "quote":
        quote = _format_description_block_from_blocks(description["entries"])
        by = description["by"]
        return f"*{quote}* - {by}"

    if description["type"] == "list":
        bullet = "•"  # U+2022
        points = []
        for item in description["items"]:
            points.append(f"{bullet} {_format_description_block(item)}")
        return "\n".join(points)

    if description["type"] == "inset":
        return f"*{_format_description_block_from_blocks(description['entries'])}*"

    return f"**VERY DANGEROUS WARNING: This description has a type '{description['type']}' which isn't implemented yet. Please complain to your local software engineer.**"


def _format_description_block_from_blocks(descriptions: list[any]) -> str:
    blocks = [_format_description_block(desc) for desc in descriptions]
    return "\n\n".join(blocks)


def _format_description_from_table(description: any) -> str:
    return "Table entries not supported for now"


def format_descriptions(name: str, description: list[any]) -> list[tuple[str, str]]:
    subdescriptions: list[tuple[str, str]] = []

    blocks: list[str] = []

    for desc in description:
        # Special case scenario where an entry is a description on its own
        # These will be handled separately
        if not isinstance(desc, str):
            if desc["type"] == "entries":
                subdescriptions.extend(
                    format_descriptions(desc["name"], desc["entries"])
                )
            elif desc["type"] == "table":
                subdescriptions.append(_format_description_from_table(desc))
        else:
            blocks.append(_format_description_block(desc))

    descriptions = []
    if len(blocks) > 0:
        descriptions.append((name, blocks[0]))
    for i in range(1, len(blocks)):
        descriptions.append(("", blocks[i]))
    descriptions.extend(subdescriptions)

    return descriptions


class Spell(object):
    name: str
    source: str
    level: str
    school: str
    time: any
    spell_range: any
    components: any
    duration: any
    description: list[any]

    def __init__(self, json: any):
        self.name = json["name"]
        self.source = json["source"]
        self.level = json["level"]
        self.school = json["school"]
        self.time = json["time"]
        self.spell_range = json["range"]
        self.components = json["components"]
        self.duration = json["duration"]
        self.description = json["entries"]

    @property
    def is_phb2014(self) -> bool:
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
            if ignore_phb2014 and spell.is_phb2014:
                continue

            name = spell.name.strip().lower()
            if name == query:
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

        level_school = format_spell_level_school(self.spell.level, self.spell.school)
        casting_time = format_casting_time(self.spell.time)
        spell_range = format_range(self.spell.spell_range)
        components = format_components(self.spell.components)
        duration = format_duration_time(self.spell.duration)
        descriptions = format_descriptions("Description", self.spell.description)

        casting_time = f"**Casting Time:** {casting_time}"
        spell_range = f"**Range:** {spell_range}"
        components = f"**Components:** {components}"
        duration = f"**Duration:** {duration}"

        embed = discord.Embed(title=title, type="rich")
        embed.color = discord.Color.dark_green()
        embed.add_field(name="", value=level_school, inline=False)
        embed.add_field(name="", value=casting_time, inline=False)
        embed.add_field(name="", value=spell_range, inline=False)
        embed.add_field(name="", value=components, inline=False)
        embed.add_field(name="", value=duration, inline=False)
        for name, value in descriptions:
            embed.add_field(name=name, value=value, inline=False)

        return embed


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
            embed.color = discord.Color.dark_green()
            results = []
            for i, spell in enumerate(self.spells):
                results.append(f"{i+1}. {spell.name}")
            embed.add_field(name="", value="\n".join(results))
            return embed

        # No spells found
        embed = discord.Embed(title="No results found.", type="rich")
        embed.color = discord.Color.dark_green()
        embed.add_field(name="", value=f"No results found for '{self.query}'.")
        return embed
