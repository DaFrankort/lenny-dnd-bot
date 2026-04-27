import discord
from discord import Interaction
from discord.app_commands import Range, autocomplete, describe

from commands.command import BaseCommand, BaseCommandGroup
from embeds.average import AverageDamageLayoutView
from logic.average import (
    AverageDamageACResults,
    AverageDamageDCResults,
    half_dice_in_expression,
)


class AverageDamageACCommand(BaseCommand):
    name = "ac"
    desc = "Calculate the average damage of a melee attack vs various AC's!"
    help = "Calculates the average damage of an attack against various armor classes, taking critical hits and critical misses into account."

    @describe(
        hit="Your hit modifier on your attack roll, (e.g. '8', '4+1d4').",
        damage="Your damage expression on a hit (e.g. '1d8+3', '8d6')",
        min_ac="The minimum AC to compare against, default = 8.",
        max_ac="The maximum AC to compare against, default = 30.",
        crit_min="The minimum roll required on the d20 to land a critical hit, default = 20",
        miss_damage="The damage rolled on a miss, default = 0.",
    )
    async def handle(
        self,
        itr: Interaction,
        hit: str,
        damage: str,
        min_ac: Range[int, 0, 30] = 8,
        max_ac: Range[int, 0, 30] = 30,
        crit_min: Range[int, 0, 20] = 20,
        miss_damage: str = "0",
    ) -> None:
        results = AverageDamageACResults(hit, damage, min_ac, max_ac, crit_min, miss_damage)
        view = AverageDamageLayoutView(itr, results)
        await itr.response.send_message(view=view, file=results.chart)


async def miss_damage_dc_autocomplete(itr: discord.Interaction, current: str):
    choices: list[discord.app_commands.Choice[str]] = []

    current = current.strip().lower()
    if current:
        choices.append(discord.app_commands.Choice(name=current, value=current))

    damage_value = getattr(itr.namespace, "damage", None)
    if damage_value:
        half_damage = half_dice_in_expression(damage_value)
        choices.append(discord.app_commands.Choice(name=f"Half-damage ({half_damage})", value=half_damage))

    choices.append(discord.app_commands.Choice(name="No damage", value="0"))
    return choices


class AverageDamageDCCommand(BaseCommand):
    name = "dc"
    desc = "Calculate the average damage of a DC-based attack!"
    help = "Calculates the average damage of a DC-based attack against various save modifiers, taking critical hits and critical misses into account."

    @describe(
        dc="Your DC value, usually your Spell Save DC.",
        damage="Your damage expression on a hit (e.g. '1d8+3', '8d6')",
        miss_damage="The damage rolled on a miss.",
        min_mod="The minimum mod to compare against, default = -4",
        max_mod="The maximum mod to compare against, default = 12",
    )
    @autocomplete(miss_damage=miss_damage_dc_autocomplete)
    async def handle(
        self,
        itr: Interaction,
        dc: Range[int, 0, 30],
        damage: str,
        miss_damage: str,
        min_mod: Range[int, -20, 40] = -4,
        max_mod: Range[int, -20, 40] = 12,
    ) -> None:
        results = AverageDamageDCResults(dc, damage, miss_damage, min_mod, max_mod)
        view = AverageDamageLayoutView(itr, results)
        await itr.response.send_message(view=view, file=results.chart)


class AverageDamageCommandGroup(BaseCommandGroup):
    name = "average"
    desc = "Quickly calculate average damage in various scenarios."

    def __init__(self):
        super().__init__()
        self.add_command(AverageDamageACCommand())
        self.add_command(AverageDamageDCCommand())
