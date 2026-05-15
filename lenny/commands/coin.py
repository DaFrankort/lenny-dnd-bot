import discord

from commands.command import BaseCommand
from embeds.embed import UserActionEmbed
from logic.coin import Coin


class CoinCommand(BaseCommand):
    name = "coin"
    desc = "Perform D&D currency math!"
    help = "Calculate your pieces using addition, subtraction, division and multiplication!"

    async def handle(self, itr: discord.Interaction, expression: str):
        coin = Coin.from_string(expression)
        embed = UserActionEmbed(itr, title=expression.upper(), description=str(coin))
        await itr.response.send_message(embed=embed)
