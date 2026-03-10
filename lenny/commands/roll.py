import discord
from discord.app_commands import autocomplete, choices, describe

from commands.command import BaseCommand
from embeds.roll import MultiRollEmbed, RollEmbed
from logic.dicecache import DiceCache
from logic.roll import Advantage, multi_roll, roll
from logic.voice_chat import VC, SoundType


async def diceroll_autocomplete(itr: discord.Interaction, current: str):
    return DiceCache.get(itr).get_autocomplete_suggestions(current)


async def reason_autocomplete(itr: discord.Interaction, current: str):
    return DiceCache.get(itr).get_autocomplete_reason_suggestions(current)


class RollCommand(BaseCommand):
    name = "roll"
    desc = "Roll your d20s!"
    help = "Roll a single dice expression."

    @autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    @describe(
        diceroll="The dice-expression of the roll you want to make (Example: 1d20+3, 1d8ro1, ...)",
        reason="An optional reason for rolling, for additional clarity. (Example: Attack, Damage, ...)",
        advantage="Does the dice roll have advantage?",
    )
    @choices(advantage=Advantage.choices())
    async def handle(
        self,
        itr: discord.Interaction,
        diceroll: str,
        reason: str | None = None,
        advantage: str | None = None,
    ):
        if advantage is None:
            advantage = Advantage.NORMAL
        else:
            advantage = Advantage(advantage)

        result = roll(diceroll, advantage)
        DiceCache.get(itr).store_expression(result.expression)
        DiceCache.get(itr).store_reason(reason)
        embed = RollEmbed(itr, result, reason)

        await itr.response.send_message(embed=embed)
        await VC.play_dice_roll(itr, result, reason)


class D20Command(BaseCommand):
    name = "d20"
    desc = "Just roll a clean d20!"
    help = "Rolls a basic 1d20 with no modifiers."

    async def handle(self, itr: discord.Interaction):
        result = roll("1d20", Advantage.NORMAL)
        embed = RollEmbed(itr, result, None)
        await itr.response.send_message(embed=embed)
        await VC.play_dice_roll(itr, result)


class MultiRollCommand(BaseCommand):
    name = "multiroll"
    desc = "Roll multiple dice!"
    help = "Roll a dice expression multiple times."

    @autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    @choices(advantage=Advantage.choices())
    @describe(
        diceroll="The dice-expression of the roll you want to make (Example: 1d20+3, 1d8ro1, ...)",
        amount="How many times to roll the expression.",
        advantage="Roll with or without advantage, rolls normal by default.",
        reason="An optional reason for rolling, for additional clarity. (Example: Attack, Damage, ...)",
    )
    async def handle(
        self,
        itr: discord.Interaction,
        diceroll: str,
        amount: discord.app_commands.Range[int, 1, 32],
        advantage: str = Advantage.NORMAL,
        reason: str | None = None,
    ):
        result = multi_roll(diceroll, amount, Advantage(advantage))
        DiceCache.get(itr).store_expression(result.expression)
        DiceCache.get(itr).store_reason(reason)
        embed = MultiRollEmbed(itr, result, reason)

        await itr.response.send_message(embed=embed)
        await VC.play(itr, SoundType.ROLL)
