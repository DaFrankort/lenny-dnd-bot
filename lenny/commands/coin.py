import discord

from commands.command import BaseCommand
from embeds.embed import UserActionEmbed
from logic.coin import Coin


class CoinCommand(BaseCommand):
    name = "coin"
    desc = "Calculate D&D coin math!"
    help = "Calculate your pieces using addition, subtraction, division and multiplication!"

    async def handle(self, itr: discord.Interaction, expression: str, round_up: bool = False):
        coin = Coin.from_string(expression)
        if round_up:
            coin.round_up()
        embed = UserActionEmbed(itr, title=expression, description=str(coin))
        await itr.response.send_message(embed=embed)
