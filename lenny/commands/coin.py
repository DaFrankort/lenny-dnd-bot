import discord
from discord.app_commands import autocomplete, describe

from commands.command import BaseCommand
from embeds.coin import CoinLayoutView
from logic.coin import parse_coin
from logic.dicecache import DiceCache


async def coin_autocomplete(itr: discord.Interaction, current: str):
    return DiceCache.get(itr).get_coin_autocomplete_suggestions(current)


class CoinCommand(BaseCommand):
    name = "coin"
    desc = "Perform D&D currency math!"
    help = "Calculate your pieces using addition, subtraction, division and multiplication!"

    @describe(expression="Units: cp, sp, ep, gp, pp; Operators: + - * /")
    @autocomplete(expression=coin_autocomplete)
    async def handle(self, itr: discord.Interaction, expression: str):
        result = parse_coin(expression=expression)
        view = CoinLayoutView(itr, result)
        await itr.response.send_message(view=view)
        DiceCache.get(itr).store_coin(result)
