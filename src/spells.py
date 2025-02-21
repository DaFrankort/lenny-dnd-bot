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
    text = re.sub(r"\{@damage (.*?)\}", r"``\1``", text)
    text = re.sub(r"\{@i (.*?)\}", r"*\1*", text)

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


class Spells(object):
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

    def search_spell(
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
                print(f"'{query}' '{name}' {fuzz.ratio(query, name)}")
                fuzzy.append(spell)

        if len(exact) > 0:
            return exact
        return fuzzy


def clean_description(description: any) -> str:
    if isinstance(description, str):
        return clean_dnd_text(description)

    if isinstance(description, list):
        return "\n\n".join([clean_description(desc) for desc in description])

    if description["type"] == "quote":
        quote = clean_description(description["entries"])
        by = description["by"]
        return f"*{quote}* - {by}"

    return f"**VERY DANGEROUS WARNING: This description has a type '{description['type']}' which isn't implemented yet. Please complain to your local software engineer.**"


# Temporary function, need to discuss how we're going to handle message
async def pretty_response_spell(ctx: discord.Interaction, spells: list[Spell]) -> None:
    # No spells found
    if len(spells) == 0:
        await ctx.response.send_message("Couldn't find a spell with that name :(")
        return
    # More than one spell found
    if len(spells) > 1:
        response = "Multiple spells found: " + ", ".join(
            [str(spell) for spell in spells]
        )
        await ctx.response.send_message(response)

    # Exactly one spell found
    spell = spells[0]
    embed = discord.Embed(title=spell.name, type="rich")
    embed.color = discord.Color.dark_green()  # Dark green
    embed.add_field(name="Description", value=clean_description(spell.description))

    await ctx.response.send_message(embed=embed)
    return
