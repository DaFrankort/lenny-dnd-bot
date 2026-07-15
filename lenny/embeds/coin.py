import discord

from embeds.components import TitleTextDisplay
from logic.coin import CoinResult
from logic.color import UserColor


class CoinLayoutView(discord.ui.LayoutView):
    def __init__(self, itr: discord.Interaction, result: CoinResult):
        super().__init__()
        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=UserColor.get(itr))
        container.add_item(TitleTextDisplay(result.expression))
        container.add_item(discord.ui.TextDisplay(str(result.value)))
        self.add_item(container)
