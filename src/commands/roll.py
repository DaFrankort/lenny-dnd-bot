import discord

from logic.dicecache import DiceCache
from embeds.roll import MultiRollEmbed, RollEmbed
from commands.command import SimpleCommand
from logic.roll import Advantage, multi_roll, roll
from logic.voice_chat import VC, SoundType
from discord.app_commands import describe, autocomplete


async def diceroll_autocomplete(itr: discord.Interaction, current: str):
    return DiceCache.get_autocomplete_suggestions(itr, current)


async def reason_autocomplete(itr: discord.Interaction, current: str):
    return DiceCache.get_autocomplete_reason_suggestions(itr, current)


class _AbstractRollCommand(SimpleCommand):
    advantage: Advantage

    @autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    @describe(
        diceroll="The dice-expression of the roll you want to make (Example: 1d20+3, 1d8ro1, ...)",
        reason="An optional reason for rolling, for additional clarity. (Example: Attack, Damage, ...)",
    )
    async def callback(  # pyright: ignore
        self,
        itr: discord.Interaction,
        diceroll: str,
        reason: str | None = None,
    ):
        self.log(itr)
        result = roll(diceroll, self.advantage)
        DiceCache.store_expression(itr, result.expression)
        DiceCache.store_reason(itr, reason)
        embed = RollEmbed(itr, result, reason)

        await itr.response.send_message(embed=embed)
        await VC.play_dice_roll(itr, result, reason)


class RollCommand(_AbstractRollCommand):
    name = "roll"
    desc = "Roll your d20s!"
    help = "Roll a single dice expression."

    advantage = Advantage.Normal


class AdvantageRollCommand(_AbstractRollCommand):
    name = "advantage"
    desc = "Lucky you! Roll and take the best of two!"
    help = "Roll the expression twice, use the highest result."

    advantage = Advantage.Advantage


class DisadvantageRollCommand(_AbstractRollCommand):
    name = "disadvantage"
    desc = "Tough luck chump... Roll twice and suck it."
    help = "Roll the expression twice, use the lowest result."

    advantage = Advantage.Disadvantage


class D20Command(SimpleCommand):
    name = "d20"
    desc = "Just roll a clean d20!"
    help = "Rolls a basic 1d20 with no modifiers."

    async def callback(self, itr: discord.Interaction):
        self.log(itr)
        result = roll("1d20", Advantage.Normal)
        embed = RollEmbed(itr, result, None)
        await itr.response.send_message(embed=embed)
        await VC.play_dice_roll(itr, result)


class MultiRollCommand(SimpleCommand):
    name = "multiroll"
    desc = "Roll multiple dice!"
    help = "Roll a dice expression multiple times."

    @autocomplete(
        diceroll=diceroll_autocomplete,
        reason=reason_autocomplete,
    )
    @describe(
        diceroll="The dice-expression of the roll you want to make (Example: 1d20+3, 1d8ro1, ...)",
        amount="How many times to roll the expression.",
        reason="An optional reason for rolling, for additional clarity. (Example: Attack, Damage, ...)",
    )
    async def callback(  # pyright: ignore
        self,
        itr: discord.Interaction,
        diceroll: str,
        amount: discord.app_commands.Range[int, 1, 32],
        reason: str | None = None,
    ):
        self.log(itr)
        result = multi_roll(diceroll, amount)
        DiceCache.store_expression(itr, result.expression)
        DiceCache.store_reason(itr, reason)
        embed = MultiRollEmbed(itr, result, reason)

        await itr.response.send_message(embed=embed)
        await VC.play(itr, SoundType.ROLL)
