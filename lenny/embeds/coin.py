import copy
from typing import get_args

import discord

from embeds.components import TitleTextDisplay
from logic.coin import Coin, CoinResult, CoinUnit
from logic.color import UserColor


class CoinButton(discord.ui.Button["CoinLayoutView"]):
    unit: CoinUnit
    _coin_view: "CoinLayoutView"

    def __init__(self, unit: CoinUnit, view: "CoinLayoutView"):
        self.unit = unit
        self._coin_view = view
        style = discord.ButtonStyle.primary if view.toggles[unit] else discord.ButtonStyle.secondary
        disabled = unit == "cp"

        super().__init__(label=unit.upper(), style=style, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        self._coin_view.toggles[self.unit] = not self._coin_view.toggles[self.unit]
        self._coin_view.build()
        await interaction.response.edit_message(view=self._coin_view)


class CoinLayoutView(discord.ui.LayoutView):
    result: CoinResult
    coin: Coin
    color: int
    toggles: dict[CoinUnit, bool]

    def __init__(self, itr: discord.Interaction, result: CoinResult):
        self.result = result
        self.coin = copy.deepcopy(self.result.coin)
        self.color = UserColor.get(itr)

        self.toggles: dict[CoinUnit, bool] = {unit: (unit in result.used_units) for unit in get_args(CoinUnit)}

        super().__init__()
        self.build()

    def _upgrade(self):
        total_cp = self.coin.total_cp
        sign = -1 if total_cp < 0 else 1
        remaining_cp = abs(total_cp)

        for unit in Coin.DENOMINATIONS:
            setattr(self.coin, unit, 0)

        for unit in reversed(Coin.DENOMINATIONS):
            if not self.toggles.get(unit, False):
                continue

            unit_value = Coin.CONVERSIONS[unit]
            amount = remaining_cp // unit_value
            remaining_cp %= unit_value

            setattr(self.coin, unit, amount * sign)

    def _convert_coin(self):
        self.coin = copy.copy(self.result.coin)
        self.toggles["cp"] = True  # Always enabled.
        self._upgrade()

    def build(self):
        self.clear_items()
        self._convert_coin()

        container: discord.ui.Container[discord.ui.LayoutView] = discord.ui.Container(accent_color=self.color)
        container.add_item(TitleTextDisplay(self.result.expression))

        total_cp = self.coin.total_cp
        if total_cp != 0:
            buttons: discord.ui.ActionRow[discord.ui.LayoutView] = discord.ui.ActionRow()
            for unit in get_args(CoinUnit):
                if Coin.CONVERSIONS[unit] > abs(total_cp):
                    continue
                buttons.add_item(CoinButton(unit, self))
            container.add_item(buttons)
        container.add_item(discord.ui.TextDisplay(str(self.coin)))

        self.add_item(container)
