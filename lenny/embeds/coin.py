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

    def _downgrade(self, unit: CoinUnit):
        if unit == "cp":
            return

        denominations = Coin.DENOMINATIONS

        index = denominations.index(unit)
        lower_unit = denominations[index - 1]

        amount = getattr(self.coin, unit)

        ratio = Coin.CONVERSIONS[unit] // Coin.CONVERSIONS[lower_unit]

        setattr(self.coin, unit, 0)
        setattr(
            self.coin,
            lower_unit,
            getattr(self.coin, lower_unit) + amount * ratio,
        )

    def _upgrade(self):
        total_cp = self.coin.total_cp
        sign = -1 if total_cp < 0 else 1
        abs_total = abs(total_cp)
        temp_coin = Coin.from_cp(abs_total, limit_to_unit="pp")

        for unit in Coin.DENOMINATIONS:
            setattr(self.coin, unit, 0.0)

        for unit in reversed(Coin.DENOMINATIONS):
            if not self.toggles[unit]:
                continue

            value = Coin.CONVERSIONS[unit]
            for lower in Coin.DENOMINATIONS:
                if Coin.CONVERSIONS[lower] >= value:
                    continue
                amount = getattr(temp_coin, lower)
                if amount <= 0:
                    continue

                possible = (amount * Coin.CONVERSIONS[lower]) // value
                if possible:
                    setattr(temp_coin, unit, getattr(temp_coin, unit) + possible)
                    remaining = (amount * Coin.CONVERSIONS[lower]) % value
                    setattr(temp_coin, lower, remaining // Coin.CONVERSIONS[lower])

        for unit in Coin.DENOMINATIONS:
            setattr(self.coin, unit, getattr(temp_coin, unit) * sign)

    def _convert_coin(self):
        self.coin = copy.copy(self.result.coin)
        self.toggles["cp"] = True  # Always enabled.

        changed = True
        while changed:
            changed = False

            for unit, enabled in self.toggles.items():
                if enabled:
                    continue

                amount = getattr(self.coin, unit)
                if abs(amount) > 0:
                    self._downgrade(unit)
                    changed = True
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
