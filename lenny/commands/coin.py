import discord

from commands.command import BaseCommand
from discord.app_commands import describe
from embeds.embed import UserActionEmbed
from logic.coin import Coin


class CoinCommand(BaseCommand):
    name = "coin"
    desc = "Perform D&D currency math!"
    help = "Calculate your pieces using addition, subtraction, division and multiplication!"

    @describe(expression="Units: cp, sp, ep, gp, pp; Operators: + - * /")
    async def handle(self, itr: discord.Interaction, expression: str):
        coin = Coin.from_string(expression)
        embed = UserActionEmbed(itr, title=expression.lower(), description=str(coin))
        await itr.response.send_message(embed=embed)
