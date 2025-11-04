import dataclasses
import random
from typing import TypeVar

import discord
from logic.dnd.abstract import DNDObject
from logic.dnd.background import Background
from logic.dnd.class_ import Class
from logic.dnd.data import Data
from logic.dnd.name import Gender
from logic.dnd.species import Species
from logic.dnd.table import DNDTable
from logic.stats import Stats


def species_choices(xphb_only: bool = True) -> list[discord.app_commands.Choice[str]]:
    species = [e.name for e in Data.species.entries if (e.source == "XPHB" or not xphb_only) and "(" not in e.name]
    return [discord.app_commands.Choice(name=spec, value=spec) for spec in species[:25]]


def class_choices(xphb_only: bool = True) -> list[discord.app_commands.Choice[str]]:
    classes = [e.name for e in Data.classes.entries if (e.source == "XPHB" or not xphb_only)]
    return [discord.app_commands.Choice(name=char_cls, value=char_cls) for char_cls in classes[:25]]


@dataclasses.dataclass
class CharacterGenResult(object):
    name: str
    gender: Gender
    species: Species
    char_class: Class
    background: Background
    backstory: str
    stats: list[tuple[int, str]]
    boosted_stats: list[tuple[int, str]]


TDND = TypeVar("TDND", bound=DNDObject)


def _get_random_xphb_object(entries: list[TDND]) -> TDND:
    xphb_entries = [e for e in entries if e.source == "XPHB" and "(" not in e.name]
    return random.choice(xphb_entries)


def _get_dnd_table(table_name: str, source: str = "XPHB") -> DNDTable | None:
    for table in Data.tables.get(query=table_name, allowed_sources=set([source])):
        if table.name == table_name:
            return table
    return None


def _get_optimal_background(char_class: Class) -> Background:
    """
    Determines and returns an optimal Background for a given character class based on its primary ability.

    This method uses the "Choose a Background; Ability Scores and Backgrounds" table to find backgrounds
    that best match the class's primary ability. Only classes from the XPHB (Expanded Player's Handbook)
    are supported, as older data may not include primary abilities.
    """

    table_name = "Choose a Background; Ability Scores and Backgrounds"
    background_table = _get_dnd_table(table_name)
    if background_table is None:
        raise LookupError("Background table is required for CharacterGen, but it could not be found!")

    # If the primary ability of the class cannot be determined, choose randomly
    if char_class.primary_ability is None:
        backgrounds = Data.backgrounds.entries
    else:
        recommended: set[str] = set()
        for ability, backgrounds in background_table.table["value"]["rows"]:
            backgrounds = backgrounds.split(",")
            if ability.lower() in char_class.primary_ability.lower():
                recommended.update(bg.strip().lower() for bg in backgrounds)
        backgrounds = [entry for entry in Data.backgrounds.entries if entry.name.lower() in recommended]

    background: Background = _get_random_xphb_object(backgrounds)
    return background


def _get_optimal_stats(char_class: Class) -> list[tuple[int, str]]:
    """
    To optimally assign rolled stats, we use the 'Assign Ability Scores; Standard Array by Class' table.
    Both the optimal stats and rolled stats are sorted from highest to lowest, so we can match the best rolled values to the most important abilities.
    Finally, the list is reordered to follow the standard D&D stat order: Str, Dex, Con, Int, Wis, Cha.
    """

    table_name = "Assign Ability Scores; Standard Array by Class"
    ability_table = _get_dnd_table(table_name)
    if ability_table is None:
        raise LookupError("Ability table is required for CharacterGen, but it could not be found!")

    headers = ability_table.table["value"]["headers"][1:]  # skip "Class"
    optimal_stats = None
    for row in ability_table.table["value"]["rows"]:
        if row[0].lower() == char_class.name.lower():
            values = row[1:]
            optimal_stats = [(int(val), stat) for stat, val in zip(headers, values)]
            optimal_stats.sort(key=lambda x: x[0], reverse=True)
            break

    if optimal_stats is None:
        raise LookupError(f"Class '{char_class.name}' does not exist in CharacterGen Standard Array table!")

    stats = Stats()
    rolled_stats = [val for _, val in stats.stats]
    rolled_stats.sort(reverse=True)

    character_stats: list[tuple[int, str]] = [(rolled_stats[i], stat_name) for i, (_, stat_name) in enumerate(optimal_stats)]
    # Put back in standard stat-order
    character_stats.sort(key=lambda x: headers.index(x[1]))
    return character_stats


def _apply_background_boosts(stats: list[tuple[int, str]], background: Background, char_class: Class):
    bg_abilities = [f"{ability[:3].title()}." for ability in background.abilities]
    abilities = [(value, name) for value, name in stats if name in bg_abilities]
    abilities.sort(key=lambda x: x[0], reverse=True)

    up_each_by_one = True
    if abilities[2][0] < 13:  # Lowest ability below 13.
        up_each_by_one = False
    elif abilities[0][0] % 2 == 0:  # Highest value is round number
        up_each_by_one = False

    if not up_each_by_one and char_class.primary_ability is not None:
        class_abilities = char_class.primary_ability.replace(" or ", " ")
        class_abilities = class_abilities.replace(" and ", " ")
        class_abilities = class_abilities.split()
        primary_abilities = [f"{word[:3].title()}." for word in class_abilities]
        abilities.sort(key=lambda x: (x[1] not in primary_abilities, -x[0]))

    if up_each_by_one:
        updated = [(value + 1, name) for value, name in abilities]
    else:
        updated = [
            (abilities[0][0] + 2, abilities[0][1]),
            (abilities[1][0] + 1, abilities[1][1]),
            abilities[2],
        ]

    new_stats = []
    for val, name in stats:
        if name in bg_abilities:
            new_stats.append(next((v, n) for v, n in updated if n == name))
            continue
        new_stats.append((val, name))

    return new_stats


def _get_backstory(table_name: str, object: DNDObject) -> str:
    table_name = f"{table_name} [{object.name}]"
    table = _get_dnd_table(table_name, "XGE")
    if table is None:
        return ""

    roll = table.roll()
    if roll is None:
        return ""

    reason = roll[0][1]
    if not reason.startswith("I "):
        reason = reason[0].lower() + reason[1:]

    prefix = table.table["value"]["headers"][1].replace("...", " ")
    return prefix + reason


def generate_dnd_character(gender_str: str | None, species_str: str | None, char_class_str: str | None) -> CharacterGenResult:
    gender = Gender.OTHER if gender_str is None else Gender(gender_str)

    if species_str is None:
        species: Species = _get_random_xphb_object(Data.species.entries)
    else:
        species: Species = Data.species.get(query=species_str, allowed_sources=set(["XPHB"]))[0]
    name, _, gender = Data.names.get_random(species.name, gender)

    if name is None or gender is None:
        raise LookupError("Could not determine name and gender for generated character.")

    if char_class_str is None:
        char_class: Class = _get_random_xphb_object(Data.classes.entries)
    else:
        char_class: Class = Data.classes.get(query=char_class_str, allowed_sources=set(["XPHB"]))[0]
    background = _get_optimal_background(char_class)

    class_backstory = _get_backstory("Class Training; I became...", char_class)
    background_backstory = _get_backstory("Background; I became...", background)
    backstory = class_backstory + "\n" + background_backstory

    stats = _get_optimal_stats(char_class)
    boosted_stats = _apply_background_boosts(stats=stats, background=background, char_class=char_class)

    return CharacterGenResult(name, gender, species, char_class, background, backstory, stats, boosted_stats)
