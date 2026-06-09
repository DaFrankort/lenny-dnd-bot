import discord
from discord.app_commands import autocomplete, describe

from commands.command import BaseCommand
from embeds.embed import UserActionEmbed
from logic.coin import Coin
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
        coin = Coin.from_string(expression)
        embed = UserActionEmbed(itr, title=expression.lower(), description=str(coin))
        await itr.response.send_message(embed=embed)
        DiceCache.get(itr).store_coin(coin)
